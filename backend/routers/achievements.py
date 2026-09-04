from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.deps import get_db, rows_to_list, row_to_dict
from db.models import Achievement
from ai.extraction import suggest_achievement
from common import record_skill_evidence, csv_list

router = APIRouter(tags=["achievements"])


class AchievementIn(BaseModel):
    title: str
    category: str = ""
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""
    metric: str = ""
    skills: str = ""
    resume_bullet: str = ""
    source_work_log_id: Optional[int] = None
    project_id: Optional[int] = None


class SuggestIn(BaseModel):
    raw_text: str
    extra_context: str = ""


@router.get("/achievements")
def list_achievements(db: Session = Depends(get_db)):
    achievements = db.execute(select(Achievement).order_by(Achievement.created_at.desc())).scalars().all()
    return rows_to_list(achievements)


@router.post("/achievements/suggest")
def suggest(payload: SuggestIn):
    return suggest_achievement(payload.raw_text, payload.extra_context) or {}


@router.post("/achievements")
def create_achievement(payload: AchievementIn, db: Session = Depends(get_db)):
    achievement = Achievement(**payload.model_dump())
    db.add(achievement)
    db.commit()
    record_skill_evidence(db, csv_list(achievement.skills), "achievement", achievement.id, note=achievement.title)
    db.commit()
    return row_to_dict(achievement)


@router.delete("/achievements/{achievement_id}")
def delete_achievement(achievement_id: int, db: Session = Depends(get_db)):
    achievement = db.get(Achievement, achievement_id)
    if not achievement:
        raise HTTPException(404, "Not found")
    db.delete(achievement)
    db.commit()
    return {"ok": True}
