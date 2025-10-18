from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool
from pypdf import PdfReader
import os
import requests
import gradio as gr


load_dotenv(override=True)

# Load personal data
name = "Seung-Gu"

# Load LinkedIn profile
reader = PdfReader("me/linkedin.pdf")
linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text
with open("me/summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()


# Notification helper (same as agent.py)
def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

# Tools implemented in agent style
@function_tool
def record_user_details(email: str, name: str = "Name not provided", notes: str = "not provided"):
    """Record that a user is interested in being in touch and provided an email address.

    Args:
        email: The email address of this user
        name: The user's name, if provided
        notes: Any extra context from the conversation
    """
    push(f"Recording {name} with email {email} and notes {notes}")
    return "ok"


@function_tool
def record_unknown_question(question: str):
    """Record any question the assistant couldn't answer."""
    push(f"Recording {question}")
    return "ok"



# Build instructions (same intent as agent.py)
instructions = f"You are acting as {name}. You are answering questions on {name}'s website, particularly questions related to {name}'s career, background, skills and experience. Your responsibility is to represent {name} for interactions on the website as faithfully as possible. You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. Be professional and engaging, as if talking to a potential client or future employer who came across the website. If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool.\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\nWith this context, please chat with the user, always staying in character as {name}."


# to use a different model not from openai, this is prerequisite
"""
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
gemini_client = AsyncOpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai/", api_key=os.getenv('GOOGLE_API_KEY'))
gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)
agent1 = Agent(
    name=name,
    instructions=instructions,
    model=gemini_model,
    tools=[record_user_details, record_unknown_question]
)
"""


# Temporary agent without tools; tools will be added in the next 
career_agent = Agent(
    name=name,
    instructions=instructions,
    model="gpt-4o-mini",
    tools=[record_user_details, record_unknown_question]
)



async def chat(message, history):
    # history is a list of dicts with role/content when type="messages"
    context = []
    for m in history:
        if m.get("role") in ("user", "assistant"):
            context.append({"role": m["role"], "content": m["content"]})

    with trace("Career Agent"):
        result = await Runner.run(career_agent, input=message, context=context)

    return result.final_output


if __name__ == "__main__":
    # Gradio UI
    gr.ChatInterface(
        fn=chat,
        type="messages",
        chatbot=gr.Chatbot(
            type="messages",
            value=[{"role": "assistant", "content": "Hi, I'm Seung-Gu's agent. Ask me anything!"}],
        ),
    ).launch()