
from app.tools.document import mcp, read_document
import os
import glob
import json
from app.agents.material_generator.graph import app as material_generator_app

def run_server():
    """Registers all tools and runs the MCP server."""
    print("🚀 Starting MCP Server on port 8000...")
    
    # Register the generic read_document tool
    mcp.register(read_document)
    
    # You can register more tools here in the future
    # mcp.register(another_tool)
    
    # Start the server
    print("Tools registered. Starting server...")
    mcp.run(transport="sse", port=8000)

def test_document_loaders():
    print("\n--- Starting Document Loader Test ---")
    
    while True:
        try:
            source_path = input("Enter file path or URL to test (e.g., test_files/sample.txt or https://www.example.com, or 'q' to quit): ")
            if source_path.lower() == 'q':
                break
            if not source_path:
                continue

            print(f"\n--- Testing source: {source_path} ---")
            try:
                # Call the read_document tool
                result_json_str = read_document(source_path)
                result = json.loads(result_json_str)

                if "error" in result:
                    print(f"Error: {result["error"]}")
                else:
                    content = result.get("content", "")
                    images = result.get("images", [])
                    
                    print("Extracted Text (first 500 chars):\n")
                    print(content[:1500] + ("..." if len(content) > 1500 else ""))
                    print(f"\nTotal Images Extracted: {len(images)}")
                    if images:
                        print("First Image URI (truncated):\n")
                        print(images[0][:100] + "...")

            except json.JSONDecodeError:
                print(f"Failed to decode JSON from tool output: {result_json_str}")
            except Exception as e:
                print(f"An unexpected error occurred during test for {source_path}: {e}")
        except EOFError:
            print("\nEOF received, exiting test.")
            break
        except KeyboardInterrupt:
            print("\nTest interrupted by user.")
            break

    print("\n--- Document Loader Test Finished ---")

def test_agent_material_generation():
    print("\n--- Starting Agent Material Generation Test ---")
    while True:
        try:
            document_source = input("Enter document path or URL for agent (e.g., test_files/sample.txt or https://www.example.com, or 'q' to quit): ")
            if document_source.lower() == 'q':
                break
            if not document_source:
                print("Document source cannot be empty.")
                continue

            question_type = input("Enter question type (multiple_choice, short_answer, true_false): ")
            if question_type not in ["multiple_choice", "short_answer", "true_false"]:
                print("Invalid question type. Please choose from multiple_choice, short_answer, true_false.")
                continue
            
            user_query = input("Enter your query for the agent (e.g., 'Generate 5 questions based on the document'): ")
            if not user_query:
                print("Query cannot be empty.")
                continue

            print(f"\n--- Running agent for source: {document_source}, type: {question_type} ---")
            
            inputs = {
                "query": user_query,
                "document_path": document_source,
                "question_type": question_type
            }

            try:
                final_state = material_generator_app.invoke(inputs)

                print("\n--- Agent execution finished ---")
                if not final_state.get('error'):
                    print("\nGenerated Questions:")
                    print(final_state.get("generated_questions"))
                else:
                    print(f"\nFinal state has an error: {final_state.get('error')}")
            except Exception as e:
                print(f"\nAn exception occurred while running the agent: {e}")
                print("Please ensure your OPENAI_API_KEY is set correctly and the document is accessible.")

        except EOFError:
            print("\nEOF received, exiting test.")
            break
        except KeyboardInterrupt:
            print("\nTest interrupted by user.")
            break
    print("\n--- Agent Material Generation Test Finished ---")

def test_google_drive_loader():
    print("\n--- Starting Google Drive Loader Test ---")
    print("Note: The first time you run this, a browser window will open for authentication.")
    while True:
        try:
            drive_source = input("Enter Google Drive File ID or shareable link (or 'q' to quit): ")
            if drive_source.lower() == 'q':
                break
            if not drive_source:
                continue

            print(f"\n--- Testing Google Drive source: {drive_source} ---")
            try:
                result_json_str = read_document(drive_source)
                result = json.loads(result_json_str)

                if "error" in result:
                    print(f"Error: {result["error"]}")
                else:
                    content = result.get("content", "")
                    images = result.get("images", [])
                    
                    print("Extracted Text (first 500 chars):\n")
                    print(content[:1500] + ("..." if len(content) > 1500 else ""))
                    print(f"\nTotal Images Extracted: {len(images)}")
                    if images:
                        print("First Image URI (truncated):\n")
                        print(images[0][:100] + "...")

            except json.JSONDecodeError:
                print(f"Failed to decode JSON from tool output: {result_json_str}")
            except Exception as e:
                print(f"An unexpected error occurred during test for {drive_source}: {e}")
        except EOFError:
            print("\nEOF received, exiting test.")
            break
        except KeyboardInterrupt:
            print("\nTest interrupted by user.")
            break
    print("\n--- Google Drive Loader Test Finished ---")

if __name__ == "__main__":
    while True:
        print("\nChoose a test to run:")
        print("1. Document Loader Test")
        print("2. Agent Material Generation Test")
        print("3. Google Drive Loader Test")
        print("q. Quit")
        choice = input("Enter your choice (1, 2, 3, or q): ")

        if choice == '1':
            test_document_loaders()
        elif choice == '2':
            test_agent_material_generation()
        elif choice == '3':
            test_google_drive_loader()
        elif choice.lower() == 'q':
            break
        else:
            print("Invalid choice. Please try again.")

    # run_server() # Commented out to run tests instead of server
