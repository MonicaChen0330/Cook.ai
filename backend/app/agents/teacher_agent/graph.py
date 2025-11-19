import time
import json
from typing import Literal
from pydantic import BaseModel, Field
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from .state import TeacherAgentState
from backend.app.utils import db_logger
from backend.app.utils.db_logger import log_task
# Import helpers from the exam_generator skill
from backend.app.agents.teacher_agent.skills.exam_generator.exam_nodes import get_llm, MODEL_PRICING
from backend.app.agents.teacher_agent.skills.exam_generator.graph import app as exam_generator_app
from backend.app.agents.teacher_agent.skills.general_chat.nodes import general_chat_node
from backend.app.agents.teacher_agent.skills.summarization.graph import app as summarization_app # New import

# --- Pydantic Model for the Router's Tool ---
class Route(BaseModel):
    """Select the next skill to use based on the user's query."""
    next_skill: Literal["exam_generation_skill", "general_chat_skill", "summarization_skill"] = Field(..., description="The name of the skill to use next.") # Updated Literal

# --- Router Node ---

@log_task(agent_name="teacher_agent_router", task_description="Route user query to an appropriate skill.", input_extractor=lambda state: {"user_query": state.get("user_query")})
def router_node(state: TeacherAgentState) -> dict:
    """
    Determines which skill to use based on the user's query using an LLM.
    The logging is handled by the @log_task decorator.
    """
    user_query = state.get("user_query", "")
    
    system_prompt = (
        "You are an expert router agent. Your job is to analyze the user's query and "
        "decide which of the available skills is most appropriate to handle the request. "
        "You must call the `Route` tool to indicate your decision."
    )
    
    skill_descriptions = [
        "## Available Skills:",
        "1. `exam_generation_skill`: Use this skill when the user explicitly asks to create, generate, or make an exam, test, quiz, or questions (e.g., '幫我出5題選擇題', 'generate a test').",
        "2. `summarization_skill`: Use this skill when the user asks to summarize, create an overview, or get the key points of the course material (e.g., '幫我總結這份教材', '給我這份文件的重點').", # New skill description
        "3. `general_chat_skill`: Use this as a fallback for any other query. This includes greetings, general questions, or requests that do not involve generating an exam or summary (e.g., '你好', '你是誰?', 'What can you do?')."
    ]
    
    human_prompt = "\n".join(skill_descriptions) + f"\n\n**User Query:**\n\"{user_query}\""
    
    try:
        llm = get_llm()
        router_llm = llm.bind_tools(tools=[Route], tool_choice="Route")
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
        
        response = router_llm.invoke(messages)
        
        if not response.tool_calls:
            raise ValueError("The router model did not call the required 'Route' tool.")
        
        chosen_route = Route(**response.tool_calls[0]['args'])
        next_node = chosen_route.next_skill
        
        print(f"LLM Router decided: {next_node}")

        token_usage = response.response_metadata.get("token_usage", {})
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        model_name = llm.model_name
        pricing = MODEL_PRICING.get(model_name, {"input": 0, "output": 0})
        estimated_cost = ((prompt_tokens / 1_000_000) * pricing["input"]) + ((completion_tokens / 1_000_000) * pricing["output"])

        return {
            "next_node": next_node,
            "action_taken": f"Routed to {next_node} skill.",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost_usd": estimated_cost
        }

    except Exception as e:
        # Fallback to keyword routing if LLM router fails
        print(f"LLM router failed: {e}. Falling back to keyword routing.")
        exam_keywords = ["exam", "test", "quiz", "考卷", "測驗", "題目"]
        summarize_keywords = ["summarize", "summary", "overview", "總結", "重點", "概述"] # New keywords for fallback
        
        if any(keyword in user_query.lower() for keyword in exam_keywords):
            next_node = "exam_generation_skill"
        elif any(keyword in user_query.lower() for keyword in summarize_keywords): # New fallback condition
            next_node = "summarization_skill"
        else:
            next_node = "general_chat_skill"
        return {"next_node": next_node, "action_taken": f"LLM router failed, falling back to keyword routing. Routed to {next_node} skill.", "error": f"LLM router failed: {e}"}


# --- Conditional Edge Function ---

def should_continue(state: TeacherAgentState) -> str:
    """
    Determines the next node to visit based on the router's decision.
    """
    return state.get("next_node")

# --- Skill Nodes ---

@log_task(agent_name="exam_generation_skill", task_description="Execute the exam generation sub-graph.", input_extractor=lambda state: {"user_query": state.get("user_query"), "unique_content_id": state.get("unique_content_id")})
def exam_skill_node(state: TeacherAgentState) -> dict:
    """
    Executes the exam generation sub-graph.
    The logging is handled by the @log_task decorator.
    """
    try:
        # The decorator injects the current task's ID into the state.
        # We use it as the parent_task_id for the sub-graph we are about to call.
        skill_input = {
            "job_id": state["job_id"],
            "query": state["user_query"],
            "unique_content_id": state["unique_content_id"],
            "parent_task_id": state.get("current_task_id"), 
        }
        final_skill_state = exam_generator_app.invoke(skill_input)

        if final_skill_state.get("error"):
            raise Exception(f"Exam generator skill failed: {final_skill_state['error']}")
        
        final_result = final_skill_state
        return {"final_result": final_result}

    except Exception as e:
        return {"error": str(e)}

@log_task(agent_name="summarization_skill", task_description="Execute the summarization sub-graph.", input_extractor=lambda state: {"user_query": state.get("user_query"), "unique_content_id": state.get("unique_content_id")})
def summarization_skill_node(state: TeacherAgentState) -> dict: # New skill node
    """
    Executes the summarization sub-graph.
    The logging is handled by the @log_task decorator.
    """
    try:
        skill_input = {
            "job_id": state["job_id"],
            "query": state["user_query"],
            "unique_content_id": state["unique_content_id"],
            "parent_task_id": state.get("current_task_id"),
        }
        final_skill_state = summarization_app.invoke(skill_input)

        if final_skill_state.get("error"):
            raise Exception(f"Summarization skill failed: {final_skill_state['error']}")
        
        final_result = final_skill_state
        return {"final_result": final_result}

    except Exception as e:
        return {"error": str(e)}

# --- Final Aggregation Node ---

@log_task(agent_name="aggregate_output", task_description="Final node to aggregate content and finalize job status.", input_extractor=lambda state: {"job_id": state.get("job_id"), "next_node": state.get("next_node"), "error_status": state.get("error")})
def aggregate_output_node(state: TeacherAgentState) -> dict:
    job_id = state['job_id']
    next_node = state.get("next_node")
    final_api_response = {"job_id": job_id}
    
    # Check for critical errors from previous nodes
    if state.get("error"):
        db_logger.update_job_status(job_id, 'failed', error_message=state["error"])
        final_api_response["display_type"] = "text_message"
        final_api_response["content"] = {"message": "Job failed due to a critical error.", "error_details": state["error"]}
        return final_api_response

    final_result = state.get("final_result")

    # Format the final result based on the skill used for DB logging
    db_title = None

    if next_node == "general_chat_skill":
        if final_result and isinstance(final_result, dict) and "content" in final_result:
            final_api_response["display_type"] = "text_message"
            final_api_response["title"] = final_result.get('title', "Cook AI 助教回覆")
            final_api_response["content"] = final_result.get('content')

            db_title = final_result.get("title", "Cook AI 助教回覆")
        else:
            final_api_response["display_type"] = "text_message"
            final_api_response["content"] = {
                "message": "General chat skill executed, but no content was generated.",
                "debug_final_result": str(final_result)
            }
            
    elif next_node == "summarization_skill":
        # final_result is the entire state from the summarization_app.invoke()
        summary_content = final_result.get("final_generated_content")
        
        if (summary_content and isinstance(summary_content, dict) and 
            summary_content.get("type") == "summary" and 
            "title" in summary_content and "sections" in summary_content):
            
            final_api_response["display_type"] = "summary_report"
            final_api_response["title"] = summary_content.get("title", "教材摘要")
            final_api_response["content"] = summary_content.get("sections", [])
            
            db_title = summary_content.get("title", "教材摘要")
        else:
            final_api_response["display_type"] = "text_message"
            final_api_response["content"] = {
                "message": "Summarization skill executed, but the final_result was not in the expected format.",
                "debug_final_result": str(final_result)
            }
            
    elif next_node == "exam_generation_skill":
        main_title = final_result.get("main_title") if isinstance(final_result, dict) else None
        exam_data = final_result.get("final_generated_content") if isinstance(final_result, dict) else final_result
        
        if exam_data and isinstance(exam_data, list) and len(exam_data) > 0:
            final_api_response["display_type"] = "exam_questions"
            final_api_response["title"] = main_title if main_title else f"未命名測驗 ({datetime.now().strftime('%Y-%m-%d')})"
            final_api_response["content"] = exam_data
            
            db_title = main_title if main_title else f"未命名測驗 ({datetime.now().strftime('%Y-%m-%d')})"
        else:
            final_api_response["display_type"] = "text_message"
            final_api_response["content"] = {
                "message": "Exam generation ran, but no content was passed from the skill.",
                "debug_final_result": str(final_result)
            }
            
    else: # Fallback for unknown skills
        final_api_response["display_type"] = "text_message"
        final_api_response["content"] = {"message": f"Unknown skill '{next_node}' executed or no content generated."}

    # 統一資料庫儲存邏輯：儲存完整的 final_api_response
    if db_title and final_api_response.get("display_type") != "text_message":
        try:
            task_id = state.get("current_task_id")
            final_content_type = final_api_response.get("display_type", "unknown")
            
            content_id = None
            if task_id:
                content_id = db_logger.save_generated_content(
                    task_id=task_id,
                    content_type=final_content_type,
                    title=db_title,
                    content=json.dumps(final_api_response, ensure_ascii=False)
                )

            if content_id:
                db_logger.update_job_final_output(job_id, content_id)
            else:
                 print(f"[DB Logger] WARNING: Could not save final content, current_task_id not found or content generation failed.")

        except Exception as e:
            print(f"[DB Logger] ERROR: Failed to save final content for {next_node}. Reason: {e}")
            

    # Update the main job status to completed if it wasn't already failed
    current_job_status = db_logger.get_job_status(job_id)
    if current_job_status not in ['failed', 'partial_success']:
        db_logger.update_job_status(job_id, 'completed')
    
    return {
    "final_result": final_api_response
    }

# --- Graph Definition ---

builder = StateGraph(TeacherAgentState)

# Add the nodes
builder.add_node("router", router_node)
builder.add_node("exam_generation_skill", exam_skill_node)
builder.add_node("general_chat_skill", general_chat_node)
builder.add_node("summarization_skill", summarization_skill_node) # Add new skill node
builder.add_node("aggregate_output", aggregate_output_node)

# Set the entry point
builder.set_entry_point("router")

# Add the conditional edge from the router to the skills
builder.add_conditional_edges(
    "router",
    should_continue,
    {
        "exam_generation_skill": "exam_generation_skill",
        "general_chat_skill": "general_chat_skill",
        "summarization_skill": "summarization_skill", # Add new skill to edges
    },
)

# Add edges from skill nodes to the aggregation node
builder.add_edge("exam_generation_skill", "aggregate_output")
builder.add_edge("general_chat_skill", "aggregate_output")
builder.add_edge("summarization_skill", "aggregate_output") # Add new skill edge

# The aggregation node is the final step
builder.add_edge("aggregate_output", END)

# Compile the graph
app = builder.compile()