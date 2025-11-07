from . import Document, DocumentLoader
from langchain_community.document_loaders import WebBaseLoader
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from .image_utils import image_to_base64_uri

class WebLoader(DocumentLoader):
    """A loader for web pages using LangChain's WebBaseLoader and BeautifulSoup for images."""

    def load(self, source: str) -> Document:
        """Loads content from a URL and extracts images."""
        full_content = ""
        image_parts = []

        try:
            # Use WebBaseLoader for text content
            loader = WebBaseLoader(source)
            langchain_docs = loader.load()
            
            for doc in langchain_docs:
                full_content += doc.page_content + "\n\n"
            
            print(f"Successfully read text content from URL: {source}")

            # Use requests and BeautifulSoup for image extraction
            response = requests.get(source, timeout=10)
            response.raise_for_status() # Raise an exception for HTTP errors
            soup = BeautifulSoup(response.text, 'html.parser')

            for img_tag in soup.find_all('img'):
                img_url = img_tag.get('src')
                if img_url:
                    absolute_img_url = urljoin(source, img_url)
                    try:
                        img_response = requests.get(absolute_img_url, timeout=5)
                        img_response.raise_for_status()
                        base64_image_uri = image_to_base64_uri(img_response.content)
                        if base64_image_uri:
                            image_parts.append(base64_image_uri)
                    except requests.exceptions.RequestException as img_e:
                        print(f"Warning: Could not fetch image {absolute_img_url}: {img_e}")
                    except Exception as img_e:
                        print(f"Warning: Error processing image {absolute_img_url}: {img_e}")

            print(f"Successfully extracted {len(image_parts)} images from URL: {source}")

            return Document(content=full_content.strip(), source=source, images=image_parts)
        except requests.exceptions.RequestException as e:
            error_message = f"Error fetching URL {source}: {str(e)}"
            print(f"{error_message}")
            raise e
        except Exception as e:
            error_message = f"Error reading URL {source}: {str(e)}"
            print(f"{error_message}")
            raise e
