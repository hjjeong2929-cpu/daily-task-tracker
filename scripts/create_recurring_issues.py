"""Create today's instances of every recurring task that applies today.

Reads data/recurring_rules.json. A rule fires today when:
  - today's weekday is in rule["days"], AND
  - today is within [start_date, end_date] if either is set (both optional)

Each fired rule creates ONE issue for today, titled "{title} (YYYY-MM-DD)"
and labeled "recurring" (+ optional category label). This does NOT touch
the rule itself, so deleting/closing today's instance later never affects
tomorrow's (or any other day's) instance.
"""
import json
import os

from ghutil import GitHub, RECURRING_LABEL, today_kst

WEEKDAY_MAP = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def load_rules(path="data/recurring_rules.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def rule_applies_today(rule, today):
    weekday = WEEKDAY_MAP[today.weekday()]
    if weekday not in rule.get("days", []):
        return False
    start = rule.get("start_date")
    end = rule.get("end_date")
    if start and today.isoformat() < start:
        return False
    if end and today.isoformat() > end:
        return False
    return True


def main():
    gh = GitHub()
    today = today_kst()
    today_str = today.isoformat()

    gh.ensure_label(RECURRING_LABEL, "0e8a16", "매일 아침 자동 생성되는 반복 할일 인스턴스")

    rules = load_rules()
    created = []
    for rule in rules:
        if not rule_applies_today(rule, today):
            continue
        title = f"{rule['title']} ({today_str})"
        if gh.issue_exists_with_title(title, state="all"):
            continue  # already created (e.g. workflow re-run)
        labels = [RECURRING_LABEL]
        category = rule.get("category")
        if category:
            gh.ensure_label(category, "c5def5", f"카테고리: {category}")
            labels.append(category)
        issue = gh.create_issue(
            title=title,
            body=f"반복 할일 규칙 `{rule.get('id', rule['title'])}`에서 자동 생성됨.",
            labels=labels,
            assignees=[gh.owner_login],
        )
        created.append(issue["number"])

    print(f"created {len(created)} recurring instance(s) for {today_str}: {created}")


if __name__ == "__main__":
    main()
