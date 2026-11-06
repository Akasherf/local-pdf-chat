import os
import hashlib
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

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_indexed" not in st.session_state:
    st.session_state.pdf_indexed = False
if "pdf_hash" not in st.session_state:
    st.session_state.pdf_hash = None
if "collection_name" not in st.session_state:
    st.session_state.collection_name = None
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None

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
    # Compute file hash
    file_bytes = uploaded.getvalue()
    current_hash = hashlib.sha256(file_bytes).hexdigest()[:16]

    # Check if new PDF or same PDF
    is_new_pdf = st.session_state.pdf_hash != current_hash

    if is_new_pdf:
        # Reset state for new PDF
        st.session_state.messages = []
        st.session_state.pdf_indexed = False
        st.session_state.pdf_hash = current_hash
        st.session_state.collection_name = f"pdf_{current_hash}"
        st.session_state.pdf_name = uploaded.name

        # Process new PDF
        try:
            # Extract text
            uploaded.seek(0)
            reader = PdfReader(uploaded)
            text = "\n".join(p.extract_text() or "" for p in reader.pages)

            if not text.strip():
                st.sidebar.error("❌ No text extracted. PDF may be scanned or empty.")
                st.stop()

            # Chunk
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
            )
            chunks = splitter.split_text(text)

            if not chunks:
                st.sidebar.error("❌ No chunks created from PDF text.")
                st.stop()

            # Progress UI
            progress_bar = st.sidebar.progress(0, text="Starting...")
            status_text = st.sidebar.empty()

            # Embed + Store in Chroma (with progress)
            client = chromadb.Client()
            coll = client.get_or_create_collection(st.session_state.collection_name)

            # Process embeddings in larger batches for speed
            total_chunks = len(chunks)
            all_embeddings = []

            for i in range(0, total_chunks, BATCH_SIZE):
                batch = chunks[i : i + BATCH_SIZE]
                batch_embeddings = ollama.embed(model=EMBEDDING_MODEL, input=batch)[
                    "embeddings"
                ]
                all_embeddings.extend(batch_embeddings)

                # Update progress less frequently (every 10% or at end)
                processed = min(i + BATCH_SIZE, total_chunks)
                pct = int((processed / total_chunks) * 100)
                if pct % 10 == 0 or processed == total_chunks:
                    progress_bar.progress(
                        pct / 100,
                        text=f"Embedding: {processed}/{total_chunks} chunks ({pct}%)",
                    )
                    status_text.info(
                        f"Processing chunk {processed} of {total_chunks}..."
                    )

            # Store all embeddings
            progress_bar.progress(1.0, text="Storing in vector DB...")
            coll.add(
                documents=chunks,
                embeddings=all_embeddings,
                ids=[str(i) for i in range(total_chunks)],
            )

            progress_bar.empty()
            status_text.empty()
            st.sidebar.success(
                f"✅ Indexed {total_chunks} chunks from **{uploaded.name}**"
            )
            st.session_state.pdf_indexed = True

        except Exception as e:
            st.sidebar.error(f"❌ Error processing PDF: {str(e)}")
            st.session_state.pdf_indexed = False
            st.stop()

# Show current PDF status
if st.session_state.pdf_indexed:
    st.sidebar.info(f"📄 **Current:** {st.session_state.pdf_name}")
    if st.sidebar.button("🗑️ Clear & Upload New"):
        for key in [
            "messages",
            "pdf_indexed",
            "pdf_hash",
            "collection_name",
            "pdf_name",
        ]:
            st.session_state[key] = [] if key == "messages" else None
        st.rerun()

# --- Chat ---
# Display messages
for m in st.session_state.messages:
    st.chat_message(m["role"]).write(m["content"])

# Chat input - disabled until PDF indexed
chat_disabled = not st.session_state.pdf_indexed
placeholder = (
    "Ask about the PDF..." if st.session_state.pdf_indexed else "📤 Upload a PDF first"
)

if prompt := st.chat_input(placeholder, disabled=chat_disabled):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    try:
        # Search
        client = chromadb.Client()
        coll = client.get_collection(st.session_state.collection_name)
        q_emb = ollama.embed(model=EMBEDDING_MODEL, input=[prompt])["embeddings"][0]
        results = coll.query(query_embeddings=[q_emb], n_results=TOP_K)
        context = "\n\n".join(results["documents"][0])

        # Build conversation history (last 6 messages = 3 exchanges)
        history = []
        for m in st.session_state.messages[-6:]:
            history.append({"role": m["role"], "content": m["content"]})

        # Generate with context + history
        messages = [
            {
                "role": "system",
                "content": f"Answer using ONLY this context:\n{context}",
            },
        ] + history

        response = ollama.chat(model=LLM_MODEL, messages=messages)
        answer = response["message"]["content"]

    except Exception as e:
        answer = f"❌ Error: {str(e)}"
        if "collection" in str(e).lower():
            answer += "\n\nTry re-uploading the PDF."

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.chat_message("assistant").write(answer)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("local-pdf-chat • 100% local • Powered by Ollama")
