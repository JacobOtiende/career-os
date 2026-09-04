import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
from sqlalchemy import select, func

from db.database import init_db, get_session
from db.models import Skill, SkillEvidence, WorkLog, Project, Achievement

st.set_page_config(page_title="Skills", page_icon="🧠", layout="wide")
init_db()
st.title("🧠 Skills & Competency Graph")
st.caption("Not just a level — every skill is backed by linked evidence.")

session = get_session()
skills = session.execute(select(Skill).order_by(Skill.category, Skill.name)).scalars().all()

if not skills:
    st.info("No skills tracked yet. They accumulate automatically as you log work, projects, and achievements.")
    session.close()
    st.stop()

category_filter = st.multiselect(
    "Category", sorted({s.category for s in skills}), default=sorted({s.category for s in skills})
)

rows = []
for s in skills:
    if s.category not in category_filter:
        continue
    evidence = session.execute(select(SkillEvidence).where(SkillEvidence.skill_id == s.id)).scalars().all()
    last_demo = max((e.demonstrated_on for e in evidence), default=None)
    rows.append({
        "id": s.id, "Skill": s.name, "Category": s.category,
        "Evidence Count": len(evidence), "Last Demonstrated": last_demo,
    })

df = pd.DataFrame(rows).sort_values("Evidence Count", ascending=False)
st.dataframe(df.drop(columns="id"), width='stretch', hide_index=True)

st.divider()
st.subheader("Evidence detail")
selected_skill_name = st.selectbox("Select a skill to see evidence", df["Skill"].tolist())
skill_id = df[df["Skill"] == selected_skill_name]["id"].iloc[0]
evidence = session.execute(
    select(SkillEvidence).where(SkillEvidence.skill_id == skill_id).order_by(SkillEvidence.demonstrated_on.desc())
).scalars().all()

for e in evidence:
    label_map = {"work_log": "Work Log", "project": "Project", "achievement": "Achievement"}
    st.markdown(f"**{e.demonstrated_on}** — {label_map.get(e.source_type, e.source_type)} #{e.source_id}: {e.note}")

session.close()
