from . import Document, DocumentLoader
from docx import Document as DocxDocument
from .image_utils import image_to_base64_uri
from .ocr_utils import ocr_image_to_text

class DocxLoader(DocumentLoader):
    """A loader for Microsoft Word (.docx) files."""

    def load(self, source: str) -> Document:
        """Reads text and extracts images from a .docx file."""
        try:
            doc = DocxDocument(source)
            full_text = []
            image_parts = []

            for para in doc.paragraphs:
                full_text.append(para.text)
            
            # Extract images from inline shapes
            for rel in doc.part.rels:
                if "image" in doc.part.rels[rel].target_ref:
                    image_part = doc.part.rels[rel].target_part
                    image_bytes = image_part.blob
                    
                    # Perform OCR on the image
                    ocr_text = ocr_image_to_text(image_bytes)
                    if ocr_text:
                        full_text.append(f"\n[Text from Image]:\n{ocr_text}\n")

                    base64_image_uri = image_to_base64_uri(image_bytes)
                    if base64_image_uri:
                        image_parts.append(base64_image_uri)

            content = "\n".join(full_text)
            print(f"Successfully read content and {len(image_parts)} images from {source}")
            return Document(content=content, source=source, images=image_parts)
        except Exception as e:
            print(f"Error reading DOCX file: {str(e)}")
            raise e
