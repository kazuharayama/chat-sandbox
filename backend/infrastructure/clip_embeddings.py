import logging
from typing import List

from langchain_core.embeddings import Embeddings
from PIL import Image
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "clip-ViT-B-32"


class CLIPTextEmbeddings(Embeddings):
    """CLIP text encoder for LangChain compatibility."""

    def __init__(self, model_name: str = MODEL_NAME):
        self.model = SentenceTransformer(model_name)
        logger.info("CLIP text encoder loaded: %s", model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()


class CLIPImageEncoder:
    """CLIP image encoder for generating image embeddings."""

    def __init__(self, model_name: str = MODEL_NAME):
        self.model = SentenceTransformer(model_name)
        logger.info("CLIP image encoder loaded: %s", model_name)

    def encode_image(self, image_path: str) -> List[float]:
        image = Image.open(image_path).convert("RGB")
        embedding = self.model.encode(image, convert_to_numpy=True)
        return embedding.tolist()

    def encode_images(self, image_paths: List[str]) -> List[List[float]]:
        images = [Image.open(p).convert("RGB") for p in image_paths]
        embeddings = self.model.encode(images, convert_to_numpy=True)
        return embeddings.tolist()
