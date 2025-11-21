---
title: career_conversation
app_file: agent.py
sdk: gradio
sdk_version: 5.49.1
---
# career_agent
An AI agent that understands my background, experiences, and career path, and can communicate or explain them naturally in conversations.


### You can start career conversations with the agent by clicking [here](https://huggingface.co/spaces/Seung-gu/career_conversation).

## Setup

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
PUSHOVER_TOKEN=your_pushover_token
PUSHOVER_USER=your_pushover_user

# Optional: GitHub private repositories
GITHUB_TOKEN=ghp_your_github_personal_access_token
GITHUB_REPOS=owner/repo1,owner/repo2,owner/repo3
```

### GitHub Integration

To include information from **multiple** private GitHub repositories:

1. Create a GitHub Personal Access Token:
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate a new token with `repo` scope (for private repos)
   - Copy the token

2. Set environment variables in `.env`:
   ```bash
   GITHUB_TOKEN=ghp_your_token_here
   ```

   **Two options for repositories:**
   
   **Option A (Recommended)**: Auto-fetch all your repositories
   - Just set `GITHUB_TOKEN` - the agent will automatically fetch ALL your repositories
   - No need to manually list them!
   
   **Option B**: Specify specific repositories
   ```bash
   GITHUB_REPOS=owner/repo1,owner/repo2,owner/repo3
   ```
   - Only if you want to limit to specific repos
   - Format: `owner/repo-name` (e.g., `seung-gu/my-project`)
   - Separate multiple repos with commas

3. What happens:
   - **All** repositories in the list are cloned on startup
   - README and development_log files are extracted from **each** repository
   - Agent can access any repository by its exact name (e.g., `"seung-gu/web-app"`)
   - Agent tools: `read_repo_file("owner/repo", "file.txt")` and `list_repo_files("owner/repo", "dir", "*.md")`

**Note**: Repository cloning happens on startup and may take a few seconds depending on the number and size of repositories.


