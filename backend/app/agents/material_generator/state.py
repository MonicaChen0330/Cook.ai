
from typing import TypedDict, List

class ExamGenerationState(TypedDict):
    """Defines the state for the exam generation graph."""
    # Inputs
    query: str
    unique_content_id: int # New input: ID for the content to be processed
    question_type: str  # e.g., 'multiple_choice', 'short_answer', 'true_false'
    
    # Internal state
    retrieved_content: str # Renamed from document_content
    document_images: List[str] # To hold base64 encoded images from the document
    
    # Outputs
    generated_questions: str # Or you can use List[dict] for structured questions
    error: str | None

