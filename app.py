import os
import streamlit as st
import ollama
import chromadb
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
TOP_K = int(os.getenv("TOP_K", "3"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

st.set_page_config(page_title="local-pdf-chat", layout="wide")
st.title("📄 local-pdf-chat")

# --- Sidebar: Configuration ---
with st.sidebar.expander("⚙️ Settings", expanded=False):
    st.caption(f"Embedding: `{EMBEDDING_MODEL}`")
    st.caption(f"LLM: `{LLM_MODEL}`")
    st.caption(f"Chunk size: `{CHUNK_SIZE}`")
    st.caption(f"Chunk overlap: `{CHUNK_OVERLAP}`")
    st.caption(f"Top-K retrieval: `{TOP_K}`")
    st.caption(f"Batch size: `{BATCH_SIZE}`")

# --- Sidebar: Upload ---
uploaded = st.sidebar.file_uploader("Upload PDF", type="pdf")
if uploaded:
    # Extract text
    reader = PdfReader(uploaded)
    text = "\n".join(p.extract_text() or "" for p in reader.pages)

    # Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_text(text)

    # Progress UI
    progress_bar = st.sidebar.progress(0, text="Starting...")
    status_text = st.sidebar.empty()

    # Embed + Store in Chroma (with progress)
    client = chromadb.Client()
    coll = client.get_or_create_collection("pdf")

    # Process embeddings in larger batches for speed
    total_chunks = len(chunks)
    all_embeddings = []

    for i in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_embeddings = ollama.embed(model=EMBEDDING_MODEL, input=batch)["embeddings"]
        all_embeddings.extend(batch_embeddings)

        # Update progress less frequently (every 10% or at end)
        processed = min(i + BATCH_SIZE, total_chunks)
        pct = int((processed / total_chunks) * 100)
        if pct % 10 == 0 or processed == total_chunks:
            progress_bar.progress(pct / 100, text=f"Embedding: {processed}/{total_chunks} chunks ({pct}%)")
            status_text.info(f"Processing chunk {processed} of {total_chunks}...")

    # Store all embeddings
    progress_bar.progress(1.0, text="Storing in vector DB...")
    coll.add(documents=chunks, embeddings=all_embeddings, ids=[str(i) for i in range(total_chunks)])

    progress_bar.empty()
    status_text.empty()
    st.sidebar.success(f"✅ Indexed {total_chunks} chunks!")

# --- Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    st.chat_message(m["role"]).write(m["content"])

if prompt := st.chat_input("Ask about the PDF..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Search
    client = chromadb.Client()
    coll = client.get_collection("pdf")
    q_emb = ollama.embed(model=EMBEDDING_MODEL, input=[prompt])["embeddings"][0]
    results = coll.query(query_embeddings=[q_emb], n_results=TOP_K)
    context = "\n\n".join(results["documents"][0])

    # Generate
    response = ollama.chat(model=LLM_MODEL, messages=[
        {"role": "system", "content": f"Answer using ONLY this context:\n{context}"},
        {"role": "user", "content": prompt}
    ])
    answer = response["message"]["content"]

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.chat_message("assistant").write(answer)