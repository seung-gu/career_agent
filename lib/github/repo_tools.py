"""GitHub repository tools for agent."""

import os
import fnmatch
from typing import Optional
from agents import function_tool

from .repository_manager import get_repo_paths, SKIP_DIRS, SKIP_EXTENSIONS


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


@function_tool
def list_repo_files(repo_name: str, directory: str = ".", pattern: str = "") -> str:
    """List files in a GitHub repository directory, optionally filtered by pattern.
    
    ALWAYS use this tool FIRST when users ask about private projects or want to explore repositories.
    This will help you understand what projects are available and their structure before reading specific files.
    
    Workflow:
    1. Use list_repo_files to see what files exist in a repository
    2. Then use read_repo_file to read specific files based on what you found
    
    Args:
        repo_name: The repository name in format "owner/repo" (e.g., "username/project")
        directory: Relative directory path from repo root (default: root, e.g., "src", "docs")
        pattern: Optional pattern to filter files (e.g., "*.md", "README*", "*log*")
    
    Returns:
        List of file paths relative to repo root, or error message
    """
    _repo_paths = get_repo_paths()
    
    if repo_name not in _repo_paths:
        available_repos = ", ".join(_repo_paths.keys()) if _repo_paths else "none"
        return f"Error: Repository '{repo_name}' not found. Available repositories: {available_repos}"
    
    repo_path = _repo_paths[repo_name]
    full_dir = os.path.join(repo_path, directory)
    
    # Security: prevent path traversal
    is_valid, error_msg = _validate_path(repo_path, full_dir)
    if not is_valid:
        return f"Error: {error_msg}"
    
    if not os.path.exists(full_dir):
        return f"Error: Directory not found in {repo_name}: {directory}"
    
    if not os.path.isdir(full_dir):
        return f"Error: Path is not a directory in {repo_name}: {directory}"
    
    files = []
    try:
        for root, dirs, filenames in os.walk(full_dir):
            # Skip hidden and common ignore directories
            dirs[:] = [d for d in dirs if not _should_skip_dir(d)]
            
            for filename in filenames:
                if _should_skip_file(filename):
                    continue
                
                # Apply pattern filter if provided
                if pattern:
                    if not fnmatch.fnmatch(filename, pattern) and pattern not in filename:
                        continue
                
                rel_path = os.path.relpath(os.path.join(root, filename), repo_path)
                files.append(rel_path)
                
                # Limit to avoid overwhelming output
                if len(files) >= 200:
                    files.append(f"... (showing first 200 files)")
                    break
            
            if len(files) >= 200:
                break
    except Exception as e:
        return f"Error listing files in {repo_name}: {str(e)}"
    
    return "\n".join(files) if files else f"No files found in {repo_name}/{directory}"


@function_tool
def read_repo_file(repo_name: str, file_path: str) -> str:
    """Read a specific file from a GitHub repository.
    
    Use this tool AFTER using list_repo_files to read specific files when users ask about
    a particular project. Always use list_repo_files first to discover what files exist, then
    read the relevant files (README, documentation, source code) to provide detailed information.
    
    Workflow:
    1. First use list_repo_files to see what files are available
    2. Then use read_repo_file to read specific files like README.md, documentation, or source code
    
    Args:
        repo_name: The repository name in format "owner/repo" (e.g., "username/project")
        file_path: Relative path to the file from repo root (e.g., "README.md", "src/main.py")
    
    Returns:
        The content of the file, or error message if file cannot be read
    """
    _repo_paths = get_repo_paths()
    
    if repo_name not in _repo_paths:
        available_repos = ", ".join(_repo_paths.keys()) if _repo_paths else "none"
        return f"Error: Repository '{repo_name}' not found. Available repositories: {available_repos}"
    
    repo_path = _repo_paths[repo_name]
    full_path = os.path.join(repo_path, file_path)
    
    # Security: prevent path traversal
    is_valid, error_msg = _validate_path(repo_path, full_path)
    if not is_valid:
        return f"Error: {error_msg}"
    
    if not os.path.exists(full_path):
        return f"Error: File not found in {repo_name}: {file_path}"
    
    if not os.path.isfile(full_path):
        return f"Error: Path is not a file in {repo_name}: {file_path}"
    
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            return content
    except Exception as e:
        return f"Error reading {file_path} from {repo_name}: {str(e)}"

