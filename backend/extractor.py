import ollama
import json
import re

EXTRACT_PROMPT = """You are a JSON extraction machine. You output ONLY raw JSON. No words before or after. No explanation. No markdown. No backticks.

Extract from the student message below and fill this exact JSON structure:
{{"topics": [], "sources": [], "arguments": [], "deadlines": [], "questions": [], "summary": ""}}

Rules:
- topics: research subjects mentioned (e.g. "LoRA", "transformers", "PEFT")
- sources: papers, books, authors, URLs (e.g. "Vaswani et al", "Attention is All You Need")
- arguments: claims or insights the student states
- deadlines: any dates or time constraints mentioned (e.g. "June 15", "next week")
- questions: things the student is unsure about
- summary: one sentence, max 15 words
- Empty list [] if nothing relevant for that field
- Output ONLY the JSON object. First character must be {{

Student message: {message}

JSON:"""


def extract_facts(message: str, model: str = "llama3.2") -> dict:
    """Extract structured research facts from a student message."""
    prompt = EXTRACT_PROMPT.format(message=message)
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.1}
    )
    raw = response["message"]["content"].strip()
    # Strip markdown code fences if present
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "topics": [],
            "sources": [],
            "arguments": [],
            "deadlines": [],
            "questions": [],
            "summary": message[:200]
        }


def facts_to_memory_string(facts: dict) -> str:
    """Convert extracted facts into a readable memory string."""
    parts = []
    if facts.get("summary"):
        parts.append(f"Summary: {facts['summary']}")
    if facts.get("topics"):
        parts.append(f"Topics: {', '.join(facts['topics'])}")
    if facts.get("sources"):
        parts.append(f"Sources: {', '.join(facts['sources'])}")
    if facts.get("arguments"):
        parts.append(f"Arguments: {'; '.join(facts['arguments'])}")
    if facts.get("deadlines"):
        parts.append(f"Deadlines: {', '.join(facts['deadlines'])}")
    if facts.get("questions"):
        parts.append(f"Open questions: {'; '.join(facts['questions'])}")
    return "\n".join(parts)