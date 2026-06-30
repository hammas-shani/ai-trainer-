KNOWLEDGE_PACKS = {
    "software_engineer": {
        "terminology": ["React", "FastAPI", "Docker", "Kubernetes", "System Design", "Microservices", "CI/CD"],
        "follow_up_strategies": [
            "If they mention a database, ask how they handled scaling or indexing.",
            "If they mention an architecture, ask about the trade-offs they considered."
        ],
        "evaluation_criteria": ["Problem solving", "Code quality", "Architecture understanding"]
    },
    "sales": {
        "terminology": ["B2B", "SaaS", "ARR", "Churn", "Sales Cycle", "Objection Handling", "Closing"],
        "follow_up_strategies": [
            "If they mention a closed deal, ask what the main objection was and how they overcame it.",
            "If they mention quotas, ask about their strategy for pipeline generation."
        ],
        "evaluation_criteria": ["Persuasion", "Resilience", "Strategic thinking"]
    }
}

def get_knowledge_pack(field: str) -> dict:
    key = field.lower().replace(" ", "_")
    for pack_key in KNOWLEDGE_PACKS:
        if pack_key in key:
            return KNOWLEDGE_PACKS[pack_key]
    return {}
