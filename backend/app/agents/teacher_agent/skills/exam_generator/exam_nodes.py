import os
import json
import time
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .state import ExamGenerationState
from backend.app.agents.rag_agent import rag_agent
from backend.app.utils import db_logger

# --- Pydantic Models for Tool-based Planning ---
class Task(BaseModel):
    """A single task for generating questions."""
    type: str = Field(..., description="The type of task, e.g., 'multiple_choice', 'short_answer', 'true_false'.")
    count: int = Field(..., description="The number of questions to generate for this task.")
    topic: Optional[str] = Field(None, description="The specific topic for this task, if any.")

class Plan(BaseModel):
    """A structured plan consisting of a list of generation tasks."""
    tasks: List[Task] = Field(..., description="A list of generation tasks to perform based on the user's query.")


# --- Pricing Info ---
# Prices per 1 million tokens in USD
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 5.00, "output": 15.00},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
}


# --- Helper Functions ---

def get_llm() -> ChatOpenAI:
    """Initializes the ChatOpenAI model."""
    model_name = os.getenv("GENERATOR_MODEL", "gpt-4o-mini")
    # Note: To see verbose output from LangChain, you can add `verbose=True`
    return ChatOpenAI(model=model_name)

def call_openai_api(llm: ChatOpenAI, prompt: str, images: List[str] = None) -> Any:
    """Calls the LLM with a multimodal payload and returns the full response object."""
    message_content = [{"type": "text", "text": prompt}]
    if images:
        for image_uri in images:
            message_content.append({
                "type": "image_url",
                "image_url": {"url": image_uri, "detail": "low"}
            })
    
    messages = [
        SystemMessage(content="You are a helpful assistant expert in creating educational materials."),
        HumanMessage(content=message_content)
    ]
    response = llm.invoke(messages)
    return response

def _prepare_multimodal_content(retrieved_page_content: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
    """Prepares content from structured page content for the LLM."""
    max_images = int(os.getenv("MAX_IMAGES_PER_PROMPT", "5"))
    combined_text_parts, image_data_urls, image_source_map = [], [], []

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
                        mime_type = element.get("mime_type", "image/jpeg")
                        valid_image_url = f"data:{mime_type};base64,{base64_data}" if not base64_data.startswith("data:") else base64_data
                        image_data_urls.append(valid_image_url)
                        image_index = len(image_data_urls)
                        combined_text_parts.append(f"\n[Image {image_index} is here. Source: Page {page_num}]\n")
                        image_source_map.append(f"Image {image_index}: Sourced from Page {page_num}")
            combined_text_parts.append(f"--- [END] Source: Page {page_num} ---\n")

    final_text = "\n".join(combined_text_parts)
    if image_source_map:
        final_text += "\n\n--- Image Source Key ---\n" + "\n".join(image_source_map)
    return final_text, image_data_urls

# --- Node Functions ---

def retrieve_chunks_node(state: ExamGenerationState) -> ExamGenerationState:
    """Retrieves context using RAGAgent and populates the state."""
    task_id = db_logger.create_task(
        state['job_id'], 
        "retriever", 
        "Retrieve relevant document chunks using RAG.",
        task_input={"query": state["query"], "unique_content_id": state["unique_content_id"]},
        parent_task_id=state.get("parent_task_id") # Use the ID passed from the parent graph
    )
    state["parent_task_id"] = task_id # Set self as parent for the next node in this sub-graph
    start_time = time.perf_counter()
    try:
        rag_results = rag_agent.search(state["query"], state["unique_content_id"])
        state["retrieved_text_chunks"] = rag_results["text_chunks"]
        state["retrieved_page_content"] = rag_results["page_content"]
        
        # Log the retrieved sources to the database
        db_logger.log_task_sources(task_id, rag_results["text_chunks"])

        state["generation_plan"], state["final_generated_content"], state["error"] = [], [], None
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        db_logger.update_task(task_id, 'completed', f"Retrieved {len(rag_results['text_chunks'])} chunks.", duration_ms=duration_ms)
    except Exception as e:
        state["error"] = f"Failed to retrieve context: {str(e)}"
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        db_logger.update_task(task_id, 'failed', error_message=str(e), duration_ms=duration_ms)
    return state

def plan_generation_tasks_node(state: ExamGenerationState) -> ExamGenerationState:
    """Analyzes the user query to create a structured generation plan."""
    if state.get("generation_plan") or state.get("final_generated_content"):
        return state
    
    try:
        # This node uses an LLM, so we get it here to log its details
        llm = get_llm()
        model_params = {"temperature": llm.temperature}

        task_id = db_logger.create_task(
            state['job_id'], 
            "plan_generation_tasks", 
            "Analyze user query to create a generation plan.",
            parent_task_id=state.get("parent_task_id"),
            model_name=llm.model_name,
            model_parameters=model_params
        )
        state["parent_task_id"] = task_id # Become the parent for all subsequent generation tasks
        start_time = time.perf_counter()

        prompt = f"Analyze the user's query to create a step-by-step generation plan.\n\n**User Query:** \"{state['query']}\"\n\nYou must respond by calling the `Plan` tool."
        planner_llm = llm.bind_tools(tools=[Plan], tool_choice="Plan")
        messages = [SystemMessage(content="You are a helpful assistant that creates a structured generation plan."), HumanMessage(content=prompt)]
        response = planner_llm.invoke(messages)
        
        if not response.tool_calls:
            raise ValueError("The model did not call the required 'Plan' tool.")
            
        plan = Plan(**response.tool_calls[0]['args'])
        state["generation_plan"] = [task.model_dump() for task in plan.tasks]
        
        # --- Log tokens and cost for the planner ---
        prompt_tokens = response.response_metadata.get("token_usage", {}).get("prompt_tokens", 0)
        completion_tokens = response.response_metadata.get("token_usage", {}).get("completion_tokens", 0)
        model_name = llm.model_name
        pricing = MODEL_PRICING.get(model_name, {"input": 0, "output": 0})
        estimated_cost = ((prompt_tokens / 1_000_000) * pricing["input"]) + ((completion_tokens / 1_000_000) * pricing["output"])

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        db_logger.update_task(
            task_id, 
            'completed', 
            str(state["generation_plan"]), 
            duration_ms=duration_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost_usd=estimated_cost
        )
    except Exception as e:
        state["error"] = f"Failed to create a generation plan: {e}"
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        db_logger.update_task(task_id, 'failed', error_message=str(e), duration_ms=duration_ms)
    return state

def prepare_next_task_node(state: ExamGenerationState) -> ExamGenerationState:
    """Pops the next task from the plan and sets it as the current task."""
    state["error"] = None
    if state.get("generation_plan") and len(state["generation_plan"]) > 0:
        state["current_task"] = state["generation_plan"].pop(0)
    else:
        state["current_task"] = None
    return state

def should_continue_router(state: ExamGenerationState) -> str:
    """Router that checks the current task and decides where to go next."""
    if state.get("error"): return "handle_error"
    current_task = state.get("current_task")
    if current_task:
        task_type = current_task.get("type")
        return f"generate_{task_type}" if task_type in ["multiple_choice", "short_answer", "true_false"] else "handle_error"
    return "end"

# --- Refactored Generation Logic ---

MC_PROMPT_TEMPLATE = """You are a professional university professor (您是一位專業的大學教師) designing an exam. Your task is to generate high-quality multiple-choice questions based on the provided text content and images.

**--- CRITICAL PRINCIPLES ---**
1.  **Must Provide Correct Answer:** Every question must have a clearly indicated correct answer.
2.  **Must Cite Source with Evidence:** DO NOT just provide the page number. You MUST include the **Page Number** AND a **brief quote or explanation** from the text that supports why the answer is correct.
    - **Wrong Example:** "**出處:** 第 5 頁"
    - **Correct Example:** "**出處:** 第 5 頁，文中提到 '粒線體是細胞的發電廠'。"
3.  **Clean and Contextualize the Evidence:** The quoted text must be cleaned. Remove any formatting artifacts (like '○', bullet points, etc.). Ensure it forms a complete, coherent sentence or phrase that provides sufficient context for the answer, even if the question implies part of the context.
4.  **Language:** All output must be in Traditional Chinese (繁體中文).
5.  **Subject Relevance:** All questions must be strictly relevant to the main subject of the document.

**--- INPUTS ---**
- **Overall User Query:** {query}
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
**出處:** [Page Number], [佐證該答案的關鍵原文或理由]
---
"""

SA_PROMPT_TEMPLATE = """You are a professional university professor (您是一位專業的大學教師) designing an exam. Your task is to generate high-quality short-answer questions based on the provided text content and images.

**--- CRITICAL PRINCIPLES ---**
1.  **Must Provide Answer:** Every question must have a sample correct answer.
2.  **Must Cite Source with Evidence:** DO NOT just provide the page number. You MUST include the **Page Number** AND a **brief quote or explanation** from the text that supports why the answer is correct.
    - **Wrong Example:** "**出處:** 第 5 頁"
    - **Correct Example:** "**出處:** 第 5 頁，文中提到 '粒線體是細胞的發電廠'。"
3.  **Clean and Contextualize the Evidence:** The quoted text must be cleaned. Remove any formatting artifacts (like '○', bullet points, etc.). Ensure it forms a complete, coherent sentence or phrase that provides sufficient context for the answer, even if the question implies part of the context.
4.  **Language:** All output must be in Traditional Chinese (繁體中文).
5.  **Subject Relevance:** All questions must be strictly relevant to the main subject of the document.

**--- INPUTS ---**
- **Overall User Query:** {query}
- **Current Task:** {task_details}
- **Retrieved Content:**
{combined_retrieved_text}
- **Images:** [Images are provided if available]

**--- OUTPUT FORMAT ---**
Please format your output EXACTLY as follows for each question (do not use markdown code blocks):

[Question Number]. [Question Text]
---
**參考答案:** [A detailed sample answer]
**出處:** [Page Number], [佐證該答案的關鍵原文或理由]
---
"""

TF_PROMPT_TEMPLATE = """You are a professional university professor (您是一位專業的大學教師) designing an exam. Your task is to generate high-quality true/false questions based on the provided text content and images.

**--- CRITICAL PRINCIPLES ---**
1.  **Must Provide Correct Answer:** Every question must have a clearly indicated correct answer (True or False).
2.  **Must Cite Source with Evidence:** DO NOT just provide the page number. You MUST include the **Page Number** AND a **brief quote or explanation** from the text that supports why the answer is True or False.
    - **Wrong Example:** "**出處:** 第 17 頁"
    - **Correct Example:** "**出處:** 第 17 頁，文中提到正規化是將數值縮放到 [0, 1] 區間。"
3.  **Clean and Contextualize the Evidence:** The quoted text must be cleaned. Remove any formatting artifacts (like '○', bullet points, etc.). Ensure it forms a complete, coherent sentence or phrase that provides sufficient context for the answer, even if the question implies part of the context.
4.  **Language:** All output must be in Traditional Chinese (繁體中文).
5.  **Subject Relevance:** All questions must be strictly relevant to the main subject of the document.

**--- INPUTS ---**
- **Overall User Query:** {query}
- **Current Task:** {task_details}
- **Retrieved Content:**
{combined_retrieved_text}
- **Images:** [Images are provided if available]

**--- OUTPUT FORMAT ---**
Please format your output EXACTLY as follows for each question (do not use markdown code blocks):

[Question Number]. [Statement Text]
---
**答案:** [True/False]
**出處:** [Page Number], [佐證該答案的關鍵原文或理由]
---
"""

def _generic_generate_question(state: ExamGenerationState, prompt_template: str, task_type_name: str) -> ExamGenerationState:
    """A generic function that handles question generation for a given task type."""
    current_task = state.get("current_task", {})
    
    # Get LLM details here to log them at task creation
    llm = get_llm()
    model_params = {"temperature": llm.temperature}

    task_id = db_logger.create_task(
        state['job_id'], 
        f"generate_{task_type_name}", 
        f"Generate {task_type_name} questions.",
        parent_task_id=state.get("parent_task_id"),
        task_input=current_task,
        model_name=llm.model_name,
        model_parameters=model_params
    )
    start_time = time.perf_counter()
    try:
        task_details = f"Task: Generate {current_task.get('count', 1)} {task_type_name.replace('_', ' ')} question(s)"
        if current_task.get('topic'):
            task_details += f" about '{current_task.get('topic')}'"

        combined_retrieved_text, image_data_urls = _prepare_multimodal_content(state["retrieved_page_content"])
        final_prompt = prompt_template.format(query=state['query'], task_details=task_details, combined_retrieved_text=combined_retrieved_text)
        
        response = call_openai_api(llm, final_prompt, image_data_urls)
        generated_part = response.content
        state["final_generated_content"].append(generated_part)
        
        # --- Log tokens and cost ---
        token_usage = response.response_metadata.get("token_usage", {})
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        
        model_name = llm.model_name
        pricing = MODEL_PRICING.get(model_name, {"input": 0, "output": 0})
        estimated_cost = ((prompt_tokens / 1_000_000) * pricing["input"]) + ((completion_tokens / 1_000_000) * pricing["output"])

        # Save the generated content to the database
        title = f"Generated {current_task.get('count', 1)} {task_type_name.replace('_', ' ')} questions"
        db_logger.save_generated_content(task_id, task_type_name, title, generated_part)
        
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        db_logger.update_task(
            task_id, 
            'completed', 
            generated_part, 
            duration_ms=duration_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost_usd=estimated_cost
        )
    except Exception as e:
        state["error"] = f"Error in {task_type_name} generation: {str(e)}"
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        db_logger.update_task(task_id, 'failed', error_message=str(e), duration_ms=duration_ms)
    return state

def generate_multiple_choice_node(state: ExamGenerationState) -> ExamGenerationState:
    return _generic_generate_question(state, MC_PROMPT_TEMPLATE, "multiple_choice")

def generate_short_answer_node(state: ExamGenerationState) -> ExamGenerationState:
    return _generic_generate_question(state, SA_PROMPT_TEMPLATE, "short_answer")

def generate_true_false_node(state: ExamGenerationState) -> ExamGenerationState:
    return _generic_generate_question(state, TF_PROMPT_TEMPLATE, "true_false")

def handle_error_node(state: ExamGenerationState) -> ExamGenerationState:
    """Handles any errors that occurred during the process."""
    # This error is now logged at the node where it occurred.
    # This node is primarily for graph control flow.
    return state