
from . import Document, DocumentLoader

class TxtLoader(DocumentLoader):
    """A loader for plain text (.txt) files."""

    def load(self, source: str) -> Document:
        """Reads text from a .txt file."""
        try:
            with open(source, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"Successfully read content from {source}")
            return Document(content=content, source=source)
        except Exception as e:
            print(f"Error reading TXT file: {str(e)}")
            raise e
