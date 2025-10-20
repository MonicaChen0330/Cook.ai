
from app.tools.document import mcp, read_document

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

if __name__ == "__main__":
    run_server()
