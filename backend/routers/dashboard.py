import datetime as dt
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.deps import get_db, rows_to_list
from db.models import WorkLog, Project, Achievement, Skill, GeneratedResume

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    today = dt.date.today()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    hours_month = db.execute(
        select(func.coalesce(func.sum(WorkLog.hours), 0.0)).where(WorkLog.date >= month_start)
    ).scalar()
    hours_year = db.execute(
        select(func.coalesce(func.sum(WorkLog.hours), 0.0)).where(WorkLog.date >= year_start)
    ).scalar()
    active_projects = db.execute(
        select(func.count()).select_from(Project).where(Project.status == "active")
    ).scalar()
    accomplishments_month = db.execute(
        select(func.count()).select_from(Achievement).where(
            Achievement.created_at >= dt.datetime.combine(month_start, dt.time.min)
        )
    ).scalar()
    skills_count = db.execute(select(func.count()).select_from(Skill)).scalar()
    resumes_count = db.execute(select(func.count()).select_from(GeneratedResume)).scalar()

    current_projects = db.execute(
        select(Project).where(Project.status == "active").order_by(Project.start_date.desc())
    ).scalars().all()
    recent_achievements = db.execute(
        select(Achievement).order_by(Achievement.created_at.desc()).limit(5)
    ).scalars().all()
    recent_logs = db.execute(select(WorkLog).order_by(WorkLog.date.desc()).limit(10)).scalars().all()

    return {
        "hours_month": hours_month,
        "hours_year": hours_year,
        "active_projects": active_projects,
        "accomplishments_month": accomplishments_month,
        "skills_count": skills_count,
        "resumes_count": resumes_count,
        "current_projects": rows_to_list(current_projects),
        "recent_achievements": rows_to_list(recent_achievements),
        "recent_logs": rows_to_list(recent_logs),
    }
