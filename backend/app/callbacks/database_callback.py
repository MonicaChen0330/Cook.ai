import time
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from backend.app.utils import db_logger

class DatabaseCallbackHandler(BaseCallbackHandler):
    """A custom LangChain callback handler to log execution details to the database."""

    def __init__(self, job_id: int):
        super().__init__()
        self.job_id = job_id
        self.task_starts: Dict[UUID, float] = {}
        self.task_ids: Dict[UUID, int] = {}
        print(f"[Callback] DatabaseCallbackHandler initialized for job_id: {self.job_id}")

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> None:
        """Called when an LLM run starts."""
        try:
            model_name = kwargs.get("invocation_params", {}).get("model_name", "unknown")
            # The prompt is often the last message in the list
            task_input = {"prompt": prompts[-1]} if prompts else {}
            
            task_id = db_logger.create_task(
                job_id=self.job_id,
                agent_name=f"llm_call_{model_name}",
                task_description=f"Executing LLM call with model {model_name}",
                task_input=task_input,
                model_name=model_name
            )
            if task_id:
                self.task_starts[run_id] = time.perf_counter()
                self.task_ids[run_id] = task_id
        except Exception as e:
            print(f"[Callback] ERROR in on_llm_start: {e}")

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        """Called when an LLM run ends."""
        try:
            if run_id in self.task_ids:
                task_id = self.task_ids[run_id]
                start_time = self.task_starts.get(run_id, time.perf_counter())
                duration_ms = int((time.perf_counter() - start_time) * 1000)

                # Extract token usage
                token_usage = response.llm_output.get("token_usage", {})
                prompt_tokens = token_usage.get("prompt_tokens")
                completion_tokens = token_usage.get("completion_tokens")
                
                # The output is the content of the first generation
                output = response.generations[0][0].text if response.generations else None

                db_logger.update_task(
                    task_id=task_id,
                    status='completed',
                    output=output,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    duration_ms=duration_ms
                )
                # Clean up after logging
                del self.task_starts[run_id]
                del self.task_ids[run_id]
        except Exception as e:
            print(f"[Callback] ERROR in on_llm_end: {e}")

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], *, run_id: UUID, **kwargs: Any
    ) -> None:
        """Called when an LLM run errors."""
        try:
            if run_id in self.task_ids:
                task_id = self.task_ids[run_id]
                start_time = self.task_starts.get(run_id, time.perf_counter())
                duration_ms = int((time.perf_counter() - start_time) * 1000)

                db_logger.update_task(
                    task_id=task_id,
                    status='failed',
                    error_message=str(error),
                    duration_ms=duration_ms
                )
                # Clean up after logging
                del self.task_starts[run_id]
                del self.task_ids[run_id]
        except Exception as e:
            print(f"[Callback] ERROR in on_llm_error: {e}")

    # Note: You can also implement on_chain_start, on_chain_end, on_tool_start, etc.
    # for even more granular logging if needed in the future.
