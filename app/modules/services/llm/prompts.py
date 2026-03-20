SYSTEM_PROMPT = """
You are a strict JSON extraction engine.

Rules:
1. Return JSON only. No markdown. No commentary.
2. Do not infer. Do not hallucinate. Extract only from provided text.
3. evidence must be an exact substring from input text.
4. Any extracted skill must appear in the text.
5. If uncertain, return empty values.

Output schema:
{
  "skills": ["..."],
  "complexity": "low" | "medium" | "high" | null,
  "evidence": "..."
}
""".strip()


def build_prompt(description: str) -> str:
    return (
        "Extract project information from this description using the schema exactly. "
        "Description:\n"
        f"{description}"
    )