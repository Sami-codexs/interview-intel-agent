"""GitHub API search retriever for GPT Researcher.

Follows the same interface as TavilySearch so it can be registered
alongside other retrievers via RETRIEVER=tavily,github.
"""

import base64
import json
import logging
import os
from typing import List, Dict, Any

import requests

logger = logging.getLogger(__name__)


class GitHubSearch:
    """GitHub API Retriever.

    Discovers org repos, extracts languages/topics, and fetches README
    first paragraphs for the top N most-starred repositories.
    """

    def __init__(self, query, headers=None, topic="general", query_domains=None):
        self.query = query.strip().lower().replace(" ", "-")
        self.headers = headers or {}
        self._api_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = self._get_token()
        if token:
            self._api_headers["Authorization"] = f"Bearer {token}"

    def _get_token(self) -> str | None:
        token = self.headers.get("github_token") or os.environ.get("GITHUB_TOKEN")
        return token

    def _get(self, url: str) -> dict | None:
        try:
            resp = requests.get(url, headers=self._api_headers, timeout=20)
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                logger.warning(f"GitHub rate limit hit for {url}. Consider setting GITHUB_TOKEN.")
                return None
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"GitHub API request failed: {e}")
            return None

    def _fetch_org_repos(self, org: str) -> List[Dict[str, Any]]:
        url = f"https://api.github.com/orgs/{org}/repos?per_page=100&sort=stars&direction=desc"
        data = self._get(url)
        if data is None:
            return []
        if isinstance(data, list):
            return data
        return []

    def _search_repos(self, org: str) -> List[Dict[str, Any]]:
        url = (
            f"https://api.github.com/search/repositories"
            f"?q=org:{org}&sort=stars&order=desc&per_page=30"
        )
        data = self._get(url)
        if data is None:
            return []
        return data.get("items", [])

    def _fetch_readme_snippet(self, owner: str, repo: str) -> str:
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        data = self._get(url)
        if not data or "content" not in data:
            return ""
        try:
            decoded = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            for line in decoded.split("\n\n"):
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    return stripped[:800]
            return ""
        except Exception as e:
            logger.debug(f"Failed to decode README for {owner}/{repo}: {e}")
            return ""

    def _format_repo(self, repo: dict) -> dict:
        owner = repo.get("owner", {}).get("login", "")
        name = repo.get("name", "")
        html_url = repo.get("html_url", "")
        language = repo.get("language") or "Unknown"
        topics = repo.get("topics", [])
        stars = repo.get("stargazers_count", 0)
        description = repo.get("description") or ""

        readme_snippet = ""
        if owner and name:
            readme_snippet = self._fetch_readme_snippet(owner, name)

        body_lines = [
            f"Repository: {name}",
            f"Stars: {stars}",
            f"Primary Language: {language}",
            f"Topics: {', '.join(topics) if topics else 'None'}",
            f"Description: {description}",
        ]
        if readme_snippet:
            body_lines.append(f"README excerpt: {readme_snippet}")

        return {
            "href": html_url,
            "body": "\n".join(body_lines),
            "title": name,
        }

    def search(self, max_results=10) -> List[Dict[str, str]]:
        try:
            repos = self._fetch_org_repos(self.query)
            if not repos:
                logger.info(f"No org repos found for '{self.query}', falling back to search.")
                repos = self._search_repos(self.query)

            if not repos:
                logger.warning(f"No GitHub repos found for '{self.query}'.")
                return []

            repos_sorted = sorted(
                repos,
                key=lambda r: r.get("stargazers_count", 0),
                reverse=True,
            )[:max_results]

            results = [self._format_repo(r) for r in repos_sorted]
            logger.info(f"GitHub retriever returned {len(results)} repos for '{self.query}'.")
            return results

        except Exception as e:
            logger.error(f"GitHub retriever error: {e}")
            return []