import os
from openai import OpenAI
from typing import List
from .state import ExamGenerationState

# Initialize the OpenAI client
try:
    client = OpenAI()
    print("OpenAI client initialized successfully.")
except Exception as e:
    print(f"Failed to initialize OpenAI client: {e}")
    client = None


def call_openai_api(prompt: str, images: List[str] = None) -> str:
    """Calls the OpenAI API with a multimodal payload (text and optional images)."""
    if not client:
        raise ConnectionError("OpenAI client is not initialized. Please check your API key.")

    message_content = [{"type": "text", "text": prompt}]
    if images:
        for image_uri in images:
            message_content.append({
                "type": "image_url",
                "image_url": {"url": image_uri}
            })

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant expert in creating educational materials."},
            {"role": "user", "content": message_content},
        ]
    )
    return response.choices[0].message.content


def retrieve_chunks_node(state: ExamGenerationState) -> ExamGenerationState:
    """
    Retrieves pre-processed text chunks from the database using unique_content_id.
    This is a mock implementation for now.
    """
    print("Node: retrieve_chunks_node")
    try:
        content_id = state["unique_content_id"]
        print(f"Simulating fetching chunks for unique_content_id: {content_id}")
        
        # In a real implementation, you would query the DOCUMENT_CHUNKS table:
        # from app.database import SessionLocal
        # from app.models import DocumentChunk
        # db = SessionLocal()
        # chunks = db.query(DocumentChunk).filter(DocumentChunk.unique_content_id == content_id).order_by(DocumentChunk.chunk_order).all()
        # retrieved_content = "\n\n".join([chunk.chunk_text for chunk in chunks])
        # db.close()

        # Mock content for demonstration purposes
        mock_content = f"This is the pre-processed and chunked content for document ID {content_id}. " \
                       "It was retrieved from the database, not from a raw file. " \
                       "This new process is much more efficient as it avoids re-reading the file."
        
        state["retrieved_content"] = mock_content
        # TODO: Image handling will also need to be adapted to use the database in the future.
        # For now, we assume no images are retrieved with chunks.
        state["document_images"] = [] 
        state["error"] = None
    except Exception as e:
        state["error"] = f"Failed to retrieve chunks from DB: {str(e)}"
    return state


def generate_multiple_choice_node(state: ExamGenerationState) -> ExamGenerationState:
    """Generates high-quality multiple-choice questions based on provided content."""
    print("Node: generate_multiple_choice_node")
    # TODO: The AI's role/persona could be made configurable by the user in the future.
    prompt = f"""You are a professional university professor (您是一位專業的大學教師) designing an exam. Your task is to generate high-quality multiple-choice questions based on the provided text content and images.

**--- CRITICAL PRINCIPLES ---**
1.  **Must Provide Correct Answer:** Every question must have a clearly indicated correct answer.
2.  **Must Cite Source:** For each question, you MUST specify where the answer can be found (e.g., "Source: Page 5, Paragraph 2" or "Source: Figure 1").
3.  **Language:** All output must be in Traditional Chinese (繁體中文).
4.  **Subject Relevance:** All questions must be strictly relevant to the main subject of the document. Filter out any questions not related to the core professional topic.

**--- INPUTS ---**
- **User Query:** {state['query']}
- **Retrieved Content:**
{state['retrieved_content']}
- **Images:** [Images are provided if available]

**--- OUTPUT FORMAT ---**
Please format your output EXACTLY as follows for each question (do not use markdown code blocks):

[Question Number]. [Question Text]
(A) [Option A]
(B) [Option B]
(C) [Option C]
(D) [Option D]
---
**答案:** [Correct Answer Letter, e.g., A]
**出處:** [Source of the answer, e.g., Page 3, Paragraph 1 or Figure 2]
---
"""
    try:
        state["generated_questions"] = call_openai_api(prompt, state.get("document_images"))
    except Exception as e:
        state["error"] = f"OpenAI API call failed: {str(e)}"
    return state


def generate_short_answer_node(state: ExamGenerationState) -> ExamGenerationState:
    """Generates high-quality short-answer questions based on provided content."""
    print("Node: generate_short_answer_node")
    # TODO: The AI's role/persona could be made configurable by the user in the future.
    prompt = f"""You are a professional university professor (您是一位專業的大學教師) designing an exam. Your task is to generate high-quality short-answer questions based on the provided text content and images.

**--- CRITICAL PRINCIPLES ---**
1.  **Must Provide Answer:** Every question must have a sample correct answer.
2.  **Must Cite Source:** For each question, you MUST specify where the answer can be found (e.g., "Source: Page 5, Paragraph 2" or "Source: Figure 1").
3.  **Language:** All output must be in Traditional Chinese (繁體中文).
4.  **Subject Relevance:** All questions must be strictly relevant to the main subject of the document. Filter out any questions not related to the core professional topic.

**--- INPUTS ---**
- **User Query:** {state['query']}
- **Retrieved Content:**
{state['retrieved_content']}
- **Images:** [Images are provided if available]

**--- OUTPUT FORMAT ---**
Please format your output EXACTLY as follows for each question (do not use markdown code blocks):

[Question Number]. [Question Text]
---
**參考答案:** [A detailed sample answer]
**出處:** [Source of the answer, e.g., Page 3, Paragraph 1 or Figure 2]
---
"""
    try:
        state["generated_questions"] = call_openai_api(prompt, state.get("document_images"))
    except Exception as e:
        state["error"] = f"OpenAI API call failed: {str(e)}"
    return state


def generate_true_false_node(state: ExamGenerationState) -> ExamGenerationState:
    """Generates high-quality true/false questions based on provided content."""
    print("Node: generate_true_false_node")
    # TODO: The AI's role/persona could be made configurable by the user in the future.
    prompt = f"""You are a professional university professor (您是一位專業的大學教師) designing an exam. Your task is to generate high-quality true/false questions based on the provided text content and images.

**--- CRITICAL PRINCIPLES ---**
1.  **Must Provide Correct Answer:** Every question must have a clearly indicated correct answer (True or False).
2.  **Must Cite Source:** For each question, you MUST specify where the answer can be found (e.g., "Source: Page 5, Paragraph 2" or "Source: Figure 1").
3.  **Language:** All output must be in Traditional Chinese (繁體中文).
4.  **Subject Relevance:** All questions must be strictly relevant to the main subject of the document. Filter out any questions not related to the core professional topic.

**--- INPUTS ---**
- **User Query:** {state['query']}
- **Retrieved Content:**
{state['retrieved_content']}
- **Images:** [Images are provided if available]

**--- OUTPUT FORMAT ---**
Please format your output EXACTLY as follows for each question (do not use markdown code blocks):

[Question Number]. [Statement Text]
---
**答案:** [True/False]
**出處:** [Source of the answer, e.g., Page 3, Paragraph 1 or Figure 2]
---
"""
    try:
        state["generated_questions"] = call_openai_api(prompt, state.get("document_images"))
    except Exception as e:
        state["error"] = f"OpenAI API call failed: {str(e)}"
    return state


def handle_error_node(state: ExamGenerationState) -> ExamGenerationState:
    """Handles any errors that occurred during the process."""
    print(f"Node: handle_error_node. Error: {state['error']}")
    return state


def route_generation_task_node(state: ExamGenerationState) -> str:
    """Decides the next step based on errors or the requested question type."""
    print("Node: route_generation_task_node")
    if state["error"]:
        return "handle_error"

    question_type = state.get("question_type")
    if question_type == "multiple_choice":
        return "generate_multiple_choice"
    elif question_type == "short_answer":
        return "generate_short_answer"
    elif question_type == "true_false":
        return "generate_true_false"
    else:
        state["error"] = f"Unsupported question type: {question_type}"
        return "handle_error"