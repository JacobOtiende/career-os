import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import datetime as dt
import streamlit as st
from sqlalchemy import select, func

from db.database import init_db, get_session
from db.models import Volunteer, WorkLog

st.set_page_config(page_title="Volunteer", page_icon="🤝", layout="wide")
init_db()
st.title("🤝 Volunteer & Community Experience")

session = get_session()

with st.expander("➕ Add a volunteer organization", expanded=False):
    with st.form("add_volunteer", clear_on_submit=True):
        organization = st.text_input("Organization*")
        role = st.text_input("Role")
        c1, c2 = st.columns(2)
        start_date = c1.date_input("Start Date", value=dt.date.today())
        end_date = c2.date_input("End Date", value=None)
        responsibilities = st.text_area("Responsibilities")
        community_impact = st.text_area("Community Impact")
        events = st.text_area("Events / Presentations")
        partnerships = st.text_input("Partnerships")
        if st.form_submit_button("Save") and organization:
            v = Volunteer(
                organization=organization, role=role, start_date=start_date, end_date=end_date,
                responsibilities=responsibilities, community_impact=community_impact,
                events=events, partnerships=partnerships,
            )
            session.add(v)
            session.commit()
            st.success(f"Saved {organization}")
            st.rerun()

st.divider()
orgs = session.execute(select(Volunteer)).scalars().all()
if not orgs:
    st.info("No volunteer experience recorded yet.")
else:
    for v in orgs:
        hours = session.execute(
            select(func.coalesce(func.sum(WorkLog.hours), 0.0)).where(WorkLog.volunteer_org_id == v.id)
        ).scalar()
        with st.expander(f"{v.organization} — {v.role} ({hours:.1f} logged hours)"):
            st.markdown(f"**Dates:** {v.start_date} – {v.end_date or 'present'}")
            if v.responsibilities: st.markdown(f"**Responsibilities:** {v.responsibilities}")
            if v.community_impact: st.markdown(f"**Community Impact:** {v.community_impact}")
            if v.events: st.markdown(f"**Events/Presentations:** {v.events}")
            if v.partnerships: st.markdown(f"**Partnerships:** {v.partnerships}")
            st.caption("Log volunteer hours on the Daily Work Log page (select this org, category = volunteer).")
            if st.button("Delete", key=f"del_vol_{v.id}"):
                session.delete(v)
                session.commit()
                st.rerun()

session.close()
