from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from .state import ExamGenerationState

# Load environment variables from .env file
# This should be at the very top of your application's entry point
load_dotenv()

from .exam_nodes import (
    read_document_node,
    generate_multiple_choice_node,
    generate_short_answer_node,
    generate_true_false_node,
    handle_error_node,
    route_generation_task_node
)

# Create a new graph
workflow = StateGraph(ExamGenerationState)

# Add the nodes to the graph
workflow.add_node("read_document", read_document_node)
workflow.add_node("generate_multiple_choice", generate_multiple_choice_node)
workflow.add_node("generate_short_answer", generate_short_answer_node)
workflow.add_node("generate_true_false", generate_true_false_node)
workflow.add_node("handle_error", handle_error_node)

# The router node is not explicitly added with add_node, 
# as it's used directly in the conditional edge logic.

# Set the entry point
workflow.set_entry_point("read_document")

# Add the conditional edge after the reader node
# This edge uses the router function to decide the next step
workflow.add_conditional_edges(
    "read_document",
    route_generation_task_node,
    {
        "generate_multiple_choice": "generate_multiple_choice",
        "generate_short_answer": "generate_short_answer",
        "generate_true_false": "generate_true_false",
        "handle_error": "handle_error"
    }
)

# Add normal edges from each generator to the end
workflow.add_edge('generate_multiple_choice', END)
workflow.add_edge('generate_short_answer', END)
workflow.add_edge('generate_true_false', END)
workflow.add_edge('handle_error', END)

# Compile the graph into a runnable app
app = workflow.compile()

# Example of how to run the graph
if __name__ == '__main__':
    import os

    # --- Configuration ---
    # 1. Place a PDF file named 'sample.pdf' in your 'backend' directory.
    # 2. Choose the question type to test below.
    # Possible values: "multiple_choice", "short_answer", "true_false"
    QUESTION_TYPE_TO_TEST = "true_false"
    PDF_FILE_PATH = "sample.pdf" # Path relative to the backend directory

    # Check if the sample PDF exists
    if not os.path.exists(PDF_FILE_PATH):
        print(f"Error: Test file not found at '{PDF_FILE_PATH}'")
        print("Please place a PDF named 'sample.pdf' in the 'backend' directory to run this test.")
        exit()

    # Define the initial input for the graph
    # The query is kept simple as we are focusing on question_type routing
    inputs = {
        "query": f"Generate 5 {QUESTION_TYPE_TO_TEST.replace('_', ' ')} questions based on the document content.",
        "document_path": PDF_FILE_PATH,
        "question_type": QUESTION_TYPE_TO_TEST
    }

    print(f"--- Running graph for question type: '{QUESTION_TYPE_TO_TEST}' on file: '{PDF_FILE_PATH}' ---")

    # Run the graph
    try:
        final_state = app.invoke(inputs)

        print("\n--- Graph execution finished ---")
        if not final_state.get('error'):
            print("\nGenerated Questions:")
            print(final_state.get("generated_questions"))
        else:
            print(f"\nFinal state has an error: {final_state.get('error')}")
    except Exception as e:
        print(f"\nAn exception occurred while running the graph: {e}")
        print("Please ensure your OPENAI_API_KEY is set correctly.")