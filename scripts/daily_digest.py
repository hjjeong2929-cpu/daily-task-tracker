"""Create (or refresh) today's anchor issue: "📋 오늘의 할일 (YYYY-MM-DD)".

This issue is assigned to the owner and later gets two comments during the
day (see notify_push.py) that self-mention the owner to trigger a GitHub
Mobile push at fixed times. It is not a to-do item itself, so it always
carries the "digest" label and is excluded from every other list/stat.

Note: tasks never roll over to the next day (that was decided on purpose),
so this only looks at tasks whose title date is exactly today -- never
anything from a previous day.
"""
from ghutil import (
    GitHub,
    DIGEST_LABEL,
    SKIPPED_LABEL,
    extract_due_date,
    today_kst,
)


def collect_today_tasks(gh, today):
    """Every open, non-digest, non-skipped issue due exactly today."""
    tasks = []
    for issue in gh.list_open_issues():
        labels = {l["name"] for l in issue.get("labels", [])}
        if DIGEST_LABEL in labels or SKIPPED_LABEL in labels:
            continue
        due = extract_due_date(issue["title"])
        if due == today:
            tasks.append({"issue": issue, "due": due})
    tasks.sort(key=lambda t: t["issue"]["number"])
    return tasks


def render_body(tasks, today):
    if not tasks:
        return f"오늘({today.isoformat()}) 기준으로 남은 할일이 없어요. 여유로운 하루네요."
    lines = [f"오늘({today.isoformat()}) 기준 할일 {len(tasks)}개", ""]
    for t in tasks:
        issue = t["issue"]
        lines.append(f"- [ ] {issue['title']} (#{issue['number']})")
    return "\n".join(lines)


def main():
    gh = GitHub()
    today = today_kst()
    today_str = today.isoformat()
    title = f"📋 오늘의 할일 ({today_str})"

    gh.ensure_label(DIGEST_LABEL, "5319e7", "매일 아침 자동 생성되는 오늘의 할일 안내 이슈")

    if gh.issue_exists_with_title(title, state="all"):
        print(f"digest issue already exists for {today_str}, skipping creation")
        return

    tasks = collect_today_tasks(gh, today)
    body = render_body(tasks, today)
    issue = gh.create_issue(
        title=title,
        body=body,
        labels=[DIGEST_LABEL],
        assignees=[gh.owner_login],
    )
    print(f"created digest issue #{issue['number']} with {len(tasks)} task(s)")


if __name__ == "__main__":
    main()
