"""Career agent main application."""

from dotenv import load_dotenv
from agents import Agent, Runner, trace
import gradio as gr
import os

# Load environment variables
load_dotenv(override=True)

# Import modules
from lib.personal_data import load_personal_data
from lib.github import load_github_repos, get_repo_paths
from lib.github.repo_tools import list_repo_files, read_repo_file
from lib.tools import record_user_details, record_unknown_question


def _build_agent_instructions(personal_data, repo_paths: dict[str, str]) -> str:
    """Build the agent instructions with personal data and GitHub repository info."""
    name = personal_data.name
    
    instructions = f"""You are acting as {name}. You are answering questions on {name}'s website, particularly questions related to {name}'s career, background, skills and experience. Your responsibility is to represent {name} for interactions on the website as faithfully as possible. You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. Be professional and engaging, as if talking to a potential client or future employer who came across the website. If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool.

## Summary:
{personal_data.summary}

## LinkedIn Profile:
{personal_data.linkedin}
"""
    
    # Add GitHub repository information if available
    if repo_paths:
        repo_list = list(repo_paths.keys())
        repos_formatted = "\n".join([f"  - {repo}" for repo in repo_list])
        example_repo = repo_list[0] if repo_list else "owner/repo"
        
        instructions += f"""
## Private Projects (GitHub Repositories):

{name} has {len(repo_list)} private GitHub repositories available:
{repos_formatted}

### IMPORTANT: How to handle questions about private projects

When users ask about private projects, you MUST follow this workflow:

**STEP 1: Always start with list_repo_files to discover what's available**
- When user asks "what projects do you have?" or "tell me about your projects"
- Use list_repo_files(repo_name, ".", "") to explore repository structure
- This shows you what files exist in each project
- Look for README files, documentation, and key source files
- Example: list_repo_files("{example_repo}", ".", "")

**STEP 2: Use read_repo_file to get detailed information about specific projects**
- When user asks about a SPECIFIC project (e.g., "tell me about stock-agent" or "what does smart-labeler do?")
- First identify which repository matches the project name from the list above
- Then use read_repo_file(repo_name, "README.md") to read the README
- Read other important files like documentation, main source files, or config files
- Example: read_repo_file("{example_repo}", "README.md")

**Workflow examples:**
- User: "What projects have you worked on?"
  → Use list_repo_files on several repos to show project overview and structure
  
- User: "Tell me about [project name]"
  → 1) Use list_repo_files to find which repo contains it and see structure
  → 2) Use read_repo_file to read README and key files for details
  
- User: "How does [project] work?"
  → 1) Use list_repo_files to find the repo and see what files exist
  → 2) Use read_repo_file to read README, main source files, and documentation

**Available tools:**
- list_repo_files(repo_name, directory, pattern) - ALWAYS use FIRST to explore repository structure
- read_repo_file(repo_name, file_path) - Use AFTER listing to read specific files for details

Repository names are in "owner/repo" format (e.g., "{example_repo}").
"""
    
    instructions += f"\nWith this context, please chat with the user, always staying in character as {name}."
    return instructions


# Load personal data
print("Loading personal data...")
personal_data = load_personal_data()

# Load GitHub repository information
print("Loading GitHub repositories...")
# Only load repos if GITHUB_TOKEN is set (to avoid errors in Space)
repo_paths = {}
if os.getenv("GITHUB_TOKEN"):
    try:
        load_github_repos()
        repo_paths = get_repo_paths()
        print(f"Loaded {len(repo_paths)} repositories")
    except Exception as e:
        print(f"Warning: Could not load GitHub repos: {e}")
else:
    print("GITHUB_TOKEN not set, skipping repository loading")

# Build agent instructions
instructions = _build_agent_instructions(personal_data, repo_paths)

# Create the career agent
career_agent = Agent(
    name=personal_data.name,
    instructions=instructions,
    model="gpt-4o-mini",
    tools=[record_user_details, record_unknown_question, list_repo_files, read_repo_file]
)

# Example: To use a different model (e.g., Gemini), uncomment and configure:
# from openai import AsyncOpenAI
# from agents import OpenAIChatCompletionsModel
# gemini_client = AsyncOpenAI(
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
#     api_key=os.getenv('GOOGLE_API_KEY')
# )
# gemini_model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=gemini_client)
# career_agent = Agent(
#     name=personal_data.name,
#     instructions=instructions,
#     model=gemini_model,
#     tools=[record_user_details, record_unknown_question, list_repo_files, read_repo_file]
# )


async def chat(message: str, history: list[dict]) -> str:
    """Handle chat messages from Gradio interface.
    
    Args:
        message: The user's message
        history: List of previous messages with role/content
    
    Returns:
        The agent's response
    """
    # Convert Gradio history format to agent context format
    context = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in ("user", "assistant")
    ]

    with trace("Career Agent"):
        result = await Runner.run(career_agent, input=message, context=context)

    return result.final_output


# Create Gradio interface
print("Initializing Gradio interface...")
demo = gr.ChatInterface(
    fn=chat,
    type="messages",
    chatbot=gr.Chatbot(
        type="messages",
        value=[{"role": "assistant", "content": f"Hi, I'm {personal_data.name}'s agent. Ask me anything!"}],
    ),
    title=f"{personal_data.name}'s Career Agent",
)

if __name__ == "__main__":
    demo.launch()
