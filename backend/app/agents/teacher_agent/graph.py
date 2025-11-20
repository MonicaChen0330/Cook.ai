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
# TEMPORARILY DISABLED FOR TESTING - Critic integration
# from backend.app.agents.teacher_agent.critics.graph import critic_app # Import Critic Agent
# from backend.app.agents.teacher_agent.critics.state import CriticState # Import Critic State

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
        generated_content = final_skill_state.get("final_generated_content")
        return {"final_result": final_result, "final_generated_content": generated_content}

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
        generated_content = final_skill_state.get("final_generated_content")
        return {"final_result": final_result, "final_generated_content": generated_content}

    except Exception as e:
        return {"error": str(e)}

# --- Critic Node --- TEMPORARILY DISABLED FOR TESTING
# @log_task(agent_name="critic_agent", task_description="Execute the critic sub-graph.", input_extractor=lambda state: {"iteration_count": state.get("iteration_count")})
# async def critic_node(state: TeacherAgentState) -> dict:
#     """
#     Executes the critic sub-graph.
#     """
#     try:
#         # Prepare input for Critic
#         # We need to pass 'content' and 'workflow_mode'
#         # 'final_generated_content' from TeacherState is the content.
        
#         # Check if we have content to criticize
#         content = state.get("final_generated_content")
#         if not content:
#             # If no content, we can't criticize. Skip or error?
#             # For now, return empty feedback which will cause aggregation.
#             return {"critic_feedback": []}
            
#         # Ensure content is in the expected format (List[Dict]) for the critic
#         # If it's a dict (like from exam generator), wrap it or extract.
#         # The exam generator returns a list of dicts (sections) or a dict.
#         # The critic expects a list of items to iterate over.
#         # Let's normalize it here.
        
#         critic_input_content = []
#         if isinstance(content, list):
#             critic_input_content = content
#         elif isinstance(content, dict):
#             # If it's a result dict, try to find the list
#             if "content" in content and isinstance(content["content"], list):
#                 critic_input_content = content["content"]
#             else:
#                 critic_input_content = [content]
        
#         skill_input = {
#             "content": critic_input_content,
#             "workflow_mode": state.get("workflow_mode", "generator_only")
#         }
        
#         final_critic_state = await critic_app.ainvoke(skill_input)
        
#         # Extract feedback
#         final_feedback = final_critic_state.get("final_feedback", [])
#         overall_status = final_critic_state.get("overall_status", "pass")
        
#         # Update Teacher State
#         # We append the feedback to history
#         new_feedback_entry = {
#             "iteration": state.get("iteration_count", 0),
#             "overall_status": overall_status,
#             "feedback_items": final_feedback
#         }
        
#         current_history = state.get("critic_feedback", [])
#         updated_history = current_history + [new_feedback_entry]
        
#         return {
#             "critic_feedback": updated_history,
#             "iteration_count": state.get("iteration_count", 0) + 1
#         }

#     except Exception as e:
#         print(f"Critic failed: {e}")
#         # If critic fails, we shouldn't block the whole flow, just log and proceed?
#         # Or return error.
#         return {"error": f"Critic failed: {str(e)}"}


# --- Conditional Edge for Critic ---

def should_continue_from_critic(state: TeacherAgentState) -> str:
    """
    Decides whether to loop back to the skill (refine) or finish.
    """
    feedback_history = state.get("critic_feedback", [])
    if not feedback_history:
        return "aggregate_output"
        
    latest = feedback_history[-1]
    if latest.get("overall_status") == "pass":
        return "aggregate_output"
        
    # Check iterations
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 3)
    
    if iteration >= max_iter:
        print(f"Max iterations ({max_iter}) reached. Proceeding to aggregation.")
        return "aggregate_output"
        
    # If failed and under limit, go back to the skill that generated the content.
    # We need to know which skill was used.
    # We can use 'next_node' from the state, which holds the last executed skill name (from router).
    # Wait, 'next_node' is updated by the router. 
    # When we come from the skill, 'next_node' might still be the skill name?
    # Actually, the router sets 'next_node'. The skill node doesn't change it.
    # So state['next_node'] should be "exam_generation_skill", etc.
    
    last_skill = state.get("next_node")
    if last_skill in ["exam_generation_skill", "summarization_skill"]:
        return last_skill
        
    return "aggregate_output"


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
# TEMPORARILY DISABLED - Critic node
# builder.add_node("critic_node", critic_node) # Add critic node
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

# TEMPORARILY DISABLED - Critic integration (originally edges to critic_node)
# Add edges from skill nodes directly to aggregate for testing
builder.add_edge("exam_generation_skill", "aggregate_output")  # TEMP: Skip critic
builder.add_edge("general_chat_skill", "aggregate_output")
builder.add_edge("summarization_skill", "aggregate_output")  # TEMP: Skip critic

# CRITIC EDGES COMMENTED OUT FOR TESTING:
# builder.add_edge("exam_generation_skill", "critic_node")
# builder.add_edge("summarization_skill", "critic_node")
# builder.add_conditional_edges(
#     "critic_node",
#     should_continue_from_critic,
#     {
#         "aggregate_output": "aggregate_output",
#         "exam_generation_skill": "exam_generation_skill",
#         "summarization_skill": "summarization_skill"
#     }
# )

# The aggregation node is the final step
builder.add_edge("aggregate_output", END)

# Compile the graph
app = builder.compile()