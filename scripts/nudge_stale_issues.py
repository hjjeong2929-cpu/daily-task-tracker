#!/usr/bin/env python3
"""3일 넘게 열려있는 할일에 넛지 댓글을 달고, 7일 넘으면 우선순위를 P1로 올린다."""
from datetime import datetime

from ghutil import GitHub, DIGEST_LABEL, PRIORITY_COLORS, now_kst

NUDGE_AFTER_DAYS = 3
ESCALATE_AFTER_DAYS = 7
BOT_MARK = "<!-- stale-nudge-bot -->"


def days_open(issue, now) -> int:
    created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
    return (now - created).days


def already_nudged_today(gh, issue_number, today_str) -> bool:
    for c in gh.list_comments(issue_number):
        if BOT_MARK in c.get("body", "") and c["created_at"].startswith(today_str):
            return True
    return False


def main():
    gh = GitHub()
    now = now_kst()
    today_str = now.date().isoformat()

    nudged = 0
    for issue in gh.list_open_issues():
        labels = {l["name"] for l in issue.get("labels", [])}
        if DIGEST_LABEL in labels:
            continue  # 다이제스트 요약 이슈 자체는 넛지 대상이 아님

        age = days_open(issue, now)
        if age < NUDGE_AFTER_DAYS:
            continue
        if already_nudged_today(gh, issue["number"], today_str):
            continue

        if age >= ESCALATE_AFTER_DAYS and "P1" not in labels:
            gh.ensure_label("P1", PRIORITY_COLORS["P1"])
            new_labels = [l for l in labels if l not in ("P1", "P2", "P3")] + ["P1"]
            gh.set_labels(issue["number"], new_labels)
            gh.add_comment(
                issue["number"],
                f"{BOT_MARK}\n🔥 이 작업이 {age}일째 열려 있어요. 우선순위를 P1로 올렸어요. 오늘 끝내볼까요?",
            )
        else:
            gh.add_comment(
                issue["number"],
                f"{BOT_MARK}\n⏰ 이 작업이 {age}일째 그대로예요. 오늘 조금이라도 진행해보는 건 어떨까요?",
            )
        nudged += 1
        print(f"넛지: #{issue['number']} ({age}일째)")

    print(f"총 {nudged}건 넛지")


if __name__ == "__main__":
    main()
