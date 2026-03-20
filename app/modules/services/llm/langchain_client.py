from __future__ import annotations

import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.logger import get_logger


logger = get_logger("llm")


def _build_client() -> ChatGoogleGenerativeAI | None:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.info("Gemini API key not configured; skipping LLM enhancement")
        return None

    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        google_api_key=api_key,
    )


def call_llm(system_prompt: str, user_prompt: str) -> str:
    client = _build_client()
    if client is None:
        return ""

    logger.debug("Invoking Gemini model for project description analysis")

    response = client.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )

    content = response.content
    if isinstance(content, str):
        return content

    return str(content)
