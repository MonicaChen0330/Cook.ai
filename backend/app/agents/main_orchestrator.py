from typing import TypedDict, Dict, Any
import json
from langgraph.graph import StateGraph, END
from openai import OpenAI
from dotenv import load_dotenv

# --- 1. Load environment, clients, and the AGENT REGISTRY ---
load_dotenv()
client = OpenAI()

from .registry import AGENT_REGISTRY
from .material_generator.graph import app as material_generator_app

# --- 2. Define the State for the Main Orchestrator ---
class MainOrchestratorState(TypedDict):
    user_query: str
    document_path: str
    parsed_task: Dict[str, Any]
    final_result: Any
    error: str | None

# --- 3. Define the Nodes for the Main Orchestrator ---

def analyze_query_node(state: MainOrchestratorState) -> MainOrchestratorState:
    """Dynamically analyzes the user's query based on the agent registry."""
    print("--- L3 Orchestrator: Analyzing Query Node ---")
    
    # Dynamically generate the list of available tasks from the registry
    available_tasks_str = "\n".join([
        f"- `{agent['task_name']}`: {agent['description']}" for agent in AGENT_REGISTRY
    ])

    prompt = f"""Analyze the user's query and extract the task and its parameters into a JSON object.

**User Query:** "{state['user_query']}"

**Available Tasks:**
{available_tasks_str}

**JSON Output Schema:**
{{
  "task": "<task_name>",
  "parameters": {{
    "question_type": "<e.g., multiple_choice>",
    "quantity": <number_of_questions>
  }}
}}

Provide the JSON object based on the user query.""" 
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful assistant that parses user requests into structured JSON."},
                {"role": "user", "content": prompt},
            ]
        )
        parsed_json = json.loads(response.choices[0].message.content)
        state["parsed_task"] = parsed_json
        print(f"Parsed Task: {state['parsed_task']}")
    except Exception as e:
        state["error"] = f"Failed to parse query: {e}"
    return state

def route_task_node(state: MainOrchestratorState) -> str:
    """Dynamically routes to the appropriate handler based on the registry."""
    print("--- L3 Orchestrator: Routing Task Node ---")
    if state.get("error"):
        return "handle_error"
    
    parsed_task_name = state.get("parsed_task", {}).get("task")
    
    # Look up the handler node in the registry
    for agent in AGENT_REGISTRY:
        if agent["task_name"] == parsed_task_name:
            return agent["handler_node_name"]
    
    # If no matching agent is found
    return "handle_unsupported_task"

def run_exam_generator_node(state: MainOrchestratorState) -> MainOrchestratorState:
    """Invokes the exam generation sub-graph."""
    print("--- L3 Orchestrator: Invoking Exam Generator Sub-Graph ---")
    task_params = state["parsed_task"].get("parameters", {})
    sub_graph_input = {
        "query": state["user_query"],
        "document_path": state["document_path"],
        "question_type": task_params.get("question_type", "multiple_choice")
    }
    print(f"Calling sub-graph with input: {sub_graph_input}")
    final_sub_state = material_generator_app.invoke(sub_graph_input)
    
    if final_sub_state.get("error"):
        state["error"] = f"Sub-graph execution failed: {final_sub_state['error']}"
    else:
        state["final_result"] = final_sub_state.get("generated_questions")
    return state

def handle_unsupported_task_node(state: MainOrchestratorState) -> MainOrchestratorState:
    """Provides a polite response for unsupported tasks."""
    print("--- L3 Orchestrator: Unsupported Task Handler ---")
    task = state.get("parsed_task", {}).get("task", "unknown")
    polite_message = f"非常抱歉，我目前還無法處理『{task}』這個任務，但我正在努力學習中！我目前主要支援生成不同類型的題目。"
    state["final_result"] = polite_message
    return state

def handle_error_node(state: MainOrchestratorState) -> MainOrchestratorState:
    """Handles errors for the main orchestrator."""
    print(f"--- L3 Orchestrator: Error Handler ---")
    error_message = f"Error: {state['error']}"
    print(error_message)
    state["final_result"] = error_message
    return state

# --- 4. Build and Compile the Main Orchestrator Graph ---

# Create a mapping from the handler names in the registry to the actual node functions
NODE_HANDLERS = {
    "run_exam_generator": run_exam_generator_node,
    # Add other handlers here as you create them, e.g.:
    # "run_summarizer": run_summarizer_node,
}

workflow = StateGraph(MainOrchestratorState)

workflow.add_node("analyze_query", analyze_query_node)
workflow.add_node("handle_unsupported_task", handle_unsupported_task_node)
workflow.add_node("handle_error", handle_error_node)

# Add nodes from the registry handlers
for handler_name, handler_func in NODE_HANDLERS.items():
    workflow.add_node(handler_name, handler_func)

workflow.set_entry_point("analyze_query")

# The routing logic is now fully dynamic based on the registry
workflow.add_conditional_edges(
    "analyze_query",
    route_task_node,
    {
        **{agent["handler_node_name"]: agent["handler_node_name"] for agent in AGENT_REGISTRY},
        "handle_unsupported_task": "handle_unsupported_task",
        "handle_error": "handle_error"
    }
)

# Connect all registered handlers to the end
for handler_name in NODE_HANDLERS.keys():
    workflow.add_edge(handler_name, END)

workflow.add_edge("handle_unsupported_task", END)
workflow.add_edge("handle_error", END)

main_orchestrator_app = workflow.compile()

# --- 5. Interactive Runner for the Main Orchestrator ---

if __name__ == '__main__':
    import os

    PDF_FILE_PATH = "sample.pdf"
    
    if not os.path.exists(PDF_FILE_PATH):
        print(f"Error: Test file not found at '{PDF_FILE_PATH}'. Please run this from the 'backend' directory.")
        exit()

    print("--- AI 教材小幫手已啟動 ---")
    print("請輸入您的指令，或輸入 'exit' 來離開。")
    print("範例指令：請幫我出 5 題是非題")

    while True:
        user_query = input("\n> ")
        if user_query.lower() in ["exit", "quit"]:
            break
        if not user_query:
            continue

        inputs = {
            "user_query": user_query,
            "document_path": PDF_FILE_PATH,
        }

        print("--- ...總協調器執行中... ---")
        final_state = main_orchestrator_app.invoke(inputs)
        print("--- ...總協調器執行完畢... ---")

        print("\nAI 回應:")
        print("-" * 20)
        print(final_state.get("final_result"))
        print("-" * 20)
