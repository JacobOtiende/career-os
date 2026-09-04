"""
Built-in keyword lexicon used for rule-based extraction when no LLM is
configured, and as a candidate list the LLM is grounded against when one is.
Extend freely -- this is just a starting seed, not a limit on what a user
can record (free-text skills typed by the user are always kept too).
"""

TECHNICAL_SKILLS = [
    "Python", "SQL", "PowerShell", "Bash", "Windows", "Linux", "macOS",
    "Networking", "Active Directory", "Endpoint Management", "MDM", "Intune",
    "Cloud", "AWS", "Azure", "GCP", "Data Analytics", "Data Visualization",
    "Machine Learning", "AI", "RAG", "LLM", "NLP", "ChromaDB", "Embeddings",
    "Git", "Docker", "Kubernetes", "REST API", "FastAPI", "Streamlit",
    "Excel", "Power BI", "Tableau", "ETL", "Pandas", "NumPy", "Imaging",
    "Deployment", "Troubleshooting", "Ticketing", "ITSM", "ServiceNow",
    "Microsoft 365", "Exchange", "VMware", "Virtualization", "Scripting",
    "Automation", "Security", "Backup", "Vendor Management",
]

BUSINESS_SKILLS = [
    "Business Analytics", "Process Improvement", "Project Management",
    "Requirements Analysis", "Stakeholder Communication", "Budgeting",
    "Strategic Planning", "Risk Management", "Documentation", "Reporting",
    "Change Management", "Procurement",
]

LEADERSHIP_SKILLS = [
    "Team Leadership", "Training", "Mentoring", "Coaching", "Delegation",
    "Conflict Resolution", "Performance Management", "Onboarding",
    "Presentation", "Communication", "Public Speaking", "Fundraising",
    "Community Outreach", "Relationship Building",
]

ALL_SKILLS = TECHNICAL_SKILLS + BUSINESS_SKILLS + LEADERSHIP_SKILLS

SKILL_CATEGORY = {s: "Technical" for s in TECHNICAL_SKILLS}
SKILL_CATEGORY.update({s: "Business" for s in BUSINESS_SKILLS})
SKILL_CATEGORY.update({s: "Leadership" for s in LEADERSHIP_SKILLS})

COMPETENCIES = [
    "Problem Solving", "Technical Support", "Incident Management",
    "Leadership", "Communication", "Strategic Planning", "Collaboration",
    "Adaptability", "Critical Thinking", "Time Management",
]


def find_keywords(text: str, vocabulary: list[str]) -> list[str]:
    """Case-insensitive substring match of vocabulary terms in text,
    preserving canonical casing from the vocabulary."""
    lowered = text.lower()
    return [term for term in vocabulary if term.lower() in lowered]
