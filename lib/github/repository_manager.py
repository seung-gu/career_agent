"""GitHub repository loading and management."""

import os
import subprocess
import tempfile
import shutil
import atexit
import requests
from typing import Optional

# Constants
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build', '.pytest_cache', 'target', 'out'}
SKIP_EXTENSIONS = {'.pyc', '.pyo', '.so', '.dylib', '.dll', '.exe', '.bin'}

# Global storage for cloned repositories (keyed by repo name)
_repo_paths = {}


def get_repo_paths() -> dict[str, str]:
    """Get the current repository paths dictionary."""
    return _repo_paths.copy()


def _validate_path(repo_path: str, target_path: str) -> tuple[bool, Optional[str]]:
    """Validate that target_path is within repo_path to prevent path traversal."""
    target_norm = os.path.normpath(target_path)
    repo_norm = os.path.normpath(repo_path)
    
    if not target_norm.startswith(repo_norm):
        return False, "Invalid path (path traversal attempt)"
    return True, None


def _should_skip_file(filename: str) -> bool:
    """Check if a file should be skipped based on extension."""
    return any(filename.endswith(ext) for ext in SKIP_EXTENSIONS)


def _should_skip_dir(dirname: str) -> bool:
    """Check if a directory should be skipped."""
    return dirname.startswith('.') or dirname in SKIP_DIRS


def fetch_user_repositories(github_token: str, username: Optional[str] = None) -> list[str]:
    """Fetch all repositories for a GitHub user using the GitHub API.
    
    Args:
        github_token: GitHub personal access token
        username: Optional GitHub username. If not provided, will fetch from token.
    
    Returns:
        List of repository names in "owner/repo" format
    """
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    repos = []
    
    try:
        # If username not provided, get it from the token
        if not username:
            user_response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            if user_response.status_code == 200:
                username = user_response.json().get("login")
            else:
                print(f"Could not get username from token: {user_response.status_code}")
                return []
        
        # Fetch all repositories (including private)
        url = "https://api.github.com/user/repos"
        page = 1
        per_page = 100
        
        while True:
            params = {"page": page, "per_page": per_page, "affiliation": "owner", "sort": "updated"}
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"GitHub API error: {response.status_code} - {response.text[:200]}")
                break
            
            data = response.json()
            if not data:
                break
            
            for repo in data:
                repo_name = repo.get("full_name")
                if repo_name:
                    repos.append(repo_name)
            
            # Check if there are more pages
            if len(data) < per_page:
                break
            page += 1
        
        return repos
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repositories from GitHub API: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error fetching repositories: {e}")
        return []


def _clone_repository(repo: str, github_token: str, temp_dir: str) -> Optional[str]:
    """Clone a single repository and return its local path."""
    try:
        repo_url = f"https://{github_token}@github.com/{repo}.git"
        repo_path = os.path.join(temp_dir, repo.replace("/", "_"))
        
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", repo_url, repo_path],
            capture_output=True,
            timeout=60,
            text=True
        )
        
        if result.returncode != 0:
            return None
        
        return repo_path
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
        return None


def _find_files_by_pattern(repo_path: str, patterns: list[str], extensions: Optional[tuple] = None) -> list[str]:
    """Find files in repository matching given patterns."""
    found_files = []
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not _should_skip_dir(d)]
        
        for file in files:
            if _should_skip_file(file):
                continue
            if extensions and not file.endswith(extensions):
                continue
            
            file_lower = file.lower()
            if any(pattern in file_lower for pattern in patterns):
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                found_files.append(rel_path)
    
    # Sort by depth (root level first)
    found_files.sort(key=lambda x: (x.count('/'), x))
    return found_files


def _read_file_safe(file_path: str) -> Optional[str]:
    """Safely read a file and return its content."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


def _get_repo_file_sample(repo_path: str, max_files: int = 50) -> list[str]:
    """Get a sample of files from the repository."""
    files = []
    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not _should_skip_dir(d)]
        for filename in filenames:
            if not _should_skip_file(filename):
                rel_path = os.path.relpath(os.path.join(root, filename), repo_path)
                if len(files) < max_files:
                    files.append(rel_path)
                else:
                    return files
    return files


def _extract_repo_info(repo_path: str) -> str:
    """Extract repository information by dynamically finding and reading key files."""
    info_parts = []
    
    # Find README files
    readme_files = _find_files_by_pattern(repo_path, ['readme'])
    for readme_path in readme_files[:2]:  # Top 2 READMEs
        full_path = os.path.join(repo_path, readme_path)
        content = _read_file_safe(full_path)
        if content:
            info_parts.append(f"README ({readme_path}):\n{content}\n")
    
    # Find development log files
    dev_log_files = _find_files_by_pattern(
        repo_path, 
        ['development', 'dev_log', 'changelog', 'changes', 'history'],
        extensions=('.md', '.txt', '.rst', '.markdown')
    )
    for dev_log_path in dev_log_files[:2]:  # Top 2 dev logs
        full_path = os.path.join(repo_path, dev_log_path)
        content = _read_file_safe(full_path)
        if content:
            info_parts.append(f"Development Log ({dev_log_path}):\n{content}\n")
    
    # Provide file listing sample
    files = _get_repo_file_sample(repo_path, max_files=50)
    if files:
        info_parts.append(f"Repository structure (sample):\n" + "\n".join(files) + "\n")
        info_parts.append("Note: Use read_repo_file(repo_name, file_path) and list_repo_files(repo_name, directory, pattern) tools to explore specific files.")
    
    return "\n".join(info_parts) if info_parts else "Repository structure available for exploration."


def load_github_repos() -> str:
    """Load information from private GitHub repositories and keep them available for agent tools.
    
    Set environment variables:
    - GITHUB_TOKEN: Your GitHub personal access token with repo access
    - GITHUB_REPOS: (Optional) Comma-separated list of specific repos. If not set, will fetch all your repos.
    
    Returns summary info and stores repo paths globally for tool access.
    """
    global _repo_paths
    _repo_paths = {}
    
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return ""
    
    # Get list of repositories
    explicit_repos = os.getenv("GITHUB_REPOS", "").strip()
    if explicit_repos:
        repos = [r.strip() for r in explicit_repos.split(",") if r.strip()]
    else:
        # Automatically fetch all user's repositories
        try:
            repos = fetch_user_repositories(github_token)
            if repos:
                print(f"Auto-fetched {len(repos)} repositories from GitHub")
            else:
                return ""
        except Exception as e:
            print(f"Could not auto-fetch repositories: {e}")
            print("Set GITHUB_REPOS explicitly or check GITHUB_TOKEN permissions")
            return ""
    
    if not repos:
        return ""
    
    repo_info = []
    temp_dir = tempfile.mkdtemp(prefix="github_repos_")
    
    # Register cleanup for temp_dir when process exits
    atexit.register(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
    
    for repo in repos:
        repo_path = _clone_repository(repo, github_token, temp_dir)
        
        if not repo_path:
            repo_info.append(f"## Repository: {repo}\n(Error cloning repository)\n")
            continue
        
        # Store repo path for tool access
        _repo_paths[repo] = repo_path
        
        # Extract relevant information
        repo_summary = _extract_repo_info(repo_path)
        repo_info.append(f"## Repository: {repo}\n{repo_summary}\n")
    
    return "\n".join(repo_info)

