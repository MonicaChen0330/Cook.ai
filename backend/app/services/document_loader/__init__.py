from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import os
import re

@dataclass
class ExtractedImage:
    """A dataclass to hold an image's URI and its OCR'd text."""
    image_uri: str
    ocr_text: str

@dataclass
class Page:
    """A dataclass to represent a single page of a document, with distinct text and image sources."""
    page_number: int
    structured_elements: List[Dict[str, Any]]
    extracted_images: List[ExtractedImage] = field(default_factory=list)

    generated_text_for_chunking: Optional[str] = field(init=False, default=None)

@dataclass
class Document:
    """A dataclass to represent a loaded document, with page-by-page content."""
    source: str  # e.g., file path or URL
    pages: List[Page] = field(default_factory=list)
    
    @property
    def content(self) -> str:
        """Returns the full text content by concatenating all pages."""
        return "\n\n".join([page.text for page in self.pages if page.text])

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
