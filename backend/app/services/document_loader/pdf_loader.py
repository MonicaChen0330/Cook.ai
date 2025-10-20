
import pypdf
import base64
import io
from PIL import Image
from . import Document, DocumentLoader

class PdfLoader(DocumentLoader):
    """A loader for PDF files that extracts text and converts images to a web-safe format."""

    def load(self, source: str) -> Document:
        """Reads text and extracts/converts images from a PDF."""
        try:
            with open(source, "rb") as f:
                reader = pypdf.PdfReader(f)
                text_parts = []
                image_parts = []

                for page_num, page in enumerate(reader.pages):
                    # Extract text
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                    
                    # Extract and convert images
                    for i, image_file_object in enumerate(page.images):
                        try:
                            # Open the raw image data with Pillow
                            raw_image = io.BytesIO(image_file_object.data)
                            pil_image = Image.open(raw_image)

                            # Convert to PNG and write to an in-memory buffer
                            with io.BytesIO() as buffer:
                                pil_image.save(buffer, format="PNG")
                                png_image_bytes = buffer.getvalue()

                            # Encode the PNG bytes in base64
                            base64_image = base64.b64encode(png_image_bytes).decode('utf-8')
                            image_uri = f"data:image/png;base64,{base64_image}"
                            image_parts.append(image_uri)
                            # print(f"Successfully converted and extracted image {i+1} from page {page_num + 1}.")
                        except Exception as e:
                            print(f"Warning: Could not process an image on page {page_num + 1}: {e}")

                full_content = "\n\n".join(text_parts)
                print(f"Successfully read content and {len(image_parts)} images from {source}")
                return Document(content=full_content, source=source, images=image_parts)

        except Exception as e:
            print(f"Error reading PDF: {str(e)}")
            raise e
