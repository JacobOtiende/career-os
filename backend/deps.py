import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import datetime as dt
from sqlalchemy import inspect as sa_inspect
from db.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def row_to_dict(obj) -> dict:
    d = {}
    for col in sa_inspect(obj).mapper.column_attrs:
        val = getattr(obj, col.key)
        if isinstance(val, (dt.date, dt.datetime)):
            val = val.isoformat()
        d[col.key] = val
    return d


def rows_to_list(objs) -> list[dict]:
    return [row_to_dict(o) for o in objs]
