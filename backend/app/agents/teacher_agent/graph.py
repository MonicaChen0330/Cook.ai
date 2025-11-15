import time
from langgraph.graph import StateGraph, END

from .state import TeacherAgentState
from backend.app.utils import db_logger
from backend.app.agents.teacher_agent.skills.exam_generator.graph import app as exam_generator_app

# This is the new "Teacher Agent" graph.
# It acts as a router to different skills based on the user's request.

def run_skill_node(state: TeacherAgentState) -> TeacherAgentState:
    """
    Routes to and executes the appropriate skill-based sub-graph.
    """
    task_name = state.get("task_name", "exam_generation") # Default to exam generation
    task_id = db_logger.create_task(
        state['job_id'], 
        "teacher_agent_router", 
        "Route user query to a skill.",
        task_input={"user_query": state.get("user_query")}
    )
    start_time = time.perf_counter()

    try:
        if task_name == "exam_generation":
            # Prepare the input for the exam_generator sub-graph
            skill_input = {
                "job_id": state["job_id"],
                "query": state["user_query"],
                "unique_content_id": state["unique_content_id"],
                "parent_task_id": task_id, # Pass the router's task_id as the parent
            }
            
            # Invoke the sub-graph
            final_skill_state = exam_generator_app.invoke(skill_input)

            # Process the output
            if final_skill_state.get("error"):
                raise Exception(f"Exam generator skill failed: {final_skill_state['error']}")
            
            state["final_result"] = final_skill_state.get("final_generated_content")
            # The router's output is the name of the skill it chose
            db_logger.update_task(task_id, 'completed', output=task_name, duration_ms=int((time.perf_counter() - start_time) * 1000))

        else:
            # In the future, you can add more skills here
            # elif task_name == "summary_generation":
            #     ...
            raise NotImplementedError(f"Skill '{task_name}' is not implemented in the Teacher Agent.")

    except Exception as e:
        error_message = str(e)
        state["error"] = error_message
        db_logger.update_task(task_id, 'failed', error_message=error_message, duration_ms=int((time.perf_counter() - start_time) * 1000))

    return state


# Define the graph
workflow = StateGraph(TeacherAgentState)

# Add the single node that runs the selected skill
workflow.add_node("run_skill", run_skill_node)

# Set the entry and end points
workflow.set_entry_point("run_skill")
workflow.add_edge("run_skill", END)

# Compile the graph
app = workflow.compile()
