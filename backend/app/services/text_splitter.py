'''
RAG chunking的參數在這裡調
'''
from typing import List, Dict, Any, Tuple
from ..services.document_loader import Page

def chunk_document(
    pages: List[Page],
    chunk_size: int,
    chunk_overlap: int,
    file_name: str,
    uploader_id: int
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Chunks a document by treating it as a single text stream, but intelligently
    tracks which pages each chunk spans.

    Args:
        pages: A list of Page objects from a Document.
        chunk_size: The desired maximum size of each chunk (in characters).
        chunk_overlap: The number of characters to overlap between chunks.
        file_name: The original name of the document file.
        uploader_id: The ID of the user who uploaded the file.

    Returns:
        A list of tuples, where each tuple contains:
        - The text content of the chunk.
        - A rich metadata dictionary (e.g., 
          {'page_numbers': [1, 2], 'file_name': 'sample.pdf', 'uploader_id': 1}).
    """
    
    # 1. Concatenate all page texts and create a map of character index to page number.
    full_text = ""
    char_to_page_map = []
    for page in pages:
        page_text = page.text_for_chunking
        if not page_text:
            continue
        
        start_index = len(full_text)
        full_text += page_text + "\n\n"  # Add separators for clarity
        end_index = len(full_text)
        
        # For each character from this page, map it back to the page number
        for i in range(start_index, end_index):
            char_to_page_map.append(page.page_number)

    # 2. Split the full text into chunks.
    chunks_with_metadata = []
    start_index = 0
    while start_index < len(full_text):
        end_index = start_index + chunk_size
        chunk_text = full_text[start_index:end_index]
        
        # 3. For each chunk, determine the pages it spans.
        # Find the page number at the start and end of the chunk
        start_page = char_to_page_map[start_index] if start_index < len(char_to_page_map) else None
        end_page = char_to_page_map[min(end_index, len(char_to_page_map) - 1)] if start_index < len(char_to_page_map) else None

        page_numbers = []
        if start_page is not None and end_page is not None:
            # Create a unique, sorted list of all pages this chunk touches
            page_numbers = sorted(list(set(range(start_page, end_page + 1))))
        
        # 4. Construct rich metadata.
        metadata = {
            "page_numbers": page_numbers
        }
        
        chunks_with_metadata.append((chunk_text, metadata))
        
        # Move to the next chunk with overlap
        start_index += chunk_size - chunk_overlap
        if start_index >= len(full_text):
            break
            
    return chunks_with_metadata
