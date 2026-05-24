from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.chat import chat
from backend.memory import save_memory, search_memory, get_all_memories
from backend.extractor import extract_facts, facts_to_memory_string

app = Flask(__name__)
CORS(app)

# In-memory conversation histories keyed by session_id
conversation_histories: dict[str, list[dict]] = {}


@app.route("/api/chat", methods=["POST"])
def handle_chat():
    data = request.json
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Get or init conversation history
    history = conversation_histories.get(session_id, [])

    # Generate response
    response = chat(message=message, session_id=session_id, history=history)

    # Update history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response})
    conversation_histories[session_id] = history

    # Extract and save memory from user message (non-blocking best effort)
    try:
        facts = extract_facts(message)
        memory_str = facts_to_memory_string(facts)
        if memory_str.strip():
            save_memory(
                session_id=session_id,
                content=memory_str,
                metadata={"type": "extracted_facts", "raw_message": message[:500]}
            )
    except Exception as e:
        print(f"[Memory extraction error] {e}")

    return jsonify({"response": response, "session_id": session_id})


@app.route("/api/memory/search", methods=["GET"])
def handle_memory_search():
    query = request.args.get("q", "").strip()
    session_id = request.args.get("session_id")
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    results = search_memory(query=query, session_id=session_id, n_results=5)
    return jsonify({"results": results})


@app.route("/api/memory/all", methods=["GET"])
def handle_memory_all():
    session_id = request.args.get("session_id", "default")
    memories = get_all_memories(session_id=session_id)
    return jsonify({"memories": memories})


@app.route("/api/history", methods=["GET"])
def handle_history():
    session_id = request.args.get("session_id", "default")
    history = conversation_histories.get(session_id, [])
    return jsonify({"history": history})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=8080)
