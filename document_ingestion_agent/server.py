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

from document_ingestion_agent.agent_executor import create_foundry_agent_executor

load_dotenv()

host = os.environ["SERVER_URL"]
port = os.environ["DOCUMENT_INGESTION_AGENT_PORT"]

skills = [
    AgentSkill(
        id="ingest_legal_packet",
        name="Ingest Legal Packet",
        description="Reads the available legal packet and reports grounded metadata such as parties and available sections.",
        tags=["legal packet", "intake", "document ingestion"],
        examples=[
            "Summarize the legal documents available in the packet.",
            "Which agreement sections are available for review?",
        ],
    )
]

agent_card = AgentCard(
    name="Document Ingestion Agent",
    description="A legal-document intake specialist that identifies the available document packet and reports grounded metadata.",
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
    return PlainTextResponse("Document Ingestion Agent is running.")


routes.append(Route(path="/health", methods=["GET"], endpoint=health_check))
app = Starlette(routes=routes)


def main():
    uvicorn.run(app, host=host, port=int(port), log_level="warning")


if __name__ == "__main__":
    main()
