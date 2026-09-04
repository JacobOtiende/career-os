"""
Job description parsing + match scoring.

Design choice: the numeric match score is ALWAYS computed deterministically
from skill-set overlap (never an LLM-guessed percentage), so it stays
auditable and reproducible. The LLM, when available, is only used to pull a
richer required/preferred skill list out of messy job-posting text and to
write a short narrative gap summary -- never to set the score itself.
"""
from ai.client import complete_json, llm_available
from ai.lexicon import ALL_SKILLS, COMPETENCIES, find_keywords

JD_SYSTEM_PROMPT = """You are analyzing a job description. Extract skills and \
competencies actually mentioned or clearly implied by the text. Respond with \
strict JSON only:
{
  "required_skills": ["list"],
  "preferred_skills": ["list"],
  "competencies": ["list"]
}"""


def analyze_job_description(raw_text: str) -> dict:
    if llm_available():
        try:
            result = complete_json(JD_SYSTEM_PROMPT, raw_text)
            for key in ("required_skills", "preferred_skills", "competencies"):
                result.setdefault(key, [])
            return result
        except Exception:
            pass
    # Rule-based fallback: keyword-match against the lexicon. Everything
    # found is treated as "required" since we can't reliably tell
    # required vs. preferred apart without an LLM reading tone/wording.
    found_skills = find_keywords(raw_text, ALL_SKILLS)
    found_competencies = find_keywords(raw_text, COMPETENCIES)
    return {
        "required_skills": found_skills,
        "preferred_skills": [],
        "competencies": found_competencies,
    }


def _norm(items: list[str]) -> set[str]:
    return {s.strip().lower() for s in items if s.strip()}


def compute_match(required_skills: list[str], preferred_skills: list[str], user_skills: list[str]) -> dict:
    req = _norm(required_skills)
    pref = _norm(preferred_skills)
    have = _norm(user_skills)

    strong = sorted(req & have)
    partial = sorted(pref & have)
    gaps = sorted((req | pref) - have)

    req_pct = round(100 * len(req & have) / len(req), 1) if req else 100.0
    pref_pct = round(100 * len(pref & have) / len(pref), 1) if pref else 100.0
    # Required skills weighted more heavily than preferred.
    if req or pref:
        weight_req, weight_pref = 0.75, 0.25
        overall = round(req_pct * weight_req + pref_pct * weight_pref, 1)
    else:
        overall = 0.0

    return {
        "overall_pct": overall,
        "required_pct": req_pct,
        "preferred_pct": pref_pct,
        "strong_matches": strong,
        "partial_matches": partial,
        "gaps": gaps,
    }
