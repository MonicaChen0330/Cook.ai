from backend.app.agents.teacher_agent.state import TeacherAgentState
from backend.app.utils.db_logger import log_task

@log_task(agent_name="general_chat_skill", task_description="Provide a fallback response for an unhandled user query.")
def general_chat_node(state: TeacherAgentState) -> dict:
    """
    A fallback node that provides a default response when no other skill can handle the request.
    The logging is handled by the @log_task decorator.
    """
    final_result = {
        "type": "message",
        "content": "我是一位 AI 教學助理，請您先上傳知識參考資料，我將根據您的資料生成教材。"
    }
    
    return {"final_result": final_result}

