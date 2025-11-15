"""
Orchestrator for handling the ingestion of documents into the system.
"""
import hashlib
import time
import os
from typing import Dict, Any

from sqlalchemy import create_engine, MetaData, Table, select, insert, update, delete
from pgvector.sqlalchemy import Vector

from backend.app.utils import db_logger

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set.")

engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Reflect tables used in this orchestrator
unique_contents = Table('unique_contents', metadata, autoload_with=engine)
materials = Table('materials', metadata, autoload_with=engine)
document_content = Table('document_content', metadata, autoload_with=engine)
document_chunks = Table('document_chunks', metadata, autoload_with=engine)


def _generate_human_text_from_structured_content(content_list: list) -> str:
    # This helper function remains the same
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
def process_file(file_path: str, uploader_id: int, course_id: int, course_unit_id: int = None, force_reprocess: bool = False) -> int | None:
    """
    Processes a single file for ingestion, using the new db_logger for all logging.
    """
    file_name = os.path.basename(file_path)
    
    job_id = db_logger.create_job(
        user_id=uploader_id,
        input_prompt=f"[INGEST] Uploaded file: {file_name}",
        workflow_type='ingestion'
    )
    if not job_id:
        print(f"ERROR: Failed to create an ingestion job for file '{file_name}'. Aborting.")
        return None

    try:
        with engine.connect() as conn:
            with conn.begin() as transaction:
                last_task_id = None # Initialize for sequential parent_task_id logging

                # --- Task 1: Hashing and Get-Or-Create Unique Content ---
                task_id_hash = db_logger.create_task(job_id, "hash_file", "Calculate file hash and check for existence.", task_input={"file_path": file_path}, parent_task_id=last_task_id)
                last_task_id = task_id_hash
                start_time = time.perf_counter()
                
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                    file_hash = hashlib.sha256(file_bytes).hexdigest()
                
                existing_id = conn.execute(select(unique_contents.c.id).where(unique_contents.c.content_hash == file_hash)).scalar_one_or_none()
                
                unique_content_id = None
                if existing_id and not force_reprocess:
                    unique_content_id = existing_id
                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    db_logger.update_task(task_id_hash, 'completed', f"Content already exists with ID {unique_content_id}.", duration_ms=duration_ms)
                else:
                    if existing_id: # force_reprocess is True
                        conn.execute(delete(unique_contents).where(unique_contents.c.id == existing_id))
                    
                    insert_stmt = insert(unique_contents).values(
                        content_hash=file_hash, file_size_bytes=len(file_bytes),
                        original_file_type=file_name.split('.')[-1], processing_status='in_progress'
                    ).returning(unique_contents.c.id)
                    unique_content_id = conn.execute(insert_stmt).scalar_one()
                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    db_logger.update_task(task_id_hash, 'completed', f"Created new unique_content with ID {unique_content_id}.", duration_ms=duration_ms)

                # --- Task 2: Link Material to Course ---
                task_id_link = db_logger.create_task(job_id, "link_material", "Link content to course.", task_input={"unique_content_id": unique_content_id, "course_id": course_id, "uploader_id": uploader_id}, parent_task_id=last_task_id)
                last_task_id = task_id_link
                start_time = time.perf_counter()
                
                if not conn.execute(select(materials.c.id).where((materials.c.unique_content_id == unique_content_id) & (materials.c.course_id == course_id))).scalar_one_or_none():
                    conn.execute(insert(materials).values(
                        unique_content_id=unique_content_id, course_id=course_id,
                        uploader_id=uploader_id, course_unit_id=course_unit_id, file_name=file_name
                    ))
                
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                db_logger.update_task(task_id_link, 'completed', f"Linked content {unique_content_id} to course {course_id}.", duration_ms=duration_ms)

                if existing_id and not force_reprocess:
                    db_logger.update_job_status(job_id, 'completed')
                    return unique_content_id

                # --- Task 3: Document Loading & Parsing ---
                from backend.app.services.document_loader import get_loader
                task_id_load = db_logger.create_task(job_id, "document_loader", "Load and extract text from file.", task_input={"file_path": file_path}, parent_task_id=last_task_id)
                last_task_id = task_id_load
                start_time = time.perf_counter()
                document = get_loader(file_path).load(file_path)
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                db_logger.update_task(task_id_load, 'completed', f"Loaded {len(document.pages)} pages.", duration_ms=duration_ms)

                # --- Task 4: Save Document Content ---
                task_id_save_content = db_logger.create_task(job_id, "database_writer", "Save page-by-page content.", task_input={"unique_content_id": unique_content_id}, parent_task_id=last_task_id)
                last_task_id = task_id_save_content
                start_time = time.perf_counter()
                preview_data = []
                for page in document.pages:
                    structured_json = getattr(page, 'structured_elements', [])
                    human_readable_text = _generate_human_text_from_structured_content(structured_json)
                    page.text_for_chunking = human_readable_text
                    if structured_json:
                        preview_data.append({"unique_content_id": unique_content_id, "page_number": page.page_number, "structured_content": structured_json, "combined_human_text": human_readable_text})
                if preview_data:
                    conn.execute(insert(document_content), preview_data)
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                db_logger.update_task(task_id_save_content, 'completed', f"Saved {len(preview_data)} pages of content.", duration_ms=duration_ms)

                # --- Task 5: Document Chunking ---
                from backend.app.services.text_splitter import chunk_document
                chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
                chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "150"))
                task_id_chunk = db_logger.create_task(job_id, "text_splitter", "Split document into chunks.", task_input={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}, parent_task_id=last_task_id)
                last_task_id = task_id_chunk
                start_time = time.perf_counter()
                chunks_with_metadata = chunk_document(pages=document.pages, chunk_size=chunk_size, chunk_overlap=chunk_overlap, file_name=file_name, uploader_id=uploader_id)
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                db_logger.update_task(task_id_chunk, 'completed', f"Created {len(chunks_with_metadata)} chunks.", duration_ms=duration_ms)

                # --- Task 6: Generate Embeddings and Store Chunks ---
                task_id_embed = db_logger.create_task(job_id, "embedding_generator", "Generate embeddings and save chunks.", task_input={"num_chunks_to_embed": len(chunks_with_metadata) if chunks_with_metadata else 0}, parent_task_id=last_task_id)
                last_task_id = task_id_embed
                start_time = time.perf_counter()
                if chunks_with_metadata:
                    from backend.app.services.embedding_service import embedding_service
                    texts_to_embed = [text for text, meta in chunks_with_metadata]
                    embeddings, usage = embedding_service.create_embeddings(texts_to_embed)
                    chunk_data = [{"unique_content_id": unique_content_id, "chunk_text": text, "chunk_order": i, "metadata": meta, "embedding": embedding} for i, ((text, meta), embedding) in enumerate(zip(chunks_with_metadata, embeddings))]
                    conn.execute(insert(document_chunks), chunk_data)
                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    db_logger.update_task(task_id_embed, 'completed', f"Saved {len(chunk_data)} chunks.", duration_ms=duration_ms, prompt_tokens=usage.get("prompt_tokens"))
                else:
                    duration_ms = int((time.perf_counter() - start_time) * 1000)
                    db_logger.update_task(task_id_embed, 'completed', "No chunks to embed.", duration_ms=duration_ms)

                # --- Task 7: Finalize Status ---
                task_id_finalize = db_logger.create_task(job_id, "finalize_status", "Update unique_content status to completed.", task_input={"unique_content_id": unique_content_id}, parent_task_id=last_task_id)
                last_task_id = task_id_finalize
                start_time = time.perf_counter()
                conn.execute(update(unique_contents).where(unique_contents.c.id == unique_content_id).values(processing_status='completed'))
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                db_logger.update_task(task_id_finalize, 'completed', duration_ms=duration_ms)

        db_logger.update_job_status(job_id, 'completed')
        print(f"\nSuccessfully processed and INGESTED file '{file_name}'.")
        return unique_content_id

    except Exception as e:
        print(f"ERROR: An error occurred during file ingestion for job {job_id}. Error: {e}")
        db_logger.update_job_status(job_id, 'failed', error_message=str(e))
        # The transaction will be rolled back automatically by the 'with' statement context manager
        return None

if __name__ == '__main__':
    # This block remains for direct testing of the ingestion process
    FORCE_REPROCESS = False
    print(f"--- Starting Multimodal Document Ingestion Test (Force Reprocess: {FORCE_REPROCESS}) ---")
    TEST_FILES_DIR = "test_files"
    if not os.path.isdir(TEST_FILES_DIR):
        print(f"Error: Test files directory not found at '{TEST_FILES_DIR}'.")
        exit()
    
    test_files = ["sample.pptx"] 
    
    for test_file in test_files:
        test_file_path = os.path.join(TEST_FILES_DIR, test_file)
        print("\n" + "="*50 + f"\nProcessing file: {test_file_path}\n" + "="*50)
        try:
            content_id = process_file(file_path=test_file_path, uploader_id=1, course_id=1, force_reprocess=FORCE_REPROCESS)
            if content_id:
                print(f"\n--- Successfully processed file. Unique Content ID: {content_id} ---")
            else:
                print(f"\n--- Failed to process file: {test_file_path} ---")
        except Exception as e:
            print(f"!!! FAILED to process {test_file_path}: {e} !!!")
    print("\n--- All Document Ingestion Tests Finished ---")