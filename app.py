import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

import datetime as dt
import pandas as pd
import streamlit as st
from sqlalchemy import select, func

from db.database import init_db, get_session
from db.models import WorkLog, Project, Achievement, Skill, GeneratedResume
from ai.client import llm_available

st.set_page_config(page_title="Career OS", page_icon="📈", layout="wide")
init_db()

st.title("📈 Career OS — Professional Life Dashboard")

if llm_available():
    st.caption("AI extraction: **ON** (LLM-powered)")
else:
    st.caption("AI extraction: **OFF** — running on rule-based keyword extraction. "
               "Set ANTHROPIC_API_KEY or OPENAI_API_KEY in a `.env` file to enable LLM extraction.")

session = get_session()
today = dt.date.today()
month_start = today.replace(day=1)
year_start = today.replace(month=1, day=1)

hours_month = session.execute(
    select(func.coalesce(func.sum(WorkLog.hours), 0.0)).where(WorkLog.date >= month_start)
).scalar()
hours_year = session.execute(
    select(func.coalesce(func.sum(WorkLog.hours), 0.0)).where(WorkLog.date >= year_start)
).scalar()
active_projects = session.execute(
    select(func.count()).select_from(Project).where(Project.status == "active")
).scalar()
accomplishments_month = session.execute(
    select(func.count()).select_from(Achievement).where(Achievement.created_at >= dt.datetime.combine(month_start, dt.time.min))
).scalar()
skills_count = session.execute(select(func.count()).select_from(Skill)).scalar()
resumes_count = session.execute(select(func.count()).select_from(GeneratedResume)).scalar()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Hours This Month", f"{hours_month:.1f}")
col2.metric("Hours This Year", f"{hours_year:.1f}")
col3.metric("Active Projects", active_projects)
col4.metric("Achievements This Month", accomplishments_month)
col5.metric("Skills Tracked", skills_count)

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Current Projects")
    projects = session.execute(
        select(Project).where(Project.status == "active").order_by(Project.start_date.desc())
    ).scalars().all()
    if projects:
        for p in projects:
            st.markdown(f"● **{p.name}** — {p.organization or '—'}")
    else:
        st.info("No active projects yet. Add one on the Projects page.")

with right:
    st.subheader("Recent Accomplishments")
    achievements = session.execute(
        select(Achievement).order_by(Achievement.created_at.desc()).limit(5)
    ).scalars().all()
    if achievements:
        for a in achievements:
            st.markdown(f"✓ {a.title}")
    else:
        st.info("No achievements logged yet. Add one on the Achievements page.")

st.divider()
st.subheader("Recent Work Log Entries")
logs = session.execute(select(WorkLog).order_by(WorkLog.date.desc()).limit(10)).scalars().all()
if logs:
    df = pd.DataFrame([{
        "Date": l.date, "Hours": l.hours, "Category": l.category,
        "Summary": (l.raw_text[:80] + "…") if len(l.raw_text) > 80 else l.raw_text,
    } for l in logs])
    st.dataframe(df, width='stretch', hide_index=True)
else:
    st.info("No work log entries yet. Start on the **Daily Work Log** page in the sidebar.")

session.close()

st.divider()
st.caption(
    "Use the sidebar to navigate: Daily Work Log → Projects → Achievements → Skills → "
    "Volunteer → Career Journey → Job Analyzer → Resume Generator → Data Export."
)
