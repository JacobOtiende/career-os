import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from sqlalchemy import select, inspect

from db.database import init_db, get_session, engine
from db import models

st.set_page_config(page_title="Data Export", page_icon="💾", layout="wide")
init_db()
st.title("💾 Data Export")
st.caption("This database is meant to become years of irreplaceable career evidence — back it up regularly.")

session = get_session()
inspector = inspect(engine)
table_names = inspector.get_table_names()

st.subheader("Export a table as CSV")
table_name = st.selectbox("Table", sorted(table_names))
df = pd.read_sql_table(table_name, engine)
st.dataframe(df, width='stretch', hide_index=True)
st.download_button(
    f"⬇️ Download {table_name}.csv",
    data=df.to_csv(index=False),
    file_name=f"{table_name}.csv",
    mime="text/csv",
)

st.divider()
st.subheader("Export everything as JSON")
if st.button("Build full export"):
    all_data = {name: pd.read_sql_table(name, engine).to_dict(orient="records") for name in table_names}
    import json
    st.download_button(
        "⬇️ Download career_os_export.json",
        data=json.dumps(all_data, default=str, indent=2),
        file_name="career_os_export.json",
        mime="application/json",
    )

st.divider()
st.subheader("Database file location")
from db.database import DB_PATH
st.code(str(DB_PATH))
st.caption("Copy this file directly for a full backup, or use the exports above.")

session.close()
