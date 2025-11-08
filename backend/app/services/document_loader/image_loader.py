from . import Document, Page, ExtractedImage, DocumentLoader
from .ocr_utils import ocr_image_to_text
from .image_utils import image_to_base64_uri
import os

class ImageLoader(DocumentLoader):
    """A loader for standalone image files that performs OCR and converts to base64."""

    def load(self, source: str) -> Document:
        """Reads an image file, performs OCR, and wraps it in Page/ExtractedImage objects."""
        try:
            with open(source, "rb") as f:
                image_bytes = f.read()
            
            # Perform OCR on the image
            ocr_text = ocr_image_to_text(image_bytes) or ""

            # Convert image to base64 URI
            base64_image_uri = image_to_base64_uri(image_bytes)
            
            # Create an ExtractedImage object
            extracted_image = ExtractedImage(image_uri=base64_image_uri, ocr_text=ocr_text)

            # Treat the image and its OCR text as a single page with no native text
            single_page = Page(page_number=1, native_text="", extracted_images=[extracted_image])

            print(f"Successfully processed image {source}")
            return Document(source=source, pages=[single_page])
        except Exception as e:
            print(f"Error reading image file {source}: {str(e)}")
            raise e
