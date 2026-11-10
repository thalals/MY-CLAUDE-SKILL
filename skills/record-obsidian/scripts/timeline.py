"""Claude·Codex 세션 원본(jsonl)에서 기록용 KST 시각을 뽑는다.

사용: python3 timeline.py [--session <세션 ID 앞부분 또는 jsonl 경로>] [--since "MM-DD HH:MM"] [--until "MM-DD HH:MM"] [--tools] [--span] [--width N]

- 기본은 현재 작업 디렉터리의 최근 Claude 세션이다. Codex 는 --session 경로 또는 ID 로 지정한다.
- --tools 는 도구 이름과 설명을, --span 은 날짜별 첫·마지막 실제 활동을 낸다.
- Codex response_item 만 읽어 event_msg 의 중복 발언을 제외한다. 주입된 지침·메타 정보는 활동이 아니다.
- 원본은 읽기만 한다. iter_events 와 last_activity 는 기록 알림 훅에서도 같은 기준으로 쓴다.
"""
import argparse
import datetime
import json
import os
import re
from pathlib import Path

KST = datetime.timezone(datetime.timedelta(hours=9))
PROJECTS = Path.home() / ".claude" / "projects"
CODEX_SESSIONS = Path.home() / ".codex" / "sessions"
HARNESS = ("<task-notification>", "<agent-message", "<system-reminder>", "<local-command", "Caveat:", "Base directory for this skill:", "# AGENTS.md instructions", "<environment_context>")
REJECT = ("The user doesn't want to proceed with this tool use", "The user doesn't want to take this action right now")
ANSWER = ("Your questions have been answered", "User has answered your questions")


def find_session(arg):
    if arg and Path(arg).exists():
        return Path(arg)
    if arg:
        hits = list(PROJECTS.glob(f"*/{arg}*.jsonl"))
        hits += list(CODEX_SESSIONS.rglob(f"*{arg}*.jsonl"))
    else:
        proj = PROJECTS / re.sub(r"[^A-Za-z0-9-]", "-", os.getcwd())
        hits = list(proj.glob("*.jsonl"))
    if not hits:
        raise FileNotFoundError(f"세션을 찾지 못했다: {arg or os.getcwd()}")
    return max(hits, key=lambda p: p.stat().st_mtime)


def text_of(c):
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(x.get("text", "") for x in c if isinstance(x, dict))
    return ""


def normalize(o):
    """두 원본 형식을 Claude 형태로 맞춘다. Codex 미러 이벤트는 읽지 않는다."""
    if o.get("type") != "response_item":
        return o
    p = o.get("payload") or {}
    typ = p.get("type")
    if typ == "message" and p.get("role") in ("user", "assistant"):
        blocks = [{**b, "type": "text"} for b in p.get("content", [])
                  if isinstance(b, dict) and b.get("type") in ("input_text", "output_text", "text")]
        return {"type": p["role"], "message": {"content": blocks}}
    if typ in ("function_call", "custom_tool_call"):
        raw = p.get("arguments", p.get("input", {}))
        try:
            args = json.loads(raw) if isinstance(raw, str) else raw
        except ValueError:
            args = {}
        return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": p.get("name"), "input": args if isinstance(args, dict) else {}}]}}
    if typ in ("function_call_output", "custom_tool_call_output"):
        return {"type": "user", "message": {"content": [{"type": "tool_result", "content": p.get("output", "")}]}}
    return {}


def iter_events(path):
    """실제 활동의 (KST datetime, 정규화 레코드)를 반환한다. 손상된 행은 건너뛴다."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                raw = json.loads(line)
                t = datetime.datetime.fromisoformat(raw["timestamp"].replace("Z", "+00:00"))
                if t.tzinfo is None:
                    continue
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
            o = normalize(raw)
            if o.get("isMeta") or o.get("isCompactSummary"):
                continue
            att = o.get("attachment") or {}
            if att.get("type") == "queued_command":
                s = text_of(att.get("prompt"))
                if s.strip() and not s.lstrip().startswith(HARNESS):
                    yield t.astimezone(KST), o
                continue
            if o.get("type") not in ("user", "assistant"):
                continue
            c = (o.get("message") or {}).get("content")
            blocks = [{"type": "text", "text": c}] if isinstance(c, str) else (c or [])
            blocks = [b for b in blocks if isinstance(b, dict) and
                      (b.get("type") in ("tool_use", "tool_result") or
                       b.get("type") == "text" and b.get("text", "").strip() and
                       not b["text"].lstrip().startswith(HARNESS))]
            if blocks:
                yield t.astimezone(KST), {**o, "message": {"content": blocks}}


def last_activity(path):
    return max((t for t, _ in iter_events(path)), default=None)


def one_line(s, width):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= width else s[:width - 1] + "…"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Claude·Codex 세션 원본에서 기록용 시각을 뽑는다")
    ap.add_argument("--session")
    ap.add_argument("--since", default="")
    ap.add_argument("--until", default="")
    ap.add_argument("--tools", action="store_true")
    ap.add_argument("--span", action="store_true")
    ap.add_argument("--width", type=int, default=120)
    a = ap.parse_args(argv)
    try:
        path = find_session(a.session)
    except FileNotFoundError as e:
        ap.exit(1, f"{e}\n")
    print(f"세션 {path.stem}")
    span = {}

    def emit(key, label, s):
        print(f"{key}  {label}  {one_line(s, a.width)}")

    for t, o in iter_events(path):
        key = t.strftime("%m-%d %H:%M")
        if (a.since and key < a.since) or (a.until and key > a.until):
            continue
        lo, hi = span.get(key[:5], (key, key))
        span[key[:5]] = (min(lo, key), max(hi, key))
        att = o.get("attachment") or {}
        if att.get("type") == "queued_command":
            emit(key, "발언", text_of(att.get("prompt")))
            continue
        for b in o["message"]["content"]:
            if o["type"] == "user":
                if b.get("type") == "tool_result":
                    s = text_of(b.get("content")).lstrip()
                    if s.startswith(ANSWER):
                        emit(key, "답변", s.split(":", 1)[-1])
                    elif s.startswith(REJECT):
                        m = re.search(r"the user said:\s*(.*)", s, re.S | re.I)
                        emit(key, "거절", m.group(1) if m else "도구 실행 거절")
                    continue
                if b.get("type") != "text":
                    continue
                s = b.get("text", "")
                if "<command-name>" in s or "<command-message>" in s:
                    n = re.search(r"<command-name>(.*?)</command-name>", s) or re.search(r"<command-message>(.*?)</command-message>", s)
                    g = re.search(r"<command-args>(.*?)</command-args>", s, re.S)
                    emit(key, "명령", (n.group(1) if n else "") + (" " + g.group(1).strip() if g and g.group(1).strip() else ""))
                elif s.startswith("[Request interrupted"):
                    emit(key, "중단", s)
                else:
                    emit(key, "발언", s)
            elif a.tools and b.get("type") == "tool_use":
                i = b.get("input") or {}
                d = i.get("description") or i.get("title") or i.get("file_path") or i.get("skill") or i.get("subject") or i.get("query") or ""
                emit(key, "도구", f"{b.get('name')} {d}")
    if a.span:
        print("날짜별 활동")
        for _, (lo, hi) in sorted(span.items()):
            print(f"  {lo} ~ {hi[6:]}")


if __name__ == "__main__":
    main()
