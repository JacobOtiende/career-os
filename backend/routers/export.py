import csv
import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import inspect as sa_inspect, text

from db.database import engine

router = APIRouter(tags=["export"])


def _table_rows(table_name: str) -> list[dict]:
    if table_name not in sa_inspect(engine).get_table_names():
        raise HTTPException(404, "Unknown table")
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {table_name}"))
        return [dict(row._mapping) for row in result]


@router.get("/export/tables")
def list_tables():
    return sa_inspect(engine).get_table_names()


@router.get("/export/table/{table_name}")
def export_table(table_name: str):
    return _table_rows(table_name)


@router.get("/export/table/{table_name}/csv")
def export_table_csv(table_name: str):
    rows = _table_rows(table_name)
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={table_name}.csv"},
    )


@router.get("/export/all")
def export_all():
    tables = sa_inspect(engine).get_table_names()
    return {t: _table_rows(t) for t in tables}
