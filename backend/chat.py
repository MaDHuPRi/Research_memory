import ollama
from backend.memory import search_memory

SYSTEM_PROMPT = """You are a smart, concise research assistant for students.

You have access to the student's research memory — past topics, papers, arguments, and questions they've explored.

Guidelines:
- Be direct and useful. No filler.
- Reference their past research when relevant (e.g. "Based on what you studied about X...")
- Help them connect ideas across sessions
- Suggest next steps, related papers, or gaps in their research when appropriate
- If you don't know something, say so clearly

Research memory context:
{memory_context}"""


def build_memory_context(query: str, session_id: str) -> str:
    """Retrieve relevant memories and format them as context."""
    memories = search_memory(query=query, n_results=6)
    if not memories:
        return "No prior research history found."
    lines = []
    for m in memories:
        ts = m["metadata"].get("timestamp", "")[:10]
        lines.append(f"[{ts}] {m['content']}")
    return "\n".join(lines)


def chat(
    message: str,
    session_id: str,
    history: list[dict],
    model: str = "llama3.2"
) -> str:
    """Send a message and get a response with memory-augmented context."""
    memory_context = build_memory_context(message, session_id)
    system = SYSTEM_PROMPT.format(memory_context=memory_context)

    messages = [{"role": "system", "content": system}]
    # Include last 10 turns of conversation history
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": message})

    response = ollama.chat(
        model=model,
        messages=messages,
        options={"temperature": 0.7}
    )
    return response["message"]["content"]
