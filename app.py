from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import chromadb
from chromadb.utils import embedding_functions
import requests
import json
import uuid
import datetime

app = Flask(__name__)
CORS(app)

# ── Chroma setup ──
chroma_client = chromadb.PersistentClient(path="./memory_db")
ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Two collections: one for memories, one for chat history
memory_collection = chroma_client.get_or_create_collection(
    name="research_memory",
    embedding_function=ef
)
history_collection = chroma_client.get_or_create_collection(
    name="chat_history",
    embedding_function=ef
)

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"


def ollama_chat(messages: list, system: str = "") -> str:
    """Call Ollama and return response text."""
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": messages
    }
    if system:
        payload["messages"] = [{"role": "system", "content": system}] + messages

    r = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["message"]["content"]


def extract_memories(user_message: str, assistant_reply: str) -> list[dict]:
    """Ask the LLM to extract memorable facts from this exchange."""
    prompt = f"""Extract key research facts worth remembering from this conversation exchange.
Only extract facts that would be useful in future research conversations.

User said: {user_message}
Assistant replied: {assistant_reply}

Return a JSON array of memory objects. Each object has:
- "fact": the specific thing to remember (one sentence)
- "category": one of [topic, source, argument, deadline, preference, question]
- "importance": 1-3 (3 = very important)

Return ONLY the JSON array, no other text. Example:
[{{"fact": "Student is researching climate change impacts on agriculture", "category": "topic", "importance": 3}}]

If nothing worth remembering, return empty array: []"""

    try:
        raw = ollama_chat([{"role": "user", "content": prompt}])
        match = __import__('re').search(r'\[.*\]', raw, __import__('re').DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"Memory extraction error: {e}")
    return []


def recall_memories(query: str, n=5) -> list[str]:
    """Semantic search for relevant memories."""
    try:
        results = memory_collection.query(
            query_texts=[query],
            n_results=min(n, memory_collection.count())
        )
        if results["documents"] and results["documents"][0]:
            return results["documents"][0]
    except Exception:
        pass
    return []


def recall_history(query: str, n=4) -> list[str]:
    """Recall relevant past exchanges."""
    try:
        count = history_collection.count()
        if count == 0:
            return []
        results = history_collection.query(
            query_texts=[query],
            n_results=min(n, count)
        )
        if results["documents"] and results["documents"][0]:
            return results["documents"][0]
    except Exception:
        pass
    return []


def store_memory(fact: str, category: str, importance: int):
    """Store a memory in Chroma."""
    memory_collection.add(
        documents=[fact],
        ids=[str(uuid.uuid4())],
        metadatas=[{
            "category": category,
            "importance": importance,
            "timestamp": datetime.datetime.now().isoformat()
        }]
    )


def store_history(user_msg: str, assistant_msg: str):
    """Store exchange in history collection."""
    combined = f"Student: {user_msg}\nAssistant: {assistant_msg}"
    history_collection.add(
        documents=[combined],
        ids=[str(uuid.uuid4())],
        metadatas=[{"timestamp": datetime.datetime.now().isoformat()}]
    )


# ── Routes ──

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # 1. Recall relevant memories and history
    memories = recall_memories(user_message)
    history = recall_history(user_message)

    # 2. Build context-aware system prompt
    memory_block = ""
    if memories:
        memory_block = "\n\nWhat you remember about this student:\n" + \
            "\n".join(f"- {m}" for m in memories)

    history_block = ""
    if history:
        history_block = "\n\nRelevant past conversations:\n" + \
            "\n".join(f"  {h}" for h in history)

    system = f"""You are a helpful research assistant with memory. You help students with academic research — finding sources, structuring arguments, understanding papers, and staying organized.

You have a persistent memory of this student's research journey.{memory_block}{history_block}

Use your memory naturally in responses — reference past topics, build on previous conversations, notice patterns. Be specific, not generic. If you remember something relevant, mention it."""

    # 3. Get response
    response = ollama_chat(
        [{"role": "user", "content": user_message}],
        system=system
    )

    # 4. Extract and store new memories (async-ish — after response)
    new_memories = extract_memories(user_message, response)
    stored_count = 0
    for mem in new_memories:
        store_memory(mem["fact"], mem.get("category", "general"), mem.get("importance", 1))
        stored_count += 1

    # 5. Store exchange in history
    store_history(user_message, response)

    return jsonify({
        "response": response,
        "memories_stored": stored_count,
        "memories_used": len(memories)
    })


@app.route("/memories", methods=["GET"])
def get_memories():
    """Return all stored memories."""
    try:
        results = memory_collection.get()
        memories = []
        for i, doc in enumerate(results["documents"]):
            meta = results["metadatas"][i] if results["metadatas"] else {}
            memories.append({
                "fact": doc,
                "category": meta.get("category", "general"),
                "importance": meta.get("importance", 1),
                "timestamp": meta.get("timestamp", "")
            })
        # Sort by timestamp descending
        memories.sort(key=lambda x: x["timestamp"], reverse=True)
        return jsonify(memories)
    except Exception as e:
        return jsonify([])


@app.route("/memories/clear", methods=["POST"])
def clear_memories():
    """Wipe all memory."""
    global memory_collection, history_collection
    chroma_client.delete_collection("research_memory")
    chroma_client.delete_collection("chat_history")
    memory_collection = chroma_client.get_or_create_collection(
        name="research_memory", embedding_function=ef)
    history_collection = chroma_client.get_or_create_collection(
        name="chat_history", embedding_function=ef)
    return jsonify({"ok": True})


@app.route("/status", methods=["GET"])
def status():
    """Check Ollama connection."""
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        return jsonify({
            "ollama": True,
            "models": models,
            "memory_count": memory_collection.count(),
            "history_count": history_collection.count()
        })
    except Exception as e:
        return jsonify({"ollama": False, "error": str(e)})


if __name__ == "__main__":
    print("🧠 Research Memory Assistant starting...")
    print("   Open http://localhost:5000")
    app.run(debug=True, port=5000)
