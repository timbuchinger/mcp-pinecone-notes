import argparse
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from nomic import embed  # type: ignore
from pinecone import Pinecone  # type: ignore

logging.basicConfig(stream=sys.stderr, level=logging.ERROR)
logger = logging.getLogger("mcp_pinecone_notes")
# Initialize FastMCP server
mcp = FastMCP("pinecone_notes")

# Global variables
_pinecone_client: Optional[Pinecone] = None
_pinecone_index: Any = None
_pinecone_namespace: Optional[str] = None  # Will be set in get_pinecone_client()
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
    parser.add_argument(
        "--pinecone-namespace",
        default="mcp",
        help="Pinecone namespace (overrides environment variable, defaults to 'mcp')",
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
    if args.pinecone_namespace:
        os.environ["PINECONE_NAMESPACE"] = args.pinecone_namespace

    # Load environment variables from .env file
    load_dotenv(override=False)

    _pinecone_client = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    _pinecone_index = _pinecone_client.Index(
        os.environ.get("PINECONE_INDEX", ""),
        host=os.environ.get("PINECONE_HOST", ""),
    )
    _pinecone_namespace = os.environ.get("PINECONE_NAMESPACE", "mcp")


@mcp.tool()
async def search_notes(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """Search notes based on a query.

    Args:
        query: The query to search for.
    """
    logger.info(f"Search request: {query}")

    # Initialize Pinecone client
    api_key = os.environ.get("PINECONE_API_KEY")
    pinecone_client = Pinecone(api_key=api_key)
    pinecone_host = os.environ.get("PINECONE_HOST")
    logger.info(f"Connecting to Pinecone at {pinecone_host}")
    pinecone_index = pinecone_client.Index(
        os.environ.get("PINECONE_INDEX", ""),
        host=pinecone_host,
    )

    logger.info("Preparing embeddings...")
    try:
        embedding_output = embed.text(
            texts=[query],
            model="nomic-embed-text-v1.5",
            task_type="search_document",
            inference_mode="local",
        )
        # Extract the vector from the embeddings output
        vector = embedding_output["embeddings"][0]
        logger.info("Embedding generated successfully")
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return {"documents": []}
    logger.info("embedding complete")

    try:
        # Get list of all namespaces
        index_stats = pinecone_index.describe_index_stats()
        namespaces = list(index_stats.namespaces.keys())
        logger.info(f"Found {len(namespaces)} namespaces: {namespaces}")

        # Query each namespace and collect results
        all_results = []
        for namespace in namespaces:
            logger.info(f"Querying Pinecone for '{namespace}' namespace...")
            results = pinecone_index.query(
                namespace=namespace,
                vector=vector,
                top_k=3,
                include_metadata=True,
            )
            logger.info(f"{namespace} count: {len(results.matches)}")
            # Process results
            for match in results.matches:
                metadata = match.metadata if match.metadata else {}
                # Base result structure
                result = {
                    "content": metadata.get("text", "No content available"),
                    "score": float(match.score) if match.score is not None else 1.0,
                    "source": "notion" if metadata.get("notion_id") else "aichat",
                }

                # Add title only if it exists
                if metadata.get("title"):
                    result["title"] = metadata["title"]

                all_results.append(result)

        # Sort by score and take top 3
        formatted_results = sorted(all_results, key=lambda x: x["score"], reverse=True)[
            :3
        ]

        logger.info(
            f"Returning {len(formatted_results)} documents "
            f"from {len(namespaces)} namespaces."
        )
        return {"documents": formatted_results}

    except Exception as e:
        logger.error(f"Error querying Pinecone: {e}")
        return {"documents": []}


@mcp.tool()
async def add_note(note: str) -> Dict[str, str]:
    """Add a note to storage.

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
    await _pinecone_index.upsert(
        vectors=[
            {
                "id": doc_id,
                "values": vector,
                "metadata": {"text": note, "date_added": current_time},
            }
        ],
        namespace=_pinecone_namespace,
    )
    return {"message": "Successfully added note."}


def main() -> None:
    """Entry point for the Pinecone Notes MCP server."""

    get_pinecone_client()

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
