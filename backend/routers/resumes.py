import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.deps import get_db, rows_to_list, row_to_dict
from db.models import ResumeProfile, JobDescription, Achievement, GeneratedResume, Skill, WorkLog, Project
from ai.resume import build_resume_bullets
from ai.matching import compute_match
from common import csv_list

router = APIRouter(tags=["resumes"])


class ResumeProfileIn(BaseModel):
    name: str
    description: str = ""
    emphasis_skills: str = ""


class GenerateResumeIn(BaseModel):
    profile_id: Optional[int] = None
    job_description_id: Optional[int] = None
    top_n: int = 8


@router.get("/resume-profiles")
def list_profiles(db: Session = Depends(get_db)):
    return rows_to_list(db.execute(select(ResumeProfile)).scalars().all())


@router.post("/resume-profiles")
def create_profile(payload: ResumeProfileIn, db: Session = Depends(get_db)):
    p = ResumeProfile(**payload.model_dump())
    db.add(p)
    db.commit()
    return row_to_dict(p)


@router.get("/resumes")
def list_resumes(db: Session = Depends(get_db)):
    resumes = db.execute(select(GeneratedResume).order_by(GeneratedResume.created_at.desc())).scalars().all()
    result = []
    for r in resumes:
        d = row_to_dict(r)
        d["bullets"] = json.loads(r.bullets_json)
        result.append(d)
    return result


@router.get("/resumes/{resume_id}")
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    r = db.get(GeneratedResume, resume_id)
    if not r:
        raise HTTPException(404, "Not found")
    d = row_to_dict(r)
    bullets = json.loads(r.bullets_json)
    for b in bullets:
        if b.get("source_type") == "achievement":
            a = db.get(Achievement, b["source_id"])
            if a:
                evidence = row_to_dict(a)
                if a.source_work_log_id:
                    wl = db.get(WorkLog, a.source_work_log_id)
                    evidence["work_log"] = row_to_dict(wl) if wl else None
                if a.project_id:
                    proj = db.get(Project, a.project_id)
                    evidence["project"] = row_to_dict(proj) if proj else None
                b["evidence"] = evidence
    d["bullets"] = bullets
    return d


@router.post("/resumes")
def generate_resume(payload: GenerateResumeIn, db: Session = Depends(get_db)):
    achievements = db.execute(select(Achievement)).scalars().all()
    if not achievements:
        raise HTTPException(400, "No achievements recorded yet.")

    profile = db.get(ResumeProfile, payload.profile_id) if payload.profile_id else None
    jd = db.get(JobDescription, payload.job_description_id) if payload.job_description_id else None

    target_skills = []
    if profile:
        target_skills += csv_list(profile.emphasis_skills)
    if jd:
        target_skills += csv_list(jd.required_skills) + csv_list(jd.preferred_skills)

    bullets = build_resume_bullets(achievements, target_skills, top_n=payload.top_n)

    match_score = None
    if jd:
        user_skills = [s.name for s in db.execute(select(Skill)).scalars().all()]
        match = compute_match(csv_list(jd.required_skills), csv_list(jd.preferred_skills), user_skills)
        match_score = match["overall_pct"]

    record = GeneratedResume(
        profile_id=profile.id if profile else None,
        job_description_id=jd.id if jd else None,
        target_role=(jd.title if jd else (profile.name if profile else "General")),
        match_score=match_score,
        bullets_json=json.dumps(bullets),
    )
    db.add(record)
    db.commit()

    d = row_to_dict(record)
    d["bullets"] = bullets
    return d
