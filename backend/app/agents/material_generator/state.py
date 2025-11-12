
from typing import TypedDict, List, Dict, Any, Optional

class ExamGenerationState(TypedDict):
    """
    Defines the state for the exam generation graph under the new plan-and-execute architecture.
    """
    # Inputs
    query: str
    unique_content_id: int
    
    # This will be deprecated by the plan, but is kept for now.
    question_type: str  

    # --- New Architecture Fields ---
    # Planning state
    generation_plan: List[Dict[str, Any]] # The plan from the LLM router (e.g., [{'type': 'multiple_choice', 'count': 3}])
    current_task: Optional[Dict[str, Any]] # The current task being executed by a generation node
    
    # Retrieval state
    retrieved_text_chunks: List[Dict[str, Any]]  # Lightweight, for debugging and planning
    retrieved_page_content: List[Dict[str, Any]] # Heavyweight, with base64, for generation
    
    # Output state
    final_generated_content: List[str] # Accumulates results from each generation task
    
    error: Optional[str]

