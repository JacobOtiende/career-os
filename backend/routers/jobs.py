from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.deps import get_db, rows_to_list, row_to_dict
from db.models import JobDescription, Skill, Achievement
from ai.matching import analyze_job_description, compute_match
from common import csv_list

router = APIRouter(tags=["jobs"])


class JobDescriptionIn(BaseModel):
    title: str = ""
    company: str = ""
    raw_text: str


def _match_and_evidence(db: Session, jd: JobDescription) -> dict:
    required = csv_list(jd.required_skills)
    preferred = csv_list(jd.preferred_skills)
    user_skills = [s.name for s in db.execute(select(Skill)).scalars().all()]
    match = compute_match(required, preferred, user_skills)

    target = {s.lower() for s in required + preferred}
    achievements = db.execute(select(Achievement)).scalars().all()
    scored = []
    for a in achievements:
        overlap = len({s.strip().lower() for s in csv_list(a.skills)} & target)
        if overlap > 0:
            scored.append((a, overlap))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    recommended = [{"id": a.id, "title": a.title, "overlap": overlap} for a, overlap in scored[:5]]

    return {"match": match, "recommended_evidence": recommended}


@router.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    return rows_to_list(db.execute(select(JobDescription).order_by(JobDescription.created_at.desc())).scalars().all())


@router.post("/jobs")
def create_job(payload: JobDescriptionIn, db: Session = Depends(get_db)):
    analysis = analyze_job_description(payload.raw_text)
    jd = JobDescription(
        title=payload.title,
        company=payload.company,
        raw_text=payload.raw_text,
        required_skills=", ".join(analysis.get("required_skills", [])),
        preferred_skills=", ".join(analysis.get("preferred_skills", [])),
        competencies=", ".join(analysis.get("competencies", [])),
    )
    db.add(jd)
    db.commit()
    result = row_to_dict(jd)
    result.update(_match_and_evidence(db, jd))
    return result


@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    jd = db.get(JobDescription, job_id)
    if not jd:
        raise HTTPException(404, "Not found")
    result = row_to_dict(jd)
    result.update(_match_and_evidence(db, jd))
    return result
