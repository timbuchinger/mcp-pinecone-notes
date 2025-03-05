# MCP-Pinecone-Notes

An MCP server for managing notes using Pinecone vector database for semantic search capabilities.

## Installation

You can install mcp-pinecone-notes from PyPI:

```bash
pip install mcp-pinecone-notes
```

Or install from source:

```bash
git clone https://github.com/yourusername/mcp-pinecone-notes.git
cd mcp-pinecone-notes
pip install -e .
```

### Development Setup

For development, first install the package with development dependencies:

```bash
pip install -e .[dev]
```

This will install all required development tools:
- ruff: For linting
- black: For code formatting
- mypy: For type checking
- pytest: For running tests

To run the same lint checks as the CI pipeline:

```bash
# Run linting
ruff check .

# Check code formatting
black --check .

# Run type checking
mypy .

# Run tests
pytest
```

## Configuration

The server can be configured through command line arguments or environment variables. Command line arguments take precedence over environment variables.

### Command Line Arguments

- `--pinecone-api-key`: Your Pinecone API key
- `--pinecone-host`: Host URL for your Pinecone index

Example:
```bash
mcp-pinecone-notes --pinecone-api-key YOUR_KEY --pinecone-host YOUR_HOST
```

With uvx:
```bash
uvx run mcp-pinecone-notes -- --pinecone-api-key YOUR_KEY --pinecone-host YOUR_HOST
```

### Environment Variables

The following environment variables are supported:

- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_INDEX`: Name of your Pinecone index
- `PINECONE_HOST`: Host URL for your Pinecone index
- `PINECONE_NAMESPACE`: (Optional) Namespace for your notes, defaults to "default"

You can set these in a `.env` file or export them in your shell.

## Usage

### Basic Usage

Run the MCP server:

```bash
mcp-pinecone-notes
```

### Development

For development, you can run directly with:

```bash
uv run src/mcp_pinecone_notes/main.py
```

Use the MCP inspector for testing:

```bash
npx @modelcontextprotocol/inspector uvx run mcp-pinecone-notes
npx @modelcontextprotocol/inspector uv run mcp-pinecone-notes -- --pinecone-api-key YOUR_KEY --pinecone-host YOUR_HOST
```

## Docker

Build the Docker image:
```bash
docker build -t mcp-pinecone-notes .
```

Run the container:
```bash
docker run \
  -e PINECONE_API_KEY=<key> \
  -e PINECONE_INDEX=<index> \
  -e PINECONE_HOST=<host> \
  -e PINECONE_NAMESPACE=<namespace> \  # Optional, defaults to "default"
  mcp-pinecone-notes
```

Note: The PINECONE_NAMESPACE environment variable is optional and will default to "default" if not specified.

## MCP Tools

### add_note

Add a note to storage with semantic embedding:

```json
{
  "name": "add_note",
  "arguments": {
    "note": "Your note text here"
  }
}
```

The note will be embedded using the nomic-embed-text-v1.5 model and stored in Pinecone with a unique ID and timestamp.

## Integration in Claude

```json
{
  "mcpServers": {
    "pinecone": {
      "command": "mcp-pinecone-notes",
      "args": []
    }
  }
}

## Update Agent

```bash
cp -r ~/git/mcp-pinecone-notes/agent/ ~/git/github/llm-functions/agents/notes/
```
