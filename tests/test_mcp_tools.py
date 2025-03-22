import os
from unittest.mock import AsyncMock, patch

import pytest

from mcp_pinecone_notes.main import add_note, mcp


@pytest.fixture
def mock_embed():
    with patch("mcp_pinecone_notes.main.embed") as mock:
        mock.text.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
        yield mock


@pytest.fixture
def mock_pinecone_index():
    with patch("mcp_pinecone_notes.main._pinecone_index") as mock:

        async def async_return():
            return None

        mock.upsert = AsyncMock(return_value=async_return())
        yield mock


def test_server_initialization():
    """Test that the MCP server is initialized with correct name."""
    assert mcp.name == "pinecone_notes"
    # Check that tools are registered
    assert mcp.tool is not None


@pytest.mark.asyncio
async def test_add_note(mock_embed, mock_pinecone_index):
    """Test adding a note with mocked dependencies."""
    # Test data
    test_note = "Test note content"

    # Configure environment
    os.environ["PINECONE_API_KEY"] = "test_key"
    os.environ["PINECONE_INDEX"] = "test_index"
    os.environ["PINECONE_HOST"] = "test_host"

    # Call add_note
    result = await add_note(test_note)

    # Verify the result
    assert result["message"] == "Successfully added note."

    # Verify embed.text was called correctly
    mock_embed.text.assert_called_once_with(
        texts=[test_note],
        model="nomic-embed-text-v1.5",
        task_type="search_document",
        inference_mode="local",
    )

    # Verify upsert was called and await it
    mock_pinecone_index.upsert.assert_called_once()
    await mock_pinecone_index.upsert.return_value
