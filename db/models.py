import datetime as dt
from sqlalchemy import String, Text, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def now() -> dt.datetime:
    return dt.datetime.utcnow()


class Employment(Base):
    __tablename__ = "employments"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)

    work_logs: Mapped[list["WorkLog"]] = relationship(back_populates="employment")


class Volunteer(Base):
    __tablename__ = "volunteer_orgs"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    responsibilities: Mapped[str] = mapped_column(Text, default="")
    community_impact: Mapped[str] = mapped_column(Text, default="")
    events: Mapped[str] = mapped_column(Text, default="")
    partnerships: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)

    work_logs: Mapped[list["WorkLog"]] = relationship(back_populates="volunteer_org")


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    organization: Mapped[str] = mapped_column(String(200), default="")
    role: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(50), default="active")  # planned/active/completed/on_hold
    start_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    problem: Mapped[str] = mapped_column(Text, default="")
    objective: Mapped[str] = mapped_column(Text, default="")
    responsibilities: Mapped[str] = mapped_column(Text, default="")
    technologies: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    tools: Mapped[str] = mapped_column(Text, default="")
    methods: Mapped[str] = mapped_column(Text, default="")
    challenges: Mapped[str] = mapped_column(Text, default="")
    solutions: Mapped[str] = mapped_column(Text, default="")
    results: Mapped[str] = mapped_column(Text, default="")
    metrics: Mapped[str] = mapped_column(Text, default="")
    people_teams: Mapped[str] = mapped_column(Text, default="")
    leadership: Mapped[str] = mapped_column(Text, default="")
    lessons_learned: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)

    work_logs: Mapped[list["WorkLog"]] = relationship(back_populates="project")
    achievements: Mapped[list["Achievement"]] = relationship(back_populates="project")


class WorkLog(Base):
    __tablename__ = "work_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, default=dt.date.today)
    employment_id: Mapped[int | None] = mapped_column(ForeignKey("employments.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    volunteer_org_id: Mapped[int | None] = mapped_column(ForeignKey("volunteer_orgs.id"), nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="regular")
    # regular / project / training / professional_development / volunteer
    hours: Mapped[float] = mapped_column(Float, default=0.0)
    raw_text: Mapped[str] = mapped_column(Text)  # Level 1: what the user actually typed
    problems_solved: Mapped[str] = mapped_column(Text, default="")
    accomplishments: Mapped[str] = mapped_column(Text, default="")
    collaborators: Mapped[str] = mapped_column(Text, default="")
    tools_used: Mapped[str] = mapped_column(Text, default="")  # comma-separated, AI-suggested/editable
    skills: Mapped[str] = mapped_column(Text, default="")  # comma-separated, AI-suggested/editable
    notes: Mapped[str] = mapped_column(Text, default="")
    ai_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)

    employment: Mapped["Employment"] = relationship(back_populates="work_logs")
    project: Mapped["Project"] = relationship(back_populates="work_logs")
    volunteer_org: Mapped["Volunteer"] = relationship(back_populates="work_logs")


class Achievement(Base):
    __tablename__ = "achievements"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(100), default="")  # Leadership/Technical/Analytics/...
    situation: Mapped[str] = mapped_column(Text, default="")
    task: Mapped[str] = mapped_column(Text, default="")
    action: Mapped[str] = mapped_column(Text, default="")
    result: Mapped[str] = mapped_column(Text, default="")
    metric: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    resume_bullet: Mapped[str] = mapped_column(Text, default="")
    source_work_log_id: Mapped[int | None] = mapped_column(ForeignKey("work_logs.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)

    project: Mapped["Project"] = relationship(back_populates="achievements")


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    category: Mapped[str] = mapped_column(String(50), default="Technical")  # Technical/Business/Leadership


class SkillEvidence(Base):
    __tablename__ = "skill_evidence"
    id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    source_type: Mapped[str] = mapped_column(String(50))  # work_log / project / achievement / volunteer
    source_id: Mapped[int] = mapped_column()
    note: Mapped[str] = mapped_column(Text, default="")
    demonstrated_on: Mapped[dt.date] = mapped_column(Date, default=dt.date.today)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)


class Education(Base):
    __tablename__ = "education"
    id: Mapped[int] = mapped_column(primary_key=True)
    school: Mapped[str] = mapped_column(String(200))
    degree: Mapped[str] = mapped_column(String(200), default="")
    field: Mapped[str] = mapped_column(String(200), default="")
    start_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)


class Certification(Base):
    __tablename__ = "certifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    issuer: Mapped[str] = mapped_column(String(200), default="")
    date_earned: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    expires: Mapped[dt.date | None] = mapped_column(Date, nullable=True)


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    company: Mapped[str] = mapped_column(String(200), default="")
    raw_text: Mapped[str] = mapped_column(Text)
    required_skills: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    preferred_skills: Mapped[str] = mapped_column(Text, default="")
    competencies: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)


class ResumeProfile(Base):
    __tablename__ = "resume_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text, default="")
    emphasis_skills: Mapped[str] = mapped_column(Text, default="")  # comma-separated
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)


class ResumeImport(Base):
    __tablename__ = "resume_imports"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(300))
    file_path: Mapped[str] = mapped_column(String(500), default="")
    raw_text: Mapped[str] = mapped_column(Text)
    bullets_json: Mapped[str] = mapped_column(Text, default="[]")
    # list of {text, title, category, skills, imported, achievement_id}
    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)


class GeneratedResume(Base):
    __tablename__ = "generated_resumes"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("resume_profiles.id"), nullable=True)
    job_description_id: Mapped[int | None] = mapped_column(ForeignKey("job_descriptions.id"), nullable=True)
    target_role: Mapped[str] = mapped_column(String(200), default="")
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    bullets_json: Mapped[str] = mapped_column(Text)  # JSON list of {text, source_type, source_id}
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=now)
