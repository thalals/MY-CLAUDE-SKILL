"""record-obsidian 1단계 시작 출력. 한 번의 호출로 daily 를 쓰는 데 필요한 것을 낸다.

사용: python3 start.py [--session <세션 ID 앞부분 또는 jsonl 경로>] [--vault <볼트 경로>]

- 오늘 날짜·시각(KST), daily history/SKILL.md 전문, 열린 제안과 마지막 전체 검진,
  오늘 날짜 노트의 frontmatter 와 주제(H2) 줄 번호·설명 줄, 이 세션이 이미 기록된 범위 끝,
  그 뒤의 타임라인(timeline.py --span)을 낸다.
- 세션은 timeline.py 와 같은 기준으로 찾는다(기본은 현재 작업 디렉터리의 최근 Claude 세션).
- 파일은 읽기만 한다. 세션 원본이 없으면 그렇다고 쓰고 타임라인을 건너뛴다.
"""

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import timeline  # noqa: E402

VAULT = Path.home() / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents" / "Obsidian"
WEEK = "월화수목금토일"
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
RANGE = re.compile(r"(\d{2}-\d{2} (?:\d{2}:\d{2}|미확인)) ~ (\d{2}-\d{2} (?:\d{2}:\d{2}|미확인))")


def head(title):
    print(f"\n===== {title}")


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else ""


def proposals(vault, today):
    text = (vault / "proposals.md").read_text(encoding="utf-8")
    m = re.search(r"마지막 전체 검진:\s*(\d{4}-\d{2}-\d{2})", text)
    if m:
        days = (today - datetime.date.fromisoformat(m.group(1))).days
        note = " · 7일 넘음: 보고 끝에서 전체 검진을 할지 묻는다" if days > 7 else ""
        print(f"마지막 전체 검진: {m.group(1)} ({days}일 전){note}")
    else:
        print("마지막 전체 검진: 없음 · 보고 끝에서 전체 검진을 할지 묻는다")
    opened = []
    for block in re.split(r"^## ", text, flags=re.M)[1:]:
        title = block.splitlines()[0].strip()
        if not re.match(r"\d{4}-\d{2}-\d{2} ", title):
            continue
        state = re.search(r"^- 상태:\s*(.+)$", block, re.M)
        opened.append(f"- {title} · 상태: {state.group(1).strip() if state else '없음'}")
    print("\n".join(opened) if opened else "열린 제안 없음")


def today_note(vault, now):
    rel = f"daily history/{now:%Y}/{now:%m}/{now:%Y-%m-%d}.md"
    path = vault / rel
    print(rel)
    if not path.exists():
        print("없음 · 새로 만든다")
        return
    text = path.read_text(encoding="utf-8")
    print(f"있음 · {len(text.encode())} bytes · 병합한다. 병합할 주제 절만 읽는다")
    fm = frontmatter(text)
    for line in fm.splitlines():
        s = line.strip()
        if s.startswith("- ") and len(s) > 200:
            s = s[:200] + " …"
        print(f"  {s}" if line.startswith(" ") else s)
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("## ") or line == "## 목차":
            continue
        desc = next((x for x in lines[i + 1:i + 4] if x.strip() and not x.startswith("#")), "")
        print(f"{i + 1}: {line}")
        if desc:
            print(f"    {desc[:240]}")


def recorded_end(vault, sid):
    """daily 노트 sessions 줄에서 이 세션의 기록 범위를 찾는다. (파일, 범위) 의 가장 최근 것."""
    hits = []
    for f in sorted((vault / "daily history").rglob("????-??-??.md")):
        for line in frontmatter(f.read_text(encoding="utf-8")).splitlines():
            if sid in line:
                m = RANGE.search(line)
                if m:
                    hits.append((f.stem, m.group(1), m.group(2)))
    return hits[-1] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session")
    ap.add_argument("--vault", default=str(VAULT))
    a = ap.parse_args()
    vault = Path(a.vault)
    now = datetime.datetime.now(timeline.KST)

    head("오늘")
    print(f"{now:%Y-%m-%d %H:%M} ({WEEK[now.weekday()]}) KST")

    head("daily history/SKILL.md (규칙 전문)")
    print((vault / "daily history" / "SKILL.md").read_text(encoding="utf-8").rstrip())

    head("proposals.md")
    proposals(vault, now.date())

    head("오늘 날짜 노트")
    today_note(vault, now)

    head("이 세션")
    try:
        src = timeline.find_session(a.session)
    except FileNotFoundError as e:
        print(f"세션 원본 없음({e}). 타임라인과 sessions 의 시각은 'MM-DD 미확인' 으로 쓰고 보고에서 묻는다")
        rec = recorded_end(vault, a.session) if a.session else None
        print(f"기록됨: [[{rec[0]}]] {rec[1]} ~ {rec[2]} · 이미 기록한 대화는 그 날짜 노트와 대조해 거른다" if rec else "날짜 노트 sessions 에 이 세션 없음")
        return
    m = UUID.search(src.name)
    sid = m.group(0) if m else src.stem
    kind = "Codex" if ".codex" in str(src) else "Claude Code"
    print(f"{kind} · {sid}")
    rec = recorded_end(vault, sid)
    since = None
    if rec:
        since = rec[2] if "미확인" not in rec[2] else None
        tail = "그 뒤의 대화만 기록한다" if since else "범위 끝이 미확인이라 타임라인을 처음부터 낸다. 이미 기록한 대화는 그 날짜 노트와 대조해 거른다"
        print(f"기록됨: [[{rec[0]}]] {rec[1]} ~ {rec[2]} · {tail}")
    else:
        print("아직 기록 안 됨 · 세션 전체를 기록한다")

    head(f"타임라인 (--span{' --since ' + since if since else ''})")
    cmd = [sys.executable, str(HERE / "timeline.py"), "--session", str(src), "--span"]
    if since:
        cmd += ["--since", since]
    out = subprocess.run(cmd, capture_output=True, text=True)
    print((out.stdout or out.stderr).rstrip() or "(이 범위에 활동 없음)")


if __name__ == "__main__":
    main()
