"""User interaction tools for the agent."""

from agents import function_tool
from ..notification import push


@function_tool
def record_user_details(email: str, name: str = "Name not provided", notes: str = "not provided") -> str:
    """Record that a user is interested in being in touch and provided an email address.

    Args:
        email: The email address of this user
        name: The user's name, if provided
        notes: Any extra context from the conversation
    """
    push(f"Recording {name} with email {email} and notes {notes}")
    return "ok"


@function_tool
def record_unknown_question(question: str) -> str:
    """Record any question the assistant couldn't answer."""
    push(f"Recording {question}")
    return "ok"

