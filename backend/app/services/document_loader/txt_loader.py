from . import Document, Page, DocumentLoader

class TxtLoader(DocumentLoader):
    """A loader for plain text (.txt) files."""

    def load(self, source: str) -> Document:
        """Reads text from a .txt file and wraps it in a Page object."""
        try:
            with open(source, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Treat the entire file as a single page
            single_page = Page(page_number=1, native_text=content, extracted_images=[])
            
            print(f"Successfully read content from {source}")
            return Document(source=source, pages=[single_page])
        except Exception as e:
            print(f"Error reading TXT file: {str(e)}")
            raise e
