from . import Document, DocumentLoader
from pptx import Presentation
from .image_utils import image_to_base64_uri
from pptx.enum.shapes import MSO_SHAPE_TYPE
from .ocr_utils import ocr_image_to_text

class PptxLoader(DocumentLoader):
    """A loader for Microsoft PowerPoint (.pptx) files."""

    def load(self, source: str) -> Document:
        """Reads text and extracts images from a .pptx file."""
        try:
            prs = Presentation(source)
            full_text = []
            image_parts = []

            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        full_text.append(shape.text)
                    
                    # Check if the shape is a picture before trying to access its image data
                    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                        image_bytes = shape.image.blob
                        
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
            print(f"Error reading PPTX file: {str(e)}")
            raise e
