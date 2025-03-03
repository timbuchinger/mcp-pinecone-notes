import argparse
import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from nomic import embed
from pinecone import Pinecone

# Initialize FastMCP server
mcp = FastMCP("pinecone_notes")

# Global variables
_pinecone_client = None
_pinecone_namespace = None  # Will be set in get_pinecone_client()
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # Disable GPU support


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Pinecone Notes MCP Server")
    parser.add_argument(
        "--pinecone-api-key",
        help="Pinecone API key (overrides environment variable)",
    )
    parser.add_argument(
        "--pinecone-host",
        help="Pinecone host (overrides environment variable)",
    )
    return parser.parse_args()


def get_pinecone_client() -> None:
    global _pinecone_client
    global _pinecone_index
    global _pinecone_namespace

    # Parse command line arguments first
    args = parse_args()

    # Set environment variables from command line args if provided
    if args.pinecone_api_key:
        os.environ["PINECONE_API_KEY"] = args.pinecone_api_key
    if args.pinecone_host:
        os.environ["PINECONE_HOST"] = args.pinecone_host

    # Load environment variables from .env file
    load_dotenv(override=False)

    _pinecone_client = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    _pinecone_index = _pinecone_client.Index(
        os.environ.get("PINECONE_INDEX", ""), host=os.environ.get("PINECONE_HOST", "")
    )
    _pinecone_namespace = os.environ.get("PINECONE_NAMESPACE", "default")


@mcp.tool()
async def add_note(note: str) -> str:
    """Add a note to storage without embeddings.

    Args:
        note: The note to add.
    """

    # Generate vector embedding
    output = embed.text(
        texts=[note],
        model="nomic-embed-text-v1.5",
        task_type="search_document",
        inference_mode="local",
    )

    # Get the first vector since we only embedded one text
    vector = output["embeddings"][0]
    # Insert the document into Pinecone with timestamp
    doc_id = str(uuid.uuid4())
    current_time = datetime.now().isoformat()
    _pinecone_index.upsert(
        vectors=[
            {
                "id": doc_id,
                "values": vector,
                "metadata": {"text": note, "date_added": current_time},
            }
        ],
        namespace=_pinecone_namespace,
    )
    return "Successfully added note."


def main() -> None:
    """Entry point for the Pinecone Notes MCP server."""

    get_pinecone_client()

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
