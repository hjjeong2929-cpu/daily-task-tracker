#!/usr/bin/env python3
"""오늘 챙겨야 할 일(연체 · 오늘 마감 · P1)을 모아 '오늘의 할 일' 이슈로 정리한다.

반복 이슈 생성 다음 단계로 실행되는 것을 전제로 한다.
"""
from ghutil import GitHub, DIGEST_LABEL, DIGEST_LABEL_COLOR, extract_due_date, today_kst

DIGEST_TITLE_PREFIX = "📋 오늘의 할 일"


def classify(issue, today):
    due = extract_due_date(issue["title"])
    labels = {l["name"] for l in issue.get("labels", [])}
    is_p1 = "P1" in labels
    overdue = due is not None and due < today
    due_today = due is not None and due == today
    return due, is_p1, overdue, due_today


def main():
    gh = GitHub()
    today = today_kst()
    today_str = today.isoformat()

    gh.ensure_label(DIGEST_LABEL, DIGEST_LABEL_COLOR)

    digest_title = f"{DIGEST_TITLE_PREFIX} ({today_str})"
    if gh.issue_exists_with_title(digest_title):
        print("오늘 요약 이슈가 이미 있어서 건너뜀")
        return

    open_issues = gh.list_open_issues()
    picked = []
    for issue in open_issues:
        if issue["title"].startswith(DIGEST_TITLE_PREFIX):
            continue
        due, is_p1, overdue, due_today = classify(issue, today)
        if overdue or due_today or is_p1:
            # 정렬 키: 연체 먼저, 그다음 마감일이 이른 순, 그다음 P1 우선
            sort_due = due or today
            picked.append((0 if overdue else 1, sort_due, 0 if is_p1 else 1, overdue, issue))

    picked.sort(key=lambda x: (x[0], x[1], x[2]))

    if not picked:
        body = "오늘은 연체되거나 급한 할 일이 없어요. 🎉"
    else:
        lines = []
        for _, due, _, overdue, issue in picked:
            if overdue:
                tag = f"🔴 연체({due.isoformat()})"
            elif due == today:
                tag = "🟡 오늘 마감"
            else:
                tag = "🔵 P1"
            lines.append(f"- [ ] {tag} [#{issue['number']}]({issue['html_url']}) {issue['title']}")
        body = "\n".join(lines)
        body += "\n\n_체크박스는 표시용입니다. 실제 완료 처리는 각 이슈를 Close 해주세요._"

    issue = gh.create_issue(digest_title, body, labels=[DIGEST_LABEL], assignee=gh.owner_login)
    print(f"오늘의 할 일 요약 생성: {len(picked)}건 -> {issue['html_url']}")


if __name__ == "__main__":
    main()
