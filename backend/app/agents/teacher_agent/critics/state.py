from typing import TypedDict, List, Dict, Any, Optional

class CriticState(TypedDict):
    """
    Represents the state of the Critic Agent sub-graph.
    """
    # Input
    content: Any # The content to be evaluated (usually List[Dict])
    workflow_mode: str # 'fact_critic', 'quality_critic', 'dual_critic'
    
    # Intermediate results
    fact_score: Optional[float]
    quality_score: Optional[float]
    fact_feedback: List[Dict[str, Any]]
    quality_feedback: List[Dict[str, Any]]
    
    # Output
    final_feedback: List[Dict[str, Any]] # Aggregated feedback
    overall_status: str # 'pass' or 'fail'
