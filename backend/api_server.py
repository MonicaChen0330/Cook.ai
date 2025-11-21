import os
import shutil
import tempfile
import time
from typing import Any, List, Optional
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
    "http://140.115.54.162:3001",
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
            api_response_payload = final_state.get("final_result")

            if not isinstance(api_response_payload, dict):
                 raise HTTPException(status_code=500, detail="Final result payload structure missing or invalid.")

            json_serializable_content = json.loads(json.dumps(api_response_payload, ensure_ascii=False))
            
            if 'job_id' in json_serializable_content:
                del json_serializable_content['job_id']
            
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

# --- Quality Critic Testing Endpoints ---

class EvaluateExamRequest(BaseModel):
    """
    Request model for evaluating exam from generation API response.
    
    Accepts the direct output from exam generation API:
    {
        "type": "exam_questions",
        "title": "...",
        "job_id": 266,
        "content": [
            {
                "type": "multiple_choice" | "short_answer" | "true_false" | ...,
                "questions": [...]
            }
        ],
        "display_type": "exam_questions"
    }
    """
    # Accept the entire generation response (all fields optional except content)
    type: Optional[str] = None
    title: Optional[str] = None
    job_id: Optional[int] = None
    content: List[dict]  # Required - contains the actual exam content
    display_type: Optional[str] = None
    rag_content: Optional[str] = None  # Optional RAG context

class EvaluateSingleQuestionRequest(BaseModel):
    """Request model for evaluating a single question."""
    question: dict
    rag_content: str = None

@testing_router.post("/critic/evaluate_exam")
async def evaluate_exam_endpoint(request: EvaluateExamRequest):
    """
    **Quality Critic Test Endpoint:** Evaluate an entire exam.
    
    Accepts direct output from exam generation API.
    
    Example request body (from generation API):
    {
        "type": "exam_questions",
        "title": "生成簡答題的計畫",
        "job_id": 266,
        "content": [
            {
                "type": "short_answer",
                "questions": [
                    {
                        "question_number": 1,
                        "question_text": "...",
                        "sample_answer": "...",
                        "source": {"page_number": "...", "evidence": "..."}
                    }
                ]
            }
        ],
        "display_type": "exam_questions",
        "rag_content": "Optional RAG context..."
    }
    
    Supports all question types: multiple_choice, short_answer, true_false, etc.
    """
    try:
        from backend.app.agents.teacher_agent.critics.quality_critic import QualityCritic
        from backend.app.agents.teacher_agent.skills.exam_generator.exam_nodes import get_llm
        
        # Extract the actual exam content from the generation response
        if not request.content or len(request.content) == 0:
            raise HTTPException(status_code=400, detail="No content found in exam")
        
        # Get the first content item (usually there's only one)
        exam_content = request.content[0]
        
        # Validate structure
        if "questions" not in exam_content:
            raise HTTPException(status_code=400, detail="No questions found in content")
        
        # Prepare exam in the format expected by QualityCritic
        exam = {
            "type": exam_content.get("type", "unknown"),  # multiple_choice, short_answer, etc.
            "questions": exam_content["questions"]
        }
        
        llm = get_llm()
        critic = QualityCritic(llm, threshold=4.0)
        
        result = await critic.evaluate_exam(
            exam=exam,
            rag_content=request.rag_content
        )
        
        # Add metadata from generation response
        result["exam_metadata"] = {
            "title": request.title,
            "job_id": request.job_id,
            "question_type": exam_content.get("type")
        }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@testing_router.post("/critic/evaluate_single_question")
async def evaluate_single_question_endpoint(request: EvaluateSingleQuestionRequest):
    """
    **Quality Critic Test Endpoint:** Evaluate a single question.
    
    Example request body:
    {
        "question": {
            "question_number": 1,
            "question_text": "...",
            "sample_answer": "..." (for short_answer),
            OR
            "options": {"A": "...", "B": "..."} (for multiple_choice),
            "correct_answer": "A",
            "source": {"page_number": "...", "evidence": "..."}
        },
        "rag_content": "Optional educational material context..."
    }
    """
    try:
        from backend.app.agents.teacher_agent.critics.quality_critic import QualityCritic
        from backend.app.agents.teacher_agent.skills.exam_generator.exam_nodes import get_llm
        
        llm = get_llm()
        critic = QualityCritic(llm, threshold=4.0)
        
        result = await critic.evaluate_single_question(
            question=request.question,
            rag_content=request.rag_content
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

# --- Quality Critic: Evaluate by Job ID (Database Integration) ---

class EvaluateByJobRequest(BaseModel):
    """Request model for evaluating exam by job_id from database."""
    job_id: int = Field(..., description="Job ID from ORCHESTRATION_JOBS table")
    mode: str = Field("quick", description="Evaluation mode: 'quick' (overall only) or 'comprehensive' (full analysis)")

@testing_router.post("/critic/evaluate_by_job")
async def evaluate_by_job_endpoint(request: EvaluateByJobRequest):
    """
    **Quality Critic Endpoint:** Evaluate generated content by job_id with mode selection.
    
    Modes:
    - quick: Overall evaluation only (cost-effective, default)
    - comprehensive: Overall + per-question + statistics (full analysis)
    
    Automatically fetches:
    1. Generated content from GENERATED_CONTENTS
    2. RAG chunks from DOCUMENT_CHUNKS (via retriever agent tasks)
    
    Example:
    {
        "job_id": 268,
        "mode": "quick"
    }
    
    Note: Evaluation results are automatically saved to database.
    """
    import time
    import json
    start_time = time.time()
    
    try:
        from backend.app.agents.teacher_agent.critics.quality_critic import QualityCritic
        from backend.app.agents.teacher_agent.skills.exam_generator.exam_nodes import get_llm
        from backend.app.agents.teacher_agent.critics.critic_db_utils import (
            get_generated_content_by_job_id,
            get_rag_chunks_by_job_id,
            save_evaluation_to_db
        )
        from backend.app.agents.teacher_agent.critics.critic_formatters import EvaluationFormatter
        
        # Step 1: Get generated content
        content_data = get_generated_content_by_job_id(request.job_id)
        if not content_data:
            raise HTTPException(status_code=404, detail=f"No content found for job_id {request.job_id}")
        
        # Step 2: Parse and merge all question types
        content = content_data["content"]
        all_questions = []
        
        if isinstance(content, dict) and "content" in content:
            exam_data = content["content"]
            if isinstance(exam_data, list):
                for question_block in exam_data:
                    all_questions.extend(question_block.get("questions", []))
        elif isinstance(content, list):
            for question_block in content:
                all_questions.extend(question_block.get("questions", []))
        elif isinstance(content, dict) and "questions" in content:
            all_questions = content["questions"]
        
        if not all_questions:
            raise HTTPException(status_code=400, detail="No questions found in content")
        
        # Renumber questions globally
        for idx, q in enumerate(all_questions, start=1):
            q["question_number"] = idx
        
        exam = {
            "type": "exam",
            "questions": all_questions
        }
        
        # Step 3: Get RAG context (using job_id to find retriever tasks)
        rag_chunks = get_rag_chunks_by_job_id(request.job_id, limit=10)
        rag_content = None
        if rag_chunks:
            combined = [f"[頁 {c.get('metadata', {}).get('page_number', '?')}] {c['chunk_text']}" 
                       for c in rag_chunks]
            rag_content = "\n\n".join(combined)
        
        # Step 4: Run evaluation
        llm = get_llm()
        critic = QualityCritic(llm=llm, threshold=4.0)
        
        start_time = time.time()
        evaluation = await critic.evaluate_exam(
            exam=exam,
            rag_content=rag_content,
            mode=request.mode
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Step 5: Use EvaluationFormatter to transform data
        num_questions = len(all_questions)
        
        # Format for frontend (API response)
        response = EvaluationFormatter.for_frontend(evaluation, num_questions)
        
        # Step 6: Save to database
        # Format for revise agent
        feedback_for_generator = EvaluationFormatter.for_revise_agent(evaluation)
        
        # Format for metrics/analytics
        metrics_detail = EvaluationFormatter.for_metrics(evaluation, duration_ms, num_questions)
        
        # Determine evaluation_mode
        evaluation_mode = f"exam_{request.mode}"
        
        save_result = save_evaluation_to_db(
            job_id=request.job_id,
            parent_task_id=content_data["source_agent_task_id"],
            evaluation_result=evaluation,  # Complete evaluation stored in AGENT_TASKS.output
            duration_ms=duration_ms,
            is_passed=metrics_detail["is_passed"],
            feedback=feedback_for_generator,
            metrics_detail=metrics_detail,
            evaluation_mode=evaluation_mode
        )
        
        if save_result:
            eval_task_id, task_eval_id = save_result
            response["saved"] = {
                "evaluation_task_id": eval_task_id,
                "task_evaluation_id": task_eval_id
            }

        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


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
