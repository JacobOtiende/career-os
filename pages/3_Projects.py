import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import datetime as dt
import streamlit as st
from sqlalchemy import select

from db.database import init_db, get_session
from db.models import Project
from common import record_skill_evidence, csv_list

st.set_page_config(page_title="Projects", page_icon="📁", layout="wide")
init_db()
st.title("📁 Project Portfolio")

session = get_session()

with st.expander("➕ Add a project", expanded=False):
    with st.form("add_project", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Project Name*")
        organization = c2.text_input("Organization")
        role = c3.text_input("Your Role")

        c4, c5, c6 = st.columns(3)
        start_date = c4.date_input("Start Date", value=dt.date.today())
        end_date = c5.date_input("End Date", value=None)
        status = c6.selectbox("Status", ["planned", "active", "completed", "on_hold"])

        problem = st.text_area("Problem")
        objective = st.text_area("Objective")
        responsibilities = st.text_area("Responsibilities")

        c7, c8, c9 = st.columns(3)
        technologies = c7.text_input("Technologies (comma-separated)")
        tools = c8.text_input("Tools (comma-separated)")
        methods = c9.text_input("Methods")

        challenges = st.text_area("Challenges")
        solutions = st.text_area("Solutions")
        results = st.text_area("Results")
        metrics = st.text_input("Metrics")
        people_teams = st.text_input("People / Teams")
        leadership = st.text_area("Leadership")
        lessons_learned = st.text_area("Lessons Learned")

        if st.form_submit_button("Save project") and name:
            project = Project(
                name=name, organization=organization, role=role,
                start_date=start_date, end_date=end_date, status=status,
                problem=problem, objective=objective, responsibilities=responsibilities,
                technologies=technologies, tools=tools, methods=methods,
                challenges=challenges, solutions=solutions, results=results,
                metrics=metrics, people_teams=people_teams, leadership=leadership,
                lessons_learned=lessons_learned,
            )
            session.add(project)
            session.commit()
            tech_skills = csv_list(technologies) + csv_list(tools)
            record_skill_evidence(session, tech_skills, "project", project.id, note=f"Project: {name}")
            session.commit()
            st.success(f"Saved {name}")
            st.rerun()

st.divider()

projects = session.execute(select(Project).order_by(Project.start_date.desc())).scalars().all()
if not projects:
    st.info("No projects yet.")
else:
    status_filter = st.multiselect("Filter by status", ["planned", "active", "completed", "on_hold"],
                                    default=["planned", "active", "completed", "on_hold"])
    for p in [p for p in projects if p.status in status_filter]:
        with st.expander(f"{'●' if p.status == 'active' else '○'} {p.name} — {p.organization} ({p.status})"):
            st.markdown(f"**Role:** {p.role}  \n**Dates:** {p.start_date} – {p.end_date or 'present'}")
            if p.objective:
                st.markdown(f"**Objective:** {p.objective}")
            if p.responsibilities:
                st.markdown(f"**Responsibilities:** {p.responsibilities}")
            if p.technologies:
                st.markdown(f"**Technologies:** {p.technologies}")
            if p.tools:
                st.markdown(f"**Tools:** {p.tools}")
            if p.challenges:
                st.markdown(f"**Challenges:** {p.challenges}")
            if p.solutions:
                st.markdown(f"**Solutions:** {p.solutions}")
            if p.results:
                st.markdown(f"**Results:** {p.results}")
            if p.metrics:
                st.markdown(f"**Metrics:** {p.metrics}")
            if p.leadership:
                st.markdown(f"**Leadership:** {p.leadership}")
            if p.lessons_learned:
                st.markdown(f"**Lessons Learned:** {p.lessons_learned}")

            if st.button("Delete project", key=f"del_{p.id}"):
                session.delete(p)
                session.commit()
                st.rerun()

session.close()
