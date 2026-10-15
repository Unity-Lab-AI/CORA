"""
C.O.R.A Git Operations Tool
Full GitHub integration - clone, pull, push, commit, merge, branch, and more.
Includes GitHub API for repo creation, authentication, and management.

Created by: Unity AI Lab
"""

# Split into the cora_tools.git_parts package on 2026-10-14; this module keeps every name it always had.
from cora_tools.git_parts import _base  # noqa: F401
from cora_tools.git_parts._base import Any, Dict, List, Optional, PROJECT_DIR, Path, _git, base64, get_git, git_add, git_branch, git_checkout, git_clone, git_commit, git_diff, git_log, git_merge, git_pull, git_push, git_stash, git_stash_pop, git_status, github_create_pr, github_create_repo, github_fork, github_login, github_login_browser, github_logout, github_prs, github_repos, github_user, json, load_dotenv, os, subprocess, urllib  # noqa: F401
from cora_tools.git_parts.github import GitHubAPI  # noqa: F401
from cora_tools.git_parts.git import GitOperations, _validate_git_ref, _validate_path  # noqa: F401




# Test
if __name__ == "__main__":
    print("=== Git Operations Test ===\n")

    git = get_git()

    if git.is_repo():
        print("Current directory is a git repo\n")

        # Status
        status = git.status_short()
        print(f"Status: {status.get('count', 0)} files changed")

        # Branch
        branch = git.current_branch()
        print(f"Branch: {branch.get('branch', 'unknown')}")

        # Log
        log = git.log(5)
        print(f"\nRecent commits:")
        for commit in log.get('commits', [])[:5]:
            print(f"  {commit}")

        # Remotes
        remotes = git.remote()
        print(f"\nRemotes:\n{remotes.get('remotes', 'none')}")
    else:
        print("Not in a git repository")

    print("\n=== Available Commands ===")
    print("  git_status()     - Get status")
    print("  git_pull()       - Pull from origin")
    print("  git_push()       - Push to origin")
    print("  git_commit(msg)  - Commit changes")
    print("  git_add(files)   - Stage files")
    print("  git_branch()     - List branches")
    print("  git_checkout(b)  - Switch branch")
    print("  git_merge(b)     - Merge branch")
    print("  git_clone(url)   - Clone repo")
    print("  git_log(n)       - Show commits")
    print("  git_diff()       - Show changes")
    print("  git_stash()      - Stash changes")
