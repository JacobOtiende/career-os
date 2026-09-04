import datetime as dt
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.deps import get_db, row_to_dict
from db.models import Volunteer, WorkLog

router = APIRouter(tags=["volunteer"])


class VolunteerIn(BaseModel):
    organization: str
    role: str = ""
    start_date: Optional[dt.date] = None
    end_date: Optional[dt.date] = None
    responsibilities: str = ""
    community_impact: str = ""
    events: str = ""
    partnerships: str = ""


@router.get("/volunteer")
def list_volunteer(db: Session = Depends(get_db)):
    orgs = db.execute(select(Volunteer)).scalars().all()
    result = []
    for v in orgs:
        hours = db.execute(
            select(func.coalesce(func.sum(WorkLog.hours), 0.0)).where(WorkLog.volunteer_org_id == v.id)
        ).scalar()
        d = row_to_dict(v)
        d["logged_hours"] = hours
        result.append(d)
    return result


@router.post("/volunteer")
def create_volunteer(payload: VolunteerIn, db: Session = Depends(get_db)):
    v = Volunteer(**payload.model_dump())
    db.add(v)
    db.commit()
    return row_to_dict(v)


@router.delete("/volunteer/{volunteer_id}")
def delete_volunteer(volunteer_id: int, db: Session = Depends(get_db)):
    v = db.get(Volunteer, volunteer_id)
    if not v:
        raise HTTPException(404, "Not found")
    db.delete(v)
    db.commit()
    return {"ok": True}
