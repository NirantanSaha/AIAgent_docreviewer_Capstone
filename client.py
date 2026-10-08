"""Client for the legal document review application."""

import asyncio
import os

import requests
from dotenv import load_dotenv

load_dotenv()

server = os.environ["SERVER_URL"]
port = os.environ["ORCHESTRATOR_AGENT_PORT"]

HELP_TEXT = """Example questions:
1. Summarize the legal documents available in the packet.
2. Extract the retention, audit, and incident notification clauses.
3. Validate the packet for GDPR-style compliance risks.
4. Give me a grounded legal review summary with precedent context.
5. What issues should legal counsel review before signature?
"""


def send_prompt(prompt: str) -> str:
    url = f"http://{server}:{port}/message"
    payload = {"message": prompt}
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "No response from the legal review agent.")
        return "Unable to retrieve the required legal-review information. Please verify that the capstone data files are available and try again."
    except Exception:
        return "Unable to retrieve the required legal-review information. Please verify that the capstone data files are available and try again."


async def main() -> None:
    print("\nAI-Powered Legal Document Review System")
    print("----------------------------------------")
    print("Enter your question or type 'help' for examples.")
    print("Type 'quit' to exit.")

    while True:
        user_input = input("\nUser: ")
        if not user_input:
            continue

        command = user_input.strip().lower()
        if command == "quit":
            print("Goodbye.")
            break

        if command == "help":
            print(HELP_TEXT)
            continue

        response = send_prompt(user_input)
        print(f"\n{response}\n")


if __name__ == "__main__":
    asyncio.run(main())
