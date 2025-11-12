
from typing import List
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmbeddingService:
    """
    A service for generating text embeddings using OpenAI's API.
    """
    _instance = None
    _client = None
    _model_name = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            
            # Initialize OpenAI client only once
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_BASE_URL") # Optional, for custom endpoints
            
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set for EmbeddingService.")
            
            cls._client = OpenAI(api_key=api_key, base_url=base_url)
            cls._model_name = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
            
            print(f"OpenAI EmbeddingService initialized with model: {cls._model_name}")
        return cls._instance

    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a list of texts using OpenAI's API.

        Args:
            texts: A list of strings to be embedded.

        Returns:
            A list of embedding vectors (each as a list of floats).
        """
        if not texts:
            return []
        
        print(f"Generating embeddings for {len(texts)} text chunks using OpenAI model: {self._model_name}...")
        
        try:
            response = self._client.embeddings.create(
                input=texts,
                model=self._model_name
            )
            embeddings = [data.embedding for data in response.data]
            print("Embeddings generated successfully.")
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings with OpenAI: {e}")
            raise

# Singleton instance for easy access
embedding_service = EmbeddingService()

