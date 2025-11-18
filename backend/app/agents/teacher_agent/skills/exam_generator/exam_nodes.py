import os
import json
import time
from datetime import datetime # Add this import
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .state import ExamGenerationState
from backend.app.agents.rag_agent import rag_agent
from backend.app.utils import db_logger # Add this import
from backend.app.utils.db_logger import log_task, log_task_sources

# --- Pydantic Models for Tool-based Planning ---
class Task(BaseModel):
    """A single task for generating questions."""
    type: str = Field(..., description="The type of task, e.g., 'multiple_choice', 'short_answer', 'true_false'.")
    count: int = Field(..., description="The number of questions to generate for this task.")
    topic: Optional[str] = Field(None, description="The specific topic for this task, if any.")

class Plan(BaseModel):
    """A structured plan consisting of a list of generation tasks."""
    tasks: List[Task] = Field(..., description="A list of generation tasks to perform based on the user's query.")

# --- Pydantic Models for Question Types ---
class Source(BaseModel):
    page_number: str = Field(..., description="The page number from which the information was sourced.")
    evidence: str = Field(..., description="A brief quote or explanation from the text that supports the answer.")

class MultipleChoiceQuestion(BaseModel):
    question_number: int = Field(..., description="The sequential number of the question.")
    question_text: str = Field(..., description="The text of the multiple-choice question.")
    options: Dict[str, str] = Field(..., description="A dictionary of options, e.g., {'A': 'Option Text A', ...}.")
    correct_answer: str = Field(..., description="The letter corresponding to the correct answer (e.g., 'A', 'B').")
    source: Source = Field(..., description="The source of the answer within the provided document.")

class TrueFalseQuestion(BaseModel):
    question_number: int = Field(..., description="The sequential number of the question.")
    statement_text: str = Field(..., description="The statement to be evaluated as true or false.")
    correct_answer: str = Field(..., description="The correct answer, either 'True' or 'False'.")
    source: Source = Field(..., description="The source of the answer within the provided document.")

class ShortAnswerQuestion(BaseModel):
    question_number: int = Field(..., description="The sequential number of the question.")
    question_text: str = Field(..., description="The text of the short-answer question.")
    sample_answer: str = Field(..., description="A detailed sample correct answer for the question.")
    source: Source = Field(..., description="The source of the answer within the provided document.")

# A model to hold a list of questions for a specific type, for tool calling
class MultipleChoiceQuestionsList(BaseModel):
    questions: List[MultipleChoiceQuestion] = Field(..., description="A list of multiple-choice questions.")

class TrueFalseQuestionsList(BaseModel):
    questions: List[TrueFalseQuestion] = Field(..., description="A list of true/false questions.")

class ShortAnswerQuestionsList(BaseModel):
    questions: List[ShortAnswerQuestion] = Field(..., description="A list of short-answer questions.")


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

@log_task(agent_name="retriever", task_description="Retrieve relevant document chunks using RAG.", input_extractor=lambda state: {"query": state.get("query"), "unique_content_id": state.get("unique_content_id")})
def retrieve_chunks_node(state: ExamGenerationState) -> dict:
    """Retrieves context using RAGAgent and populates the state."""
    try:
        rag_results = rag_agent.search(state["query"], state["unique_content_id"])
        # The decorator has already created the task and injected its ID into the state
        log_task_sources(state["current_task_id"], rag_results["text_chunks"])

        return {
            "retrieved_text_chunks": rag_results["text_chunks"],
            "retrieved_page_content": rag_results["page_content"],
            "generation_plan": [],
            "final_generated_content": [],
            "generation_errors": [],
            "parent_task_id": state["current_task_id"] # Set self as parent for the next node
        }
    except Exception as e:
        return {"error": f"Failed to retrieve context: {str(e)}"}

@log_task(agent_name="plan_generation_tasks", task_description="Analyze user query to create a generation plan.", input_extractor=lambda state: {"query": state.get("query")})
def plan_generation_tasks_node(state: ExamGenerationState) -> dict:
    """Analyzes the user query to create a structured generation plan using an LLM."""
    # This node is not supposed to run if a plan already exists.
    if state.get("generation_plan") or state.get("final_generated_content"):
        return {}

    try:
        llm = get_llm()
        prompt = f"Analyze the user's query to create a step-by-step generation plan.\n\n**User Query:** \"{state['query']}\"\n\nYou must respond by calling the `Plan` tool."
        planner_llm = llm.bind_tools(tools=[Plan], tool_choice="Plan")
        messages = [SystemMessage(content="You are a helpful assistant that creates a structured generation plan."), HumanMessage(content=prompt)]
        
        response = planner_llm.invoke(messages)
        
        if not response.tool_calls:
            raise ValueError("The model did not call the required 'Plan' tool.")
            
        plan = Plan(**response.tool_calls[0]['args'])
        generation_plan = [task.model_dump() for task in plan.tasks]
        
        # --- Extract tokens and cost for the decorator ---
        token_usage = response.response_metadata.get("token_usage", {})
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        model_name = llm.model_name
        pricing = MODEL_PRICING.get(model_name, {"input": 0, "output": 0})
        estimated_cost = ((prompt_tokens / 1_000_000) * pricing["input"]) + ((completion_tokens / 1_000_000) * pricing["output"])

        return {
            "generation_plan": generation_plan,
            "parent_task_id": state["current_task_id"], # Pass self as parent for next nodes
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost_usd": estimated_cost
        }
    except Exception as e:
        error_message = f"Failed to create a generation plan: {e}"
        return {"error": error_message, "generation_errors": [{"task": "plan_generation_tasks", "error_message": str(e)}]}

def prepare_next_task_node(state: ExamGenerationState) -> ExamGenerationState:
    """Pops the next task from the plan and sets it as the current task."""
    state["error"] = None # Clear temporary error for next task
    if state.get("generation_plan") and len(state["generation_plan"]) > 0:
        state["current_task"] = state["generation_plan"].pop(0)
    else:
        state["current_task"] = None
    return state

def should_continue_router(state: ExamGenerationState) -> str:
    """Router that checks the current task and decides where to go next."""
    # If there's a temporary error from the previous task, it's already logged in generation_errors.
    # We want to continue processing other tasks if possible, or go to aggregation.
    current_task = state.get("current_task")
    if current_task:
        task_type = current_task.get("type")
        return f"generate_{task_type}" if task_type in ["multiple_choice", "short_answer", "true_false"] else "end" # Return "end" for aggregation
    return "end" # Go to aggregation if no more tasks

# --- Refactored Generation Logic ---

def _generic_generate_question(state: ExamGenerationState, task_type_name: str) -> dict:
    """
    A generic internal function that handles question generation.
    It is called by the public-facing, decorated node functions.
    It returns a dictionary with results and metrics for the decorator to log.
    """
    current_task = state.get("current_task", {})
    
    try:
        llm = get_llm()
        task_details = f"Task: Generate {current_task.get('count', 1)} {task_type_name.replace('_', ' ')} question(s)"
        if current_task.get('topic'):
            task_details += f" about '{current_task.get('topic')}'"

        combined_retrieved_text, image_data_urls = _prepare_multimodal_content(state["retrieved_page_content"])
        
        system_message_content = "You are a professional university professor (您是一位專業的大學教師) designing an exam. Your task is to generate high-quality questions based on the provided text content and images. You MUST use the provided tool to output the questions."
        
        human_message_content = [
            {"type": "text", "text": f"**--- CRITICAL PRINCIPLES ---**\n"},
            {"type": "text", "text": f"1.  **Must Provide Correct Answer:** Every question must have a clearly indicated correct answer.\n"},
            {"type": "text", "text": f"2.  **Must Cite Source with Evidence:** You MUST include the **Page Number** AND a **brief quote or explanation** from the text that supports why the answer is correct.\n"},
            {"type": "text", "text": f"3.  **Clean and Contextualize the Evidence:** The quoted text must be cleaned. Remove any formatting artifacts (like '○', bullet points, etc.). Ensure it forms a complete, coherent sentence or phrase that provides sufficient context for the answer, even if the question implies part of the context.\n"},
            {"type": "text", "text": f"4.  **Language:** All output must be in Traditional Chinese (繁體中文).\n"},
            {"type": "text", "text": f"5.  **Subject Relevance:** All questions must be strictly relevant to the main subject of the document.\n"},
            {"type": "text", "text": f"\n**--- INPUTS ---**\n"},
            {"type": "text", "text": f"- **Overall User Query:** {state['query']}\n"},
            {"type": "text", "text": f"- **Current Task:** {task_details}\n"},
            {"type": "text", "text": f"- **Retrieved Content:**\n{combined_retrieved_text}\n"},
            {"type": "text", "text": f"- **Images:** [Images are provided if available]\n"}
        ]

        if task_type_name == "multiple_choice":
            human_message_content.append({"type": "text", "text": f"\n**--- MULTIPLE CHOICE SPECIFIC INSTRUCTIONS ---**\n"})
            human_message_content.append({"type": "text", "text": f"For multiple-choice questions, you MUST provide exactly four options (A, B, C, D) for each question. This is CRITICAL. The 'options' field in the tool MUST be a dictionary with keys 'A', 'B', 'C', 'D' and their corresponding text values. DO NOT OMIT THE 'OPTIONS' FIELD. Each question requires the 'options' dictionary with four choices.\n"})
            human_message_content.append({"type": "text", "text": f"\n**--- EXAMPLE MULTIPLE CHOICE QUESTION JSON ---**\n"})
            human_message_content.append({"type": "text", "text": f"```json\n{{\n  \"questions\": [\n    {{\n      \"question_number\": 1,\n      \"question_text\": \"以下哪項是地球上最豐富的氣體？\",\n      \"options\": {{\n        \"A\": \"氧氣\",\n        \"B\": \"氮氣\",\n        \"C\": \"二氧化碳\",\n        \"D\": \"氫氣\"\n      }},\n      \"correct_answer\": \"B\",\n      \"source\": {{\n        \"page_number\": \"10\",\n        \"evidence\": \"地球大氣層約有78%是氮氣。\"\n      }}\n    }}\n  ]\n}}\n```\n"})

        if image_data_urls:
            for image_uri in image_data_urls:
                human_message_content.append({
                    "type": "image_url",
                    "image_url": {"url": image_uri, "detail": "low"}
                })

        messages = [
            SystemMessage(content=system_message_content),
            HumanMessage(content=human_message_content)
        ]

        tool_model_map = {
            "multiple_choice": MultipleChoiceQuestionsList,
            "true_false": TrueFalseQuestionsList,
            "short_answer": ShortAnswerQuestionsList,
        }
        tool_model = tool_model_map.get(task_type_name)
        if not tool_model:
            raise ValueError(f"Unsupported task type: {task_type_name}")

        tool_llm = llm.bind_tools(tools=[tool_model], tool_choice={"type": "function", "function": {"name": tool_model.__name__}})
        response = tool_llm.invoke(messages)
        
        if not response.tool_calls:
            raise ValueError("The model did not call the required tool to generate questions.")
            
        generated_questions_list = tool_model(**response.tool_calls[0]['args'])
        
        final_generated_content = {
            "type": task_type_name,
            "questions": [q.model_dump() for q in generated_questions_list.questions]
        }
        
        token_usage = response.response_metadata.get("token_usage", {})
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        model_name = llm.model_name
        pricing = MODEL_PRICING.get(model_name, {"input": 0, "output": 0})
        estimated_cost = ((prompt_tokens / 1_000_000) * pricing["input"]) + ((completion_tokens / 1_000_000) * pricing["output"])

        # The decorator will handle logging the output.
        # We append to a new list to avoid modifying state directly in a deep way.
        new_final_generated_content = state.get("final_generated_content", []) + [final_generated_content]

        return {
            "final_generated_content": new_final_generated_content,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost_usd": estimated_cost
        }
    except Exception as e:
        error_message = f"Error in {task_type_name} generation: {str(e)}"
        new_generation_errors = state.get("generation_errors", []) + [{"task_type": task_type_name, "error_message": str(e), "task_input": current_task}]
        return {"error": error_message, "generation_errors": new_generation_errors}

@log_task(agent_name="generate_multiple_choice", task_description="Generate multiple choice questions.", input_extractor=lambda state: {"current_task": state.get("current_task")})
def generate_multiple_choice_node(state: ExamGenerationState) -> dict:
    return _generic_generate_question(state, "multiple_choice")

@log_task(agent_name="generate_short_answer", task_description="Generate short answer questions.", input_extractor=lambda state: {"current_task": state.get("current_task")})
def generate_short_answer_node(state: ExamGenerationState) -> dict:
    return _generic_generate_question(state, "short_answer")

@log_task(agent_name="generate_true_false", task_description="Generate true/false questions.", input_extractor=lambda state: {"current_task": state.get("current_task")})
def generate_true_false_node(state: ExamGenerationState) -> dict:
    return _generic_generate_question(state, "true_false")

def handle_error_node(state: ExamGenerationState) -> ExamGenerationState:
    """Handles any errors that occurred during the process."""
    # This error is now logged at the node where it occurred.
    # This node is primarily for graph control flow.
    return state

@log_task(agent_name="aggregate_exam_output", task_description="Aggregating all generated exam content into a final structured output.", input_extractor=lambda state: {"query": state.get("query"), "aggregated_item_count": len(state.get("final_generated_content", []))})
def aggregate_final_output_node(state: ExamGenerationState) -> dict:
    """
    Aggregates all generated content, saves it to the database, and updates the job's final_output_id.
    This node's execution is logged by the @log_task decorator.
    """
    job_id = state['job_id']
    
    try:
        aggregated_output = []
        for content_item in state["final_generated_content"]:
            if isinstance(content_item, dict) and "type" in content_item and "questions" in content_item:
                aggregated_output.append(content_item)
            else:
                aggregated_output.append({"type": "unstructured_content", "content": content_item})

        query_snippet = state['query'][:50] + "..." if len(state['query']) > 50 else state['query']
        generated_title = f"Exam: {query_snippet} ({datetime.now().strftime('%Y-%m-%d')})"

        if state.get("generation_errors"):
            aggregated_output.insert(0, {
                "type": "generation_warnings",
                "message": "Some question types failed to generate. Please check the details below.",
                "errors": state["generation_errors"]
            })
        
        final_json_output = json.dumps(aggregated_output, ensure_ascii=False, indent=2)

        # The decorator has already created the task for this node. We use its ID.
        current_task_id = state["current_task_id"]
        final_content_id = db_logger.save_generated_content(
            current_task_id,
            "final_exam_output",
            generated_title,
            final_json_output
        )

        if final_content_id:
            db_logger.update_job_final_output(job_id, final_content_id)
        else:
            raise Exception("Failed to save final aggregated content.")

        job_status = 'completed'
        if state.get("generation_errors"):
            job_status = 'partial_success' if len(aggregated_output) > 1 else 'failed'
        
        db_logger.update_job_status(job_id, job_status, error_message="Some generation tasks failed." if job_status == 'partial_success' else None)

        # Return the final aggregated content for the decorator to log as this node's output
        return {"final_generated_content": aggregated_output}

    except Exception as e:
        error_message = f"Error aggregating final output: {str(e)}"
        db_logger.update_job_status(job_id, 'failed', error_message=error_message)
        # Return the error for the decorator to log
        return {"error": error_message, "generation_errors": state.get("generation_errors", []) + [{"task": "aggregate_final_output", "error_message": str(e)}]}


def handle_error_node(state: ExamGenerationState) -> ExamGenerationState:
    """Handles any errors that occurred during the process."""
    # This error is now logged at the node where it occurred.
    # This node is primarily for graph control flow.
    return state

def aggregate_final_output_node(state: ExamGenerationState) -> ExamGenerationState:
    """
    Aggregates all generated content (which are now structured JSON objects) into a single
    structured JSON object, saves it to the database, and updates the job's final_output_id.
    Also generates a title for the aggregated content.
    """
    job_id = state['job_id']
    duration_ms = 0 # Initialize duration_ms

    task_id = db_logger.create_task(
        job_id,
        "aggregate_final_output",
        "Aggregating all generated exam content into a final structured output.",
        parent_task_id=state.get("parent_task_id"),
        task_input={"query": state["query"], "aggregated_item_count": len(state["final_generated_content"])}
    )
    start_time = time.perf_counter()

    aggregated_output = []
    
    try:
        for content_item in state["final_generated_content"]:
            # content_item is expected to be a dictionary like {"type": "multiple_choice", "questions": [...]}
            if isinstance(content_item, dict) and "type" in content_item and "questions" in content_item:
                aggregated_output.append(content_item)
            else:
                # Fallback for any unexpected format, though with tool calling, this should be rare
                aggregated_output.append({
                    "type": "unstructured_content",
                    "content": content_item # Store as is if not structured
                })

        # Generate a title for the aggregated content
        # Example: "Exam based on 'User Query' - [Date]"
        query_snippet = state['query'][:50] + "..." if len(state['query']) > 50 else state['query']
        generated_title = f"Exam: {query_snippet} ({datetime.now().strftime('%Y-%m-%d')})"

        # Add generation errors to the aggregated output if any
        if state["generation_errors"]:
            aggregated_output.insert(0, { # Insert at the beginning for prominence
                "type": "generation_warnings",
                "message": "Some question types failed to generate. Please check the details below.",
                "errors": state["generation_errors"]
            })
        
        # Convert the aggregated output to a JSON string
        final_json_output = json.dumps(aggregated_output, ensure_ascii=False, indent=2)

        # Save the final aggregated content to the database
        final_content_id = db_logger.save_generated_content(
            task_id,
            "final_exam_output",
            generated_title,
            final_json_output
        )

        if final_content_id:
            db_logger.update_job_final_output(job_id, final_content_id)
            # Update state with the actual aggregated output (parsed JSON object)
            state["final_generated_content"] = aggregated_output
        else:
            raise Exception("Failed to save final aggregated content.")

        # Determine final job status
        job_status = 'completed'
        if state["generation_errors"]:
            if aggregated_output and len(aggregated_output) > 1: # More than just the warning message
                job_status = 'partial_success'
            else:
                job_status = 'failed'
        
        duration_ms = int((time.perf_counter() - start_time) * 1000) # Define duration_ms here
        db_logger.update_task(task_id, job_status, json.loads(final_json_output), duration_ms=duration_ms)

    except Exception as e:
        state["error"] = f"Error aggregating final output: {str(e)}"
        state["generation_errors"].append({"task": "aggregate_final_output", "error_message": str(e)})
        job_status = 'failed'
        db_logger.update_task(task_id, job_status, error_message=str(e), duration_ms=duration_ms) # Use initialized duration_ms
    
    # Update the main job status based on the overall outcome
    if job_status == 'failed':
        db_logger.update_job_status(job_id, 'failed', error_message=state["error"])
    elif job_status == 'partial_success':
        db_logger.update_job_status(job_id, 'partial_success', error_message="Some generation tasks failed.")
    else:
        db_logger.update_job_status(job_id, 'completed')

    return state