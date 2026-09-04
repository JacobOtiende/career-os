import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import datetime as dt
import pandas as pd
import streamlit as st
from sqlalchemy import select

from db.database import init_db, get_session
from db.models import WorkLog, Employment, Project

st.set_page_config(page_title="Time Tracking", page_icon="⏱️", layout="wide")
init_db()
st.title("⏱️ Time Tracking")

session = get_session()
logs = session.execute(select(WorkLog)).scalars().all()

if not logs:
    st.info("No work log entries yet. Add some on the Daily Work Log page.")
    session.close()
    st.stop()

emp_map = {e.id: e.organization for e in session.execute(select(Employment)).scalars().all()}
proj_map = {p.id: p.name for p in session.execute(select(Project)).scalars().all()}

df = pd.DataFrame([{
    "Date": l.date,
    "Organization": emp_map.get(l.employment_id, ""),
    "Project": proj_map.get(l.project_id, ""),
    "Category": l.category,
    "Hours": l.hours,
} for l in logs])
df["Date"] = pd.to_datetime(df["Date"])
df["Month"] = df["Date"].dt.to_period("M").astype(str)

col1, col2 = st.columns(2)
month_options = sorted(df["Month"].unique(), reverse=True)
selected_month = col1.selectbox("Month", ["All"] + month_options)
view = df if selected_month == "All" else df[df["Month"] == selected_month]

col1.metric("Total Hours", f"{view['Hours'].sum():.1f}")
col2.metric("Entries", len(view))

st.subheader("Hours by category")
by_category = view.groupby("Category")["Hours"].sum().sort_values(ascending=False)
st.bar_chart(by_category)

st.subheader("Hours by organization")
by_org = view[view["Organization"] != ""].groupby("Organization")["Hours"].sum().sort_values(ascending=False)
if not by_org.empty:
    st.bar_chart(by_org)

st.subheader("Hours by project")
by_proj = view[view["Project"] != ""].groupby("Project")["Hours"].sum().sort_values(ascending=False)
if not by_proj.empty:
    st.bar_chart(by_proj)

st.subheader("Monthly trend")
monthly = df.groupby("Month")["Hours"].sum()
st.line_chart(monthly)

st.divider()
st.subheader("Raw log")
st.dataframe(view.sort_values("Date", ascending=False), width='stretch', hide_index=True)

session.close()
