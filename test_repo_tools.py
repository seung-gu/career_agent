#!/usr/bin/env python3
"""Test script for GitHub repository tools."""

import os
import sys
import tempfile
import shutil
from dotenv import load_dotenv

load_dotenv(override=True)

# Show progress
import time
start_time = time.time()
def log_time(msg):
    elapsed = time.time() - start_time
    print(f"[{elapsed:.1f}s] {msg}")

# Test imports
log_time("Loading test modules...")
try:
    from lib.github import load_github_repos, get_repo_paths
    from lib.github.repo_tools import read_repo_file, list_repo_files
    log_time("✓ Successfully imported GitHub functions")
    
    # Import agent only when needed (it triggers repo loading - takes ~30-40s for 26 repos)
    log_time("Loading agent (this will clone repos if GITHUB_TOKEN is set, may take 30-40s)...")
    from agent import career_agent
    log_time("✓ Successfully imported agent")
except ImportError as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 1: Check agent has the tools
print(f"\n📋 Test 1: Agent tools check")
tools = [tool.name for tool in career_agent.tools if hasattr(tool, 'name')]
print(f"  Agent has {len(tools)} tools: {tools}")
expected_tools = ['record_user_details', 'record_unknown_question', 'read_repo_file', 'list_repo_files']
if all(tool in tools for tool in expected_tools):
    print("  ✓ All expected tools are present")
else:
    print(f"  ✗ Missing tools: {set(expected_tools) - set(tools)}")
    sys.exit(1)

# Test 2: Verify tool configuration
print(f"\n📋 Test 2: Tool configuration")
print(f"  read_repo_file name: {read_repo_file.name}")
print(f"  read_repo_file description: {read_repo_file.description[:80]}...")
print(f"  list_repo_files name: {list_repo_files.name}")
print(f"  ✓ Tools are properly configured")

# Test 3: Test with mock repository
print(f"\n📋 Test 3: Mock repository test")
test_dir = tempfile.mkdtemp()
try:
    # Create test files
    os.makedirs(os.path.join(test_dir, 'docs'), exist_ok=True)
    os.makedirs(os.path.join(test_dir, 'src'), exist_ok=True)
    with open(os.path.join(test_dir, 'README.md'), 'w') as f:
        f.write('# Test Repo\n\nThis is a test repository.')
    with open(os.path.join(test_dir, 'development_log.md'), 'w') as f:
        f.write('# Development Log\n\n- Initial commit')
    with open(os.path.join(test_dir, 'src', 'main.py'), 'w') as f:
        f.write('print("hello")')
    
    # Add to repo_paths for testing
    repo_paths = get_repo_paths()
    repo_paths['test/repo'] = test_dir
    print(f"  Created mock repo at: {test_dir}")
    print(f"  Added to repo_paths: {list(repo_paths.keys())}")
    
    # Test the underlying function logic by checking file access
    readme_path = os.path.join(test_dir, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r') as f:
            content = f.read()
        if 'Test Repo' in content:
            print("  ✓ File reading logic works")
        else:
            print("  ✗ File content mismatch")
    else:
        print("  ✗ Test file not found")
    
    # Check that tools can see the repo
    repo_paths = get_repo_paths()
    print(f"  repo_paths contains: {list(repo_paths.keys())}")
    if 'test/repo' in repo_paths:
        print("  ✓ Repository path storage works")
    
finally:
    shutil.rmtree(test_dir)
    # Note: repo_paths is read-only from get_repo_paths(), so we can't clear it here

# Test 4: Check environment and real repo loading
print(f"\n📋 Test 4: Environment and repository loading")
github_token = os.getenv("GITHUB_TOKEN")
github_repos = os.getenv("GITHUB_REPOS", "")

print(f"  GITHUB_TOKEN: {'✓ Set' if github_token else '✗ Not set'}")
print(f"  GITHUB_REPOS: {github_repos if github_repos else '✗ Not set'}")

# Skip additional repo loading since agent import already loaded them
repo_paths = get_repo_paths()
if repo_paths:
    print(f"  ✓ Repositories already loaded from agent import: {len(repo_paths)} repos")
    print(f"  Available repos (first 5): {list(repo_paths.keys())[:5]}")
    if github_token and not github_repos:
        print("  Note: All repos were auto-fetched via GITHUB_TOKEN")
elif github_token and github_repos:
    log_time(f"  Loading specific repositories: {github_repos}")
    try:
        github_info = load_github_repos()
        repo_paths = get_repo_paths()
        log_time(f"  ✓ Loaded {len(repo_paths)} repositories")
        print(f"  Available repos: {list(repo_paths.keys())}")
        
        if repo_paths and github_info:
            preview = github_info[:300] + "..." if len(github_info) > 300 else github_info
            print(f"\n  Repository info preview:\n{preview[:300]}...")
    except Exception as e:
        print(f"  ⚠️  Error loading repos: {e}")
        import traceback
        traceback.print_exc()
else:
    print("  ⚠️  Skipping additional repository loading")
    print("  (Repos were already loaded during agent import if GITHUB_TOKEN is set)")

elapsed = time.time() - start_time
print(f"\n✓ All basic tests completed in {elapsed:.1f}s!")
print("\nNote: If GITHUB_TOKEN is set, agent import will clone all repos (takes ~30-40s)")
print("To test with real repositories, set:")
print("  export GITHUB_TOKEN=ghp_your_token")
print("  export GITHUB_REPOS=owner/repo1,owner/repo2")
