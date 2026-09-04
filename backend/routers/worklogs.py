import datetime as dt
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.deps import get_db, rows_to_list, row_to_dict
from db.models import WorkLog
from ai.extraction import extract_work_log
from common import record_skill_evidence, csv_list

router = APIRouter(tags=["worklogs"])


class WorkLogIn(BaseModel):
    date: dt.date
    employment_id: Optional[int] = None
    project_id: Optional[int] = None
    volunteer_org_id: Optional[int] = None
    category: str = "regular"
    hours: float = 0.0
    raw_text: str
    problems_solved: str = ""
    accomplishments: str = ""
    collaborators: str = ""
    tools_used: str = ""
    skills: str = ""
    notes: str = ""
    ai_processed: bool = False


class ExtractIn(BaseModel):
    raw_text: str


@router.get("/worklogs")
def list_worklogs(limit: int = 100, db: Session = Depends(get_db)):
    logs = db.execute(select(WorkLog).order_by(WorkLog.date.desc(), WorkLog.id.desc()).limit(limit)).scalars().all()
    return rows_to_list(logs)


@router.post("/worklogs/extract")
def extract(payload: ExtractIn):
    return extract_work_log(payload.raw_text)


@router.post("/worklogs")
def create_worklog(payload: WorkLogIn, db: Session = Depends(get_db)):
    log = WorkLog(**payload.model_dump())
    db.add(log)
    db.commit()
    record_skill_evidence(db, csv_list(log.skills), "work_log", log.id, note=log.raw_text[:150], demonstrated_on=log.date)
    db.commit()
    return row_to_dict(log)


@router.delete("/worklogs/{log_id}")
def delete_worklog(log_id: int, db: Session = Depends(get_db)):
    log = db.get(WorkLog, log_id)
    if not log:
        raise HTTPException(404, "Not found")
    db.delete(log)
    db.commit()
    return {"ok": True}
