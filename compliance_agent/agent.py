"""Compliance validation agent for the legal review workflow."""

import os

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import Agent, ListSortOrder, MessageRole
from azure.identity import DefaultAzureCredential

from review_data import (
    get_compliance_rules,
    get_context_for_question,
    retrieve_precedents,
    validate_compliance,
)


class ComplianceValidationAgent:

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
                name="compliance-validation-agent",
                instructions="""
                You are a legal compliance validation specialist.

                Use only the provided legal packet, compliance checklist, and precedent notes.
                Flag grounded compliance issues, identify missing protections, and do not invent legal findings.
                """,
            )
            return self.agent
        except Exception:
            self.azure_available = False
            return None

    def _fallback_answer(self, user_message: str) -> str:
        findings = validate_compliance()
        precedents = retrieve_precedents(user_message or "compliance legal review")
        rules = get_compliance_rules()
        sections = [
            "Compliance Validation Summary",
            "-----------------------------",
        ]
        for control, result in findings.items():
            sections.append(f"{control}: {result}")

        sections.append("")
        sections.append("Retrieved Precedent Context")
        if precedents:
            for precedent in precedents:
                sections.append(f"- {precedent.title}: {precedent.detail}")
        else:
            sections.append("- No directly matching precedent snippet was retrieved from the local knowledge file.")

        sections.extend([
            "",
            "Compliance Rules",
            rules,
            "",
            "Assessment Summary",
            "The compliance findings above are grounded in the local checklist and the supplied legal packet. They are review flags, not legal advice.",
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
                content=f"Use only the provided legal packet, compliance checklist, and precedent notes.\n\n{get_context_for_question(user_message)}\n\nQuestion: {user_message}",
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


async def create_foundry_compliance_agent() -> ComplianceValidationAgent:
    agent = ComplianceValidationAgent()
    await agent.create_agent()
    return agent
