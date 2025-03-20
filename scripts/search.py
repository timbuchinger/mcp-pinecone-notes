#!/usr/bin/env python3
import logging
import os
import sys
from typing import Any, Dict, List

from dotenv import load_dotenv
from nomic import embed
from pinecone import Pinecone

# Setup logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("pinecone_search")

# Disable GPU support (matching main.py configuration)
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


def initialize_pinecone() -> tuple[Any, Any]:
    """Initialize Pinecone client and index."""
    # Load environment variables
    load_dotenv(override=False)

    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable is required")

    pinecone_client = Pinecone(api_key=api_key)
    pinecone_host = os.environ.get("PINECONE_HOST")
    if not pinecone_host:
        raise ValueError("PINECONE_HOST environment variable is required")

    pinecone_index = pinecone_client.Index(
        os.environ.get("PINECONE_INDEX", ""),
        host=pinecone_host,
    )

    return pinecone_client, pinecone_index


def get_namespaces(pinecone_index: Any) -> List[str]:
    """Get list of all available namespaces."""
    index_stats = pinecone_index.describe_index_stats()
    return list(index_stats.namespaces.keys())


def display_namespace_menu(namespaces: List[str]) -> None:
    """Display the namespace selection menu."""
    print("\nSelect namespace to search:")
    for i, namespace in enumerate(namespaces, 1):
        print(f"{i}. {namespace}")
    print(f"{len(namespaces) + 1}. all")
    print("0. exit")


def get_embeddings(query: str) -> List[float]:
    """Generate vector embeddings for the query."""
    try:
        embedding_output = embed.text(
            texts=[query],
            model="nomic-embed-text-v1.5",
            task_type="search_document",
            inference_mode="local",
        )
        return embedding_output["embeddings"][0]
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise


def search_namespaces(
    pinecone_index: Any, vector: List[float], namespaces: List[str]
) -> List[Dict[str, Any]]:
    """Search within specified namespaces and return formatted results."""
    all_results = []

    for namespace in namespaces:
        logger.info(f"Searching in namespace: {namespace}")
        try:
            results = pinecone_index.query(
                namespace=namespace,
                vector=vector,
                top_k=3,
                include_metadata=True,
            )

            # Process results
            for match in results.matches:
                metadata = match.metadata if match.metadata else {}
                result = {
                    "content": metadata.get("text", "No content available"),
                    "score": float(match.score) if match.score is not None else 1.0,
                    "source": "notion" if metadata.get("notion_id") else "aichat",
                    "namespace": namespace,
                }

                if metadata.get("title"):
                    result["title"] = metadata["title"]

                all_results.append(result)

        except Exception as e:
            logger.error(f"Error querying namespace {namespace}: {e}")
            continue

    # Sort by score and take top 3 overall
    return sorted(all_results, key=lambda x: x["score"], reverse=True)[:3]


def display_results(results: List[Dict[str, Any]]) -> None:
    """Display search results in a formatted way."""
    if not results:
        print("\nNo matching documents found.")
        return

    print("\nSearch Results:")
    print("-" * 80)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']:.4f} | Namespace: {result['namespace']}")
        if "title" in result:
            print(f"Title: {result['title']}")
        print(f"Content: {result['content']}")
        print("-" * 80)


def main() -> None:
    """Main interactive search loop."""
    try:
        # Initialize Pinecone
        _, pinecone_index = initialize_pinecone()

        while True:
            # Get and display available namespaces
            namespaces = get_namespaces(pinecone_index)
            if not namespaces:
                print("No namespaces found in the index.")
                break

            display_namespace_menu(namespaces)

            # Get namespace choice
            try:
                choice = int(input("\nEnter choice: "))
                if choice == 0:
                    break
                elif choice == len(namespaces) + 1:
                    selected_namespaces = namespaces
                elif 1 <= choice <= len(namespaces):
                    selected_namespaces = [namespaces[choice - 1]]
                else:
                    print("Invalid choice. Please try again.")
                    continue

                # Get search query
                query = input("\nEnter search query: ").strip()
                if not query:
                    print("Query cannot be empty. Please try again.")
                    continue

                # Generate embeddings and search
                vector = get_embeddings(query)
                results = search_namespaces(pinecone_index, vector, selected_namespaces)

                # Display results
                display_results(results)

                # Ask to continue
                if input("\nSearch again? (y/n): ").lower() != "y":
                    break

            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
