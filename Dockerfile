FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY src/ src/

RUN pip install -r requirements.txt && \
    pip install ./src

ENV CUDA_VISIBLE_DEVICES=-1

CMD ["mcp-pinecone-notes"]
