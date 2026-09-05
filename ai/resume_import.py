"""
Extracts text from an uploaded resume file and splits it into candidate
accomplishment bullets for review. Every candidate is grounded in text that
was literally already in the uploaded file (Level 1 fact) -- the LLM path
is instructed never to invent or merge bullets, and the rule-based fallback
just finds lines that already look like bullets.
"""
import io
import re

from ai.client import complete_json, llm_available
from ai.lexicon import ALL_SKILLS, find_keywords

SUPPORTED_EXTENSIONS = {"pdf", "docx", "txt", "md"}

BULLET_PREFIX = re.compile(r"^[\s]*[•\-\*•●‣▪⁃]\s*")
ACTION_VERB_START = re.compile(
    r"^(Led|Managed|Built|Developed|Designed|Implemented|Resolved|Reduced|Improved|"
    r"Automated|Launched|Created|Coordinated|Trained|Mentored|Delivered|Analyzed|"
    r"Diagnosed|Deployed|Migrated|Optimized|Negotiated|Directed|Established|"
    r"Spearheaded|Streamlined|Increased|Decreased|Achieved|Administered|Configured)\b"
)


def extract_text_from_file(filename: str, content: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: .{ext}")

    if ext == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == "docx":
        from docx import Document
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)

    return content.decode("utf-8", errors="ignore")


def _rule_based_bullets(raw_text: str) -> list[dict]:
    candidates = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        text = BULLET_PREFIX.sub("", stripped).strip()
        looked_like_bullet = text != stripped
        if not looked_like_bullet and not ACTION_VERB_START.match(text):
            continue
        if len(text) < 25 or len(text) > 400:
            continue
        candidates.append({
            "text": text,
            "title": text[:80],
            "category": "",
            "skills": find_keywords(text, ALL_SKILLS),
        })
    return candidates


RESUME_PARSE_SYSTEM_PROMPT = """You are extracting individual accomplishment \
bullet points from resume text. Return ONLY bullets that are already \
present in the text -- do not invent new ones, do not merge multiple \
bullets into one, do not add facts not stated. Skip section headers, dates, \
contact info, and job titles; only actual accomplishment/responsibility \
lines. Respond with strict JSON only:
{"bullets": [{"text": "exact original bullet text", "title": "short title", \
"category": "Leadership|Technical|Analytics|Process Improvement|Other", \
"skills": ["list", "of", "skills"]}]}"""


def parse_resume_bullets(raw_text: str) -> list[dict]:
    if llm_available():
        try:
            result = complete_json(RESUME_PARSE_SYSTEM_PROMPT, raw_text, max_tokens=3000)
            bullets = result.get("bullets", []) if isinstance(result, dict) else result
            cleaned = []
            for b in bullets:
                if not b.get("text"):
                    continue
                cleaned.append({
                    "text": b["text"],
                    "title": b.get("title") or b["text"][:80],
                    "category": b.get("category", ""),
                    "skills": b.get("skills", []),
                })
            if cleaned:
                return cleaned
        except Exception:
            pass
    return _rule_based_bullets(raw_text)
