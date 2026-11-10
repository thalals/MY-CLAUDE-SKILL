"""record-obsidian 세션 훅. ~/.claude/settings.json 의 SessionEnd·SessionStart 훅이 부른다.

사용: python3 session_hook.py end|start   (stdin 으로 훅 입력 JSON 을 받는다)

- end(SessionEnd): 사용자 발언이 3개 이상이면 마지막 실제 활동 시각·원본 경로·종료 시각을 pending.tsv 에 남긴다.
- start(SessionStart): 남은 세션 가운데 daily history 날짜 노트의 sessions 에 그 끝 시각까지 기록되지 않은 것이 있으면
  hookSpecificOutput.additionalContext 로 기록을 제안하는 문구를 낸다. 기록됐거나 14일 지난 줄은 지운다.
- 어떤 실패도 세션을 막지 않는다(항상 exit 0). 원본 기록과 볼트는 읽기만 한다.
"""
import datetime, importlib.util, json, re, sys
from pathlib import Path

# Claude 설정은 python3 -I 로 실행하므로 같은 폴더를 명시적으로 로드한다.
_spec = importlib.util.spec_from_file_location("record_timeline", Path(__file__).with_name("timeline.py"))
timeline = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(timeline)

KST = datetime.timezone(datetime.timedelta(hours=9))
STATE = Path.home() / ".claude" / "record-obsidian" / "pending.tsv"
DAILY = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian/daily history"
HARNESS = ("<task-notification>", "<agent-message", "<system-reminder>", "<local-command", "<command-", "Caveat:", "Base directory for this skill:")
KEEP_DAYS = 14
MIN_UTTERANCES = 3


def user_utterances(transcript):
    n = 0
    for _, o in timeline.iter_events(transcript):
        if o.get("type") != "user":
            continue
        c = (o.get("message") or {}).get("content") or []
        texts = [b.get("text", "") for b in c if b.get("type") == "text"]
        n += sum(1 for s in texts if s.strip() and not s.lstrip().startswith(HARNESS))
    return n


def recorded_until():
    """세션 ID → 날짜 노트 sessions 에 기록된 범위 끝(KST datetime) 가운데 가장 늦은 것."""
    out = {}
    for d in DAILY.rglob("????-??-??.md"):
        year = int(d.stem[:4])
        text = d.read_text(encoding="utf-8")
        head = text.split("\n---", 1)[0] if text.startswith("---") else ""
        for sid, mm, dd, hh, mi in re.findall(r"·\s*([0-9a-f-]{8,})\s*·[^\"\n]*~\s*(\d{2})-(\d{2}) (\d{2}):(\d{2})", head):
            t = datetime.datetime(year, int(mm), int(dd), int(hh), int(mi), tzinfo=KST)
            out[sid] = max(out.get(sid, t), t)
    return out


def read_state():
    if not STATE.exists():
        return []
    rows = []
    for l in STATE.read_text(encoding="utf-8").splitlines():
        parts = l.split("\t")
        if len(parts) >= 4:
            rows.append(parts[:6])
    return rows


def write_state(rows):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text("".join("\t".join(r) + "\n" for r in rows), encoding="utf-8")


def on_end(data):
    sid, transcript = data.get("session_id", ""), data.get("transcript_path", "")
    if not sid or not transcript or not Path(transcript).exists():
        return
    n = user_utterances(transcript)
    if n < MIN_UTTERANCES:
        return
    activity = timeline.last_activity(transcript)
    if activity is None:
        return
    now = datetime.datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    rows = [r for r in read_state() if r[0] != sid]
    rows.append([sid, activity.strftime("%Y-%m-%d %H:%M"), data.get("cwd", ""), str(n), transcript, now])
    write_state(rows)


def on_start(data):
    rows = read_state()
    if not rows:
        return
    now = datetime.datetime.now(KST)
    done = recorded_until()
    keep = []
    for row in rows:
        sid, ended, cwd, n = row[:4]
        closed = row[5] if len(row) >= 6 else ended
        try:
            closed_at = datetime.datetime.strptime(closed, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
            t = datetime.datetime.strptime(ended, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
        except ValueError:
            continue
        if (now - closed_at).days > KEEP_DAYS:
            continue
        # 이전 4열 상태도 원본을 찾아 활동 시각으로 이행한다. 원본이 없으면 기존 시각을 보존한다.
        transcript = row[4] if len(row) >= 5 else ""
        try:
            path = Path(transcript) if transcript and Path(transcript).is_file() else timeline.find_session(sid)
            activity = timeline.last_activity(path)
            if activity:
                t = activity.replace(second=0, microsecond=0)
                transcript = str(path)
        except (OSError, ValueError):
            pass
        rec = done.get(sid)
        if rec and rec >= t:
            continue
        keep.append([sid, t.strftime("%Y-%m-%d %H:%M"), cwd, n, transcript, closed])
    write_state(keep)
    if not keep:
        return
    items = "; ".join(f"{r[0][:8]} ({Path(r[2]).name or r[2]}, 마지막 활동 {r[1][5:]}, 사용자 발언 {r[3]}개)" for r in sorted(keep, key=lambda r: r[1], reverse=True)[:3])
    more = f" 외 {len(keep) - 3}개" if len(keep) > 3 else ""
    text = (f"record-obsidian: Obsidian daily history 에 아직 기록하지 않은 지난 세션이 {len(keep)}개 있다 — {items}{more}. "
            "사용자의 첫 요청을 먼저 처리하고, 응답 끝에 이 세션들을 기록할지 한 줄로 묻는다. 기록하면 record-obsidian 스킬로 한다.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        data = json.loads(sys.stdin.read() or "{}")
        {"end": on_end, "start": on_start}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda d: None)(data)
    except Exception:
        pass
    sys.exit(0)
