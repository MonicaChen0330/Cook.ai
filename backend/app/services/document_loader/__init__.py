
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List
import os

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
    _, extension = os.path.splitext(source)
    extension = extension.lower()

    if extension == '.pdf':
        from .pdf_loader import PdfLoader
        return PdfLoader()
    # Example for future expansion
    # elif source.startswith('http://') or source.startswith('https://'):
    #     from .web_loader import WebLoader
    #     return WebLoader()
    else:
        raise ValueError(f"Unsupported source type: {source}")

