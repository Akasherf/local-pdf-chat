import importlib
import os
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """Test that all required modules can be imported."""
    modules = [
        "streamlit",
        "ollama",
        "chromadb",
        "pypdf",
        "langchain_text_splitters",
        "dotenv",
    ]
    for module in modules:
        importlib.import_module(module)


def test_config_defaults():
    """Test configuration defaults."""
    from app import (
        BATCH_SIZE,
        CHUNK_OVERLAP,
        CHUNK_SIZE,
        EMBEDDING_MODEL,
        LLM_MODEL,
        TOP_K,
    )

    assert EMBEDDING_MODEL == "nomic-embed-text"
    assert LLM_MODEL == "llama3.1:8b"
    assert CHUNK_SIZE == 500
    assert CHUNK_OVERLAP == 50
    assert TOP_K == 3
    assert BATCH_SIZE == 100


def test_text_splitter():
    """Test text splitting functionality."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
    text = "This is a test document. " * 10
    chunks = splitter.split_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 120 for c in chunks)  # chunk_size + overlap


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
