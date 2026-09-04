import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import json
import streamlit as st
from sqlalchemy import select

from db.database import init_db, get_session
from db.models import ResumeProfile, JobDescription, Achievement, GeneratedResume, WorkLog, Project
from ai.resume import build_resume_bullets
from ai.matching import compute_match
from common import csv_list

st.set_page_config(page_title="Resume Generator", page_icon="📄", layout="wide")
init_db()
st.title("📄 Resume Generator")
st.caption("Every bullet traces back to an Achievement, then its Work Log / Project source.")

session = get_session()

with st.expander("➕ Manage resume profiles", expanded=False):
    with st.form("add_profile", clear_on_submit=True):
        name = st.text_input("Profile name (e.g. 'IT Operations', 'Data Analytics', 'AI/ML')")
        description = st.text_input("Description")
        emphasis_skills = st.text_input("Skills to emphasize (comma-separated)")
        if st.form_submit_button("Save profile") and name:
            session.add(ResumeProfile(name=name, description=description, emphasis_skills=emphasis_skills))
            session.commit()
            st.rerun()
    profiles = session.execute(select(ResumeProfile)).scalars().all()
    for p in profiles:
        st.markdown(f"**{p.name}** — emphasizes: {p.emphasis_skills}")

st.divider()

profiles = session.execute(select(ResumeProfile)).scalars().all()
jds = session.execute(select(JobDescription).order_by(JobDescription.created_at.desc())).scalars().all()

c1, c2 = st.columns(2)
profile_options = {"— none —": None} | {p.name: p.id for p in profiles}
jd_options = {"— none —": None} | {f"{jd.title or 'Untitled'} (#{jd.id})": jd.id for jd in jds}
profile_choice = c1.selectbox("Resume profile (optional)", list(profile_options.keys()))
jd_choice = c2.selectbox("Target job description (optional)", list(jd_options.keys()))

profile = session.get(ResumeProfile, profile_options[profile_choice]) if profile_options[profile_choice] else None
jd = session.get(JobDescription, jd_options[jd_choice]) if jd_options[jd_choice] else None

target_skills = []
if profile:
    target_skills += csv_list(profile.emphasis_skills)
if jd:
    target_skills += csv_list(jd.required_skills) + csv_list(jd.preferred_skills)

top_n = st.slider("Number of bullets", 3, 15, 8)

if st.button("Generate resume", type="primary"):
    achievements = session.execute(select(Achievement)).scalars().all()
    if not achievements:
        st.warning("No achievements recorded yet — add some on the Achievements page first.")
    else:
        with st.spinner("Selecting evidence and drafting bullets..."):
            bullets = build_resume_bullets(achievements, target_skills, top_n=top_n)

        match_score = None
        if jd:
            from db.models import Skill
            user_skills = [s.name for s in session.execute(select(Skill)).scalars().all()]
            match = compute_match(csv_list(jd.required_skills), csv_list(jd.preferred_skills), user_skills)
            match_score = match["overall_pct"]

        record = GeneratedResume(
            profile_id=profile.id if profile else None,
            job_description_id=jd.id if jd else None,
            target_role=(jd.title if jd else (profile.name if profile else "General")),
            match_score=match_score,
            bullets_json=json.dumps(bullets),
        )
        session.add(record)
        session.commit()
        st.session_state.last_resume_id = record.id
        st.rerun()

st.divider()
generated = session.execute(select(GeneratedResume).order_by(GeneratedResume.created_at.desc())).scalars().all()
if not generated:
    st.info("No resumes generated yet.")
    session.close()
    st.stop()

resume_options = {f"{r.target_role} — {r.created_at:%Y-%m-%d %H:%M}": r.id for r in generated}
default_index = 0
if "last_resume_id" in st.session_state:
    for i, r in enumerate(generated):
        if r.id == st.session_state.last_resume_id:
            default_index = i
            break
selected_label = st.selectbox("View a generated resume", list(resume_options.keys()), index=default_index)
resume = session.get(GeneratedResume, resume_options[selected_label])
bullets = json.loads(resume.bullets_json)

st.subheader(f"Resume: {resume.target_role}")
if resume.match_score is not None:
    st.metric("Match score at time of generation", f"{resume.match_score}%")

full_text_lines = []
for b in bullets:
    st.markdown(f"- {b['text']}")
    full_text_lines.append(f"- {b['text']}")
    with st.expander("Show evidence"):
        if b["source_type"] == "achievement":
            a = session.get(Achievement, b["source_id"])
            if a:
                st.markdown(f"**Achievement #{a.id}:** {a.title}")
                st.markdown(f"S: {a.situation}\n\nT: {a.task}\n\nA: {a.action}\n\nR: {a.result}\n\nMetric: {a.metric}")
                if a.source_work_log_id:
                    wl = session.get(WorkLog, a.source_work_log_id)
                    if wl:
                        st.markdown(f"↳ **Work Log** {wl.date}: {wl.raw_text}")
                if a.project_id:
                    proj = session.get(Project, a.project_id)
                    if proj:
                        st.markdown(f"↳ **Project:** {proj.name}")
            else:
                st.caption("Source achievement was deleted.")

st.download_button(
    "⬇️ Download as plain text",
    data="\n".join(full_text_lines),
    file_name=f"resume_{resume.target_role.replace(' ', '_')}.txt",
)

session.close()
