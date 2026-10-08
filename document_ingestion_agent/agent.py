"""Document ingestion agent for the legal review workflow."""

import os

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import Agent, ListSortOrder, MessageRole
from azure.identity import DefaultAzureCredential

from review_data import (
    get_context_for_question,
    get_document_ingestion_rules,
    summarize_available_documents,
)


class DocumentIngestionAgent:

    def __init__(self):
        self.client = AgentsClient(
            endpoint=os.environ["PROJECT_ENDPOINT"],
            credential=DefaultAzureCredential(
                exclude_environment_credential=True,
                exclude_managed_identity_credential=True,
            ),
        )
        self.agent: Agent | None = None
        self.azure_available = True

    async def create_agent(self) -> Agent | None:
        if self.agent:
            return self.agent

        try:
            self.agent = self.client.create_agent(
                model=os.environ["MODEL_DEPLOYMENT_NAME"],
                name="document-ingestion-agent",
                instructions="""
                You are a legal document ingestion specialist.

                Use only the provided legal packet and ingestion rules.
                Identify what documents or sections are available, name the parties when stated,
                and capture grounded metadata without inventing missing legal evidence.
                """,
            )
            return self.agent
        except Exception:
            self.azure_available = False
            return None

    def _fallback_answer(self, user_message: str) -> str:
        summary = summarize_available_documents()
        rules = get_document_ingestion_rules()
        sections = [
            "Document Ingestion Summary",
            "--------------------------",
            f"Packet Name: {summary['packet_name']}",
            f"Document Type: {summary['document_type']}",
            "Parties:",
        ]

        for party in summary["parties"]:
            sections.append(f"- {party}")

        sections.append("Available Sections:")
        for header in summary["section_headers"]:
            sections.append(f"- {header}")

        sections.extend([
            "",
            "Ingestion Rules",
            rules,
            "",
            "Assessment Summary",
            "The ingestion summary is grounded only in the supplied legal packet. No external repository, filing system, or additional attachment was used.",
        ])
        return "\n".join(sections)

    async def run_conversation(self, user_message: str) -> list[str]:
        if not self.agent and self.azure_available:
            try:
                await self.create_agent()
            except Exception:
                self.azure_available = False

        if not self.azure_available or self.agent is None:
            return [self._fallback_answer(user_message)]

        try:
            thread = self.client.threads.create()
            self.client.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=f"Use only the provided legal packet.\n\n{get_context_for_question(user_message)}\n\nQuestion: {user_message}",
            )
            run = self.client.runs.create_and_process(
                thread_id=thread.id,
                agent_id=self.agent.id,
            )

            if run.status == "failed":
                return [self._fallback_answer(user_message)]

            messages = self.client.messages.list(
                thread_id=thread.id,
                order=ListSortOrder.DESCENDING,
            )
            responses = []
            for msg in messages:
                if msg.role == MessageRole.AGENT and msg.text_messages:
                    for text_msg in msg.text_messages:
                        responses.append(text_msg.text.value)
                    break
            return responses if responses else [self._fallback_answer(user_message)]
        except Exception:
            return [self._fallback_answer(user_message)]


async def create_foundry_document_ingestion_agent() -> DocumentIngestionAgent:
    agent = DocumentIngestionAgent()
    await agent.create_agent()
    return agent
