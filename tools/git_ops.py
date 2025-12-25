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

# Load .env for GitHub token
PROJECT_DIR = Path(__file__).parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_DIR / '.env')
except ImportError:
    pass


class GitHubAPI:
    """GitHub API integration with browser-based OAuth authentication."""

    # GitHub OAuth App - Device Flow (no client secret needed)
    # You can create your own at: https://github.com/settings/developers
    CLIENT_ID = "Ov23liYourClientIdHere"  # Replace with your OAuth App client ID

    API_BASE = "https://api.github.com"
    CONFIG_DIR = Path.home() / '.cora'
    TOKEN_FILE = CONFIG_DIR / 'github_token.json'

    def __init__(self):
        self.token = None
        self._load_token()

    def _load_token(self):
        """Load saved GitHub token from .env or token file."""
        # First check .env file (preferred for persistent login)
        env_token = os.environ.get('GITHUB_TOKEN')
        if env_token:
            self.token = env_token
            return

        # Fallback to token file
        try:
            if self.TOKEN_FILE.exists():
                with open(self.TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                    self.token = data.get('access_token')
        except:
            pass

    def _save_token(self, token: str):
        """Save GitHub token."""
        try:
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.TOKEN_FILE, 'w') as f:
                json.dump({'access_token': token}, f)
            self.token = token
        except Exception as e:
            print(f"[GitHub] Could not save token: {e}")

    def _api_request(self, endpoint: str, method: str = 'GET',
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GitHub API request."""
        if not self.token:
            return {'success': False, 'error': 'Not authenticated. Run github_login() first'}

        url = f"{self.API_BASE}{endpoint}"
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'CORA-Assistant'
        }

        try:
            req_data = json.dumps(data).encode() if data else None
            req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())
                return {'success': True, 'data': result}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            return {'success': False, 'error': f'HTTP {e.code}: {error_body}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def is_authenticated(self) -> bool:
        """Check if we have a valid token."""
        if not self.token:
            return False
        # Verify token works
        result = self._api_request('/user')
        return result.get('success', False)

    def login_with_token(self, token: str) -> Dict[str, Any]:
        """
        Login with a Personal Access Token.
        Get one at: https://github.com/settings/tokens

        Args:
            token: GitHub Personal Access Token
        """
        self.token = token
        result = self._api_request('/user')

        if result['success']:
            self._save_token(token)
            user = result['data']
            return {
                'success': True,
                'username': user.get('login'),
                'name': user.get('name'),
                'message': f"Logged in as {user.get('login')}"
            }
        else:
            self.token = None
            return {'success': False, 'error': 'Invalid token'}

    def login_browser(self) -> Dict[str, Any]:
        """
        Start browser-based login flow.
        Opens GitHub in browser to get a Personal Access Token.
        """
        import webbrowser

        # Direct user to create a token
        token_url = "https://github.com/settings/tokens/new?scopes=repo,user&description=CORA-Assistant"

        print("\n[GitHub] Opening browser for authentication...")
        print("[GitHub] Create a new token with 'repo' and 'user' scopes")
        print("[GitHub] Copy the token and use: github_login('your_token_here')\n")

        webbrowser.open(token_url)

        return {
            'success': True,
            'message': 'Browser opened. Create a token and use github_login(token) to complete login',
            'url': token_url
        }

    def logout(self) -> Dict[str, Any]:
        """Remove saved GitHub credentials."""
        try:
            if self.TOKEN_FILE.exists():
                os.remove(self.TOKEN_FILE)
            self.token = None
            return {'success': True, 'message': 'Logged out from GitHub'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_user(self) -> Dict[str, Any]:
        """Get current authenticated user info."""
        result = self._api_request('/user')
        if result['success']:
            user = result['data']
            return {
                'success': True,
                'username': user.get('login'),
                'name': user.get('name'),
                'email': user.get('email'),
                'repos': user.get('public_repos'),
                'followers': user.get('followers'),
                'url': user.get('html_url')
            }
        return result

    def list_repos(self, per_page: int = 30) -> Dict[str, Any]:
        """List user's repositories."""
        result = self._api_request(f'/user/repos?per_page={per_page}&sort=updated')
        if result['success']:
            repos = []
            for repo in result['data']:
                repos.append({
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'private': repo['private'],
                    'url': repo['html_url'],
                    'clone_url': repo['clone_url'],
                    'description': repo.get('description', ''),
                    'language': repo.get('language'),
                    'stars': repo.get('stargazers_count', 0)
                })
            return {
                'success': True,
                'repos': repos,
                'count': len(repos),
                'message': f'Found {len(repos)} repositories'
            }
        return result

    def create_repo(self, name: str, description: str = '',
                    private: bool = False, init_readme: bool = True) -> Dict[str, Any]:
        """
        Create a new GitHub repository.

        Args:
            name: Repository name
            description: Repository description
            private: Make repository private
            init_readme: Initialize with README
        """
        data = {
            'name': name,
            'description': description,
            'private': private,
            'auto_init': init_readme
        }

        result = self._api_request('/user/repos', method='POST', data=data)
        if result['success']:
            repo = result['data']
            return {
                'success': True,
                'name': repo['name'],
                'full_name': repo['full_name'],
                'url': repo['html_url'],
                'clone_url': repo['clone_url'],
                'ssh_url': repo['ssh_url'],
                'message': f"Created repository: {repo['full_name']}"
            }
        return result

    def delete_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Delete a repository (requires delete_repo scope)."""
        result = self._api_request(f'/repos/{owner}/{repo}', method='DELETE')
        if result['success']:
            return {'success': True, 'message': f'Deleted repository: {owner}/{repo}'}
        return result

    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository info."""
        result = self._api_request(f'/repos/{owner}/{repo}')
        if result['success']:
            r = result['data']
            return {
                'success': True,
                'name': r['name'],
                'full_name': r['full_name'],
                'description': r.get('description'),
                'private': r['private'],
                'url': r['html_url'],
                'clone_url': r['clone_url'],
                'default_branch': r['default_branch'],
                'stars': r.get('stargazers_count', 0),
                'forks': r.get('forks_count', 0),
                'language': r.get('language')
            }
        return result

    def fork_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fork a repository."""
        result = self._api_request(f'/repos/{owner}/{repo}/forks', method='POST', data={})
        if result['success']:
            fork = result['data']
            return {
                'success': True,
                'name': fork['full_name'],
                'url': fork['html_url'],
                'clone_url': fork['clone_url'],
                'message': f"Forked to: {fork['full_name']}"
            }
        return result

    def list_branches(self, owner: str, repo: str) -> Dict[str, Any]:
        """List branches in a repository."""
        result = self._api_request(f'/repos/{owner}/{repo}/branches')
        if result['success']:
            branches = [b['name'] for b in result['data']]
            return {
                'success': True,
                'branches': branches,
                'count': len(branches),
                'message': f'{len(branches)} branches'
            }
        return result

    def create_branch(self, owner: str, repo: str, branch_name: str,
                      from_branch: str = 'main') -> Dict[str, Any]:
        """Create a new branch from an existing branch."""
        # First get the SHA of the source branch
        ref_result = self._api_request(f'/repos/{owner}/{repo}/git/ref/heads/{from_branch}')
        if not ref_result['success']:
            return ref_result

        sha = ref_result['data']['object']['sha']

        # Create new branch
        data = {
            'ref': f'refs/heads/{branch_name}',
            'sha': sha
        }
        result = self._api_request(f'/repos/{owner}/{repo}/git/refs', method='POST', data=data)
        if result['success']:
            return {
                'success': True,
                'branch': branch_name,
                'message': f"Created branch: {branch_name} from {from_branch}"
            }
        return result

    def create_pull_request(self, owner: str, repo: str, title: str,
                           head: str, base: str = 'main',
                           body: str = '') -> Dict[str, Any]:
        """Create a pull request."""
        data = {
            'title': title,
            'head': head,
            'base': base,
            'body': body
        }
        result = self._api_request(f'/repos/{owner}/{repo}/pulls', method='POST', data=data)
        if result['success']:
            pr = result['data']
            return {
                'success': True,
                'number': pr['number'],
                'url': pr['html_url'],
                'title': pr['title'],
                'message': f"Created PR #{pr['number']}: {pr['title']}"
            }
        return result

    def list_pull_requests(self, owner: str, repo: str,
                          state: str = 'open') -> Dict[str, Any]:
        """List pull requests."""
        result = self._api_request(f'/repos/{owner}/{repo}/pulls?state={state}')
        if result['success']:
            prs = []
            for pr in result['data']:
                prs.append({
                    'number': pr['number'],
                    'title': pr['title'],
                    'state': pr['state'],
                    'user': pr['user']['login'],
                    'url': pr['html_url']
                })
            return {
                'success': True,
                'pull_requests': prs,
                'count': len(prs),
                'message': f'{len(prs)} pull requests'
            }
        return result


class GitOperations:
    """Complete Git operations for CORA."""

    def __init__(self, working_dir: Optional[str] = None):
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
        result = self._run_git(['branch', name])
        if result['success']:
            return {
                'success': True,
                'message': f'Created branch: {name}'
            }
        return result

    def branch_delete(self, name: str, force: bool = False) -> Dict[str, Any]:
        """Delete a branch."""
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
        result = self._run_git(['checkout', branch])
        if result['success']:
            return {
                'success': True,
                'message': f'Switched to: {branch}'
            }
        return result

    def checkout_new(self, branch: str) -> Dict[str, Any]:
        """Create and switch to new branch."""
        result = self._run_git(['checkout', '-b', branch])
        if result['success']:
            return {
                'success': True,
                'message': f'Created and switched to: {branch}'
            }
        return result

    def merge(self, branch: str) -> Dict[str, Any]:
        """Merge a branch into current branch."""
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


# Global instance
_git = None

def get_git(working_dir: Optional[str] = None) -> GitOperations:
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
