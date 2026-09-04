"""Shared helpers used across Streamlit pages."""
import datetime as dt
from sqlalchemy import select
from sqlalchemy.orm import Session
from db.models import Skill, SkillEvidence
from ai.lexicon import SKILL_CATEGORY


def ensure_skill(session: Session, name: str) -> Skill:
    name = name.strip()
    skill = session.execute(select(Skill).where(Skill.name == name)).scalar_one_or_none()
    if skill is None:
        skill = Skill(name=name, category=SKILL_CATEGORY.get(name, "Technical"))
        session.add(skill)
        session.flush()
    return skill


def record_skill_evidence(
    session: Session,
    skill_names: list[str],
    source_type: str,
    source_id: int,
    note: str = "",
    demonstrated_on: dt.date | None = None,
):
    demonstrated_on = demonstrated_on or dt.date.today()
    for raw_name in skill_names:
        name = raw_name.strip()
        if not name:
            continue
        skill = ensure_skill(session, name)
        exists = session.execute(
            select(SkillEvidence).where(
                SkillEvidence.skill_id == skill.id,
                SkillEvidence.source_type == source_type,
                SkillEvidence.source_id == source_id,
            )
        ).scalar_one_or_none()
        if exists is None:
            session.add(SkillEvidence(
                skill_id=skill.id,
                source_type=source_type,
                source_id=source_id,
                note=note,
                demonstrated_on=demonstrated_on,
            ))


def csv_list(text: str) -> list[str]:
    return [s.strip() for s in (text or "").split(",") if s.strip()]
