"""Post a self-mention comment on today's digest issue to trigger a push.

Runs twice a day (16:30 and 21:30 KST, see .github/workflows/push_notify.yml).
GitHub Mobile only pushes for 4 event types (mentions, assignments, review
requests, deployment approvals) -- a plain comment does NOT push even on an
issue you're assigned to. So every comment here starts with "@<owner>" to
land it in the "Direct mentions" push, which needs just one API call (no
unassign/reassign dance).

No other notification is ever sent by this project -- only these two
fixed-time comments per day.
"""
import sys

from ghutil import GitHub, DIGEST_LABEL, today_kst, now_kst
from daily_digest import collect_today_tasks


def find_digest_issue(gh, today_str):
    title = f"📋 오늘의 할일 ({today_str})"
    for issue in gh.list_issues(state="all", labels=DIGEST_LABEL, max_pages=1):
        if issue["title"] == title:
            return issue
    return None


def render_comment(mention, tasks, slot_label):
    if not tasks:
        return f"{mention} {slot_label} — 오늘 할일을 모두 끝냈어요! 수고하셨습니다 🎉"
    lines = [f"{mention} {slot_label} — 아직 안 끝난 할일 {len(tasks)}개"]
    for t in tasks:
        lines.append(f"- {t['issue']['title']}")
    return "\n".join(lines)


def main():
    gh = GitHub()
    today = today_kst()
    today_str = today.isoformat()
    hour = now_kst().hour
    slot_label = "오후 4:30 체크" if hour < 18 else "오후 9:30 마지막 체크"

    digest = find_digest_issue(gh, today_str)
    if digest is None:
        print(f"no digest issue found for {today_str}; skipping push comment")
        sys.exit(0)

    tasks = collect_today_tasks(gh, today)
    mention = f"@{gh.owner_login}"
    body = render_comment(mention, tasks, slot_label)
    gh.add_comment(digest["number"], body)
    print(f"posted push comment on #{digest['number']} ({len(tasks)} incomplete task(s))")


if __name__ == "__main__":
    main()
