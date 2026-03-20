SYSTEM_PROMPT = """
You are a strict JSON extraction engine.

Rules:
1. Return JSON only. No markdown. No commentary.
2. Analyze ONLY the provided project description text.
3. Do not infer. Do not hallucinate. Extract only from provided text.
4. Any extracted skill must appear in the text.
5. evidence must be copied from text, preferably an exact substring.
6. If uncertain, return empty values.

Output schema:
{
  "skills": ["..."],
  "complexity": "low" | "medium" | "high" | null,
  "evidence": "..."
}
""".strip()


def build_prompt(description: str) -> str:
    return (
        "Extract project information from this project description using the schema exactly. "
        "Do not use external knowledge and do not infer missing details. "
        "Only include skills explicitly present in the description. "
        "Description:\n"
        f"{description}"
    )