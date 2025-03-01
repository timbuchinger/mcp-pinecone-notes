import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from nomic import embed
from pinecone import Pinecone

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU support
# Document text for embedding
text: str = "This is a test document for vector search"

# Load environment variables first
load_dotenv()

# Generate vector embedding
output: Dict[str, List[List[float]]] = embed.text(
    texts=[text],
    model="nomic-embed-text-v1.5",
    task_type="search_document",
    inference_mode="local",
    device_type="cpu",  # Explicitly use CPU
)
# Get the first vector since we only embedded one text
vector: List[float] = output["embeddings"][0]

pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY", ""))

# Initialize Pinecone index
index = pc.Index("notes", host=os.environ.get("PINECONE_HOST", ""))

# Insert the document into Pinecone
index.upsert(vectors=[{"id": "doc1", "values": vector, "metadata": {"text": text}}])
