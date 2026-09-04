# Career OS

A personal career-evidence system, built from the project proposal in
`../Proposal.txt`. Continuously log what you actually do at work, and let
the app turn that into structured evidence — skills, achievements, project
history — that can be matched against job descriptions and turned into a
targeted, evidence-traceable resume.

## What's built (Phase 1 + a slice of Phase 2/3)

- **Daily Work Log** — free-text entry, AI-assisted (or rule-based) extraction of skills/tools/problems/accomplishments, always editable before saving
- **Time Tracking** — hours by category/org/project, monthly trend
- **Project Portfolio** — full project records (problem, actions, results, metrics, lessons learned)
- **Achievements** — STAR + Metric records, can be drafted from a work log entry with AI
- **Skills & Competency Graph** — every skill backed by linked evidence (work logs, projects, achievements), not just a claimed level
- **Volunteer & Community Experience**
- **Career Journey** — employment, education, certifications, and an auto-built timeline
- **Job Description Analyzer & Match Engine** — paste a JD, get required/preferred skills, a deterministic (non-hallucinated) match score, strong matches, gaps, and recommended evidence
- **Resume Generator** — builds bullets from your highest-relevance achievements for a target profile/job, with a "Show evidence" trace on every bullet back to its Achievement → Work Log/Project
- **Data Export** — CSV per table or a full JSON export, plus the raw SQLite file path, since this database is meant to become years of career evidence

## Deliberately deferred (see the proposal's own phase plan)

- Authentication / multi-user (this is a local, single-user app)
- Vector database / semantic search (ChromaDB) — add once you have enough entries that keyword matching stops being enough
- The proposal's 10 separate "agents" are implemented as functions in `ai/`, not separate processes — same separation of concerns, no operational overhead
- Cover letters, LinkedIn content, monthly auto-review, promotion packages — natural next additions once the core loop (log → evidence → match → resume) is in daily use

## Architecture

A FastAPI backend (`backend/`) exposes a JSON API over the same SQLite
database and `ai/` extraction/matching/resume logic used throughout. The
frontend (`frontend/`) is plain HTML/CSS/JS — no build step, no framework —
served as static files by the same FastAPI app, with real page layout
(sidebar nav, cards, tables) instead of a forms-first widget UI.

```
backend/
  main.py           FastAPI app, mounts the frontend, wires up routers
  deps.py           DB session + ORM-to-dict helpers shared by all routers
  routers/          one file per domain (worklogs, projects, achievements, ...)
frontend/
  index.html        app shell: sidebar + #content mount point
  static/js/api.js  fetch wrapper for every backend endpoint
  static/js/app.js  hash-based router, dispatches to Pages.<route>.render()
  static/js/pages/  one file per page, each sets Pages.<name> = { render }
db/, ai/, common.py  unchanged — same models and extraction/matching/resume logic
```

## Setup

```bash
cd career_os
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Optional — enable LLM-powered extraction/matching-narrative/resume drafting
(otherwise the app runs fully offline on rule-based keyword extraction):

```bash
copy .env.example .env
# then edit .env and set ANTHROPIC_API_KEY or OPENAI_API_KEY
```

Run it:

```bash
python run.py
```

Then open **http://127.0.0.1:8000**. The database is a single SQLite file
at `data/career.db`, created automatically on first run. Back it up like
any other important file (or use the Data Export page).

## AI design principle (from the proposal, §15)

Every record keeps the user's original raw text (Level 1 — fact), AI
suggestions are shown as editable fields the user confirms (Level 2 —
derived), and generated language like resume bullets always carries a
`source_type`/`source_id` back to the Achievement that produced it
(Level 3 — generated, always traceable). The Job Match score is computed
by deterministic skill-set overlap, never by an LLM guessing a percentage.
