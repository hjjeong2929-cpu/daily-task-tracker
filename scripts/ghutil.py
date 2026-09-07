"""Shared GitHub API helper for the daily-task-tracker automation scripts.

No third-party dependencies (uses urllib only) so it runs on any GitHub
Actions Python runner with zero setup.
"""
import json
import os
import re
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

DUE_DATE_RE = re.compile(r"\((\d{4}-\d{2}-\d{2})\)\s*$")

RECURRING_LABEL = "recurring"
DIGEST_LABEL = "digest"
PERIOD_LABEL = "period"
SKIPPED_LABEL = "skipped"

PERIOD_START_RE = re.compile(r"<!--\s*period_start:\s*(\d{4}-\d{2}-\d{2})\s*-->")


def today_kst():
    return datetime.now(KST).date()


def now_kst():
    return datetime.now(KST)


def extract_due_date(title):
    """Return the (YYYY-MM-DD) date embedded at the end of an issue title, or None."""
    m = DUE_DATE_RE.search(title.strip())
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None


def extract_period_start(body):
    """Return the period start date hidden in an issue body, or None."""
    if not body:
        return None
    m = PERIOD_START_RE.search(body)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None


def strip_due_date(title):
    return DUE_DATE_RE.sub("", title).strip()


class GitHub:
    def __init__(self, token=None, repository=None):
        self.token = token or os.environ["GITHUB_TOKEN"]
        self.repository = repository or os.environ["GITHUB_REPOSITORY"]
        self.owner_login, self.repo_name = self.repository.split("/", 1)
        self.api_base = "https://api.github.com"

    def request(self, method, path, payload=None):
        url = path if path.startswith("http") else f"{self.api_base}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read()
                headers = dict(resp.headers)
                return (json.loads(body) if body else None), headers
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", "replace")
            raise RuntimeError(f"{method} {url} -> {e.code}: {err_body}") from e

    # ---- issues -------------------------------------------------------
    def search_issues(self, query):
        data, _ = self.request(
            "GET", f"/search/issues?q={urllib.parse.quote(query)}&per_page=100"
        )
        return data.get("items", [])

    def issue_exists_with_title(self, title, state="open"):
        query = f'repo:{self.repository} in:title "{title}" is:issue state:{state}'
        items = self.search_issues(query)
        return any(item["title"] == title for item in items)

    def ensure_label(self, name, color="ededed", description=""):
        try:
            self.request("GET", f"/repos/{self.repository}/labels/{name}")
        except RuntimeError:
            self.request(
                "POST",
                f"/repos/{self.repository}/labels",
                {"name": name, "color": color, "description": description},
            )

    def create_issue(self, title, body="", labels=None, assignees=None):
        payload = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees
        data, _ = self.request("POST", f"/repos/{self.repository}/issues", payload)
        return data

    def list_issues(self, state="open", labels=None, per_page=100, max_pages=5):
        results = []
        page = 1
        while page <= max_pages:
            path = f"/repos/{self.repository}/issues?state={state}&per_page={per_page}&page={page}"
            if labels:
                path += f"&labels={labels}"
            data, _ = self.request("GET", path)
            if not data:
                break
            results.extend(data)
            if len(data) < per_page:
                break
            page += 1
        # The issues endpoint also returns pull requests; filter those out.
        return [i for i in results if "pull_request" not in i]

    def list_open_issues(self):
        return self.list_issues(state="open")

    def get_issue(self, number):
        data, _ = self.request("GET", f"/repos/{self.repository}/issues/{number}")
        return data

    def update_issue(self, number, payload):
        data, _ = self.request("PATCH", f"/repos/{self.repository}/issues/{number}", payload)
        return data

    def close_issue(self, number):
        return self.update_issue(number, {"state": "closed"})

    def set_labels(self, number, labels):
        data, _ = self.request(
            "PUT", f"/repos/{self.repository}/issues/{number}/labels", {"labels": labels}
        )
        return data

    def add_labels(self, number, labels):
        data, _ = self.request(
            "POST", f"/repos/{self.repository}/issues/{number}/labels", {"labels": labels}
        )
        return data

    def add_comment(self, number, body):
        data, _ = self.request(
            "POST", f"/repos/{self.repository}/issues/{number}/comments", {"body": body}
        )
        return data

    def list_comments(self, number):
        data, _ = self.request("GET", f"/repos/{self.repository}/issues/{number}/comments?per_page=100")
        return data
