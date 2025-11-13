"""
Utility functions for logging orchestration and agent task data to the database.
"""
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, MetaData, Table, insert, update, select, func, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

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

# --- Task-level Logging ---

def create_task(job_id: int, agent_name: str, task_description: str, task_input: Optional[Dict] = None, model_name: Optional[str] = None) -> Optional[int]:
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
    output: Optional[str] = None,
    error_message: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    duration_ms: Optional[int] = None
):
    """Updates an agent_task record upon completion or failure."""
    try:
        with engine.connect() as conn:
            values_to_update = {
                "status": status,
                "output": str(output) if output is not None else None,
                "error_message": error_message,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "duration_ms": duration_ms,
                "completed_at": datetime.now(TAIPEI_TZ)
            }
            # Filter out None values so they don't overwrite existing data in the DB
            values_to_update = {k: v for k, v in values_to_update.items() if v is not None}

            stmt = update(agent_tasks).where(agent_tasks.c.id == task_id).values(**values_to_update)
            conn.execute(stmt)
            conn.commit()
            print(f"[DB Logger] Updated task {task_id} to status '{status}'.")
    except Exception as e:
        print(f"[DB Logger] ERROR: Failed to update task {task_id}. Reason: {e}")
