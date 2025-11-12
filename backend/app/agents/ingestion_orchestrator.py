"""
Orchestrator for handling the ingestion of documents into the system.
"""
import hashlib
import time
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from dotenv import load_dotenv
from pgvector.sqlalchemy import Vector
from sqlalchemy import (create_engine, MetaData, Table, Column, Integer, String, 
                        DateTime, JSON, insert, update, select, Text, delete, ForeignKey, DECIMAL, BOOLEAN)

# --- Timezone Setup ---
TAIPEI_TZ = timezone(timedelta(hours=8))

# --- Database Setup ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set.")

engine = create_engine(DATABASE_URL)
metadata = MetaData()

orchestration_jobs = Table('orchestration_jobs', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('input_prompt', Text),
    Column('status', String(50)),
    Column('final_output_id', Integer, ForeignKey('generated_contents.id')),
    Column('created_at', DateTime, default=lambda: datetime.now(TAIPEI_TZ)),
    Column('updated_at', DateTime, default=lambda: datetime.now(TAIPEI_TZ), onupdate=lambda: datetime.now(TAIPEI_TZ)),
    Column('workflow_type', String(50)),
    Column('experiment_config', JSON),
    Column('total_iterations', Integer),
    Column('total_latency_ms', Integer),
    Column('total_prompt_tokens', Integer),
    Column('total_completion_tokens', Integer),
    Column('estimated_carbon_g', DECIMAL),
    Column('error_message', Text)
)

agent_tasks = Table('agent_tasks', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('job_id', Integer, ForeignKey('orchestration_jobs.id')),
    Column('parent_task_id', Integer, ForeignKey('agent_tasks.id')),
    Column('iteration_number', Integer),
    Column('agent_name', String(100)),
    Column('task_description', Text),
    Column('task_input', JSON),
    Column('output', Text),
    Column('status', String(50)),
    Column('error_message', Text),
    Column('duration_ms', Integer),
    Column('prompt_tokens', Integer),
    Column('completion_tokens', Integer),
    Column('estimated_cost_usd', DECIMAL),
    Column('model_name', String(100)),
    Column('model_parameters', JSON),
    Column('created_at', DateTime, default=lambda: datetime.now(TAIPEI_TZ)),
    Column('completed_at', DateTime)
)

unique_contents = Table('unique_contents', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('content_hash', String(64), unique=True, nullable=False),
    Column('file_size_bytes', Integer),
    Column('original_file_type', String(20)),
    Column('processing_status', String(20), default='pending'),
    Column('created_at', DateTime, default=lambda: datetime.now(TAIPEI_TZ))
)

materials = Table('materials', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('course_id', Integer, ForeignKey('courses.id'), nullable=False),
    Column('uploader_id', Integer, ForeignKey('users.id'), nullable=True),
    Column('course_unit_id', Integer, ForeignKey('course_units.id'), nullable=True),
    Column('file_name', String(255), nullable=False),
    Column('unique_content_id', Integer, ForeignKey('unique_contents.id', ondelete='CASCADE'), nullable=False),
    Column('created_at', DateTime, default=lambda: datetime.now(TAIPEI_TZ)),
    Column('updated_at', DateTime, default=lambda: datetime.now(TAIPEI_TZ), onupdate=lambda: datetime.now(TAIPEI_TZ))
)

document_chunks = Table('document_chunks', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('unique_content_id', Integer, ForeignKey('unique_contents.id', ondelete='CASCADE')),
    Column('chunk_text', Text),
    Column('chunk_order', Integer),
    Column('metadata', JSON),
    Column('embedding', Vector(1536)),
)

document_content = Table('document_content', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('unique_content_id', Integer, ForeignKey('unique_contents.id', ondelete='CASCADE'), nullable=False),
    Column('page_number', Integer),
    Column('structured_content', JSON),
    Column('combined_human_text', Text)
)

# --- Logging Functions ---
def _log_job_start(conn, user_id: int, file_name: str) -> int:
    print(f"[{datetime.now(TAIPEI_TZ)}] DB LOG: Creating orchestration job for user {user_id} to ingest '{file_name}'.")
    stmt = insert(orchestration_jobs).values(
        user_id=user_id, 
        input_prompt=f"[INGEST] Uploaded file: {file_name}",
        status='planning', 
        workflow_type='ingestion'
    ).returning(orchestration_jobs.c.id)
    result = conn.execute(stmt)
    return result.scalar_one()

def _log_job_end(conn, job_id: int, status: str, error_message: str = None):
    print(f"[{datetime.now(TAIPEI_TZ)}] DB LOG: Updating job {job_id} to status '{status}'.")
    update_values = {'status': status}
    if error_message:
        update_values['error_message'] = error_message
    stmt = update(orchestration_jobs).where(orchestration_jobs.c.id == job_id).values(**update_values)
    conn.execute(stmt)

def _log_agent_task(conn, job_id: int, agent_name: str, description: str, inputs: Dict[str, Any]) -> int:
    print(f"[{datetime.now(TAIPEI_TZ)}] DB LOG: Job {job_id} - Starting task for agent '{agent_name}': {description}")
    stmt = insert(agent_tasks).values(
        job_id=job_id, 
        agent_name=agent_name, 
        task_description=description,
        task_input=inputs, 
        status='in_progress', 
        iteration_number=1
    ).returning(agent_tasks.c.id)
    result = conn.execute(stmt)
    return result.scalar_one()

def _update_agent_task(conn, task_id: int, status: str, output: Any, duration_ms: int, error_message: str = None):
    print(f"[{datetime.now(TAIPEI_TZ)}] DB LOG: Task {task_id} finished with status '{status}' in {duration_ms}ms.")
    update_values = {
        'status': status,
        'output': str(output),
        'duration_ms': duration_ms,
        'completed_at': datetime.now(TAIPEI_TZ)
    }
    if error_message:
        update_values['error_message'] = error_message
    stmt = update(agent_tasks).where(agent_tasks.c.id == task_id).values(**update_values)
    conn.execute(stmt)

def _generate_human_text_from_structured_content(content_list: list) -> str:
    parts = []
    if not isinstance(content_list, list):
        return ""
    for item in content_list:
        item_type = item.get("type")
        if item_type == "text":
            parts.append(item.get("content", ""))
        elif item_type == "image":
            ocr_text = item.get("ocr_text")
            if ocr_text:
                parts.append(f"[圖片: {ocr_text}]")
            else:
                parts.append("[圖片]")
    return " ".join(parts).strip()

# --- Main Orchestrator Logic ---
def process_file(file_path: str, uploader_id: int, course_id: int, course_unit_id: int = None, force_reprocess: bool = False):
    file_name = file_path.split('/')[-1]
    file_type = file_name.split('.')[-1]
    
    with engine.connect() as conn_job_log:
        with conn_job_log.begin(): 
            job_id = _log_job_start(conn_job_log, user_id=uploader_id, file_name=file_name)
        
        try:
            with engine.connect() as conn_data:
                with conn_data.begin() as transaction:
                    
                    skip_processing = False 
                    unique_content_id = None
                    
                    # --- Task 1: Hashing and Get-Or-Create Unique Content ---
                    start_time = time.perf_counter()
                    task_id_hash = _log_agent_task(conn_data, job_id, "ingestion_orchestrator", "Calculate file hash and get/create unique content entry", {"file_path": file_path, "force_reprocess": force_reprocess})
                    
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                        file_hash = hashlib.sha256(file_bytes).hexdigest()
                        file_size = len(file_bytes)

                    select_stmt = select(unique_contents.c.id).where(unique_contents.c.content_hash == file_hash)
                    existing_id = conn_data.execute(select_stmt).scalar_one_or_none()

                    if existing_id:
                        if not force_reprocess:
                            print(f"Content with hash {file_hash} already exists with ID {existing_id}. Will link to course.")
                            unique_content_id = existing_id
                            skip_processing = True 
                            _update_agent_task(conn_data, task_id_hash, "completed", {"status": "skipped", "file_hash": file_hash, "unique_content_id": existing_id}, int((time.perf_counter() - start_time) * 1000))
                        else:
                            print(f"Force reprocess is True. Deleting existing content with ID {existing_id} and all related data.")
                            # 由於 'ondelete=CASCADE'，我們只需要刪除 unique_contents
                            delete_stmt = delete(unique_contents).where(unique_contents.c.id == existing_id)
                            conn_data.execute(delete_stmt)
                            print(f"Successfully deleted old content and its relations (CASCADE).")
                    
                    if not unique_content_id: 
                        insert_stmt = insert(unique_contents).values(
                            content_hash=file_hash, file_size_bytes=file_size,
                            original_file_type=file_type, processing_status='in_progress'
                        ).returning(unique_contents.c.id)
                        unique_content_id = conn_data.execute(insert_stmt).scalar_one()
                        
                        duration_ms = int((time.perf_counter() - start_time) * 1000)
                        _update_agent_task(conn_data, task_id_hash, "completed", {"status": "created", "file_hash": file_hash, "unique_content_id": unique_content_id}, duration_ms)
                    
                    # --- Task 2: Link Material to Course ---
                    start_time = time.perf_counter()
                    task_id_link = _log_agent_task(conn_data, job_id, "material_linker", "Link unique content to course", {"unique_content_id": unique_content_id, "course_id": course_id})
                    
                    stmt_check_material = select(materials.c.id).where(
                        (materials.c.unique_content_id == unique_content_id) &
                        (materials.c.course_id == course_id)
                    )
                    existing_material = conn_data.execute(stmt_check_material).scalar_one_or_none()
                    
                    link_output = {}
                    if not existing_material:
                        print(f"[{datetime.now(TAIPEI_TZ)}] DB LOG: Linking content {unique_content_id} to course {course_id} with name '{file_name}'.")
                        stmt_insert_material = insert(materials).values(
                            unique_content_id=unique_content_id,
                            course_id=course_id,
                            uploader_id=uploader_id,
                            course_unit_id=course_unit_id,
                            file_name=file_name
                        )
                        conn_data.execute(stmt_insert_material)
                        link_output = {"status": "linked"}
                    else:
                        print(f"[{datetime.now(TAIPEI_TZ)}] DB LOG: Content {unique_content_id} already linked to course {course_id}.")
                        link_output = {"status": "already_exists"}

                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    _update_agent_task(conn_data, task_id_link, "completed", link_output, duration_ms)

                    # --- Check skip flag ---
                    if skip_processing:
                        print(f"File '{file_name}' was already processed. Linking complete. Skipping ingestion.")
                        _log_job_end(conn_job_log, job_id, "completed")
                        return # 退出 process_file

                    # --- Task 3: Document Loading & Parsing ---
                    start_time = time.perf_counter()
                    from app.services.document_loader import get_loader
                    task_id_load = _log_agent_task(conn_data, job_id, "document_loader", "Load and extract text from file", {"file_path": file_path})
                    
                    loader = get_loader(file_path)
                    document = loader.load(file_path)
                    
                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    _update_agent_task(conn_data, task_id_load, "completed", {"page_count": len(document.pages), "source": document.source}, duration_ms)

                    # --- Task 4: Save Document Content ---
                    start_time = time.perf_counter()
                    task_id_preview = _log_agent_task(conn_data, job_id, "database_writer", "Save page-by-page content", {"page_count": len(document.pages)})

                    preview_data = []
                    for page in document.pages:
                        try:
                            structured_json = page.structured_elements
                        except AttributeError:
                            print(f"ERROR: Page object is missing 'structured_elements'. Loader needs update!")
                            raise
                        
                        human_readable_text = _generate_human_text_from_structured_content(structured_json)
                        page.text_for_chunking = human_readable_text
                        
                        if structured_json: 
                            preview_data.append({
                                "unique_content_id": unique_content_id,
                                "page_number": page.page_number,
                                "structured_content": structured_json,
                                "combined_human_text": human_readable_text
                            })
                    
                    if preview_data:
                        conn_data.execute(insert(document_content), preview_data) # <-- 寫入 'document_content'

                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    _update_agent_task(conn_data, task_id_preview, "completed", {"saved_preview_rows": len(preview_data)}, duration_ms)

                    # --- Task 5: Document Chunking ---
                    start_time = time.perf_counter()
                    task_id_chunk = _log_agent_task(conn_data, job_id, "text_splitter", "Split document into chunks", {"page_count": len(document.pages)})
                    
                    from app.services.text_splitter import chunk_document
                    chunks_with_metadata = chunk_document(
                        pages=document.pages, 
                        chunk_size=1000, 
                        chunk_overlap=150,
                        file_name=file_name, 
                        uploader_id=uploader_id
                    )
                    
                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    _update_agent_task(conn_data, task_id_chunk, "completed", {"chunk_count": len(chunks_with_metadata)}, duration_ms)

                    # --- Task 6: Generate Embeddings and Store Chunks ---
                    start_time = time.perf_counter()
                    task_id_save = _log_agent_task(conn_data, job_id, "embedding_generator_and_writer", "Generate embeddings and save chunks", {"chunk_count": len(chunks_with_metadata)})
                    
                    chunk_data = []
                    if chunks_with_metadata:
                        # Extract text for batch embedding
                        texts_to_embed = [text for text, meta in chunks_with_metadata]
                        
                        # Generate embeddings in a batch
                        from app.services.embedding_service import embedding_service
                        embeddings = embedding_service.create_embeddings(texts_to_embed)
                        
                        # Combine chunks with their embeddings
                        for i, ((text, meta), embedding) in enumerate(zip(chunks_with_metadata, embeddings)):
                            chunk_data.append({
                                "unique_content_id": unique_content_id,
                                "chunk_text": text,
                                "chunk_order": i,
                                "metadata": meta,
                                "embedding": embedding 
                            })

                    if chunk_data:
                        conn_data.execute(insert(document_chunks), chunk_data)
                    
                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    _update_agent_task(conn_data, task_id_save, "completed", {"saved_chunks": len(chunk_data)}, duration_ms)

                    # --- Task 7: Finalize Status ---
                    start_time = time.perf_counter()
                    task_id_finalize = _log_agent_task(conn_data, job_id, "ingestion_orchestrator", "Update unique_content status to completed", {"unique_content_id": unique_content_id})
                    
                    update_status_stmt = update(unique_contents).where(unique_contents.c.id == unique_content_id).values(processing_status='completed')
                    conn_data.execute(update_status_stmt)

                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    _update_agent_task(conn_data, task_id_finalize, "completed", {"status": "completed"}, duration_ms)

                _log_job_end(conn_job_log, job_id, "completed") 
                print(f"\nSuccessfully processed and INGESTED file '{file_name}'.")

        except Exception as e:
            print(f"ERROR: An error occurred during file ingestion. Transaction for this file rolled back. Error: {e}")
            with conn_job_log.begin(): 
                _log_job_end(conn_job_log, job_id, "failed", error_message=str(e))

if __name__ == '__main__':
    FORCE_REPROCESS = False  # Set to True to force reprocessing of existing files
    print(f"--- Starting Multimodal Document Ingestion Test (Force Reprocess: {FORCE_REPROCESS}) ---")
    TEST_FILES_DIR = "test_files"
    if not os.path.isdir(TEST_FILES_DIR):
        print(f"Error: Test files directory not found at '{TEST_FILES_DIR}'.")
        print("Please make sure you are running this script from the 'backend' directory.")
        exit()
    
    test_files = ["sample2.pdf"] 
    
    for test_file in test_files:
        test_file_path = os.path.join(TEST_FILES_DIR, test_file)
        print("\n" + "="*50)
        print(f"Processing file: {test_file_path}")
        print("="*50)
        try:
            process_file(
                file_path=test_file_path,
                uploader_id=1,
                course_id=1, 
                course_unit_id=1,
                force_reprocess=FORCE_REPROCESS
            )
        except Exception as e:
            print(f"!!! FAILED to process {test_file_path}: {e} !!!")
    print("\n--- All Document Ingestion Tests Finished ---")