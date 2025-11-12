import os
import json
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

# LangChain imports for LLM wrapping and messaging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .state import ExamGenerationState
from app.agents.rag_agent import rag_agent

# Initialize the LangChain ChatOpenAI model
# This wrapper allows for automatic tracing in LangSmith
try:
    llm = ChatOpenAI(model="gpt-4-turbo")
    print("LangChain ChatOpenAI model initialized successfully.")
except Exception as e:
    print(f"Failed to initialize ChatOpenAI model: {e}")
    llm = None

# --- Pydantic Models for Tool-based Planning ---
class Task(BaseModel):
    """A single task for generating questions."""
    type: str = Field(..., description="The type of task, e.g., 'multiple_choice', 'short_answer', 'true_false'.")
    count: int = Field(..., description="The number of questions to generate for this task.")
    topic: Optional[str] = Field(None, description="The specific topic for this task, if any.")

class Plan(BaseModel):
    """A structured plan consisting of a list of generation tasks."""
    tasks: List[Task] = Field(..., description="A list of generation tasks to perform based on the user's query.")


# --- Node Functions ---

def call_openai_api(prompt: str, images: List[str] = None) -> str:
    """Calls the LLM with a multimodal payload using LangChain's wrapper."""
    if not llm:
        raise ConnectionError("ChatOpenAI model is not initialized. Please check your API key.")

    # LangChain's HumanMessage can handle multimodal content in a list
    message_content = [{"type": "text", "text": prompt}]
    if images:
        for image_uri in images:
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_uri,
                    "detail": "low"
                }
            })
    
    messages = [
        SystemMessage(content="You are a helpful assistant expert in creating educational materials."),
        HumanMessage(content=message_content)
    ]

    response = llm.invoke(messages)
    return response.content

def _prepare_multimodal_content(retrieved_page_content: List[Dict[str, Any]], max_images: int = 5) -> Tuple[str, List[str]]:
    """
    (This is the new, efficient version)
    Prepares content ONLY from structured_page_content.
    """
    combined_text_parts = []
    image_data_urls = []
    image_source_map = []

    if not retrieved_page_content:
        return "", []

    for item in retrieved_page_content:
        if item.get("type") == "structured_page_content":
            page_num = item.get("page_number", "Unknown") 
            
            combined_text_parts.append(f"\n\n--- [START] Source: Page {page_num} ---")
            
            page_content = item.get("content", [])
            for element in page_content:
                if element.get("type") == "text":
                    combined_text_parts.append(element.get("content", ""))
                
                elif element.get("type") == "image" and len(image_data_urls) < max_images:
                    base64_data = element.get("base64")
                    if base64_data:
                        valid_image_url = None
                        if base64_data.startswith("data:image"):
                            valid_image_url = base64_data
                        else:
                            mime_type = element.get("mime_type", "image/jpeg")
                            valid_image_url = f"data:{mime_type};base64,{base64_data}"
                        
                        if valid_image_url:
                            image_data_urls.append(valid_image_url)
                            image_index = len(image_data_urls)
                            combined_text_parts.append(f"\n[Image {image_index} is here. Source: Page {page_num}]\n")
                            image_source_map.append(f"Image {image_index}: Sourced from Page {page_num}")

            combined_text_parts.append(f"--- [END] Source: Page {page_num} ---\n")

    
    final_text = "\n".join(combined_text_parts)
    
    if image_source_map:
        final_text += "\n\n--- Image Source Key ---\n"
        final_text += "\n".join(image_source_map)
        
    return final_text, image_data_urls

def retrieve_chunks_node(state: ExamGenerationState) -> ExamGenerationState:
    """Retrieves context using RAGAgent and populates the state."""
    print("Node: retrieve_chunks_node")
    try:
        rag_results = rag_agent.search(state["query"], state["unique_content_id"])
        state["retrieved_text_chunks"] = rag_results["text_chunks"]
        state["retrieved_page_content"] = rag_results["page_content"]
        state["generation_plan"] = []
        state["final_generated_content"] = []
        state["error"] = None
    except Exception as e:
        state["error"] = f"Failed to retrieve context using RAGAgent: {str(e)}"
    return state

def plan_generation_tasks_node(state: ExamGenerationState) -> ExamGenerationState:
    """
    Analyzes the user query to create a structured generation plan.
    This node is now more efficient as it does not require document context.
    """
    print("Node: plan_generation_tasks_node (Optimized)")

    if state.get("generation_plan") and len(state.get("generation_plan", [])) > 0:
        print("Plan already exists, skipping planning.")
        return state
    if state.get("final_generated_content"):
         return state

    # This prompt now only uses the user's query, making it faster and cheaper.
    prompt = f"""Analyze the user's query to create a step-by-step generation plan.

**User Query:** "{state['query']}"

You must respond by calling the `Plan` tool with the appropriate tasks based on the user's query.
"""
    try:
        # Bind the Pydantic model as a tool for the LLM
        planner_llm = llm.bind_tools(tools=[Plan], tool_choice="Plan")
        
        messages = [
            SystemMessage(content="You are a helpful assistant that creates a structured generation plan based on a user query."),
            HumanMessage(content=prompt)
        ]
        
        response = planner_llm.invoke(messages)
        
        if not response.tool_calls:
            raise ValueError("The model did not call the required 'Plan' tool.")

        tool_call = response.tool_calls[0]
        plan_args = tool_call['args']
        
        # Pydantic validation happens here
        plan = Plan(**plan_args)
        
        state["generation_plan"] = [task.model_dump() for task in plan.tasks]
        print(f"Generated Plan: {state['generation_plan']}")

    except Exception as e:
        state["error"] = f"Failed to create a generation plan: {e}"
        print(f"ERROR in plan_generation_tasks_node: {e}")
        state["generation_plan"] = []
    return state

def prepare_next_task_node(state: ExamGenerationState) -> ExamGenerationState:
    """
    Pops the next task from the plan and sets it as the current task.
    This node is the entry point for the execution loop.
    """
    print("Node: prepare_next_task_node")
    # Clear previous task's error if any, to avoid premature termination
    state["error"] = None
    
    if state.get("generation_plan") and len(state["generation_plan"]) > 0:
        next_task = state["generation_plan"].pop(0)
        state["current_task"] = next_task
        print(f"Preparing to execute next task: {next_task}")
    else:
        print("Generation plan is now empty.")
        state["current_task"] = None # Explicitly set to None
    return state

def should_continue_router(state: ExamGenerationState) -> str:
    """
    Router that checks the current task and decides where to go next.
    This function has NO side effects and only performs routing logic.
    """
    print("Router: should_continue_router")
    if state.get("error"):
        return "handle_error"
    
    current_task = state.get("current_task")
    if current_task:
        task_type = current_task.get("type")
        print(f"Routing to: generate_{task_type}")
        if task_type in ["multiple_choice", "short_answer", "true_false"]:
            return f"generate_{task_type}"
        else:
            # This path should ideally not be taken if planner is correct
            return "handle_error"
    else:
        # No current task, so we end the loop.
        print("Routing to: end")
        return "end"

def generate_multiple_choice_node(state: ExamGenerationState) -> ExamGenerationState:
    """Generates multiple-choice questions for the current task in the plan."""
    print("Node: generate_multiple_choice_node")
    
    # --- DEBUGGING STEP for verification ---
    current_task = state.get("current_task", {})
    print(f"--- VERIFY: Received Current Task in generate_multiple_choice_node: {current_task} ---")
    # --- END DEBUGGING STEP ---

    task_details = f"Task: Generate {current_task.get('count', 1)} multiple choice question(s)"
    if current_task.get('topic'):
        task_details += f" about '{current_task.get('topic')}'"
    combined_retrieved_text, image_data_urls = _prepare_multimodal_content(state["retrieved_page_content"])
    prompt = f"""You are a professional university professor (您是一位專業的大學教師) designing an exam. Your task is to generate high-quality multiple-choice questions based on the provided text content and images.

**--- CRITICAL PRINCIPLES ---**
1.  **Must Provide Correct Answer:** Every question must have a clearly indicated correct answer.
2.  **Must Cite Source:** For each question, you MUST specify where the answer can be found (e.g., "Source: Page 5, Paragraph 2" or "Source: Figure 1").
3.  **Language:** All output must be in Traditional Chinese (繁體中文).
4.  **Subject Relevance:** All questions must be strictly relevant to the main subject of the document.

**--- INPUTS ---**
- **Overall User Query:** {state['query']}
- **Current Task:** {task_details}
- **Retrieved Content:**
{combined_retrieved_text}
- **Images:** [Images are provided if available]

**--- OUTPUT FORMAT ---**
Please format your output EXACTLY as follows for each question (do not use markdown code blocks):

[Question Number]. [Question Text]
(A) [Option A]
(B) [Option B]
(C) [Option C]
(D) [Option D]
---
**答案:** [Correct Answer Letter, e.g., A]
**出處:** [Source of the answer, e.g., Page 3, Paragraph 1 or Figure 2]
---
"""
    try:
        generated_part = call_openai_api(prompt, image_data_urls)
        state["final_generated_content"].append(generated_part)
    except Exception as e:
        state["error"] = f"OpenAI API call failed during multiple_choice generation: {str(e)}"
    return state

def generate_short_answer_node(state: ExamGenerationState) -> ExamGenerationState:
    """Generates short-answer questions for the current task in the plan."""
    print("Node: generate_short_answer_node")
    current_task = state.get("current_task", {})
    task_details = f"Task: Generate {current_task.get('count', 1)} short-answer question(s)"
    if current_task.get('topic'):
        task_details += f" about '{current_task.get('topic')}'"
    combined_retrieved_text, image_data_urls = _prepare_multimodal_content(state["retrieved_page_content"])
    prompt = f"""You are a professional university professor (您是一位專業的大學教師) designing an exam. Your task is to generate high-quality short-answer questions based on the provided text content and images.

**--- CRITICAL PRINCIPLES ---**
1.  **Must Provide Answer:** Every question must have a sample correct answer.
2.  **Must Cite Source:** For each question, you MUST specify where the answer can be found (e.g., "Source: Page 5, Paragraph 2" or "Source: Figure 1").
3.  **Language:** All output must be in Traditional Chinese (繁體中文).
4.  **Subject Relevance:** All questions must be strictly relevant to the main subject of the document.

**--- INPUTS ---**
- **Overall User Query:** {state['query']}
- **Current Task:** {task_details}
- **Retrieved Content:**
{combined_retrieved_text}
- **Images:** [Images are provided if available]

**--- OUTPUT FORMAT ---**
Please format your output EXACTLY as follows for each question (do not use markdown code blocks):

[Question Number]. [Question Text]
---
**參考答案:** [A detailed sample answer]
**出處:** [Source of the answer, e.g., Page 3, Paragraph 1 or Figure 2]
---
"""
    try:
        generated_part = call_openai_api(prompt, image_data_urls)
        state["final_generated_content"].append(generated_part)
    except Exception as e:
        state["error"] = f"OpenAI API call failed during short_answer generation: {str(e)}"
    return state

def generate_true_false_node(state: ExamGenerationState) -> ExamGenerationState:
    """Generates true/false questions for the current task in the plan."""
    print("Node: generate_true_false_node")
    current_task = state.get("current_task", {})
    task_details = f"Task: Generate {current_task.get('count', 1)} true/false question(s)"
    if current_task.get('topic'):
        task_details += f" about '{current_task.get('topic')}'"
    combined_retrieved_text, image_data_urls = _prepare_multimodal_content(state["retrieved_page_content"])
    prompt = f"""You are a professional university professor (您是一位專業的大學教師) designing an exam. Your task is to generate high-quality true/false questions based on the provided text content and images.

**--- CRITICAL PRINCIPLES ---**
1.  **Must Provide Correct Answer:** Every question must have a clearly indicated correct answer (True or False).
2.  **Must Cite Source:** For each question, you MUST specify where the answer can be found (e.g., "Source: Page 5, Paragraph 2" or "Source: Figure 1").
3.  **Language:** All output must be in Traditional Chinese (繁體中文).
4.  **Subject Relevance:** All questions must be strictly relevant to the main subject of the document.

**--- INPUTS ---**
- **Overall User Query:** {state['query']}
- **Current Task:** {task_details}
- **Retrieved Content:**
{combined_retrieved_text}
- **Images:** [Images are provided if available]

**--- OUTPUT FORMAT ---**
Please format your output EXACTLY as follows for each question (do not use markdown code blocks):

[Question Number]. [Statement Text]
---
**答案:** [True/False]
**出處:** [Source of the answer, e.g., Page 3, Paragraph 1 or Figure 2]
---
"""
    try:
        generated_part = call_openai_api(prompt, image_data_urls)
        state["final_generated_content"].append(generated_part)
    except Exception as e:
        state["error"] = f"OpenAI API call failed during true_false generation: {str(e)}"
    return state

def handle_error_node(state: ExamGenerationState) -> ExamGenerationState:
    """Handles any errors that occurred during the process."""
    print(f"Node: handle_error_node. Error: {state['error']}")
    state["generation_plan"] = []
    state["final_generated_content"].append(f"An error occurred: {state['error']}")
    return state