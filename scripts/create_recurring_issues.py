#!/usr/bin/env python3
"""tasks.yml 중 오늘 해당하는 반복 작업을 이슈로 생성한다.

- 제목: "{작업명} (오늘 날짜)" 형태로 만들어서 마감일 파싱과 통계에 활용
- 우선순위 라벨(P1/P2/P3)과 recurring 라벨을 붙임
- 나(레포 소유자)에게 자동 할당 → GitHub 모바일 앱 푸시 알림으로 이어짐
"""
import sys

import yaml
from ghutil import GitHub, RECURRING_LABEL, RECURRING_LABEL_COLOR, PRIORITY_COLORS, CATEGORY_LABEL_COLOR, normalize_priority, today_kst

WEEKDAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}


def load_tasks(path="tasks.yml"):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("tasks", [])


def is_due_today(task, weekday_key) -> bool:
    days = task.get("days", "all")
    if days == "all":
        return True
    if isinstance(days, str):
        days = [d.strip() for d in days.split(",")]
    return weekday_key in days


def main():
    gh = GitHub()
    today = today_kst()
    weekday_key = WEEKDAY_MAP[today.weekday()]
    today_str = today.isoformat()

    gh.ensure_label(RECURRING_LABEL, RECURRING_LABEL_COLOR)

    created = 0
    for task in load_tasks():
        if not is_due_today(task, weekday_key):
            continue

        title = f"{task['title']} ({today_str})"
        if gh.issue_exists_with_title(title):
            print(f"이미 존재해서 건너뜀: {title}")
            continue

        priority = normalize_priority(task.get("priority"))
        gh.ensure_label(priority, PRIORITY_COLORS[priority])

        labels = [RECURRING_LABEL, priority]
        category = task.get("label")
        if category:
            gh.ensure_label(category, CATEGORY_LABEL_COLOR)
            labels.append(category)

        body = (task.get("body", "") + "\n\n완료하면 이 이슈를 Close 해주세요. ✅").strip()
        issue = gh.create_issue(title, body, labels, assignee=gh.owner_login)
        created += 1
        print(f"생성됨: {title} -> {issue['html_url']}")

    print(f"오늘({today_str}, {weekday_key}) 총 {created}개 반복 이슈 생성")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"오류: {e}", file=sys.stderr)
        raise
