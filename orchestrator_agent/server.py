import os

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from orchestrator_agent.agent import get_initialized_orchestrator

load_dotenv()

app = FastAPI(title="Legal Review Orchestrator Agent")
orchestrator = None


class MessageRequest(BaseModel):
    message: str


@app.on_event("startup")
async def startup_event() -> None:
    global orchestrator
    orchestrator = await get_initialized_orchestrator()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "Legal Review Orchestrator Agent is running."}


@app.post("/message")
async def send_message(request: MessageRequest) -> dict[str, str]:
    response = await orchestrator.process_user_message(request.message)
    return {"response": response}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.environ["SERVER_URL"], port=int(os.environ["ORCHESTRATOR_AGENT_PORT"]), log_level="warning")
