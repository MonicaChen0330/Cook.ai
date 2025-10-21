from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List
import os
import re

@dataclass
class Document:
    """A dataclass to represent a loaded document, potentially with images."""
    content: str
    source: str  # e.g., file path or URL
    images: List[str] = field(default_factory=list) # List of base64 encoded images

class DocumentLoader(ABC):
    """Abstract base class for document loaders."""
    @abstractmethod
    def load(self, source: str) -> Document:
        """Load a document from a given source and return a Document object."""
        pass

def get_loader(source: str) -> DocumentLoader:
    """
    Factory function to get the appropriate document loader based on the source.
    """
    # Check for Google Drive ID or URL first
    if re.match(r"^[a-zA-Z0-9_-]{28,33}$", source) or \
       re.search(r"id=([a-zA-Z0-9_-]+)", source) or \
       re.search(r"/d/([a-zA-Z0-9_-]+)", source):
        from .google_drive_loader import GoogleDriveLoader
        return GoogleDriveLoader()

    if source.startswith('http://') or source.startswith('https://'):
        from .web_loader import WebLoader
        return WebLoader()

    _, extension = os.path.splitext(source)
    extension = extension.lower()

    if extension == '.pdf':
        from .pdf_loader import PdfLoader
        return PdfLoader()
    elif extension == '.txt':
        from .txt_loader import TxtLoader
        return TxtLoader()
    elif extension == '.docx':
        from .docx_loader import DocxLoader
        return DocxLoader()
    elif extension == '.pptx':
        from .pptx_loader import PptxLoader
        return PptxLoader()
    elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
        from .image_loader import ImageLoader
        return ImageLoader()
    else:
        raise ValueError(f"Unsupported source type: {source}")
