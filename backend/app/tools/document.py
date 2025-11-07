
from app.services.document_loader import get_loader
from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP()

@mcp.tool()
def read_document(source: str) -> str:
    """Reads the text content and extracts images from a specified document source (e.g., a PDF file path).

    Args:
        source: The path or identifier of the document to read.

    Returns:
        A JSON string containing the extracted text content ('content') and a list of base64 encoded image URIs ('images'), or an error message if reading fails.
    """
    print(f"Attempting to read document from source: {source}")
    try:
        loader = get_loader(source)
        document = loader.load(source)
        print(f"Successfully read content from {source}")
        return json.dumps({"content": document.content, "images": document.images})
    except Exception as e:
        error_message = f"Error reading document: {str(e)}"
        print(f"{error_message}")
        return json.dumps({"error": error_message})
