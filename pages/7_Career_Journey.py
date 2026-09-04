import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import datetime as dt
import streamlit as st
from sqlalchemy import select

from db.database import init_db, get_session
from db.models import Employment, Education, Certification, Project, Achievement

st.set_page_config(page_title="Career Journey", page_icon="🧭", layout="wide")
init_db()
st.title("🧭 Career Journey")

session = get_session()

tab_employment, tab_education, tab_cert, tab_timeline = st.tabs(
    ["Employment", "Education", "Certifications", "Timeline"]
)

with tab_employment:
    with st.expander("➕ Add employment", expanded=False):
        with st.form("add_employment", clear_on_submit=True):
            organization = st.text_input("Organization*")
            role = st.text_input("Role*")
            c1, c2, c3 = st.columns(3)
            start_date = c1.date_input("Start Date", value=dt.date.today())
            end_date = c2.date_input("End Date", value=None)
            is_current = c3.checkbox("Current", value=True)
            if st.form_submit_button("Save") and organization and role:
                session.add(Employment(organization=organization, role=role, start_date=start_date,
                                        end_date=end_date, is_current=is_current))
                session.commit()
                st.rerun()
    employments = session.execute(select(Employment).order_by(Employment.start_date.desc())).scalars().all()
    for e in employments:
        st.markdown(f"**{e.organization}** — {e.role} ({e.start_date} – {'present' if e.is_current else e.end_date})")

with tab_education:
    with st.expander("➕ Add education", expanded=False):
        with st.form("add_education", clear_on_submit=True):
            school = st.text_input("School*")
            degree = st.text_input("Degree")
            field = st.text_input("Field of study")
            c1, c2 = st.columns(2)
            start_date = c1.date_input("Start Date", value=dt.date.today(), key="edu_start")
            end_date = c2.date_input("End Date", value=None, key="edu_end")
            if st.form_submit_button("Save") and school:
                session.add(Education(school=school, degree=degree, field=field,
                                       start_date=start_date, end_date=end_date))
                session.commit()
                st.rerun()
    for ed in session.execute(select(Education)).scalars().all():
        st.markdown(f"**{ed.school}** — {ed.degree} in {ed.field} ({ed.start_date} – {ed.end_date or 'present'})")

with tab_cert:
    with st.expander("➕ Add certification", expanded=False):
        with st.form("add_cert", clear_on_submit=True):
            name = st.text_input("Certification name*")
            issuer = st.text_input("Issuer")
            c1, c2 = st.columns(2)
            date_earned = c1.date_input("Date earned", value=dt.date.today())
            expires = c2.date_input("Expires", value=None)
            if st.form_submit_button("Save") and name:
                session.add(Certification(name=name, issuer=issuer, date_earned=date_earned, expires=expires))
                session.commit()
                st.rerun()
    for c in session.execute(select(Certification)).scalars().all():
        exp = f" (expires {c.expires})" if c.expires else ""
        st.markdown(f"**{c.name}** — {c.issuer}, earned {c.date_earned}{exp}")

with tab_timeline:
    st.caption("Auto-built from employment, project, and achievement dates.")
    events = []
    for e in session.execute(select(Employment)).scalars().all():
        events.append((e.start_date, f"Started **{e.role}** at {e.organization}"))
        if e.end_date and not e.is_current:
            events.append((e.end_date, f"Ended role at {e.organization}"))
    for p in session.execute(select(Project)).scalars().all():
        if p.start_date:
            events.append((p.start_date, f"Started project **{p.name}**"))
    for a in session.execute(select(Achievement)).scalars().all():
        events.append((a.created_at.date(), f"Achievement: **{a.title}**"))

    events = [ev for ev in events if ev[0] is not None]
    events.sort(key=lambda ev: ev[0])
    if events:
        for date, label in events:
            st.markdown(f"**{date}** — {label}")
    else:
        st.info("No timeline events yet — add employment, projects, or achievements.")

session.close()
