# Research Memory Assistant

An AI research companion that remembers everything across sessions using ChromaDB vector memory + Ollama.

## Setup (one time)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Make sure Ollama is running with CORS enabled
OLLAMA_ORIGINS=* ollama serve

# 3. Make sure llama3.2 is pulled
ollama pull llama3.2
```

## Run

```bash
python app.py
```

Open http://localhost:5000

## How it works

1. You chat about your research
2. After each message, the AI extracts memorable facts (topics, sources, arguments, deadlines)
3. Facts are embedded and stored in ChromaDB locally
4. Every new message searches memory for relevant context
5. The AI responds with full awareness of your research history

## Memory categories
- **topic** — research areas and subjects
- **source** — papers, books, websites referenced
- **argument** — key claims and positions
- **deadline** — time-sensitive items
- **preference** — how you like to work
- **question** — open questions to explore

## Files
- `app.py` — Flask backend + Chroma + Ollama logic
- `templates/index.html` — frontend UI
- `memory_db/` — auto-created, stores your vector memory
- `requirements.txt` — Python dependencies
