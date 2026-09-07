"""Tally today's completion rate and refresh the README stats block + streak.

Runs once a day (23:50 KST). Counts every issue tagged with today's date
(via the "(YYYY-MM-DD)" title suffix), excluding the digest issue itself
and anything labeled "skipped" (those were marked "해당 없음", not a real
miss, so they shouldn't hurt the streak).
"""
import json
import os
import re

from ghutil import GitHub, DIGEST_LABEL, SKIPPED_LABEL, extract_due_date, today_kst

HISTORY_PATH = "data/history.json"
README_PATH = "README.md"
STATS_START = "<!-- STATS:START -->"
STATS_END = "<!-- STATS:END -->"


def load_history():
    if not os.path.exists(HISTORY_PATH):
        return []
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def tally_today(gh, today):
    total = 0
    completed = 0
    for issue in gh.list_issues(state="all"):
        labels = {l["name"] for l in issue.get("labels", [])}
        if DIGEST_LABEL in labels or SKIPPED_LABEL in labels:
            continue
        due = extract_due_date(issue["title"])
        if due != today:
            continue
        total += 1
        if issue["state"] == "closed":
            completed += 1
    return total, completed


def upsert_today(history, today_str, total, completed):
    for entry in history:
        if entry["date"] == today_str:
            entry["total"] = total
            entry["completed"] = completed
            return history
    history.append({"date": today_str, "total": total, "completed": completed})
    history.sort(key=lambda e: e["date"])
    return history


def compute_streak(history):
    streak = 0
    for entry in reversed(history):
        if entry["total"] > 0 and entry["completed"] == entry["total"]:
            streak += 1
        else:
            break
    return streak


def render_stats_block(history, streak):
    recent = history[-14:]
    strip = "".join(
        "🟩" if e["total"] > 0 and e["completed"] == e["total"]
        else ("🟨" if e["completed"] > 0 else "⬜")
        for e in recent
    )
    if recent:
        avg = sum(e["completed"] for e in recent) / max(sum(e["total"] for e in recent), 1) * 100
    else:
        avg = 0
    lines = [
        STATS_START,
        "",
        f"**연속 완료 스트릭:** {streak}일 🔥",
        "",
        f"**최근 {len(recent)}일:** {strip}",
        "",
        f"**최근 {len(recent)}일 평균 완료율:** {avg:.0f}%",
        "",
        STATS_END,
    ]
    return "\n".join(lines)


def update_readme(stats_block):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(re.escape(STATS_START) + r".*?" + re.escape(STATS_END), re.DOTALL)
    if pattern.search(content):
        content = pattern.sub(stats_block, content)
    else:
        content += f"\n\n{stats_block}\n"
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    gh = GitHub()
    today = today_kst()
    today_str = today.isoformat()

    total, completed = tally_today(gh, today)
    history = load_history()
    history = upsert_today(history, today_str, total, completed)
    save_history(history)

    streak = compute_streak(history)
    stats_block = render_stats_block(history, streak)
    update_readme(stats_block)

    print(f"{today_str}: {completed}/{total} completed, streak={streak}")


if __name__ == "__main__":
    main()
