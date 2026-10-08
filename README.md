# AI-Powered Legal Document Review System

It provides four agents:

- Document Ingestion Agent
- Clause Extraction Agent
- Compliance Validation Agent
- Legal Review Orchestrator Agent

The system uses grounded local text files for legal-document evidence, compliance rules,
and precedent snippets. When Azure AI Agent Service is available, each specialist can run
through Azure Agents. When it is not available, the same workflow still runs through the
local fallback logic so the project remains demonstrable.

## Project Structure

- `data/`: grounded legal packet, compliance rules, and RAG-style precedent notes
- `document_ingestion_agent/`: identifies the document set and captures a grounded intake summary
- `clause_extraction_agent/`: extracts key clauses and obligations from the provided packet
- `compliance_agent/`: validates the extracted clauses against the compliance checklist
- `orchestrator_agent/`: plans which specialists to call, keeps short memory, and produces the final review
- `run_all.py`: starts all services and opens a terminal client

## Running

1. Fill in `.env`
2. Install dependencies from `requirements.txt`
3. Run `python run_all.py`

The interactive client supports questions such as:

- `Summarize the available legal documents.`
- `Extract the data-processing and termination clauses.`
- `Validate the packet for GDPR, audit rights, and retention obligations.`
- `Give me a grounded legal review summary with precedent context.`
