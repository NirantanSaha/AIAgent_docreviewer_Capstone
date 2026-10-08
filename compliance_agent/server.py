import os

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from compliance_agent.agent_executor import create_foundry_agent_executor

load_dotenv()

host = os.environ["SERVER_URL"]
port = os.environ["COMPLIANCE_AGENT_PORT"]

skills = [
    AgentSkill(
        id="validate_legal_compliance",
        name="Validate Legal Compliance",
        description="Checks the packet against the grounded compliance checklist and local precedent notes.",
        tags=["compliance", "gdpr", "risk review"],
        examples=[
            "Validate the packet for GDPR-style compliance issues.",
            "What clauses should legal counsel review before signature?",
        ],
    )
]

agent_card = AgentCard(
    name="Compliance Validation Agent",
    description="A legal-review specialist that validates the packet against compliance checks and local precedent context.",
    url=f"http://{host}:{port}/",
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=skills,
)

agent_executor = create_foundry_agent_executor(agent_card)
request_handler = DefaultRequestHandler(
    agent_executor=agent_executor,
    task_store=InMemoryTaskStore(),
)

a2a_app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

routes = a2a_app.routes()


async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Compliance Validation Agent is running.")


routes.append(Route(path="/health", methods=["GET"], endpoint=health_check))
app = Starlette(routes=routes)


def main():
    uvicorn.run(app, host=host, port=int(port), log_level="warning")


if __name__ == "__main__":
    main()
