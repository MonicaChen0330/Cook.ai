
from typing import TypedDict, List

class ExamGenerationState(TypedDict):
    """Defines the state for the exam generation graph."""
    query: str
    document_path: str
    question_type: str  # e.g., 'multiple_choice', 'short_answer', 'true_false'
    document_content: str
    document_images: List[str] # To hold base64 encoded images from the document
    generated_questions: str # Or you can use List[dict] for structured questions
    error: str | None

