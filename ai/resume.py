"""
Resume bullet generation. Every bullet produced carries a source_type +
source_id back to the Achievement or Project it came from -- this is the
"Show evidence" chain from the proposal (Achievement -> Work Log -> Project).
No bullet is ever generated without a linked evidence record.
"""
from ai.client import complete_json, llm_available

BULLET_SYSTEM_PROMPT = """You write a single resume bullet point from a \
career achievement record. Use ONLY the facts given -- do not invent \
metrics, scope, or outcomes not present in the record. Action-verb start, \
past tense, one line, no first person. Respond with strict JSON only:
{"bullet": "..."}"""


def _template_bullet(achievement) -> str:
    if achievement.resume_bullet:
        return achievement.resume_bullet
    parts = [p for p in [achievement.action, achievement.result, achievement.metric] if p]
    if parts:
        return ". ".join(parts).strip().rstrip(".") + "."
    return achievement.title


def bullet_for_achievement(achievement) -> str:
    if achievement.resume_bullet:
        return achievement.resume_bullet
    if llm_available():
        record = (
            f"Title: {achievement.title}\nSituation: {achievement.situation}\n"
            f"Task: {achievement.task}\nAction: {achievement.action}\n"
            f"Result: {achievement.result}\nMetric: {achievement.metric}"
        )
        try:
            result = complete_json(BULLET_SYSTEM_PROMPT, record)
            bullet = result.get("bullet")
            if bullet:
                return bullet
        except Exception:
            pass
    return _template_bullet(achievement)


def rank_achievements_by_relevance(achievements: list, target_skills: list[str]) -> list[tuple]:
    """Returns (achievement, overlap_count) sorted by relevance."""
    target = {s.strip().lower() for s in target_skills if s.strip()}
    scored = []
    for a in achievements:
        a_skills = {s.strip().lower() for s in (a.skills or "").split(",") if s.strip()}
        overlap = len(a_skills & target) if target else 0
        scored.append((a, overlap))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored


def build_resume_bullets(achievements: list, target_skills: list[str], top_n: int = 8) -> list[dict]:
    """Returns a list of {text, source_type, source_id} dicts, most
    relevant achievements first."""
    ranked = rank_achievements_by_relevance(achievements, target_skills)
    bullets = []
    for achievement, _overlap in ranked[:top_n]:
        bullets.append({
            "text": bullet_for_achievement(achievement),
            "source_type": "achievement",
            "source_id": achievement.id,
        })
    return bullets
