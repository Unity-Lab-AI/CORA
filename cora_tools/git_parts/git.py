#!/usr/bin/env python3
"""cora_tools.git_parts: git (split from cora_tools/git_ops.py on 2026-10-14)."""
from __future__ import annotations

import subprocess
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import urllib.request
import urllib.error
import base64
from cora_tools.git_parts import _base  # noqa: F401
from cora_tools.git_parts._base import Any, Dict, List, Optional, os, subprocess  # noqa: F401




def _validate_git_ref(ref: str) -> bool:
    """Validate a git reference (branch name, tag, etc.) for safety.

    Rejects refs containing shell metacharacters as defense in depth.
    Note: subprocess with list args is already safe, this is extra protection.
    """
    if not ref or not ref.strip():
        return False
    # Reject shell metacharacters and control characters
    dangerous_chars = set('$`|;&<>(){}[]!*?~\\"\'')
    if any(c in ref for c in dangerous_chars):
        return False
    if any(ord(c) < 32 for c in ref):  # Control characters
        return False
    # Git ref restrictions
    if ref.startswith('-'):  # Could be interpreted as option
        return False
    if '..' in ref:  # Path traversal in refs
        return False
    return True


def _validate_path(path: str) -> bool:
    """Validate a file path for git operations."""
    if not path or not path.strip():
        return False
    # Reject shell metacharacters
    dangerous_chars = set('$`|;&<>(){}[]!*?')
    if any(c in path for c in dangerous_chars):
        return False
    if path.startswith('-'):  # Could be interpreted as option
        return False
    return True


class GitOperations:
    """Complete Git operations for CORA."""

    def __init__(self, working_dir: Optional[str] = None):
        from cora_tools.git_parts.github import GitHubAPI
        """
        Initialize Git operations.

        Args:
            working_dir: Working directory for git commands (default: current dir)
        """
        self.working_dir = working_dir or os.getcwd()
        self.github = GitHubAPI()

    def _run_git(self, args: List[str], timeout: int = 60) -> Dict[str, Any]:
        """
        Run a git command and return result.

        Args:
            args: Git command arguments (without 'git' prefix)
            timeout: Command timeout in seconds

        Returns:
            Dict with success, output, error keys
        """
        try:
            cmd = ['git'] + args
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout.strip(),
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'output': result.stdout.strip(),
                    'error': result.stderr.strip() or 'Command failed'
                }

        except subprocess.TimeoutExpired:
            return {'success': False, 'output': '', 'error': 'Command timed out'}
        except FileNotFoundError:
            return {'success': False, 'output': '', 'error': 'Git not installed'}
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}

    def set_working_dir(self, path: str) -> Dict[str, Any]:
        """Change the working directory for git operations."""
        path = os.path.expanduser(path)
        if os.path.isdir(path):
            self.working_dir = path
            return {'success': True, 'message': f'Working directory set to: {path}'}
        return {'success': False, 'error': f'Directory not found: {path}'}

    # ==================== STATUS & INFO ====================

    def status(self) -> Dict[str, Any]:
        """Get git status of current repo."""
        result = self._run_git(['status'])
        if result['success']:
            return {
                'success': True,
                'status': result['output'],
                'message': 'Got repository status'
            }
        return result

    def status_short(self) -> Dict[str, Any]:
        """Get short git status."""
        result = self._run_git(['status', '-s'])
        if result['success']:
            changes = result['output'].split('\n') if result['output'] else []
            return {
                'success': True,
                'changes': [c for c in changes if c],
                'count': len([c for c in changes if c]),
                'message': f"{len([c for c in changes if c])} files changed"
            }
        return result

    def log(self, count: int = 10) -> Dict[str, Any]:
        """Get recent commit history."""
        result = self._run_git(['log', f'-{count}', '--oneline'])
        if result['success']:
            commits = result['output'].split('\n') if result['output'] else []
            return {
                'success': True,
                'commits': commits,
                'count': len(commits),
                'message': f'Got {len(commits)} recent commits'
            }
        return result

    def log_detailed(self, count: int = 5) -> Dict[str, Any]:
        """Get detailed commit history."""
        result = self._run_git(['log', f'-{count}', '--pretty=format:%h - %s (%cr) <%an>'])
        if result['success']:
            return {
                'success': True,
                'commits': result['output'],
                'message': f'Got {count} detailed commits'
            }
        return result

    def diff(self, file: Optional[str] = None) -> Dict[str, Any]:
        """Show changes not yet staged."""
        args = ['diff']
        if file:
            args.append(file)
        result = self._run_git(args)
        if result['success']:
            return {
                'success': True,
                'diff': result['output'] or 'No changes',
                'message': 'Got diff'
            }
        return result

    def diff_staged(self) -> Dict[str, Any]:
        """Show staged changes."""
        result = self._run_git(['diff', '--staged'])
        if result['success']:
            return {
                'success': True,
                'diff': result['output'] or 'No staged changes',
                'message': 'Got staged diff'
            }
        return result

    # ==================== STAGING & COMMITS ====================

    def add(self, files: str = '.') -> Dict[str, Any]:
        """
        Stage files for commit.

        Args:
            files: File pattern or '.' for all
        """
        result = self._run_git(['add', files])
        if result['success']:
            return {
                'success': True,
                'message': f'Staged: {files}'
            }
        return result

    def add_all(self) -> Dict[str, Any]:
        """Stage all changes."""
        return self.add('.')

    def reset(self, file: Optional[str] = None) -> Dict[str, Any]:
        """Unstage files."""
        args = ['reset', 'HEAD']
        if file:
            args.append(file)
        result = self._run_git(args)
        if result['success']:
            return {
                'success': True,
                'message': f'Unstaged: {file or "all files"}'
            }
        return result

    def commit(self, message: str) -> Dict[str, Any]:
        """
        Commit staged changes.

        Args:
            message: Commit message
        """
        if not message:
            return {'success': False, 'error': 'Commit message required'}

        result = self._run_git(['commit', '-m', message])
        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'message': f'Committed: {message[:50]}...' if len(message) > 50 else f'Committed: {message}'
            }
        return result

    def commit_all(self, message: str) -> Dict[str, Any]:
        """Stage all and commit."""
        add_result = self.add_all()
        if not add_result['success']:
            return add_result
        return self.commit(message)

    def amend(self, message: Optional[str] = None) -> Dict[str, Any]:
        """Amend the last commit."""
        args = ['commit', '--amend']
        if message:
            args.extend(['-m', message])
        else:
            args.append('--no-edit')
        result = self._run_git(args)
        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'message': 'Amended last commit'
            }
        return result

    # ==================== BRANCHES ====================

    def branch(self) -> Dict[str, Any]:
        """List all branches."""
        result = self._run_git(['branch', '-a'])
        if result['success']:
            branches = [b.strip() for b in result['output'].split('\n') if b.strip()]
            current = next((b[2:] for b in branches if b.startswith('* ')), None)
            return {
                'success': True,
                'branches': branches,
                'current': current,
                'message': f'On branch: {current}'
            }
        return result

    def branch_create(self, name: str) -> Dict[str, Any]:
        """Create a new branch."""
        if not _validate_git_ref(name):
            return {'success': False, 'error': f'Invalid branch name: {name}'}
        result = self._run_git(['branch', name])
        if result['success']:
            return {
                'success': True,
                'message': f'Created branch: {name}'
            }
        return result

    def branch_delete(self, name: str, force: bool = False) -> Dict[str, Any]:
        """Delete a branch."""
        if not _validate_git_ref(name):
            return {'success': False, 'error': f'Invalid branch name: {name}'}
        flag = '-D' if force else '-d'
        result = self._run_git(['branch', flag, name])
        if result['success']:
            return {
                'success': True,
                'message': f'Deleted branch: {name}'
            }
        return result

    def checkout(self, branch: str) -> Dict[str, Any]:
        """Switch to a branch."""
        if not _validate_git_ref(branch):
            return {'success': False, 'error': f'Invalid branch name: {branch}'}
        result = self._run_git(['checkout', branch])
        if result['success']:
            return {
                'success': True,
                'message': f'Switched to: {branch}'
            }
        return result

    def checkout_new(self, branch: str) -> Dict[str, Any]:
        """Create and switch to new branch."""
        if not _validate_git_ref(branch):
            return {'success': False, 'error': f'Invalid branch name: {branch}'}
        result = self._run_git(['checkout', '-b', branch])
        if result['success']:
            return {
                'success': True,
                'message': f'Created and switched to: {branch}'
            }
        return result

    def merge(self, branch: str) -> Dict[str, Any]:
        """Merge a branch into current branch."""
        if not _validate_git_ref(branch):
            return {'success': False, 'error': f'Invalid branch name: {branch}'}
        result = self._run_git(['merge', branch])
        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'message': f'Merged: {branch}'
            }
        return result

    # ==================== REMOTE OPERATIONS ====================

    def remote(self) -> Dict[str, Any]:
        """List remotes."""
        result = self._run_git(['remote', '-v'])
        if result['success']:
            return {
                'success': True,
                'remotes': result['output'],
                'message': 'Got remotes'
            }
        return result

    def fetch(self, remote: str = 'origin') -> Dict[str, Any]:
        """Fetch from remote."""
        result = self._run_git(['fetch', remote], timeout=120)
        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'message': f'Fetched from: {remote}'
            }
        return result

    def pull(self, remote: str = 'origin', branch: Optional[str] = None) -> Dict[str, Any]:
        """Pull from remote."""
        args = ['pull', remote]
        if branch:
            args.append(branch)
        result = self._run_git(args, timeout=120)
        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'message': f'Pulled from: {remote}'
            }
        return result

    def push(self, remote: str = 'origin', branch: Optional[str] = None,
             set_upstream: bool = False) -> Dict[str, Any]:
        """Push to remote."""
        args = ['push']
        if set_upstream:
            args.append('-u')
        args.append(remote)
        if branch:
            args.append(branch)
        result = self._run_git(args, timeout=120)
        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'message': f'Pushed to: {remote}'
            }
        return result

    def push_new_branch(self, branch: Optional[str] = None) -> Dict[str, Any]:
        """Push new branch and set upstream."""
        if not branch:
            # Get current branch
            result = self._run_git(['rev-parse', '--abbrev-ref', 'HEAD'])
            if result['success']:
                branch = result['output']
            else:
                return result
        return self.push('origin', branch, set_upstream=True)

    # ==================== CLONE & INIT ====================

    def clone(self, url: str, directory: Optional[str] = None) -> Dict[str, Any]:
        """Clone a repository."""
        args = ['clone', url]
        if directory:
            args.append(directory)
        result = self._run_git(args, timeout=300)
        if result['success']:
            return {
                'success': True,
                'output': result['output'],
                'message': f'Cloned: {url}'
            }
        return result

    def init(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """Initialize a new repository."""
        if directory:
            os.makedirs(directory, exist_ok=True)
            old_dir = self.working_dir
            self.working_dir = directory

        result = self._run_git(['init'])

        if directory:
            self.working_dir = old_dir

        if result['success']:
            return {
                'success': True,
                'message': f'Initialized repo in: {directory or self.working_dir}'
            }
        return result

    # ==================== STASH ====================

    def stash(self, message: Optional[str] = None) -> Dict[str, Any]:
        """Stash current changes."""
        args = ['stash']
        if message:
            args.extend(['push', '-m', message])
        result = self._run_git(args)
        if result['success']:
            return {
                'success': True,
                'message': 'Stashed changes'
            }
        return result

    def stash_pop(self) -> Dict[str, Any]:
        """Pop last stash."""
        result = self._run_git(['stash', 'pop'])
        if result['success']:
            return {
                'success': True,
                'message': 'Popped stash'
            }
        return result

    def stash_list(self) -> Dict[str, Any]:
        """List stashes."""
        result = self._run_git(['stash', 'list'])
        if result['success']:
            stashes = result['output'].split('\n') if result['output'] else []
            return {
                'success': True,
                'stashes': [s for s in stashes if s],
                'count': len([s for s in stashes if s]),
                'message': f'{len([s for s in stashes if s])} stashes'
            }
        return result

    # ==================== UTILITY ====================

    def show_config(self) -> Dict[str, Any]:
        """Show git config."""
        result = self._run_git(['config', '--list'])
        if result['success']:
            return {
                'success': True,
                'config': result['output'],
                'message': 'Got git config'
            }
        return result

    def set_user(self, name: str, email: str, global_config: bool = True) -> Dict[str, Any]:
        """Set git user name and email."""
        scope = '--global' if global_config else '--local'

        name_result = self._run_git(['config', scope, 'user.name', name])
        if not name_result['success']:
            return name_result

        email_result = self._run_git(['config', scope, 'user.email', email])
        if email_result['success']:
            return {
                'success': True,
                'message': f'Set user: {name} <{email}>'
            }
        return email_result

    def current_branch(self) -> Dict[str, Any]:
        """Get current branch name."""
        result = self._run_git(['rev-parse', '--abbrev-ref', 'HEAD'])
        if result['success']:
            return {
                'success': True,
                'branch': result['output'],
                'message': f'On branch: {result["output"]}'
            }
        return result

    def is_repo(self) -> bool:
        """Check if current directory is a git repo."""
        result = self._run_git(['rev-parse', '--git-dir'])
        return result['success']

    def clean(self, dry_run: bool = True) -> Dict[str, Any]:
        """Remove untracked files."""
        args = ['clean', '-fd']
        if dry_run:
            args.append('-n')
        result = self._run_git(args)
        if result['success']:
            msg = 'Would remove:' if dry_run else 'Removed:'
            return {
                'success': True,
                'output': result['output'],
                'message': f'{msg} untracked files'
            }
        return result
