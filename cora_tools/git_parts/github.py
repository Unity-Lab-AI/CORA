#!/usr/bin/env python3
"""cora_tools.git_parts: github (split from cora_tools/git_ops.py on 2026-10-14)."""
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
from cora_tools.git_parts._base import Any, Dict, Optional, Path, json, os, urllib  # noqa: F401




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
