
import pdfplumber
import base64
import io
from PIL import Image
from . import Document, Page, DocumentLoader
from .ocr_utils import ocr_image_to_text
from .image_utils import image_to_base64_uri

class PdfLoader(DocumentLoader):
    """A loader for PDF files that extracts text and converts images to a web-safe format."""

    def load(self, source: str) -> Document:
        """Reads text and extracts/converts images from a PDF on a page-by-page basis."""

        doc_pages = []

        try:
            with pdfplumber.open(source) as pdf:
                for page_num, page in enumerate(pdf.pages):

                    # 處理文字
                    text_elements = []                    
                    for block in page.extract_text_lines(keep_blank_chars=True):
                        text_elements.append({
                            "type": "text",
                            "content": block["text"],
                            "top": block["top"] # 儲存垂直位置
                        })
                    
                    # 處理圖片
                    image_elements = []
                    for img in page.images:
                        image_data = img.get("stream").get_data() 
                        
                        if not image_data:
                            continue

                        base64_string = image_to_base64_uri(image_data) # 轉 Base64
                        ocr_text_result = ocr_image_to_text(image_data) # OCR提取圖片文字

                        image_elements.append({
                            "type": "image",
                            "base64": base64_string,
                            "ocr_text": ocr_text_result,
                            "top": img["top"] # 儲存垂直位置
                        })

                    # 依垂直位置 (top) 排序所有元素
                    all_elements = sorted(text_elements + image_elements, key=lambda x: x["top"])

                    # 移除 'top' 鍵，因為資料庫不需要它
                    structured_elements_for_this_page = []
                    for el in all_elements:
                        el.pop("top") # 刪除 'top'
                        structured_elements_for_this_page.append(el)

                    # 建立新的 Page 物件
                    new_page_object = Page(
                        page_number=page_num + 1,
                        structured_elements=structured_elements_for_this_page
                    )
                    doc_pages.append(new_page_object)
                    
                print(f"Successfully read {len(doc_pages)} pages from {source}")
                return Document(source=source, pages=doc_pages)

        except Exception as e:
            print(f"Error reading PDF with pdfplumber: {str(e)}")
            raise e
