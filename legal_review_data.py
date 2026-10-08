from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"


def load_all_data() -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(DATA_DIR.glob("*.txt")):
        files[path.name] = path.read_text(encoding="utf-8").strip()
    return files


def get_document_packet() -> str:
    return load_all_data().get("legal_document_packet.txt", "")


def get_precedents() -> str:
    return load_all_data().get("legal_precedents.txt", "")


def get_document_ingestion_rules() -> str:
    return load_all_data().get("document_ingestion_instructions.txt", "")


def get_clause_extraction_rules() -> str:
    return load_all_data().get("clause_extraction_instructions.txt", "")


def get_compliance_rules() -> str:
    return load_all_data().get("compliance_validation_instructions.txt", "")


def get_orchestrator_rules() -> str:
    return load_all_data().get("legal_review_orchestrator_instructions.txt", "")


def get_all_relevant_context() -> str:
    sections = []
    for file_name, content in sorted(load_all_data().items()):
        sections.append(f"--- {file_name} ---\n{content}")
    return "\n\n".join(sections)


def get_context_for_question(question: str) -> str:
    text = question.lower()
    data = load_all_data()
    relevant_files: list[str] = []

    if any(word in text for word in ["document", "packet", "agreement", "annex", "schedule", "intake"]):
        relevant_files.extend([
            "legal_document_packet.txt",
            "document_ingestion_instructions.txt",
        ])

    if any(word in text for word in ["clause", "liability", "termination", "retention", "subprocessor", "audit"]):
        relevant_files.extend([
            "legal_document_packet.txt",
            "clause_extraction_instructions.txt",
        ])

    if any(word in text for word in ["compliance", "gdpr", "precedent", "risk", "privacy", "summary"]):
        relevant_files.extend([
            "legal_document_packet.txt",
            "compliance_validation_instructions.txt",
            "legal_precedents.txt",
            "legal_review_orchestrator_instructions.txt",
        ])

    if not relevant_files:
        relevant_files = sorted(data.keys())

    unique_files: list[str] = []
    for file_name in relevant_files:
        if file_name not in unique_files:
            unique_files.append(file_name)

    sections = []
    for file_name in unique_files:
        if file_name in data:
            sections.append(f"--- {file_name} ---\n{data[file_name]}")
    return "\n\n".join(sections)


@dataclass
class RetrievedPrecedent:
    title: str
    detail: str
    score: int


def _extract_section_names(text: str) -> list[str]:
    names: list[str] = []
    for line in text.splitlines():
        clean_line = line.strip()
        if not clean_line:
            continue
        if clean_line.startswith("Section ") or clean_line.startswith("Appendix "):
            names.append(clean_line)
        elif clean_line.endswith(":") and len(clean_line.split()) <= 8:
            names.append(clean_line.rstrip(":"))
    return names


def summarize_available_documents() -> dict[str, str | list[str]]:
    packet = get_document_packet()
    sections = _extract_section_names(packet)
    metadata: dict[str, str | list[str]] = {
        "packet_name": "Contoso Data Processing Addendum Packet",
        "document_type": "Data Processing Addendum with supporting operational appendix",
        "parties": [
            "Contoso Analytics Europe GmbH",
            "Northwind Cloud Services Pvt Ltd",
        ],
        "section_headers": sections,
    }
    return metadata


def extract_clauses() -> dict[str, str]:
    packet = get_document_packet()
    results: dict[str, str] = {}
    tracked_headers = [
        "Section 1: Scope and Roles",
        "Section 2: Security Controls",
        "Section 3: Subprocessor Approval",
        "Section 4: Data Retention and Deletion",
        "Section 5: Audit Rights",
        "Section 6: Incident Notification",
        "Section 7: Cross-Border Transfers",
        "Section 8: Limitation of Liability",
        "Section 9: Termination Assistance",
        "Appendix A: Operational Notes",
    ]

    current_header = ""
    buffer: list[str] = []
    for raw_line in packet.splitlines():
        line = raw_line.strip()
        if line in tracked_headers:
            if current_header:
                results[current_header] = " ".join(buffer).strip()
            current_header = line
            buffer = []
            continue
        if current_header:
            buffer.append(line)

    if current_header:
        results[current_header] = " ".join(buffer).strip()

    return results


def retrieve_precedents(question: str, limit: int = 3) -> list[RetrievedPrecedent]:
    precedents = get_precedents().split("\n\n")
    keywords = {word for word in question.lower().replace(",", " ").split() if len(word) > 3}
    scored: list[RetrievedPrecedent] = []

    for chunk in precedents:
        lines = [line.strip() for line in chunk.splitlines() if line.strip()]
        if not lines:
            continue
        title = lines[0]
        detail = " ".join(lines[1:])
        haystack = f"{title} {detail}".lower()
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score > 0:
            scored.append(RetrievedPrecedent(title=title, detail=detail, score=score))

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:limit]


def validate_compliance() -> dict[str, str]:
    clauses = extract_clauses()
    findings: dict[str, str] = {}

    retention_clause = clauses.get("Section 4: Data Retention and Deletion", "")
    audit_clause = clauses.get("Section 5: Audit Rights", "")
    incident_clause = clauses.get("Section 6: Incident Notification", "")
    transfer_clause = clauses.get("Section 7: Cross-Border Transfers", "")
    liability_clause = clauses.get("Section 8: Limitation of Liability", "")
    termination_clause = clauses.get("Section 9: Termination Assistance", "")
    subprocessor_clause = clauses.get("Section 3: Subprocessor Approval", "")

    findings["Retention Obligation"] = (
        "Pass: deletion timeline is explicitly stated." if "30 calendar days" in retention_clause else "Flag: no explicit deletion timeline found."
    )
    findings["Audit Rights"] = (
        "Pass: annual audit right and breach-triggered audit are stated." if "once per contract year" in audit_clause and "material security incident" in audit_clause else "Flag: audit rights are incomplete."
    )
    findings["Incident Notification"] = (
        "Pass: notice window is within 72 hours." if "within 48 hours" in incident_clause else "Flag: incident notification window is missing or too broad."
    )
    findings["Cross-Border Transfers"] = (
        "Pass: transfer safeguard is specified." if "Standard Contractual Clauses" in transfer_clause else "Flag: transfer safeguard is not specified."
    )
    findings["Liability Risk"] = (
        "Flag: liability cap may undercut privacy-risk exposure." if "fees paid in the prior six months" in liability_clause else "Pass: liability cap language not flagged by the checklist."
    )
    findings["Termination Assistance"] = (
        "Pass: termination support window is defined." if "transition assistance for up to 45 days" in termination_clause else "Flag: termination assistance is not explicit."
    )
    findings["Subprocessor Governance"] = (
        "Flag: approval model is opt-out rather than explicit approval." if "deemed approved" in subprocessor_clause else "Pass: explicit subprocessor approval is stated."
    )

    return findings
