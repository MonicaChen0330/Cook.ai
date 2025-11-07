import pytesseract
from PIL import Image
import io

def ocr_image_to_text(image_bytes: bytes) -> str:
    """Performs OCR on image bytes and returns the extracted text.
    
    Note: This function requires Tesseract OCR engine to be installed on the system.
    On Debian/Ubuntu: sudo apt install tesseract-ocr
    On macOS: brew install tesseract
    On Windows: Download from https://tesseract-ocr.github.io/tessdoc/Installation.html
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang='chi_tra+eng') # Assuming Traditional Chinese and English
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        print("Error: Tesseract OCR engine not found. Please install it.")
        return "[OCR Error: Tesseract not installed]"
    except Exception as e:
        print(f"Error during OCR: {e}")
        return f"[OCR Error: {e}]"
