import os
import shutil
import tempfile
from typing import Any, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends, APIRouter
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse # Import RedirectResponse

# Correctly import the refactored modules
from backend.app.agents.teacher_agent.ingestion import process_file
from backend.app.agents.teacher_agent.graph import app as teacher_agent_app
from backend.app.utils import db_logger
from backend.app.utils.db_logger import engine, metadata
from sqlalchemy import Table, select, update

# --- FastAPI App and Routers ---

# Create the FastAPI app
app = FastAPI(
    title="Cook.ai API Server",
    description="API for ingesting documents and generating educational materials.",
)

# Create routers for different categories of endpoints
agent_router = APIRouter(prefix="/api/v1", tags=["Agent Interaction"])
data_management_router = APIRouter(prefix="/api/v1", tags=["Data Management"])
testing_router = APIRouter(prefix="/api/v1/testing", tags=["Development & Testing"])


# --- Add CORS Middleware ---
origins = [
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Models ---

class IngestResponse(BaseModel):
    unique_content_id: int
    file_name: str
    message: str

class ChatRequest(BaseModel):
    unique_content_id: int
    prompt: str
    user_id: int = 1 # Default mock user ID

class ChatResponse(BaseModel):
    job_id: int
    result: Any

class Material(BaseModel):
    id: int
    name: str = Field(alias='file_name')
    unique_content_id: int

class UpdateMaterialRequest(BaseModel):
    name: str

# --- Reflect 'materials' table ---
try:
    materials_table = Table('materials', metadata, autoload_with=engine)
except Exception as e:
    print(f"Error reflecting 'materials' table: {e}")
    materials_table = None

# --- Agent Interaction Endpoint ---

@agent_router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Main endpoint for interacting with the Teacher Agent.
    The agent's graph will route the request to the appropriate skill.
    """
    job_id = db_logger.create_job(
        user_id=request.user_id,
        input_prompt=request.prompt,
        workflow_type='agent_chat'
    )
    if not job_id:
        raise HTTPException(status_code=500, detail="Failed to create a chat job.")

    # Input for the teacher_agent graph.
    # The graph's router node will determine the task based on the user_query.
    inputs = {
        "job_id": job_id,
        "user_id": request.user_id,
        "user_query": request.prompt,
        "unique_content_id": request.unique_content_id,
    }

    try:
        final_state = await run_in_threadpool(teacher_agent_app.invoke, inputs)

        if final_state.get('error'):
            error_message = f"Generation failed: {final_state.get('error')}"
            db_logger.update_job_status(job_id, 'failed', error_message=error_message)
            raise HTTPException(status_code=500, detail=error_message)
        else:
            json_serializable_content = json.loads(json.dumps(final_state.get("final_result", []), ensure_ascii=False))
            return ChatResponse(
                job_id=job_id,
                result=json_serializable_content
            )
    except Exception as e:
        db_logger.update_job_status(job_id, 'failed', error_message=str(e))
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# --- Data Management Endpoints ---

@data_management_router.get("/materials", response_model=List[Material])
async def get_materials(course_id: int):
    """
    Endpoint to get all materials for a given course.
    """
    if materials_table is None:
        raise HTTPException(status_code=500, detail="Database table 'materials' not found.")
    query = select(materials_table).where(materials_table.c.course_id == course_id)
    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            rows = result.fetchall()
            material_list = [{"id": row.id, "file_name": row.file_name, "unique_content_id": row.unique_content_id} for row in rows]
            return material_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

@data_management_router.patch("/materials/{material_id}", status_code=204)
async def update_material_name(material_id: int, request: UpdateMaterialRequest):
    """
    Endpoint to update the name of a material.
    """
    if materials_table is None:
        raise HTTPException(status_code=500, detail="Database table 'materials' not found.")
    stmt = update(materials_table).where(materials_table.c.id == material_id).values(file_name=request.name)
    try:
        with engine.connect() as conn:
            result = conn.execute(stmt)
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"Material with id {material_id} not found.")
            conn.commit()
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database update failed: {e}")

@data_management_router.post("/ingest", response_model=IngestResponse)
async def ingest_document(course_id: int = Form(1), uploader_id: int = Form(1), file: UploadFile = File(...)):
    """
    Endpoint to ingest a document.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
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
        file_name=file.filename,
        message=f"Successfully ingested file '{file.filename}'."
    )

# --- Development & Testing Endpoints ---

@testing_router.post("/generate_exam", response_model=ChatResponse)
async def generate_exam_skill_test(request: ChatRequest):
    """
    **Skill Test Endpoint:** Directly triggers the exam generation flow.
    This bypasses the main agent router for isolated testing of the exam generation skill.
    """
    job_id = db_logger.create_job(
        user_id=request.user_id,
        input_prompt=request.prompt,
        workflow_type='skill_test_generate_exam'
    )
    if not job_id:
        raise HTTPException(status_code=500, detail="Failed to create a generation job.")

    inputs = {
        "job_id": job_id,
        "user_id": request.user_id,
        "user_query": request.prompt,
        "unique_content_id": request.unique_content_id,
        "task_name": "exam_generation", # Hardcoded for direct skill test
        "task_parameters": {}
    }

    try:
        final_state = await run_in_threadpool(teacher_agent_app.invoke, inputs)
        if final_state.get('error'):
            error_message = f"Generation failed: {final_state.get('error')}"
            db_logger.update_job_status(job_id, 'failed', error_message=error_message)
            raise HTTPException(status_code=500, detail=error_message)
        else:
            json_serializable_content = json.loads(json.dumps(final_state.get("final_result", []), ensure_ascii=False))
            return ChatResponse(
                job_id=job_id,
                result=json_serializable_content
            )
    except Exception as e:
        db_logger.update_job_status(job_id, 'failed', error_message=str(e))
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@testing_router.post("/ingest_and_generate", response_model=ChatResponse)
async def test_ingest_and_generate(prompt: str = Form(...), course_id: int = Form(1), uploader_id: int = Form(1), file: UploadFile = File(...)):
    """
    **E2E Test Endpoint:** Ingests a document and immediately triggers generation.
    """
    # Ingestion Part
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        unique_content_id = await run_in_threadpool(process_file, file_path=file_path, uploader_id=uploader_id, course_id=course_id, force_reprocess=True)
    if unique_content_id is None:
        raise HTTPException(status_code=500, detail="[Test] Failed to process the document.")

    # Generation Part
    job_id = db_logger.create_job(user_id=uploader_id, input_prompt=prompt, workflow_type='e2e_test_ingest_and_generate')
    if not job_id:
        raise HTTPException(status_code=500, detail="[Test] Failed to create a job.")
    inputs = {"job_id": job_id, "user_id": uploader_id, "user_query": prompt, "unique_content_id": unique_content_id, "task_name": "exam_generation", "task_parameters": {}}
    try:
        final_state = await run_in_threadpool(teacher_agent_app.invoke, inputs)
        if final_state.get('error'):
            error_message = f"[Test] Generation failed: {final_state.get('error')}"
            db_logger.update_job_status(job_id, 'failed', error_message=error_message)
            raise HTTPException(status_code=500, detail=error_message)
        else:
            db_logger.update_job_status(job_id, 'completed')
            return ChatResponse(job_id=job_id, result=final_state.get("final_generated_content", []))
    except Exception as e:
        db_logger.update_job_status(job_id, 'failed', error_message=str(e))
        raise HTTPException(status_code=500, detail=f"[Test] An unexpected error occurred: {str(e)}")

# --- Root, Health Check, and Router Registration ---

@app.get("/", include_in_schema=False)
def read_root():
    """
    Redirects the root URL to the API documentation.
    """
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["System"])
def health_check():
    """
    A simple health check endpoint that returns the server status.
    """
    return {"status": "ok"}

# Register the routers with the main FastAPI app
app.include_router(agent_router)
app.include_router(data_management_router)
app.include_router(testing_router)

# To run this server:
# 1. Make sure you are in the root directory of the project (Cook.ai).
# 2. Run the command: uvicorn backend.api_server:app --reload --port 8000
