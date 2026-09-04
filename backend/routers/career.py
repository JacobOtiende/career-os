import datetime as dt
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.deps import get_db, rows_to_list, row_to_dict
from db.models import Employment, Education, Certification, Project, Achievement

router = APIRouter(tags=["career"])


class EmploymentIn(BaseModel):
    organization: str
    role: str
    start_date: Optional[dt.date] = None
    end_date: Optional[dt.date] = None
    is_current: bool = False


class EducationIn(BaseModel):
    school: str
    degree: str = ""
    field: str = ""
    start_date: Optional[dt.date] = None
    end_date: Optional[dt.date] = None


class CertificationIn(BaseModel):
    name: str
    issuer: str = ""
    date_earned: Optional[dt.date] = None
    expires: Optional[dt.date] = None


@router.get("/employments")
def list_employments(db: Session = Depends(get_db)):
    return rows_to_list(db.execute(select(Employment).order_by(Employment.start_date.desc())).scalars().all())


@router.post("/employments")
def create_employment(payload: EmploymentIn, db: Session = Depends(get_db)):
    e = Employment(**payload.model_dump())
    db.add(e)
    db.commit()
    return row_to_dict(e)


@router.delete("/employments/{employment_id}")
def delete_employment(employment_id: int, db: Session = Depends(get_db)):
    e = db.get(Employment, employment_id)
    if not e:
        raise HTTPException(404, "Not found")
    db.delete(e)
    db.commit()
    return {"ok": True}


@router.get("/education")
def list_education(db: Session = Depends(get_db)):
    return rows_to_list(db.execute(select(Education)).scalars().all())


@router.post("/education")
def create_education(payload: EducationIn, db: Session = Depends(get_db)):
    e = Education(**payload.model_dump())
    db.add(e)
    db.commit()
    return row_to_dict(e)


@router.delete("/education/{education_id}")
def delete_education(education_id: int, db: Session = Depends(get_db)):
    e = db.get(Education, education_id)
    if not e:
        raise HTTPException(404, "Not found")
    db.delete(e)
    db.commit()
    return {"ok": True}


@router.get("/certifications")
def list_certifications(db: Session = Depends(get_db)):
    return rows_to_list(db.execute(select(Certification)).scalars().all())


@router.post("/certifications")
def create_certification(payload: CertificationIn, db: Session = Depends(get_db)):
    c = Certification(**payload.model_dump())
    db.add(c)
    db.commit()
    return row_to_dict(c)


@router.delete("/certifications/{cert_id}")
def delete_certification(cert_id: int, db: Session = Depends(get_db)):
    c = db.get(Certification, cert_id)
    if not c:
        raise HTTPException(404, "Not found")
    db.delete(c)
    db.commit()
    return {"ok": True}


@router.get("/timeline")
def timeline(db: Session = Depends(get_db)):
    events = []
    for e in db.execute(select(Employment)).scalars().all():
        if e.start_date:
            events.append({"date": e.start_date.isoformat(), "label": f"Started {e.role} at {e.organization}"})
        if e.end_date and not e.is_current:
            events.append({"date": e.end_date.isoformat(), "label": f"Ended role at {e.organization}"})
    for p in db.execute(select(Project)).scalars().all():
        if p.start_date:
            events.append({"date": p.start_date.isoformat(), "label": f"Started project {p.name}"})
    for a in db.execute(select(Achievement)).scalars().all():
        events.append({"date": a.created_at.date().isoformat(), "label": f"Achievement: {a.title}"})
    events.sort(key=lambda e: e["date"])
    return events
