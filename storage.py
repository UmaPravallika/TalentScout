# storage.py
import json
import os
from datetime import datetime
from typing import Dict

DATA_DIR = "data"
CANDIDATES_FILE = os.path.join(DATA_DIR, "candidates.jsonl")
os.makedirs(DATA_DIR, exist_ok=True)

def _mask_email(email: str) -> str:
    if "@" not in email:
        return email
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        masked = name[0] + "***"
    else:
        masked = name[0] + "***" + name[-1]
    return f"{masked}@{domain}"

def _mask_phone(phone: str) -> str:
    digits = "".join([c for c in phone if c.isdigit()])
    if len(digits) < 4:
        return phone
    return "***-***-" + digits[-4:]

def save_candidate(candidate: Dict) -> None:
    # Store full record locally, but mask PII in logs if needed elsewhere
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "full_name": candidate.get("full_name", ""),
        "email": candidate.get("email", ""),
        "phone": candidate.get("phone", ""),
        "years_of_experience": candidate.get("years_of_experience", ""),
        "desired_roles": candidate.get("desired_roles", []),
        "location": candidate.get("location", ""),
        "tech_stack": candidate.get("tech_stack", []),
        "answers": candidate.get("answers", {}),
    }
    with open(CANDIDATES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def anonymized_preview(candidate: Dict) -> Dict:
    return {
        "full_name": candidate.get("full_name", ""),
        "email": _mask_email(candidate.get("email", "")),
        "phone": _mask_phone(candidate.get("phone", "")),
        "years_of_experience": candidate.get("years_of_experience", ""),
        "desired_roles": candidate.get("desired_roles", []),
        "location": candidate.get("location", ""),
        "tech_stack": candidate.get("tech_stack", []),
    }
