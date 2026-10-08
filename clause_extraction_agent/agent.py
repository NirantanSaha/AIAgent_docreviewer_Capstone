"""Clause extraction agent for the legal review workflow."""

import os

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import Agent, ListSortOrder, MessageRole
from azure.identity import DefaultAzureCredential

from review_data import extract_clauses, get_clause_extraction_rules, get_context_for_question


class ClauseExtractionAgent:

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
                name="clause-extraction-agent",
                instructions="""
                You are a legal clause extraction specialist.

                Use only the provided legal packet and extraction rules.
                Extract key clauses, obligations, and exceptions without inventing missing legal text.
                """,
            )
            return self.agent
        except Exception:
            self.azure_available = False
            return None

    def _fallback_answer(self, user_message: str) -> str:
        clauses = extract_clauses()
        rules = get_clause_extraction_rules()
        sections = [
            "Clause Extraction Summary",
            "-------------------------",
        ]
        for header, content in clauses.items():
            if any(token in user_message.lower() for token in ["all", "summary", "extract", header.lower().split(":", 1)[-1].strip().split()[0].lower()]) or any(
                phrase in user_message.lower() for phrase in ["retention", "audit", "incident", "liability", "termination", "subprocessor", "transfer"]
            ):
                sections.append(f"{header}")
                sections.append(content or "No clause text available in the packet.")
                sections.append("")

        if len(sections) == 2:
            for header, content in clauses.items():
                sections.append(header)
                sections.append(content or "No clause text available in the packet.")
                sections.append("")

        sections.extend([
            "Extraction Rules",
            rules,
            "",
            "Assessment Summary",
            "The extracted clauses above are taken only from the supplied packet sections and are not expanded with outside legal text.",
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


async def create_foundry_clause_agent() -> ClauseExtractionAgent:
    agent = ClauseExtractionAgent()
    await agent.create_agent()
    return agent
