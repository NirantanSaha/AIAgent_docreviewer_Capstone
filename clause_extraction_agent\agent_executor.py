"""A2A executor for the clause extraction agent."""

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import AgentCard, Part, TaskState
from a2a.utils import new_agent_text_message

from clause_extraction_agent.agent import ClauseExtractionAgent, create_foundry_clause_agent


class ClauseExtractionExecutor(AgentExecutor):

    def __init__(self, card: AgentCard):
        self._card = card
        self._clause_agent: ClauseExtractionAgent | None = None

    async def _get_or_create_agent(self) -> ClauseExtractionAgent:
        if not self._clause_agent:
            self._clause_agent = await create_foundry_clause_agent()
        return self._clause_agent

    async def _process_request(self, message_parts: list[Part], context_id: str, task_updater: TaskUpdater) -> None:
        try:
            user_message = message_parts[0].root.text
            agent = await self._get_or_create_agent()

            await task_updater.update_status(
                TaskState.working,
                message=new_agent_text_message("Clause Extraction Agent is processing your request...", context_id=context_id),
            )

            responses = await agent.run_conversation(user_message)
            for response in responses:
                await task_updater.update_status(
                    TaskState.working,
                    message=new_agent_text_message(response, context_id=context_id),
                )

            final_message = responses[-1] if responses else "Task completed."
            await task_updater.complete(
                message=new_agent_text_message(final_message, context_id=context_id),
            )
        except Exception:
            await task_updater.failed(
                message=new_agent_text_message("Unable to retrieve the required legal-review information.", context_id=context_id),
            )

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.submit()
        await updater.start_work()
        await self._process_request(context.message.parts, context.context_id, updater)

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.failed(
            message=new_agent_text_message("Task cancelled by the user.", context_id=context.context_id),
        )


def create_foundry_agent_executor(card: AgentCard) -> ClauseExtractionExecutor:
    return ClauseExtractionExecutor(card)
