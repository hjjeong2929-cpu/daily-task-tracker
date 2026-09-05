"""GitHub REST API 호출을 위한 공용 헬퍼 모음.

모든 스크립트가 이 모듈을 통해서만 GitHub API를 호출한다.
GITHUB_TOKEN / GITHUB_REPOSITORY / GITHUB_REPOSITORY_OWNER 는
GitHub Actions가 자동으로 넣어주는 환경 변수를 사용한다.
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

# 제목 끝의 "(YYYY-MM-DD)" 를 마감일로 인식한다.
DUE_DATE_RE = re.compile(r"\((\d{4}-\d{2}-\d{2})\)\s*$")

PRIORITIES = ("P1", "P2", "P3")
PRIORITY_COLORS = {"P1": "d73a4a", "P2": "fbca04", "P3": "0e8a16"}
RECURRING_LABEL = "recurring"
RECURRING_LABEL_COLOR = "1d76db"
DIGEST_LABEL = "digest"
DIGEST_LABEL_COLOR = "5319e7"
CATEGORY_LABEL_COLOR = "c5def5"


def today_kst() -> date:
    return datetime.now(KST).date()


def now_kst() -> datetime:
    return datetime.now(KST)


def extract_due_date(title: str):
    m = DUE_DATE_RE.search(title)
    if not m:
        return None
    try:
        y, mo, d = m.group(1).split("-")
        return date(int(y), int(mo), int(d))
    except ValueError:
        return None


def normalize_priority(value) -> str:
    p = (value or "P2").upper()
    return p if p in PRIORITIES else "P2"


class GitHub:
    def __init__(self, token=None, repo=None):
        self.token = token or os.environ["GITHUB_TOKEN"]
        self.repo = repo or os.environ["GITHUB_REPOSITORY"]
        self.owner_login = os.environ.get("GITHUB_REPOSITORY_OWNER")

    def request(self, method, path_or_url, body=None):
        url = path_or_url if path_or_url.startswith("http") else f"https://api.github.com{path_or_url}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw else None

    def search_issues(self, query, per_page=100):
        url = f"/search/issues?q={urllib.parse.quote(query)}&per_page={per_page}"
        result = self.request("GET", url)
        return result.get("items", [])

    def issue_exists_with_title(self, title) -> bool:
        query = f'repo:{self.repo} is:issue in:title "{title}"'
        return len(self.search_issues(query, per_page=1)) > 0

    def ensure_label(self, name, color):
        try:
            self.request("GET", f"/repos/{self.repo}/labels/{urllib.parse.quote(name)}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.request("POST", f"/repos/{self.repo}/labels", {"name": name, "color": color})
            else:
                raise

    def create_issue(self, title, body, labels, assignee=None):
        payload = {"title": title, "body": body, "labels": labels}
        if assignee:
            payload["assignees"] = [assignee]
        return self.request("POST", f"/repos/{self.repo}/issues", payload)

    def list_open_issues(self, extra_query=""):
        query = f"repo:{self.repo} is:issue is:open {extra_query}".strip()
        return self.search_issues(query)

    def add_comment(self, issue_number, body):
        return self.request("POST", f"/repos/{self.repo}/issues/{issue_number}/comments", {"body": body})

    def list_comments(self, issue_number):
        return self.request("GET", f"/repos/{self.repo}/issues/{issue_number}/comments")

    def set_labels(self, issue_number, labels):
        return self.request("PUT", f"/repos/{self.repo}/issues/{issue_number}/labels", {"labels": labels})
