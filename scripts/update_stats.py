#!/usr/bin/env python3
"""오늘 마감(due) 이슈들의 완료 여부를 집계해 data/history.json과 README 통계를 갱신한다.

- 반복 이슈든 수동으로 만든 이슈든, 제목에 "(오늘 날짜)"가 붙어있으면 대상이 된다.
- 다이제스트 요약 이슈 자체는 집계에서 제외한다.
"""
import json
import os

from ghutil import GitHub, DIGEST_LABEL, now_kst, today_kst

HISTORY_PATH = "data/history.json"
README_PATH = "README.md"
START_MARK = "<!-- STATS:START -->"
END_MARK = "<!-- STATS:END -->"
RECENT_DAYS_SHOWN = 14


def fetch_due_today_issues(gh, today_str):
    query = f'repo:{gh.repo} is:issue in:title "({today_str})"'
    return gh.search_issues(query)


def load_history():
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        f.write("\n")


def compute_streak(history):
    streak = 0
    for entry in reversed(history):
        if entry["total"] > 0 and entry["completed"] == entry["total"]:
            streak += 1
        else:
            break
    return streak


def render_stats(history):
    recent = history[-RECENT_DAYS_SHOWN:]
    strip = []
    for e in recent:
        if e["total"] == 0:
            strip.append("⬜")
        elif e["completed"] == e["total"]:
            strip.append("🟩")
        elif e["completed"] > 0:
            strip.append("🟨")
        else:
            strip.append("🟥")

    streak = compute_streak(history)
    scored_days = [e for e in history if e["total"] > 0]
    avg_rate = (
        sum(e["completed"] / e["total"] for e in scored_days) / len(scored_days) if scored_days else 0
    )

    return "\n".join(
        [
            START_MARK,
            "",
            f"**🔥 연속 완주 스트릭:** {streak}일",
            "",
            f"**최근 {len(recent)}일:** {' '.join(strip) if strip else '(기록 없음)'}",
            "",
            f"**전체 평균 달성률:** {avg_rate * 100:.0f}% ({len(scored_days)}일 기록)",
            "",
            f"_마지막 업데이트: {now_kst().strftime('%Y-%m-%d %H:%M')} KST_",
            "",
            END_MARK,
        ]
    )


def update_readme(stats_block):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    if START_MARK in content and END_MARK in content:
        content = content.split(START_MARK)[0] + stats_block + content.split(END_MARK)[1]
    else:
        content = content.rstrip() + "\n\n" + stats_block + "\n"
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    gh = GitHub()
    today_str = today_kst().isoformat()

    issues = [
        i for i in fetch_due_today_issues(gh, today_str)
        if DIGEST_LABEL not in {l["name"] for l in i.get("labels", [])}
    ]
    total = len(issues)
    completed = sum(1 for i in issues if i["state"] == "closed")

    history = load_history()
    if history and history[-1]["date"] == today_str:
        history[-1] = {"date": today_str, "total": total, "completed": completed}
    else:
        history.append({"date": today_str, "total": total, "completed": completed})
    save_history(history)

    update_readme(render_stats(history))
    print(f"{today_str}: {completed}/{total} 완료 (누적 {len(history)}일)")


if __name__ == "__main__":
    main()
