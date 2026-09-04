import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from sqlalchemy import select

from db.database import init_db, get_session
from db.models import Achievement, WorkLog, Project
from ai.extraction import suggest_achievement
from ai.client import llm_available
from common import record_skill_evidence, csv_list

st.set_page_config(page_title="Achievements", page_icon="🏆", layout="wide")
init_db()
st.title("🏆 Achievement / Impact Tracker")
st.caption('"What changed because of your work?" — capture it as Situation / Task / Action / Result / Metric.')

session = get_session()
work_logs = session.execute(select(WorkLog).order_by(WorkLog.date.desc()).limit(100)).scalars().all()
projects = session.execute(select(Project)).scalars().all()

if "star" not in st.session_state:
    st.session_state.star = {}

with st.expander("➕ Add an achievement", expanded=False):
    if llm_available() and work_logs:
        log_options = {"— start from scratch —": None} | {
            f"{l.date} — {l.raw_text[:60]}": l.id for l in work_logs
        }
        source_choice = st.selectbox("Draft from a work log entry (optional)", list(log_options.keys()))
        if st.button("🤖 Draft STAR from this entry", disabled=log_options[source_choice] is None):
            log = session.get(WorkLog, log_options[source_choice])
            with st.spinner("Drafting..."):
                st.session_state.star = suggest_achievement(log.raw_text, extra_context=log.accomplishments) or {}
    elif not llm_available():
        st.caption("AI drafting is off (no API key set). Fill in the fields manually below.")

    star = st.session_state.star
    with st.form("add_achievement", clear_on_submit=True):
        title = st.text_input("Achievement title*", value=star.get("title", ""))
        category = st.selectbox(
            "Category",
            ["Leadership", "Technical", "Analytics", "Process Improvement", "Other"],
            index=["Leadership", "Technical", "Analytics", "Process Improvement", "Other"].index(star["category"])
            if star.get("category") in ["Leadership", "Technical", "Analytics", "Process Improvement", "Other"] else 4,
        )
        situation = st.text_area("Situation — what was happening?", value=star.get("situation", ""))
        task = st.text_area("Task — what were you responsible for?", value=star.get("task", ""))
        action = st.text_area("Action — what did you actually do?", value=star.get("action", ""))
        result = st.text_area("Result — what changed?", value=star.get("result", ""))
        metric = st.text_input("Metric — can you quantify it?", value=star.get("metric", ""))
        skills = st.text_input("Skills (comma-separated)", value=", ".join(star.get("skills", [])))
        project_options = {"— none —": None} | {p.name: p.id for p in projects}
        project_choice = st.selectbox("Related project", list(project_options.keys()))
        resume_bullet = st.text_area("Resume bullet (optional — auto-generated later if left blank)")

        if st.form_submit_button("Save achievement") and title:
            achievement = Achievement(
                title=title, category=category, situation=situation, task=task,
                action=action, result=result, metric=metric, skills=skills,
                resume_bullet=resume_bullet, project_id=project_options[project_choice],
            )
            session.add(achievement)
            session.commit()
            record_skill_evidence(session, csv_list(skills), "achievement", achievement.id, note=title)
            session.commit()
            st.session_state.star = {}
            st.success(f"Saved: {title}")
            st.rerun()

st.divider()
achievements = session.execute(select(Achievement).order_by(Achievement.created_at.desc())).scalars().all()
if not achievements:
    st.info("No achievements yet.")
else:
    for a in achievements:
        with st.expander(f"✓ {a.title} ({a.category})"):
            if a.situation: st.markdown(f"**Situation:** {a.situation}")
            if a.task: st.markdown(f"**Task:** {a.task}")
            if a.action: st.markdown(f"**Action:** {a.action}")
            if a.result: st.markdown(f"**Result:** {a.result}")
            if a.metric: st.markdown(f"**Metric:** {a.metric}")
            if a.skills: st.markdown(f"**Skills:** {a.skills}")
            if a.resume_bullet: st.markdown(f"**Resume bullet:** {a.resume_bullet}")
            if st.button("Delete", key=f"del_ach_{a.id}"):
                session.delete(a)
                session.commit()
                st.rerun()

session.close()
