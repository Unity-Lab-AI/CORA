#!/usr/bin/env python3
"""Shared base of the cora_tools.git_parts package (split from cora_tools/git_ops.py on 2026-10-14): imports, module
state, the helpers and every function that rebinds a module global."""
from __future__ import annotations
#!/usr/bin/env python3
"""
C.O.R.A Git Operations Tool
Full GitHub integration - clone, pull, push, commit, merge, branch, and more.
Includes GitHub API for repo creation, authentication, and management.

Created by: Unity AI Lab
"""

import subprocess
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import urllib.request
import urllib.error
import base64
PROJECT_DIR = Path(__file__).parent.parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_DIR / '.env')
except ImportError:
    pass


# Global instance
_git = None

def get_git(working_dir: Optional[str] = None) -> GitOperations:
    from cora_tools.git_parts.git import GitOperations
    """Get or create Git operations instance."""
    global _git
    if _git is None or working_dir:
        _git = GitOperations(working_dir)
    return _git


# Convenience functions
def git_status() -> Dict[str, Any]:
    """Get git status."""
    return get_git().status()

def git_pull() -> Dict[str, Any]:
    """Pull from origin."""
    return get_git().pull()

def git_push() -> Dict[str, Any]:
    """Push to origin."""
    return get_git().push()

def git_commit(message: str) -> Dict[str, Any]:
    """Commit with message."""
    return get_git().commit(message)

def git_add(files: str = '.') -> Dict[str, Any]:
    """Stage files."""
    return get_git().add(files)

def git_branch() -> Dict[str, Any]:
    """List branches."""
    return get_git().branch()

def git_checkout(branch: str) -> Dict[str, Any]:
    """Switch branch."""
    return get_git().checkout(branch)

def git_merge(branch: str) -> Dict[str, Any]:
    """Merge branch."""
    return get_git().merge(branch)

def git_clone(url: str, directory: Optional[str] = None) -> Dict[str, Any]:
    """Clone repo."""
    return get_git().clone(url, directory)

def git_log(count: int = 10) -> Dict[str, Any]:
    """Get commit log."""
    return get_git().log(count)

def git_diff() -> Dict[str, Any]:
    """Show diff."""
    return get_git().diff()

def git_stash() -> Dict[str, Any]:
    """Stash changes."""
    return get_git().stash()

def git_stash_pop() -> Dict[str, Any]:
    """Pop stash."""
    return get_git().stash_pop()


# GitHub API convenience functions
def github_login(token: str) -> Dict[str, Any]:
    """Login to GitHub with Personal Access Token."""
    return get_git().github.login_with_token(token)

def github_login_browser() -> Dict[str, Any]:
    """Open browser to create GitHub token."""
    return get_git().github.login_browser()

def github_logout() -> Dict[str, Any]:
    """Logout from GitHub."""
    return get_git().github.logout()

def github_user() -> Dict[str, Any]:
    """Get current GitHub user info."""
    return get_git().github.get_user()

def github_repos() -> Dict[str, Any]:
    """List your GitHub repositories."""
    return get_git().github.list_repos()

def github_create_repo(name: str, description: str = '', private: bool = False) -> Dict[str, Any]:
    """Create a new GitHub repository."""
    return get_git().github.create_repo(name, description, private)

def github_fork(owner: str, repo: str) -> Dict[str, Any]:
    """Fork a repository."""
    return get_git().github.fork_repo(owner, repo)

def github_create_pr(owner: str, repo: str, title: str, head: str, base: str = 'main') -> Dict[str, Any]:
    """Create a pull request."""
    return get_git().github.create_pull_request(owner, repo, title, head, base)

def github_prs(owner: str, repo: str) -> Dict[str, Any]:
    """List pull requests."""
    return get_git().github.list_pull_requests(owner, repo)
