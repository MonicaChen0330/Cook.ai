from typing import TypedDict, Dict, Any, Optional, List

class TeacherAgentState(TypedDict):
    """
    Represents the state for the main Teacher Agent.
    This state is passed down to the skill-specific sub-graphs.
    """
    # Core identifiers
    job_id: int
    user_id: int
    unique_content_id: int
    
    # User's request
    user_query: str
    
    # Parsed task from a higher-level router (or can be parsed here)
    # For now, we assume the task is 'exam_generation'
    task_name: str
    task_parameters: Dict[str, Any]

    # Final result from the skill sub-graph
    final_result: Any
    error: Optional[str]
    
    # For routing logic
    next_node: Optional[str]
    parent_task_id: Optional[int]
    current_task_id: Optional[int]

    # --- Generator-Critic Fields ---
    critic_feedback: List[Dict[str, Any]] # History of feedback from the critic
    critic_passed: Optional[bool] # Whether the latest critic evaluation passed
    critic_metrics: Optional[Dict[str, Any]] # Latest critic evaluation metrics
    iteration_count: int # Current refinement iteration
    max_iterations: int # Maximum allowed iterations (default: 3)
    workflow_mode: str # 'generator_only', 'fact_critic', 'quality_critic', 'dual_critic'
    final_generated_content: Any # Standardized output from skills for evaluation
