import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import datetime as dt
import pandas as pd
import streamlit as st
from sqlalchemy import select

from db.database import init_db, get_session
from db.models import WorkLog, Employment, Project, Volunteer
from ai.extraction import extract_work_log
from common import record_skill_evidence, csv_list

st.set_page_config(page_title="Daily Work Log", page_icon="📝", layout="wide")
init_db()
st.title("📝 Daily Work Log")
st.caption("Write in plain language. AI suggests structure — you confirm or edit before saving.")

session = get_session()
employments = session.execute(select(Employment)).scalars().all()
projects = session.execute(select(Project)).scalars().all()
volunteer_orgs = session.execute(select(Volunteer)).scalars().all()

if "extracted" not in st.session_state:
    st.session_state.extracted = None

with st.expander("➕ Quick-add an employer (optional)"):
    with st.form("quick_employer"):
        org = st.text_input("Organization")
        role = st.text_input("Role")
        is_current = st.checkbox("Current position", value=True)
        if st.form_submit_button("Add employer") and org:
            session.add(Employment(organization=org, role=role, start_date=dt.date.today(), is_current=is_current))
            session.commit()
            st.success(f"Added {org}")
            st.rerun()

col_date, col_hours = st.columns(2)
log_date = col_date.date_input("Date", value=dt.date.today())
hours = col_hours.number_input("Hours worked", min_value=0.0, max_value=24.0, step=0.25, value=0.0)

employment_options = {"— none —": None} | {f"{e.organization} ({e.role})": e.id for e in employments}
project_options = {"— none —": None} | {p.name: p.id for p in projects}
volunteer_options = {"— none —": None} | {v.organization: v.id for v in volunteer_orgs}

c1, c2, c3 = st.columns(3)
employment_choice = c1.selectbox("Employer", list(employment_options.keys()))
project_choice = c2.selectbox("Related project", list(project_options.keys()))
volunteer_choice = c3.selectbox("Volunteer org (if applicable)", list(volunteer_options.keys()))

category = st.selectbox("Category", ["regular", "project", "training", "professional_development", "volunteer"])

raw_text = st.text_area(
    "What did you work on today?",
    height=150,
    placeholder="Spent 3 hours troubleshooting a Windows deployment issue affecting 12 workstations. "
                "Identified an imaging configuration problem and worked with the vendor to resolve it.",
)

collaborators = st.text_input("Who did you work with? (optional)")

if st.button("🤖 Extract structure with AI", disabled=not raw_text.strip()):
    with st.spinner("Extracting..."):
        st.session_state.extracted = extract_work_log(raw_text)

extracted = st.session_state.extracted

st.subheader("Structured evidence (review and edit before saving)")
default_summary = extracted.get("summary", "") if extracted else ""
default_problems = extracted.get("problems_solved", "") if extracted else ""
default_accomplishments = extracted.get("accomplishments", "") if extracted else ""
default_tools = ", ".join(extracted.get("tools_used", [])) if extracted else ""
default_skills = ", ".join(extracted.get("skills", [])) if extracted else ""

problems_solved = st.text_area("Problems solved", value=default_problems, height=80)
accomplishments = st.text_area("Accomplishments", value=default_accomplishments, height=80)
tools_used = st.text_input("Tools/technologies used (comma-separated)", value=default_tools)
skills = st.text_input("Skills demonstrated (comma-separated)", value=default_skills)
notes = st.text_area("Anything worth remembering? (optional)", height=60)

if st.button("💾 Save entry", type="primary", disabled=not raw_text.strip()):
    log = WorkLog(
        date=log_date,
        employment_id=employment_options[employment_choice],
        project_id=project_options[project_choice],
        volunteer_org_id=volunteer_options[volunteer_choice],
        category=category,
        hours=hours,
        raw_text=raw_text,
        problems_solved=problems_solved,
        accomplishments=accomplishments,
        collaborators=collaborators,
        tools_used=tools_used,
        skills=skills,
        notes=notes,
        ai_processed=extracted is not None,
    )
    session.add(log)
    session.commit()
    record_skill_evidence(session, csv_list(skills), "work_log", log.id, note=log.raw_text[:150], demonstrated_on=log_date)
    session.commit()
    st.session_state.extracted = None
    st.success("Saved. Skills evidence recorded.")
    st.rerun()

st.divider()
st.subheader("Recent entries")
logs = session.execute(select(WorkLog).order_by(WorkLog.date.desc()).limit(25)).scalars().all()
if logs:
    df = pd.DataFrame([{
        "Date": l.date, "Hours": l.hours, "Category": l.category,
        "Summary": l.raw_text[:100], "Skills": l.skills,
    } for l in logs])
    st.dataframe(df, width='stretch', hide_index=True)
else:
    st.info("No entries yet.")

session.close()
