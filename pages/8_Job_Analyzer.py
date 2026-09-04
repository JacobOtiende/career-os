import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from sqlalchemy import select

from db.database import init_db, get_session
from db.models import JobDescription, Skill, Achievement
from ai.matching import analyze_job_description, compute_match
from common import csv_list

st.set_page_config(page_title="Job Analyzer", page_icon="🎯", layout="wide")
init_db()
st.title("🎯 Job Description Analyzer & Match Engine")

session = get_session()
user_skills = [s.name for s in session.execute(select(Skill)).scalars().all()]

st.subheader("Paste a target job description")
c1, c2 = st.columns(2)
title = c1.text_input("Job title")
company = c2.text_input("Company")
raw_text = st.text_area("Job description text", height=220)

if st.button("Analyze", type="primary", disabled=not raw_text.strip()):
    with st.spinner("Analyzing..."):
        analysis = analyze_job_description(raw_text)
    jd = JobDescription(
        title=title, company=company, raw_text=raw_text,
        required_skills=", ".join(analysis.get("required_skills", [])),
        preferred_skills=", ".join(analysis.get("preferred_skills", [])),
        competencies=", ".join(analysis.get("competencies", [])),
    )
    session.add(jd)
    session.commit()
    st.session_state.last_jd_id = jd.id
    st.rerun()

st.divider()
saved_jds = session.execute(select(JobDescription).order_by(JobDescription.created_at.desc())).scalars().all()
if not saved_jds:
    st.info("No job descriptions analyzed yet.")
    session.close()
    st.stop()

jd_options = {f"{jd.title or 'Untitled'} — {jd.company} (#{jd.id})": jd.id for jd in saved_jds}
default_index = 0
if "last_jd_id" in st.session_state:
    for i, jd in enumerate(saved_jds):
        if jd.id == st.session_state.last_jd_id:
            default_index = i
            break
selected_label = st.selectbox("Select a job description to view its match", list(jd_options.keys()), index=default_index)
jd = session.get(JobDescription, jd_options[selected_label])

required = csv_list(jd.required_skills)
preferred = csv_list(jd.preferred_skills)

st.markdown(f"**Required skills found:** {', '.join(required) or '—'}")
st.markdown(f"**Preferred skills found:** {', '.join(preferred) or '—'}")
st.markdown(f"**Competencies found:** {jd.competencies or '—'}")

match = compute_match(required, preferred, user_skills)

st.subheader("Job Match Analysis")
st.metric("Overall Match", f"{match['overall_pct']}%")
c1, c2 = st.columns(2)
c1.metric("Required Skills Match", f"{match['required_pct']}%")
c2.metric("Preferred Skills Match", f"{match['preferred_pct']}%")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**✓ Strong Matches**")
    for s in match["strong_matches"]:
        st.markdown(f"- {s}")
with c2:
    st.markdown("**△ Partial Matches**")
    for s in match["partial_matches"]:
        st.markdown(f"- {s}")
with c3:
    st.markdown("**! Gaps**")
    for s in match["gaps"]:
        st.markdown(f"- {s}")

st.subheader("Recommended evidence")
all_achievements = session.execute(select(Achievement)).scalars().all()
relevant = []
target_skills_lower = {s.lower() for s in required + preferred}
for a in all_achievements:
    a_skills = {s.strip().lower() for s in csv_list(a.skills)}
    overlap = len(a_skills & target_skills_lower)
    if overlap > 0:
        relevant.append((a, overlap))
relevant.sort(key=lambda pair: pair[1], reverse=True)
if relevant:
    for a, overlap in relevant[:5]:
        st.markdown(f"- **{a.title}** ({overlap} matching skill{'s' if overlap != 1 else ''})")
else:
    st.caption("No achievements overlap with this job's skills yet.")

st.caption("Generate a targeted resume from this analysis on the Resume Generator page.")

session.close()
