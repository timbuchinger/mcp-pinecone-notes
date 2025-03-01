# Technical Context

## Technology Stack
- **Python**: Primary implementation language
- **MCP (Model Context Protocol)**: Server framework for tool exposure
- **Pinecone**: Vector database for storing note embeddings
- **Nomic**: Text embedding generation
- **python-dotenv**: Environment configuration management

## Development Setup
1. Environment Variables Required:
   - PINECONE_API_KEY
   - PINECONE_INDEX
   - PINECONE_HOST
   - PINECONE_NAMESPACE (optional, defaults to "default")

2. Runtime Dependencies:
   - MCP SDK
   - Pinecone Python client
   - Nomic for embeddings
   - python-dotenv for configuration

## Technical Constraints
1. **GPU Support**: Currently disabled (CUDA_VISIBLE_DEVICES=-1)
2. **Embedding Model**: Uses nomic-embed-text-v1.5 with local inference
3. **Transport**: Uses stdio for MCP communication

## Infrastructure
- **Vector Storage**: Pinecone serverless infrastructure
- **Embedding Generation**: Local inference using Nomic
- **Server Communication**: MCP stdio transport

## Development Commands
```bash
# Run the server
uv run mcp_pinecone_notes

# Alternative direct execution
uv run src/mcp_pinecone_notes/main.py

# Run with MCP inspector
npx @modelcontextprotocol/inspector uv run src/mcp_pinecone_notes/main.py
```

## Dependencies Management
- Using `uv` for Python package management
- Dependencies tracked in:
  - src/pyproject.toml
  - src/uv.lock
