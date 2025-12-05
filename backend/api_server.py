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

#
from backend.app.routers import debugging_problems
from backend.app.routers import auth_router
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

# --- Test Critic Workflow ---

class TestCriticWorkflowRequest(BaseModel):
    """Request for testing the full critic workflow."""
    unique_content_id: int
    prompt: str
    user_id: int = 1
    workflow_mode: str = "quality_critic"  # For future: "fact_critic", "dual_critic"

@testing_router.post("/test_critic_workflow")
async def test_critic_workflow(request: TestCriticWorkflowRequest):
    """
    **Test API**: Triggers the complete workflow with quality critic enabled.
    
    This endpoint:
    1. Creates a new job in orchestration_jobs
    2. Routes to appropriate skill (exam/summary based on prompt)
    3. Runs quality critic evaluation
    4. Aggregates final output
    5. Saves all metrics to database
    
    Example request:
    {
        "unique_content_id": 1,
        "prompt": "生成5題選擇題關於機器學習",
        "user_id": 1,
        "workflow_mode": "quality_critic"
    }
    
    Monitor logs to see each step:
    - [Router] Routing decision
    - [Generator] Content generation
    - [Quality Critic] Evaluation process
    - [Aggregate] Final output
    - [DB Logger] Database operations
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print(f"\n{'='*80}")
    print(f"[TEST CRITIC WORKFLOW] Starting new workflow")
    print(f"  - Prompt: {request.prompt[:50]}...")
    print(f"  - Content ID: {request.unique_content_id}")
    print(f"  - Workflow Mode: {request.workflow_mode}")
    print(f"{'='*80}\n")
    
    try:
        from backend.app.agents.teacher_agent.graph import app as teacher_app
        
        # Create job
        job_id = db_logger.create_job(
            user_id=request.user_id,
            input_prompt=request.prompt,
            workflow_type=request.workflow_mode,
            experiment_config={"test_mode": True}
        )
        
        if not job_id:
            raise HTTPException(status_code=500, detail="Failed to create job in database.")
        
        print(f"[TEST] Created job_id: {job_id}")
        
        # Prepare state for teacher agent
        initial_state = {
            "job_id": job_id,
            "user_id": request.user_id,
            "unique_content_id": request.unique_content_id,
            "user_query": request.prompt,
            "task_name": "auto_detected",
            "task_parameters": {},
            "final_result": None,
            "error": None,
            "next_node": None,
            "parent_task_id": None,
            "current_task_id": None,
            "iteration_count": 1,
            "max_iterations": int(os.getenv("MAX_CRITIC_ITERATIONS", 5)),
            "workflow_mode": request.workflow_mode,
            "critic_feedback": [],
            "critic_passed": None,
            "critic_metrics": None,
            "final_generated_content": None
        }
        
        # Run the graph (async version since we have async nodes)
        print(f"\n[TEST] Invoking teacher agent graph...")
        final_state = await teacher_app.ainvoke(initial_state)
        
        if final_state.get("error"):
            error_message = final_state.get("error")
            print(f"\n[TEST] Workflow failed: {error_message}\n")
            raise HTTPException(status_code=500, detail=error_message)
        
        # Extract results
        final_result = final_state.get("final_result", {})
        critic_passed = final_state.get("critic_passed", None)
        critic_metrics = final_state.get("critic_metrics", {})
        
        print(f"\n{'='*80}")
        print(f"[TEST CRITIC WORKFLOW] Completed successfully")
        print(f"  - Job ID: {job_id}")
        print(f"  - Critic Passed: {critic_passed}")
        if critic_metrics:
            print(f"  - Failed Criteria: {critic_metrics.get('failed_criteria', [])}")
        print(f"{'='*80}\n")
        
        # Return comprehensive response
        return {
            "job_id": job_id,
            "status": "completed",
            "critic_evaluation": {
                "passed": critic_passed,
                "metrics": critic_metrics
            },
            "final_output": final_result,
            "message": "Workflow completed. Check logs for detailed execution trace."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'job_id' in locals():
            db_logger.update_job_status(job_id, 'failed', error_message=str(e))
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")



# --- Quality Critic: Evaluate by Job ID (Database Integration) ---

class EvaluateByJobRequest(BaseModel):
    """Request model for evaluating exam by job_id from database."""
    job_id: int = Field(..., description="Job ID from ORCHESTRATION_JOBS table")
    mode: str = Field("quick", description="Evaluation mode: 'quick' (overall only) or 'comprehensive' (full analysis)")

@testing_router.post("/critic/evaluate_by_job")
async def evaluate_by_job_endpoint(request: EvaluateByJobRequest):
    """
    **Quality Critic Endpoint:** Evaluate generated content by job_id with automatic format detection.
    
    Supports multiple content types:
    - exam_questions: Multiple choice, short answer, true/false questions
    - summary_report: Summary content with sections
    - (other formats can be added as needed)
    
    Modes:
    - quick: Overall evaluation only (cost-effective, default)
    - comprehensive: Overall + per-question + statistics (exam only)
    
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
        
        content = content_data["content"]
        
        # Step 2: Detect content format
        display_type = content.get("display_type", "unknown")
        
        # Step 3: Get RAG context (common for all types)
        rag_chunks = get_rag_chunks_by_job_id(request.job_id, limit=10)
        rag_content = None
        if rag_chunks:
            combined = [f"[頁 {c.get('metadata', {}).get('page_number', '?')}] {c['chunk_text']}" 
                       for c in rag_chunks]
            rag_content = "\n\n".join(combined)
        
        # Step 4: Initialize critic
        llm = get_llm()
        critic = QualityCritic(llm=llm, threshold=4.0)
        
        start_time = time.time()
        
        # Step 5: Route to appropriate evaluation method based on format
        if display_type == "exam_questions":
            # Exam format - parse questions and use evaluate_exam()
            all_questions = []
            
            if isinstance(content, dict) and "content" in content:
                exam_data = content["content"]
                if isinstance(exam_data, list):
                    for question_block in exam_data:
                        question_type = question_block.get("type", "unknown")
                        questions = question_block.get("questions", [])
                        # Add question_type to each question
                        for q in questions:
                            q["question_type"] = question_type
                        all_questions.extend(questions)
            elif isinstance(content, list):
                for question_block in content:
                    question_type = question_block.get("type", "unknown")
                    questions = question_block.get("questions", [])
                    # Add question_type to each question
                    for q in questions:
                        q["question_type"] = question_type
                    all_questions.extend(questions)
            elif isinstance(content, dict) and "questions" in content:
                # Single question block
                question_type = content.get("type", "unknown")
                all_questions = content["questions"]
                for q in all_questions:
                    q["question_type"] = question_type
            
            if not all_questions:
                raise HTTPException(status_code=400, detail="No questions found in exam content")
            
            exam = {
                "type": "exam",
                "questions": all_questions
            }
            
            evaluation = await critic.evaluate_exam(
                exam=exam,
                rag_content=rag_content,
                mode=request.mode
            )
            
            num_items = len(all_questions)
            evaluation_mode = f"exam_{request.mode}"
            
        elif display_type == "summary_report":
            # Summary format - evaluate as a whole using evaluate()
            evaluation = await critic.evaluate(
                content=content,
                criteria=None  # Use all criteria
            )
            
            # Wrap in a structure compatible with formatters
            evaluation = {
                "mode": "quick",  # Summary doesn't support comprehensive mode
                "overall": evaluation,
                "per_question": [],
                "statistics": {"note": "Summary evaluation does not have per-item breakdown"}
            }
            
            num_items = len(content.get("content", []))  # Number of sections
            evaluation_mode = "summary_quick"
            
        else:
            # Unknown format - evaluate as generic content
            evaluation = await critic.evaluate(
                content=content,
                criteria=None
            )
            
            # Wrap in a structure compatible with formatters
            evaluation = {
                "mode": "quick",
                "overall": evaluation,
                "per_question": [],
                "statistics": {"note": f"Generic evaluation for {display_type}"}
            }
            
            num_items = 1
            evaluation_mode = f"{display_type}_quick"
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Step 6: Use EvaluationFormatter to transform data
        # Format for frontend (API response)
        response = EvaluationFormatter.for_frontend(evaluation, num_items)
        
        # Step 7: Save to database
        # Format for revise agent
        feedback_for_generator = EvaluationFormatter.for_revise_agent(evaluation)
        
        # Format for metrics/analytics
        metrics_detail = EvaluationFormatter.for_metrics(evaluation, duration_ms, num_items)
        
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

app.include_router(data_management_router)
app.include_router(testing_router)
app.include_router(debugging_problems.router)

# Register functions from auth_router
app.include_router(agent_router)
app.include_router(auth_router.router)

# To run this server:
# 1. Make sure you are in the root directory of the project (Cook.ai).
# 2. Run the command: uvicorn backend.api_server:app --reload --port 8000
