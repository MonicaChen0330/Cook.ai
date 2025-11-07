from . import Document, DocumentLoader
from .ocr_utils import ocr_image_to_text
from .image_utils import image_to_base64_uri
import os

class ImageLoader(DocumentLoader):
    """A loader for standalone image files that performs OCR and converts to base64."""

    def load(self, source: str) -> Document:
        """Reads an image file, performs OCR, and converts it to a base64 URI."""
        try:
            with open(source, "rb") as f:
                image_bytes = f.read()
            
            # Perform OCR on the image
            ocr_text = ocr_image_to_text(image_bytes)
            annotated_text = f"[Text from Image: {os.path.basename(source)}]:\n{ocr_text}\n" if ocr_text else ""

            # Convert image to base64 URI
            base64_image_uri = image_to_base64_uri(image_bytes)
            image_parts = [base64_image_uri] if base64_image_uri else []

            print(f"Successfully processed image {source}")
            return Document(content=annotated_text, source=source, images=image_parts)
        except Exception as e:
            print(f"Error reading image file {source}: {str(e)}")
            raise e
