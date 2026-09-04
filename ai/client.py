"""
Thin LLM wrapper. Tries Anthropic first, then OpenAI, then reports
unavailable so callers fall back to rule-based logic. No API key is
required for the app to function.
"""
import json
import os
import re


class NoLLMAvailable(Exception):
    pass


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        start = text.find("[")
        end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON found in LLM response: {text[:200]}")
    return json.loads(text[start:end + 1])


def llm_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def complete_json(system: str, user: str, max_tokens: int = 1500) -> dict | list:
    """Call whichever LLM is configured and return parsed JSON. Raises
    NoLLMAvailable if no API key is set, or the underlying exception if the
    call itself fails (caller decides whether to fall back)."""
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if anthropic_key:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        resp = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in resp.content if hasattr(b, "text"))
        return _extract_json(text)

    if openai_key:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = resp.choices[0].message.content
        return _extract_json(text)

    raise NoLLMAvailable("No ANTHROPIC_API_KEY or OPENAI_API_KEY set.")
