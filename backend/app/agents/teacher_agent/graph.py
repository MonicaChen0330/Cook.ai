import time
import json
from typing import Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from .state import TeacherAgentState
from backend.app.utils import db_logger
from backend.app.utils.db_logger import log_task
# Import helpers from the exam_generator skill
from backend.app.agents.teacher_agent.skills.exam_generator.exam_nodes import get_llm, MODEL_PRICING
from backend.app.agents.teacher_agent.skills.exam_generator.graph import app as exam_generator_app
from backend.app.agents.teacher_agent.skills.general_chat.nodes import general_chat_node

# --- Pydantic Model for the Router's Tool ---
class Route(BaseModel):
    """Select the next skill to use based on the user's query."""
    next_skill: Literal["exam_generation_skill", "general_chat_skill"] = Field(..., description="The name of the skill to use next.")

# --- Router Node ---

@log_task(agent_name="agent_router", task_description="Route user query to an appropriate skill.")
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
        "2. `general_chat_skill`: Use this as a fallback for any other query. This includes greetings, general questions, or requests that do not involve generating an exam (e.g., '你好', '你是誰?', 'What can you do?')."
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
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost_usd": estimated_cost
        }

    except Exception as e:
        # Fallback to keyword routing if LLM router fails
        print(f"LLM router failed: {e}. Falling back to keyword routing.")
        exam_keywords = ["exam", "test", "quiz", "考卷", "測驗", "題目"]
        if any(keyword in user_query.lower() for keyword in exam_keywords):
            next_node = "exam_generation_skill"
        else:
            next_node = "general_chat_skill"
        return {"next_node": next_node, "error": f"LLM router failed: {e}"}


# --- Conditional Edge Function ---

def should_continue(state: TeacherAgentState) -> str:
    """
    Determines the next node to visit based on the router's decision.
    """
    return state.get("next_node")

# --- Skill Nodes ---

@log_task(agent_name="exam_generation_skill", task_description="Execute the exam generation sub-graph.")
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
        
        final_result = final_skill_state.get("final_generated_content")
        return {"final_result": final_result}

    except Exception as e:
        return {"error": str(e)}

# --- Final Aggregation Node ---

def aggregate_output_node(state: TeacherAgentState) -> dict:
    """
    Final node to update the main job status and save content if necessary.
    """
    job_id = state['job_id']
    
    if state.get("error"):
        db_logger.update_job_status(job_id, 'failed', error_message=state["error"])
        return {}

    # If the general chat skill ran, its output needs to be saved.
    # The exam generator skill saves its own content within its sub-graph.
    if state.get("next_node") == "general_chat_skill":
        final_result = state.get("final_result")
        if final_result:
            try:
                # Save the chat response to the generated_contents table
                content_id = db_logger.save_generated_content(
                    task_id=state["current_task_id"],
                    content_type="message",
                    title="AI Assistant Response",
                    content=json.dumps(final_result, ensure_ascii=False)
                )
                if content_id:
                    db_logger.update_job_final_output(job_id, content_id)
            except Exception as e:
                # If saving fails, log it but don't fail the whole job
                print(f"Error saving general chat content: {e}")

    # Mark the job as completed
    db_logger.update_job_status(job_id, 'completed')
    return {}

# --- Graph Definition ---

builder = StateGraph(TeacherAgentState)

# Add the nodes
builder.add_node("router", router_node)
builder.add_node("exam_generation_skill", exam_skill_node)
builder.add_node("general_chat_skill", general_chat_node)
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
    },
)

# Add edges from skill nodes to the aggregation node
builder.add_edge("exam_generation_skill", "aggregate_output")
builder.add_edge("general_chat_skill", "aggregate_output")

# The aggregation node is the final step
builder.add_edge("aggregate_output", END)

# Compile the graph
app = builder.compile()
