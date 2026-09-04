import datetime as dt
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.deps import get_db, rows_to_list, row_to_dict
from db.models import Project
from common import record_skill_evidence, csv_list

router = APIRouter(tags=["projects"])


class ProjectIn(BaseModel):
    name: str
    organization: str = ""
    role: str = ""
    status: str = "active"
    start_date: Optional[dt.date] = None
    end_date: Optional[dt.date] = None
    problem: str = ""
    objective: str = ""
    responsibilities: str = ""
    technologies: str = ""
    tools: str = ""
    methods: str = ""
    challenges: str = ""
    solutions: str = ""
    results: str = ""
    metrics: str = ""
    people_teams: str = ""
    leadership: str = ""
    lessons_learned: str = ""


@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    projects = db.execute(select(Project).order_by(Project.start_date.desc())).scalars().all()
    return rows_to_list(projects)


@router.get("/projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Not found")
    return row_to_dict(project)


@router.post("/projects")
def create_project(payload: ProjectIn, db: Session = Depends(get_db)):
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    tech_skills = csv_list(project.technologies) + csv_list(project.tools)
    record_skill_evidence(db, tech_skills, "project", project.id, note=f"Project: {project.name}")
    db.commit()
    return row_to_dict(project)


@router.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Not found")
    db.delete(project)
    db.commit()
    return {"ok": True}
