import os
import shutil
import tempfile
from typing import Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

# Correctly import the refactored modules
from backend.app.agents.teacher_agent.ingestion import process_file
from backend.app.agents.teacher_agent.graph import app as teacher_agent_app
from backend.app.utils import db_logger

# Create the FastAPI app
app = FastAPI(
    title="Cook.ai API Server",
    description="API for ingesting documents and generating educational materials.",
)

# --- API Models ---

class IngestResponse(BaseModel):
    unique_content_id: int
    message: str

class GenerateExamRequest(BaseModel):
    unique_content_id: int
    prompt: str
    user_id: int = 1 # Default mock user ID

class GenerateExamResponse(BaseModel):
    job_id: int
    result: Any

# --- API Endpoints ---

@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_document(
    course_id: int = Form(1),
    uploader_id: int = Form(1),
    file: UploadFile = File(...)
):
    """
    Endpoint to ingest a document. This is a teacher-specific action.
    Receives a file, saves it temporarily, and processes it using the ingestion service.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"File '{file.filename}' saved to temporary path: {file_path}")

        # The ingestion process is synchronous but involves I/O.
        # Running it in a thread pool is good practice for an async server.
        unique_content_id = await run_in_threadpool(
            process_file,
            file_path=file_path,
            uploader_id=uploader_id,
            course_id=course_id,
            force_reprocess=False
        )

    if unique_content_id is None:
        raise HTTPException(status_code=500, detail="Failed to process the document.")

    return IngestResponse(
        unique_content_id=unique_content_id,
        message=f"Successfully ingested file '{file.filename}'."
    )

@app.post("/api/generate_exam", response_model=GenerateExamResponse)
async def generate_exam(request: GenerateExamRequest):
    """
    Endpoint to trigger the generation of materials by the Teacher Agent.
    """
    job_id = db_logger.create_job(
        user_id=request.user_id,
        input_prompt=request.prompt,
        workflow_type='api_teacher_agent_generation'
    )
    if not job_id:
        raise HTTPException(status_code=500, detail="Failed to create a generation job.")

    # Input for the teacher_agent graph
    inputs = {
        "job_id": job_id,
        "user_id": request.user_id,
        "user_query": request.prompt,
        "unique_content_id": request.unique_content_id,
        "task_name": "exam_generation", # This would be determined by a router in a more complex system
        "task_parameters": {}
    }

    try:
        # The graph is synchronous, run it in a thread pool
        final_state = await run_in_threadpool(teacher_agent_app.invoke, inputs)

        if final_state.get('error'):
            error_message = f"Generation failed: {final_state.get('error')}"
            db_logger.update_job_status(job_id, 'failed', error_message=error_message)
            raise HTTPException(status_code=500, detail=error_message)
        else:
            db_logger.update_job_status(job_id, 'completed')
            return GenerateExamResponse(
                job_id=job_id,
                result=final_state.get("final_result", [])
            )
    except Exception as e:
        db_logger.update_job_status(job_id, 'failed', error_message=str(e))
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cook.ai API Server. Visit /docs for the API documentation."}

# --- Test Endpoint ---

@app.post("/api/test/ingest_and_generate", response_model=GenerateExamResponse)
async def test_ingest_and_generate(
    prompt: str = Form(...),
    course_id: int = Form(1),
    uploader_id: int = Form(1),
    file: UploadFile = File(...)
):
    """
    **Test Endpoint:** Ingests a document and immediately triggers generation.
    This provides a simple way to test the end-to-end flow.
    """
    # --- Part 1: Ingestion ---
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        unique_content_id = await run_in_threadpool(
            process_file,
            file_path=file_path,
            uploader_id=uploader_id,
            course_id=course_id,
            force_reprocess=True # Force reprocessing for tests
        )

    if unique_content_id is None:
        raise HTTPException(status_code=500, detail="[Test] Failed to process the document during ingestion phase.")

    # --- Part 2: Generation ---
    job_id = db_logger.create_job(
        user_id=uploader_id,
        input_prompt=prompt,
        workflow_type='api_test_ingest_and_generate'
    )
    if not job_id:
        raise HTTPException(status_code=500, detail="[Test] Failed to create a generation job.")

    inputs = {
        "job_id": job_id,
        "user_id": uploader_id,
        "user_query": prompt,
        "unique_content_id": unique_content_id,
        "task_name": "exam_generation",
        "task_parameters": {}
    }

    try:
        final_state = await run_in_threadpool(teacher_agent_app.invoke, inputs)

        if final_state.get('error'):
            error_message = f"[Test] Generation failed: {final_state.get('error')}"
            db_logger.update_job_status(job_id, 'failed', error_message=error_message)
            raise HTTPException(status_code=500, detail=error_message)
        else:
            db_logger.update_job_status(job_id, 'completed')
            return GenerateExamResponse(
                job_id=job_id,
                result=final_state.get("final_result", [])
            )
    except Exception as e:
        db_logger.update_job_status(job_id, 'failed', error_message=str(e))
        raise HTTPException(status_code=500, detail=f"[Test] An unexpected error occurred: {str(e)}")


# To run this server:
# 1. Make sure you are in the root directory of the project (Cook.ai).
# 2. Run the command: uvicorn backend.api_server:app --reload --port 8000
