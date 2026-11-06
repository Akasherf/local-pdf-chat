# 📄 local-pdf-chat

A privacy-first, fully local Retrieval-Augmented Generation (RAG) application that lets you chat with any PDF using local LLMs via Ollama. No data leaves your machine.

## ✨ Features

- **100% Local & Private** - Runs entirely on your machine, no API keys needed
- **Progress Tracking** - Real-time progress bar during PDF indexing (10% increments)
- **Optimized Performance** - Batched embeddings (100 chunks/call) for fast processing
- **Streamlit UI** - Clean, responsive chat interface
- **Persistent Models** - Keep models loaded in RAM for instant responses

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   PDF File  │────▶│  Text Split │────▶│  Embeddings │
│  (PyPDF)    │     │ (LangChain) │     │ (Ollama)    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌─────────────┐             │
                    │  ChromaDB   │◀────────────┘
                    │ (Vector DB) │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐     ┌─────────────┐
                    │  Retrieval  │────▶│    LLM      │
                    │  (Top-K)    │     │ (Ollama)    │
                    └─────────────┘     └─────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) installed

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/local-pdf-chat.git
cd local-pdf-chat

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Pull required models (one-time)
ollama pull nomic-embed-text
ollama pull llama3.1:8b
```

### Running

```bash
# Terminal 1: Start Ollama with persistent models
OLLAMA_KEEP_ALIVE=-1 ollama serve

# Terminal 2: Run the app
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

## 📖 Usage

1. **Upload a PDF** using the sidebar file uploader
2. **Wait for indexing** - progress bar shows real-time status
3. **Ask questions** in the chat input at the bottom
4. **Get answers** grounded in your PDF content

## ⚙️ Configuration

Environment variables (create `.env` file):

```env
# Model settings
EMBEDDING_MODEL=nomic-embed-text
LLM_MODEL=llama3.1:8b

# Chunking
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Retrieval
TOP_K=3

# Batch processing
BATCH_SIZE=100
```

## 📁 Project Structure

```
local-pdf-chat/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── .env.example          # Environment template
├── LICENSE               # MIT License
├── README.md             # This file
├── Makefile              # Development commands
├── Dockerfile            # Container build
├── docker-compose.yml    # Multi-container deployment
├── .github/workflows/    # CI/CD pipelines
└── tests/                # Unit tests
```

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| UI Framework | Streamlit |
| LLM & Embeddings | Ollama (local) |
| Vector Database | ChromaDB |
| PDF Processing | PyPDF |
| Text Splitting | LangChain Text Splitters |

## 🎯 Roadmap

- [ ] Multiple PDF support
- [ ] Chat history persistence
- [ ] Model selection dropdown
- [ ] Export chat as Markdown/PDF
- [ ] Dark mode toggle
- [ ] Docker support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.com/) for local LLM inference
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [Streamlit](https://streamlit.io/) for the UI framework
- [LangChain](https://www.langchain.com/) for text splitting utilities