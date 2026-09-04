"""
Turns a free-text work log entry into structured fields.

Follows the Level 1 / 2 / 3 principle from the proposal:
  Level 1 - the raw_text the user typed is never modified.
  Level 2 - skills/tools/problems/accomplishments are DERIVED and always
            shown to the user as editable suggestions before saving.
  Level 3 - resume_bullet generation happens later (ai/resume.py), never here.
"""
import re
from ai.client import complete_json, llm_available, NoLLMAvailable
from ai.lexicon import ALL_SKILLS, find_keywords

HOURS_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr)\b", re.IGNORECASE)

SYSTEM_PROMPT = """You are a career-evidence extraction assistant. You will be \
given a free-text work log entry. Extract ONLY what is stated or directly \
implied by the text. Never invent organizations, metrics, people, or tools \
that are not mentioned or clearly implied. Respond with strict JSON only, \
no prose, matching this shape:
{
  "summary": "one sentence describing what was worked on",
  "problems_solved": "problems identified/solved, or empty string",
  "accomplishments": "what was accomplished/completed, or empty string",
  "tools_used": ["list", "of", "tools/technologies mentioned"],
  "skills": ["list", "of", "skills demonstrated"],
  "hours_mentioned": <number or null if no hours stated>,
  "achievement_candidate": <true if this looks like a resume-worthy accomplishment>,
  "suggested_category": "regular|project|training|professional_development|volunteer"
}"""


def _rule_based_extract(raw_text: str) -> dict:
    hours_match = HOURS_PATTERN.search(raw_text)
    hours = float(hours_match.group(1)) if hours_match else None
    skills = find_keywords(raw_text, ALL_SKILLS)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw_text) if s.strip()]
    problem_sentences = [s for s in sentences if re.search(
        r"\b(issues?|problems?|errors?|fail\w*|troubleshoot\w*|bugs?|down|broken)\b", s, re.I)]
    accomplishment_sentences = [s for s in sentences if re.search(
        r"\b(resolv\w*|fix\w*|fixed|complet\w*|deliver\w*|implement\w*|built|build\w*|improv\w*|"
        r"reduc\w*|automat\w*|launch\w*|led|lead\w*)\b", s, re.I)]
    return {
        "summary": sentences[0] if sentences else raw_text[:150],
        "problems_solved": " ".join(problem_sentences),
        "accomplishments": " ".join(accomplishment_sentences),
        "tools_used": skills,
        "skills": skills,
        "hours_mentioned": hours,
        "achievement_candidate": bool(accomplishment_sentences),
        "suggested_category": "regular",
    }


def extract_work_log(raw_text: str) -> dict:
    """Returns a dict of suggested structured fields. Always safe to call
    with no API key configured -- falls back to keyword rules."""
    if not raw_text or not raw_text.strip():
        return _rule_based_extract("")

    if llm_available():
        try:
            result = complete_json(SYSTEM_PROMPT, raw_text)
            result.setdefault("tools_used", [])
            result.setdefault("skills", [])
            return result
        except (NoLLMAvailable, Exception):
            return _rule_based_extract(raw_text)
    return _rule_based_extract(raw_text)


ACHIEVEMENT_SYSTEM_PROMPT = """You turn a work log entry into a STAR-format \
achievement candidate. Use ONLY facts present in the provided text and any \
extra context given. Do not invent metrics -- if no number is given, leave \
"metric" empty rather than guessing. Respond with strict JSON only:
{
  "title": "short achievement title",
  "situation": "...",
  "task": "...",
  "action": "...",
  "result": "...",
  "metric": "quantified impact if stated, else empty string",
  "category": "Leadership|Technical|Analytics|Process Improvement|Other",
  "skills": ["list", "of", "skills"]
}"""


def suggest_achievement(raw_text: str, extra_context: str = "") -> dict | None:
    if not llm_available():
        return None
    try:
        prompt = raw_text if not extra_context else f"{raw_text}\n\nAdditional context: {extra_context}"
        return complete_json(ACHIEVEMENT_SYSTEM_PROMPT, prompt)
    except Exception:
        return None
