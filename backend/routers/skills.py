from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.deps import get_db, rows_to_list
from db.models import Skill, SkillEvidence

router = APIRouter(tags=["skills"])


@router.get("/skills")
def list_skills(db: Session = Depends(get_db)):
    skills = db.execute(select(Skill).order_by(Skill.category, Skill.name)).scalars().all()
    result = []
    for s in skills:
        evidence = db.execute(select(SkillEvidence).where(SkillEvidence.skill_id == s.id)).scalars().all()
        last_demo = max((e.demonstrated_on for e in evidence), default=None)
        result.append({
            "id": s.id,
            "name": s.name,
            "category": s.category,
            "evidence_count": len(evidence),
            "last_demonstrated": last_demo.isoformat() if last_demo else None,
        })
    return result


@router.get("/skills/{skill_id}/evidence")
def skill_evidence(skill_id: int, db: Session = Depends(get_db)):
    skill = db.get(Skill, skill_id)
    if not skill:
        raise HTTPException(404, "Not found")
    evidence = db.execute(
        select(SkillEvidence).where(SkillEvidence.skill_id == skill_id).order_by(SkillEvidence.demonstrated_on.desc())
    ).scalars().all()
    return rows_to_list(evidence)
