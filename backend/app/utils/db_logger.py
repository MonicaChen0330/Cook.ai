"""
Utility functions for logging orchestration and agent task data to the database.
"""
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, MetaData, Table, insert, update, select, func, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import json

# --- Timezone and Database Setup ---
TAIPEI_TZ = timezone(timedelta(hours=8))
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set.")

engine = create_engine(DATABASE_URL)
metadata = MetaData()

# --- Table Reflection ---
# Reflect existing tables to avoid re-declaring them
try:
    orchestration_jobs = Table('orchestration_jobs', metadata, autoload_with=engine)
    agent_tasks = Table('agent_tasks', metadata, autoload_with=engine)
    generated_contents = Table('generated_contents', metadata, autoload_with=engine)
    agent_task_sources = Table('agent_task_sources', metadata, autoload_with=engine)
except Exception as e:
    print(f"Error reflecting database tables: {e}")
    # Define tables with key columns as a fallback if reflection fails
    orchestration_jobs = Table('orchestration_jobs', metadata,
        Column('id', Integer, primary_key=True),
        # Add other essential columns if needed for the script to be parsable
    )
    agent_tasks = Table('agent_tasks', metadata,
        Column('id', Integer, primary_key=True),
        # ...
    )
    generated_contents = Table('generated_contents', metadata,
        Column('id', Integer, primary_key=True),
    )
    agent_task_sources = Table('agent_task_sources', metadata,
        Column('task_id', Integer, primary_key=True),
        Column('source_type', String, primary_key=True),
        Column('source_id', Integer, primary_key=True),
    )

# --- Job-level Logging ---

def create_job(user_id: int, input_prompt: str, workflow_type: str, experiment_config: Optional[Dict] = None) -> Optional[int]:
    """Creates a new record in the orchestration_jobs table."""
    try:
        with engine.connect() as conn:
            stmt = insert(orchestration_jobs).values(
                user_id=user_id,
                input_prompt=input_prompt,
                status='planning',
                workflow_type=workflow_type,
                experiment_config=experiment_config,
                created_at=datetime.now(TAIPEI_TZ),
                updated_at=datetime.now(TAIPEI_TZ)
            ).returning(orchestration_jobs.c.id)
            result = conn.execute(stmt)
            job_id = result.scalar_one()
            conn.commit()
            print(f"[DB Logger] Created job {job_id} for workflow '{workflow_type}'.")
            return job_id
    except Exception as e:
        print(f"[DB Logger] ERROR: Failed to create job. Reason: {e}")
        return None

def update_job_status(job_id: int, status: str, error_message: Optional[str] = None):
    """Updates the status and error message of a job."""
    try:
        with engine.connect() as conn:
            stmt = update(orchestration_jobs).where(orchestration_jobs.c.id == job_id).values(
                status=status,
                error_message=error_message,
                updated_at=datetime.now(TAIPEI_TZ)
            )
            conn.execute(stmt)
            conn.commit()
            print(f"[DB Logger] Updated job {job_id} status to '{status}'.")
    except Exception as e:
        print(f"[DB Logger] ERROR: Failed to update job {job_id}. Reason: {e}")

def update_job_final_output(job_id: int, final_output_id: int):
    """Updates the final_output_id of a job."""
    try:
        with engine.connect() as conn:
            stmt = update(orchestration_jobs).where(orchestration_jobs.c.id == job_id).values(
                final_output_id=final_output_id,
                updated_at=datetime.now(TAIPEI_TZ)
            )
            conn.execute(stmt)
            conn.commit()
            print(f"[DB Logger] Updated job {job_id} with final_output_id: {final_output_id}.")
    except Exception as e:
        print(f"[DB Logger] ERROR: Failed to update job {job_id} final_output_id. Reason: {e}")

# --- Task-level Logging ---

def create_task(job_id: int, agent_name: str, task_description: str, task_input: Optional[Dict] = None, model_name: Optional[str] = None, parent_task_id: Optional[int] = None, model_parameters: Optional[Dict] = None) -> Optional[int]:
    """Creates a new record in the agent_tasks table and returns its ID and start time."""
    try:
        with engine.connect() as conn:
            stmt = insert(agent_tasks).values(
                job_id=job_id,
                agent_name=agent_name,
                task_description=task_description,
                task_input=task_input,
                status='in_progress',
                model_name=model_name,
                parent_task_id=parent_task_id,
                model_parameters=model_parameters,
                created_at=datetime.now(TAIPEI_TZ)
            ).returning(agent_tasks.c.id)
            result = conn.execute(stmt)
            task_id = result.scalar_one()
            conn.commit()
            print(f"[DB Logger] Created task {task_id} for agent '{agent_name}'.")
            return task_id
    except Exception as e:
        print(f"[DB Logger] ERROR: Failed to create task for agent '{agent_name}'. Reason: {e}")
        return None

def update_task(
    task_id: int,
    status: str,
    output: Optional[Any] = None, # Changed type hint to Any
    error_message: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    duration_ms: Optional[int] = None,
    estimated_cost_usd: Optional[float] = None
):
    """Updates an agent_task record upon completion or failure."""
    try:
        with engine.connect() as conn:
            processed_output = None
            if output is not None:
                if isinstance(output, (dict, list)):
                    processed_output = output
                elif isinstance(output, str):
                    try:
                        processed_output = json.loads(output)
                    except json.JSONDecodeError:
                        processed_output = {"text_output": output} # Wrap plain strings
                else:
                    processed_output = {"value": str(output)} # Catch all other types

            values_to_update = {
                "status": status,
                "output": processed_output, # Use the processed output
                "error_message": error_message,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "duration_ms": duration_ms,
                "completed_at": datetime.now(TAIPEI_TZ),
                "estimated_cost_usd": estimated_cost_usd
            }
            # Filter out None values so they don't overwrite existing data in the DB
            values_to_update = {k: v for k, v in values_to_update.items() if v is not None}

            stmt = update(agent_tasks).where(agent_tasks.c.id == task_id).values(**values_to_update)
            conn.execute(stmt)
            conn.commit()
            print(f"[DB Logger] Updated task {task_id} to status '{status}'.")
    except Exception as e:
        print(f"[DB Logger] ERROR: Failed to update task {task_id}. Reason: {e}")


# --- Content and Source Logging ---

def log_task_sources(task_id: int, source_chunks: Optional[List[Dict]] = None):
    """Logs the retrieved source chunks for a specific task."""
    if not source_chunks:
        return

    try:
        with engine.connect() as conn:
            records_to_insert = [
                {
                    "task_id": task_id,
                    "source_type": 'chunk',
                    "source_id": chunk.get("chunk_id")
                }
                for chunk in source_chunks if chunk.get("chunk_id") is not None
            ]
            
            if not records_to_insert:
                return

            # Use a transaction for the insert
            with conn.begin():
                conn.execute(insert(agent_task_sources), records_to_insert)
            
            print(f"[DB Logger] Logged {len(records_to_insert)} sources for task {task_id}.")

    except Exception as e:
        print(f"[DB Logger] ERROR: Failed to log sources for task {task_id}. Reason: {e}")


def save_generated_content(task_id: int, content_type: str, title: str, content: str) -> Optional[int]:
    """Saves generated content to the GENERATED_CONTENTS table."""
    try:
        with engine.connect() as conn:
            # The 'content' column in the DB is JSON. Parse the incoming JSON string.
            parsed_content = json.loads(content)
            
            stmt = insert(generated_contents).values(
                source_agent_task_id=task_id,
                content_type=content_type,
                title=title,
                content=parsed_content, # Store the parsed JSON object directly
                created_at=datetime.now(TAIPEI_TZ),
                updated_at=datetime.now(TAIPEI_TZ)
            ).returning(generated_contents.c.id)
            
            result = conn.execute(stmt)
            content_id = result.scalar_one()
            conn.commit()
            
            print(f"[DB Logger] Saved generated content for task {task_id}. New content ID: {content_id}.")
            return content_id
            
    except Exception as e:
        print(f"[DB Logger] ERROR: Failed to save generated content for task {task_id}. Reason: {e}")
        return None
