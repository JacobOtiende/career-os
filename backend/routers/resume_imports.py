import datetime as dt
import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.deps import get_db, row_to_dict
from db.models import ResumeImport, Achievement
from ai.resume_import import extract_text_from_file, parse_resume_bullets, SUPPORTED_EXTENSIONS
from common import record_skill_evidence, csv_list

router = APIRouter(tags=["resume-imports"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads" / "resumes"


class ImportBulletIn(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    skills: Optional[str] = None


@router.get("/resume-imports")
def list_imports(db: Session = Depends(get_db)):
    imports = db.execute(select(ResumeImport).order_by(ResumeImport.uploaded_at.desc())).scalars().all()
    result = []
    for r in imports:
        bullets = json.loads(r.bullets_json)
        d = row_to_dict(r)
        d.pop("raw_text", None)
        d.pop("bullets_json", None)
        d["bullet_count"] = len(bullets)
        d["imported_count"] = sum(1 for b in bullets if b.get("imported"))
        result.append(d)
    return result


@router.post("/resume-imports")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = file.filename.lower().rsplit(".", 1)[-1] if file.filename and "." in file.filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: .{ext}. Use PDF, DOCX, TXT, or MD.")

    content = await file.read()
    if not content:
        raise HTTPException(400, "Empty file.")

    try:
        raw_text = extract_text_from_file(file.filename, content)
    except Exception as e:
        raise HTTPException(400, f"Could not read file: {e}")

    if not raw_text.strip():
        raise HTTPException(400, "No extractable text found in this file.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._- ") or "resume"
    stored_path = UPLOAD_DIR / f"{timestamp}_{safe_name}"
    stored_path.write_bytes(content)

    bullets = parse_resume_bullets(raw_text)
    for b in bullets:
        b["imported"] = False
        b["achievement_id"] = None

    record = ResumeImport(
        filename=file.filename,
        file_path=str(stored_path),
        raw_text=raw_text,
        bullets_json=json.dumps(bullets),
    )
    db.add(record)
    db.commit()

    d = row_to_dict(record)
    d["bullets"] = bullets
    return d


@router.get("/resume-imports/{import_id}")
def get_import(import_id: int, db: Session = Depends(get_db)):
    record = db.get(ResumeImport, import_id)
    if not record:
        raise HTTPException(404, "Not found")
    d = row_to_dict(record)
    d["bullets"] = json.loads(record.bullets_json)
    return d


@router.post("/resume-imports/{import_id}/bullets/{index}/import")
def import_bullet(import_id: int, index: int, payload: ImportBulletIn, db: Session = Depends(get_db)):
    record = db.get(ResumeImport, import_id)
    if not record:
        raise HTTPException(404, "Not found")
    bullets = json.loads(record.bullets_json)
    if index < 0 or index >= len(bullets):
        raise HTTPException(404, "Bullet index out of range")
    bullet = bullets[index]
    if bullet.get("imported"):
        raise HTTPException(400, "This bullet has already been imported.")

    title = payload.title or bullet.get("title") or bullet["text"][:80]
    category = payload.category or bullet.get("category") or "Other"
    skills = payload.skills if payload.skills is not None else ", ".join(bullet.get("skills", []))

    achievement = Achievement(
        title=title,
        category=category,
        resume_bullet=bullet["text"],
        skills=skills,
    )
    db.add(achievement)
    db.commit()
    record_skill_evidence(db, csv_list(skills), "achievement", achievement.id, note=title)

    bullet["imported"] = True
    bullet["achievement_id"] = achievement.id
    bullets[index] = bullet
    record.bullets_json = json.dumps(bullets)
    db.commit()

    return {"achievement": row_to_dict(achievement), "bullet": bullet}


@router.delete("/resume-imports/{import_id}")
def delete_import(import_id: int, db: Session = Depends(get_db)):
    record = db.get(ResumeImport, import_id)
    if not record:
        raise HTTPException(404, "Not found")
    if record.file_path:
        Path(record.file_path).unlink(missing_ok=True)
    db.delete(record)
    db.commit()
    return {"ok": True}
