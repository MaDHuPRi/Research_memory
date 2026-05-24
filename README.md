# ResearchBot

A memory-augmented AI research assistant. Runs fully local — zero cost, zero cloud.

## Stack
- **Ollama + llama3.2** — local LLM for chat and fact extraction
- **ChromaDB** — local vector store for persistent memory
- **sentence-transformers** — local embeddings (all-MiniLM-L6-v2)
- **Flask** — Python backend API
- **HTML/CSS/JS** — clean frontend

---

## Phase 1: Setup & Run

### 1. Install Ollama + pull model
```bash
# Install from https://ollama.com
ollama pull llama3.2
```

### 2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Flask backend
```bash
python -m backend.app
```

### 5. Open the frontend
Open `frontend/index.html` in your browser (or serve with Live Server in VS Code).

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send a message, get a response |
| GET | `/api/memory/search?q=<query>` | Semantic memory search |
| GET | `/api/memory/all?session_id=<id>` | All memories for a session |
| GET | `/api/history?session_id=<id>` | Conversation history |
| GET | `/api/health` | Health check |

---

## Phase 2: LoRA / QLoRA Fine-tuning (coming next)

Uncomment the Phase 2 packages in `requirements.txt`, then:

```bash
pip install -r requirements.txt
python training/train_lora.py
```

Fine-tunes llama3.2 on academic writing using QLoRA (4-bit) — runs on Mac Apple Silicon.

---

## Project Structure
```
research-bot/
├── backend/
│   ├── app.py          # Flask API
│   ├── chat.py         # Ollama chat + memory context
│   ├── memory.py       # ChromaDB read/write
│   ├── extractor.py    # Fact extraction from messages
│   └── embeddings.py   # sentence-transformers
├── training/           # Phase 2: LoRA/QLoRA scripts
├── frontend/           # HTML/CSS/JS UI
├── data/               # ChromaDB storage + training data
├── models/adapters/    # Saved LoRA weights
└── requirements.txt
```
