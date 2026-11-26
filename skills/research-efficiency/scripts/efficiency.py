#!/usr/bin/env python3
"""효율 연구실 도구. Claude Code 세션 원본(jsonl)에서 지시와 반복 절차의 비용을 재고(이 파일), 연구 장부를 다룬다(lab.py).

재기
  efficiency.py runs  [--skill 이름 ...] [--days N | --session ID] [--turns N] [--save]
                                                    스킬 실행 한 번의 호출 수, 맥락, 종류별 토큰(본 대화 + 서브에이전트)
  efficiency.py stats --skill 이름 ... [--since 날짜] [--until 날짜] [--model 이름일부] [--ctx-below N] [--ctx-above N]
                      [--session ID ...] [--not-session ID ...] [--not-run "YYYY-MM-DD HH:MM" ...]
                                                    runs.tsv 의 구간별 중앙값·최소·최대(바꾸기 전후 비교).
                                                    날짜는 "YYYY-MM-DD HH:MM" 까지 줄 수 있고 --until 날짜는 그 날 0시 전까지다
  efficiency.py trend --skill 이름 ... [--by month|week]
                                                    runs.tsv 의 기간별 추이(쌓인 측정으로 나아지는지 본다)
  efficiency.py carry --session ID [--skill 이름 [--nth K] | --agent ID] [--top N] [--list]
                                                    맥락에 들어온 것과 그것을 다시 읽은 값. --list 는 호출을 차례대로 낸다
  efficiency.py after --session ID --skill 이름 [--nth K] [--n 5]
                                                    실행 뒤의 사용자 발언(정정 요청 수를 세는 품질 확인)
  efficiency.py base  [--session ID | --project 이름일부] [--save]   늘 실리는 맥락(세션 첫 호출)의 크기와 구성
  efficiency.py base  --list [--days N] [--project 이름일부]           세션마다 첫 호출 크기(추이)
  efficiency.py reads [--days N]                    지시 파일(스타일, 스킬, 볼트 규칙)을 참조한 횟수
  efficiency.py total --session ID                  세션 전체에서 본 대화와 서브에이전트가 쓴 것
  efficiency.py check --session ID                  하니스 자체 집계(cost-state)와 이 도구 합계의 차이

장부 (자세한 쓰임은 scripts/lab.py 머리말)
  efficiency.py status | find | show | new | set | lint | index | close

--save 는 스킬 폴더 research/ 의 runs.tsv(다시 잰 줄은 새 값으로 바꾼다), base.tsv(새 세션만 더한다)에 적는다.
지표 정의와 함정은 reference/metrics.md, 장부 형식은 reference/ledger.md 에 있다. 출력에는 명령 설명이 섞이므로 장부에는 숫자만 옮긴다.
"""
import argparse
import json
import re
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOME = Path.home()
PROJECTS = HOME / ".claude" / "projects"
SKILLS = HOME / ".claude" / "skills"
ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "research"
STYLE = HOME / "Library/Mobile Documents/com~apple~CloudDocs/claude/style"
VAULT = HOME / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian"
KST = timezone(timedelta(hours=9))

# 정가($/백만 토큰): 입력, 5분 캐시 쓰기, 1시간 캐시 쓰기, 캐시 읽기, 출력. 2026-11-16 Anthropic 가격표.
# 종류가 다른 토큰을 한 숫자로 견주는 가중치다. 구독 한도의 계산식이 아니다.
PRICES = {
    "claude-fable-5-2": (8, 10, 16, 0.20, 40),
    "claude-fable-5-1": (10, 12.5, 20, 0.25, 50),
    "claude-fable-5": (10, 12.5, 20, 1, 50),
    "claude-opus-5-5": (4, 5, 8, 0.20, 20),
    "claude-opus-5": (5, 6.25, 10, 0.50, 25),
    "claude-opus-4-8": (5, 6.25, 10, 0.50, 25),
    "claude-sonnet-5-5": (2, 2.5, 4, 0.10, 10),
    "claude-sonnet-5": (2, 2.5, 4, 0.20, 10),
    "claude-haiku-5-5": (0.10, 0.125, 0.20, 0.01, 0.50),
}
HAIKU_OVER_100K = (0.50, 0.625, 1, 0.05, 2.50)
REF = PRICES["claude-opus-5-5"]  # 기준 단가. 모델이 다른 실행을 같은 단가로 쳐서 구조만 견줄 때 쓴다.
METRICS_VERSION = "1"  # 지표 정의의 판. 실행 구간이나 지표의 정의를 바꾸면 올리고 reference/metrics.md 에 적는다. runs.tsv 의 mv 열에 남는다.

RUN_COLS = ["start_kst", "skill", "session", "how", "cc_version", "model", "main_calls", "ctx_first", "ctx_max",
            "main_cum", "main_read", "main_write", "main_out", "main_think", "main_tools", "first_write",
            "sub_n", "sub_calls", "sub_ctx_max", "sub_cum", "sub_write", "sub_out", "sub_think",
            "total_cum", "total_usd", "total_ref_usd", "note", "mv"]
BASE_COLS = ["start_kst", "session", "project", "cc_version", "first_ctx_tokens", "chars_total", "system", "tools",
             "n_tools", "claude_md_global", "claude_md_project", "memory", "hook", "deferred_tools", "mcp",
             "skills_list", "n_skills", "agents_list", "other"]
HARNESS = ("<task-notification>", "<agent-message", "<system-reminder>", "<local-command", "Caveat:",
           "Base directory for this skill:", "[Request interrupted")
CMD = re.compile(r"<command-name>/?([^<\s]+)</command-name>")


def price(model, ctx):
    for key in sorted(PRICES, key=len, reverse=True):
        if model.startswith(key):
            return HAIKU_OVER_100K if key == "claude-haiku-5-5" and ctx > 100_000 else PRICES[key]
    return None


def usd(c):
    p = price(c["model"], c["ctx"])
    if p is None:
        return None
    return (c["inp"] * p[0] + c["w5m"] * p[1] + c["w1h"] * p[2] + c["read"] * p[3] + c["out"] * p[4]) / 1e6


def ref_usd(c):
    return (c["inp"] * REF[0] + c["w5m"] * REF[1] + c["w1h"] * REF[2] + c["read"] * REF[3] + c["out"] * REF[4]) / 1e6


def kst(ts, fmt="%Y-%m-%d %H:%M:%S"):
    if not ts:
        return "?"
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(KST).strftime(fmt)


def n(x):
    return f"{x:,}"


def load(path):
    """본 대화·서브에이전트 원본에서 user, assistant, system, attachment 줄만 읽는다."""
    rows = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            if line.startswith('{"type":"'):
                if line[9:line.find('"', 9)] not in ("user", "assistant", "system", "attachment"):
                    continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                r["_i"] = i
                rows.append(r)
    return rows


def calls_of(rows, main=True):
    """API 호출 목록. 한 호출이 여러 줄로 나뉘어 있어 message.id 로 묶는다."""
    by, order = {}, []
    for r in rows:
        if r.get("type") != "assistant" or (main and r.get("isSidechain")):
            continue
        m = r.get("message") or {}
        if m.get("model") == "<synthetic>":
            continue
        mid = m.get("id") or r.get("uuid")
        c = by.get(mid)
        if c is None:
            c = by[mid] = {"i": r["_i"], "ts": r.get("timestamp"), "model": m.get("model") or "", "tools": [], "u": {}}
            order.append(c)
        c["u"] = m.get("usage") or c["u"]
        for b in m.get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use" and all(b.get("id") != t.get("id") for t in c["tools"]):
                c["tools"].append(b)
    out = []
    for c in order:
        u = c.pop("u")
        c["inp"] = u.get("input_tokens") or 0
        c["read"] = u.get("cache_read_input_tokens") or 0
        c["write"] = u.get("cache_creation_input_tokens") or 0
        c["w1h"] = (u.get("cache_creation") or {}).get("ephemeral_1h_input_tokens") or 0
        c["w5m"] = c["write"] - c["w1h"]
        c["out"] = u.get("output_tokens") or 0
        c["think"] = (u.get("output_tokens_details") or {}).get("thinking_tokens") or 0
        c["ctx"] = c["inp"] + c["read"] + c["write"]
        if c["ctx"] or c["out"]:
            out.append(c)
    return out


def agg(calls):
    a = {k: sum(c[k] for c in calls) for k in ("inp", "read", "write", "out", "think")}
    costs = [usd(c) for c in calls]
    a.update(n=len(calls), cum=sum(c["ctx"] for c in calls), tools=sum(len(c["tools"]) for c in calls),
             first=calls[0]["ctx"] if calls else 0, max=max((c["ctx"] for c in calls), default=0),
             first_write=calls[0]["write"] if calls else 0, usd=sum(x for x in costs if x is not None), ref=sum(ref_usd(c) for c in calls),
             unpriced=sum(1 for x in costs if x is None), models=Counter(c["model"] for c in calls))
    return a


def text_of(c):
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    return ""


def human_rows(rows):
    """사용자가 보낸 발언(스킬 명령 포함). 도구 결과, 알림, 요약, 로컬 명령은 뺀다."""
    users = [r for r in rows if r.get("type") == "user" and not r.get("isSidechain")]
    has_origin = any(isinstance(r.get("origin"), dict) for r in users)
    out = []
    for r in users:
        if r.get("isMeta") or r.get("isCompactSummary"):
            continue
        c = (r.get("message") or {}).get("content")
        if isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
            continue
        if has_origin:
            if not (isinstance(r.get("origin"), dict) and r["origin"].get("kind") == "human"):
                continue
        elif text_of(c).lstrip().startswith(HARNESS):
            continue
        out.append(r)
    return out


def invocations(rows, names, humans):
    """스킬을 부른 지점. names 가 None 이면 모든 스킬."""
    hit = lambda s: names is None or s in names or s.split(":")[-1] in names
    results = {}
    for r in rows:
        c = (r.get("message") or {}).get("content") if r.get("type") == "user" else None
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    results[b.get("tool_use_id")] = r
    hidx = {r["_i"] for r in humans}
    inv = []
    for r in rows:
        if r.get("type") == "user" and r["_i"] in hidx:
            m = CMD.search(text_of(r["message"].get("content")))
            if m and hit(m.group(1)):
                inv.append({"i": r["_i"], "ts": r.get("timestamp"), "skill": m.group(1), "how": "명령", "agent": None})
        elif r.get("type") == "assistant" and not r.get("isSidechain"):
            for b in (r.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill":
                    s = str((b.get("input") or {}).get("skill", "")).lstrip("/")
                    if s and hit(s):
                        res = (results.get(b.get("id")) or {}).get("toolUseResult")
                        inv.append({"i": r["_i"], "ts": r.get("timestamp"), "skill": s, "how": "Skill 도구",
                                    "agent": res.get("agentId") if isinstance(res, dict) else None})
    return sorted(inv, key=lambda x: x["i"])


def subagents(path):
    d = path.with_suffix("") / "subagents"
    out = {}
    for f in sorted(d.glob("agent-*.jsonl")):
        meta = {}
        for suffix in (".meta.json", ".forked-skill.json"):
            p = d / (f.stem + suffix)
            if p.exists():
                try:
                    meta.update(json.loads(p.read_text(encoding="utf-8")))
                except ValueError:
                    pass
        out[f.stem[6:]] = {"path": f, "meta": meta}
    return out


def first_ts(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.search(r'"timestamp":"([^"]+)"', line)
            if m:
                return m.group(1)
    return None


def recent(calls):
    """마지막 호출이 10분 안인가. 원본 파일의 수정 시각은 호출이 아닌 줄로도 바뀌므로 호출 시각으로 본다."""
    cut = (datetime.now(timezone.utc) - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S")
    return any((c["ts"] or "")[:19] >= cut for c in calls)


def measure_runs(path, names, turns=1):
    """스킬 실행 구간: 스킬 호출부터 다음 사용자 발언 전까지. 포크 스킬은 그 포크 에이전트만 센다."""
    rows = load(path)
    humans = human_rows(rows)
    invs = invocations(rows, names, humans)
    if not invs:
        return []
    calls, subs, cache = calls_of(rows), subagents(path), {}
    hidx = [r["_i"] for r in humans]
    version = next((r.get("version") for r in rows if r.get("version")), "")

    def sub_calls(aid):
        if aid not in cache:
            cache[aid] = calls_of(load(subs[aid]["path"]), main=False)
        return cache[aid]

    runs = []
    for inv in invs:
        start = inv["i"]
        later = [h for h in hidx if h > start]
        end = later[turns - 1] if len(later) >= turns else 10 ** 12
        how = inv["how"]
        if inv["agent"]:
            main, agents, how = [], [inv["agent"]], "포크"
        else:
            main = [c for c in calls if start < c["i"] < end]
            ids = {b.get("id") for c in main for b in c["tools"]}
            agents = [a for a, s in subs.items() if s["meta"].get("toolUseId") in ids]
            for r in rows:
                res = r.get("toolUseResult")
                if start < r["_i"] < end and isinstance(res, dict) and res.get("agentId") in subs and res["agentId"] not in agents:
                    agents.append(res["agentId"])
            if how == "명령":
                t1 = next((r.get("timestamp") for r in humans if r["_i"] == end), None)
                for a, s in subs.items():
                    st = first_ts(s["path"]) if s["meta"].get("skillName") == inv["skill"] and a not in agents else None
                    if st and inv["ts"] and inv["ts"] <= st and (t1 is None or st < t1):
                        agents.append(a)
                        how = "명령·포크"
            agents = [a for a in agents if subs[a]["meta"].get("skillName") in (None, inv["skill"])]
        seen, queue = list(dict.fromkeys(agents)), list(agents)
        while queue:
            a = queue.pop(0)
            if a not in subs:
                continue
            ids = {b.get("id") for c in sub_calls(a) for b in c["tools"]}
            for a2, s2 in subs.items():
                if a2 not in seen and s2["meta"].get("toolUseId") in ids:
                    seen.append(a2)
                    queue.append(a2)
        seen = [a for a in seen if a in subs]
        sub = [c for a in seen for c in sub_calls(a)]
        if main or sub:
            runs.append({"skill": inv["skill"], "ts": inv["ts"], "i": start, "how": how, "session": path.stem, "version": version,
                         "live": (end == 10 ** 12 and recent(main)) or any(recent(sub_calls(a)) for a in seen),
                         "main": main, "sub": sub, "agents": seen, "subs": subs, "sub_calls": {a: sub_calls(a) for a in seen}})
    return runs


def run_row(run):
    m, s = agg(run["main"]), agg(run["sub"])
    model = (m["models"] or s["models"]).most_common(1)[0][0]
    return {"start_kst": kst(run["ts"]), "skill": run["skill"], "session": run["session"][:8], "how": run["how"],
            "cc_version": run["version"], "model": model, "main_calls": m["n"], "ctx_first": m["first"], "ctx_max": m["max"],
            "main_cum": m["cum"], "main_read": m["read"], "main_write": m["write"], "main_out": m["out"],
            "main_think": m["think"], "main_tools": m["tools"], "first_write": m["first_write"],
            "sub_n": len(run["agents"]), "sub_calls": s["n"], "sub_ctx_max": s["max"], "sub_cum": s["cum"],
            "sub_write": s["write"], "sub_out": s["out"], "sub_think": s["think"], "total_cum": m["cum"] + s["cum"],
            "total_usd": f"{m['usd'] + s['usd']:.2f}", "total_ref_usd": f"{m['ref'] + s['ref']:.2f}",
            "mv": METRICS_VERSION,
            "note": " · ".join(x for x in ("가격 모르는 모델 있음" if m["unpriced"] + s["unpriced"] else "",
                                         "마지막 호출이 10분 안(진행 중일 수 있음)" if run.get("live") else "") if x)}


def line_of(label, a):
    return (f"  {label}  호출 {a['n']}  맥락 {n(a['first'])}→최대 {n(a['max'])}  누적 입력 {n(a['cum'])}"
            f"  (읽기 {n(a['read'])} · 쓰기 {n(a['write'])} · 안 실린 입력 {n(a['inp'])})"
            f"  출력 {n(a['out'])}(생각 {n(a['think'])})  도구 {a['tools']}  ${a['usd']:.2f}  기준 단가 ${a['ref']:.2f}")


def print_run(run):
    row = run_row(run)
    print(f"{row['start_kst']}  {run['skill']}  세션 {row['session']}  {run['how']}  {row['model']}")
    if run["main"]:
        m = agg(run["main"])
        print(line_of("본 대화", m) + f"  첫 호출 캐시 쓰기 {n(m['first_write'])}")
    for a in run["agents"]:
        meta = run["subs"][a]["meta"]
        label = meta.get("description") or meta.get("skillName") or a
        print(line_of(f"서브 [{a[:8]} · {label[:28]} · {meta.get('model', '본 대화 모델')}]", agg(run["sub_calls"][a])))
    print(f"  합계  누적 입력 {n(row['total_cum'])}  정가 환산 ${row['total_usd']}  기준 단가 환산 ${row['total_ref_usd']}  {row['note']}")


def read_tsv(p):
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").splitlines()
    head = lines[0].split("\t") if lines else []
    return [dict(zip(head, ln.split("\t"))) for ln in lines[1:] if ln.strip()]


def append_tsv(p, cols, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    new = not p.exists()
    with open(p, "a", encoding="utf-8") as fh:
        if new:
            fh.write("\t".join(cols) + "\n")
        for r in rows:
            fh.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")


def find_session(arg):
    p = Path(arg).expanduser()
    if p.is_file():
        return p
    hits = sorted(PROJECTS.glob(f"*/{arg}*.jsonl"))
    if len(hits) != 1:
        sys.exit(f"세션을 하나로 정하지 못했다: {arg} → {len(hits)}개")
    return hits[0]


def recent_sessions(days):
    cut = time.time() - days * 86400
    return sorted((p for p in PROJECTS.glob("*/*.jsonl") if p.stat().st_mtime >= cut), key=lambda p: p.stat().st_mtime)


def user_skills():
    return sorted(d.name for d in SKILLS.iterdir() if (d / "SKILL.md").is_file())


def collect_runs(paths, names, turns=1):
    runs, seen = [], set()
    for p in paths:
        for run in measure_runs(p, names, turns):
            key = (run["skill"], run["ts"])
            if key not in seen:
                seen.add(key)
                runs.append(run)
    return sorted(runs, key=lambda r: r["ts"] or "")


def cmd_runs(a):
    names = set(a.skill) if a.skill else set(user_skills())
    paths = [find_session(a.session)] if a.session else recent_sessions(a.days)
    runs = collect_runs(paths, names, a.turns)
    rows = [run_row(r) for r in runs]
    for run in runs:
        print_run(run)
    print(f"\n실행 {len(runs)}번 (세션 {len(paths)}개에서 찾음, 구간은 스킬 호출부터 사용자 발언 {a.turns}번 전까지)")
    for skill in sorted({r["skill"] for r in rows}):
        rs = [r for r in rows if r["skill"] == skill]
        print(f"  {skill}: {len(rs)}번, 누적 입력 중앙값 {n(int(statistics.median(r['total_cum'] for r in rs)))}"
              f" (최소 {n(min(r['total_cum'] for r in rs))} ~ 최대 {n(max(r['total_cum'] for r in rs))}),"
              f" 정가 환산 중앙값 ${statistics.median(float(r['total_usd']) for r in rs):.2f},"
              f" 기준 단가 환산 중앙값 ${statistics.median(float(r['total_ref_usd']) for r in rs):.2f}")
    if a.save:
        key = lambda r: (r["start_kst"], r["skill"])
        old, fresh = read_tsv(RESEARCH / "runs.tsv"), {key(r): r for r in rows}
        for r in old:
            r["mv"] = r.get("mv") or "1"
        same = [r for r in old if key(r) in fresh]
        changed = sum(1 for r in same if any(str(fresh[key(r)].get(c, "")) != r.get(c, "") for c in RUN_COLS))
        merged = sorted([r for r in old if key(r) not in fresh] + list(fresh.values()), key=key)
        (RESEARCH / "runs.tsv").unlink(missing_ok=True)
        append_tsv(RESEARCH / "runs.tsv", RUN_COLS, merged)
        print(f"runs.tsv: 새로 {len(fresh) - len(same)}줄, 값이 바뀐 {changed}줄, 모두 {len(merged)}줄")


def cmd_stats(a):
    rows = [r for r in read_tsv(RESEARCH / "runs.tsv") if r["skill"] in a.skill
            and (not a.since or r["start_kst"] >= a.since) and (not a.until or r["start_kst"] < a.until)
            and (not a.session or r["session"] in a.session) and (not a.not_session or r["session"] not in a.not_session)
            and not any(r["start_kst"].startswith(t) for t in (a.not_run or []))
            and (not a.model or a.model in r["model"]) and (a.ctx_below is None or int(r["ctx_first"] or 0) < a.ctx_below)
            and (a.ctx_above is None or int(r["ctx_first"] or 0) >= a.ctx_above)]
    if not rows:
        sys.exit("그 조건의 줄이 runs.tsv 에 없다")
    print(f"{', '.join(a.skill)}: {len(rows)}번 ({rows[0]['start_kst'][:16]} ~ {rows[-1]['start_kst'][:16]}), 모델 "
          + ", ".join(f"{k} {v}" for k, v in Counter(r["model"] for r in rows).most_common()))
    live = sum(1 for r in rows if "진행 중" in r.get("note", ""))
    if live:
        print(f"  진행 중일 수 있는 줄 {live}개가 들어 있다. 끝난 뒤 runs --save 로 다시 재고 본다.")
    mvs = Counter(r.get("mv") or "1" for r in rows)
    if len(mvs) > 1:
        print("  지표 정의의 판이 다른 줄이 섞여 있다: " + ", ".join(f"판 {k} {v}줄" for k, v in sorted(mvs.items())) + ". 같은 판끼리만 견준다.")
    cols = [("total_cum", "누적 입력 합계"), ("total_ref_usd", "기준 단가 환산 $"), ("total_usd", "정가 환산 $"),
            ("main_cum", "본 대화 누적 입력"), ("main_calls", "본 대화 호출"), ("ctx_first", "시작 맥락"),
            ("ctx_max", "본 대화 최대 맥락"), ("first_write", "첫 호출 캐시 쓰기"), ("main_out", "본 대화 출력"),
            ("sub_calls", "서브 호출"), ("sub_cum", "서브 누적 입력"), ("sub_out", "서브 출력")]
    for col, label in cols:
        v = sorted(float(r[col] or 0) for r in rows)
        f = (lambda x: f"{x:,.2f}") if col.endswith("usd") else (lambda x: f"{int(x):,}")
        print(f"  {label}: 중앙값 {f(statistics.median(v))} · 최소 {f(v[0])} · 최대 {f(v[-1])} · 합 {f(sum(v))}")


def cmd_trend(a):
    """runs.tsv 의 기간별 추이. 진행 중으로 적힌 줄은 뺀다."""
    rows = [r for r in read_tsv(RESEARCH / "runs.tsv") if r["skill"] in a.skill and "진행 중" not in r.get("note", "")]
    if not rows:
        sys.exit("그 스킬의 줄이 runs.tsv 에 없다")

    def period(r):
        iso = datetime.strptime(r["start_kst"][:10], "%Y-%m-%d").isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}" if a.by == "week" else r["start_kst"][:7]

    print(f"{', '.join(a.skill)}: {len(rows)}번. 기간 · 횟수 · 기준 단가 환산 중앙값(합) · 누적 입력 중앙값 · 본 대화 호출 중앙값 · 시작 맥락 중앙값 · 서브 호출 중앙값 · 모델")
    for p in sorted({period(r) for r in rows}):
        rs = [r for r in rows if period(r) == p]
        med = lambda col: statistics.median(float(r[col] or 0) for r in rs)
        print(f"  {p}  {len(rs):>3}번  ${med('total_ref_usd'):.2f} (합 ${sum(float(r['total_ref_usd'] or 0) for r in rs):.2f})  {int(med('total_cum')):>12,}"
              f"  {med('main_calls'):>5g}  {int(med('ctx_first')):>9,}  {med('sub_calls'):>4g}  "
              + ", ".join(f"{k.replace('claude-', '')} {v}" for k, v in Counter(r["model"] for r in rs).most_common(3)))


def cmd_check(a):
    """하니스가 원본에 남긴 자체 집계(cost-state)와 이 도구의 합계를 견준다."""
    path = find_session(a.session)
    idx, usage = None, {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            if line.startswith('{"type":"cost-state"'):
                idx, usage = i, json.loads(line).get("modelUsage") or {}
    if idx is None:
        sys.exit("이 세션 원본에는 하니스 집계(cost-state)가 없다. 세션을 닫았다가 이어 열 때 남는다.")
    rows = load(path)
    cut = max((r.get("timestamp") or "" for r in rows if r["_i"] < idx), default="")
    calls = [c for c in calls_of(rows) if c["i"] < idx]
    for sub in subagents(path).values():
        calls += [c for c in calls_of(load(sub["path"]), main=False) if (c["ts"] or "") <= cut]
    print(f"세션 {path.stem[:8]}: 하니스 집계 시점은 원본 {idx}행({kst(cut)} 무렵). 도구는 그 전의 본 대화와 서브에이전트 호출을 더했다.")
    for model, h in usage.items():
        t = agg([c for c in calls if c["model"].startswith(model)])
        print(f"  {model}: 도구가 찾은 호출 {t['n']}번")
        for label, hv, tv in (("캐시 읽기", h.get("cacheReadInputTokens", 0), t["read"]), ("캐시 쓰기", h.get("cacheCreationInputTokens", 0), t["write"]),
                              ("안 실린 입력", h.get("inputTokens", 0), t["inp"]), ("출력", h.get("outputTokens", 0), t["out"]),
                              ("정가 환산 $", h.get("costUSD", 0), t["usd"])):
            f = (lambda x: f"{x:,.4f}") if label.endswith("$") else (lambda x: f"{int(x):,}")
            print(f"    {label}: 하니스 {f(hv)} · 도구 {f(tv)} · 차이 {(tv - hv) / hv if hv else 0:+.1%}")


def cmd_after(a):
    """실행 뒤의 사용자 발언. 정정 요청이 몇 번인지 읽고 세는 품질 확인용이다."""
    path = find_session(a.session)
    runs = measure_runs(path, set(a.skill))
    if len(runs) < a.nth:
        sys.exit(f"그 스킬 실행은 {len(runs)}번뿐이다")
    run = runs[a.nth - 1]
    later = [r for r in human_rows(load(path)) if r["_i"] > run["i"]][:a.n]
    print(f"{run['skill']} 실행 {a.nth}번째({kst(run['ts'])}) 뒤의 사용자 발언 {len(later)}개. 대화 내용이므로 장부에는 정정 요청 횟수만 옮긴다.")
    for r in later:
        text = re.sub(r"\s+", " ", text_of((r.get("message") or {}).get("content"))).strip()
        print(f"  {kst(r.get('timestamp'), '%m-%d %H:%M')}  {text[:a.width]}")


def cmd_total(a):
    """세션 전체: 본 대화와 서브에이전트가 각각 얼마를 썼는가."""
    path = find_session(a.session)
    subs = subagents(path)
    per = {k: agg(calls_of(load(v["path"]), main=False)) for k, v in subs.items()}
    print(f"세션 {path.stem[:8]}")
    print(line_of("본 대화", agg(calls_of(load(path)))))
    tot = {k: sum(x[k] for x in per.values()) for k in ("n", "cum", "out", "think", "usd", "ref")}
    print(f"  서브에이전트 {len(per)}개  호출 {tot['n']}  누적 입력 {n(tot['cum'])}  출력 {n(tot['out'])}(생각 {n(tot['think'])})"
          f"  ${tot['usd']:.2f}  기준 단가 ${tot['ref']:.2f}")
    for k, x in sorted(per.items(), key=lambda kv: -kv[1]["cum"])[:a.top]:
        meta = subs[k]["meta"]
        print(f"    {k[:8]}  {(meta.get('description') or meta.get('skillName') or '')[:32]}  {meta.get('model', '본 대화 모델')}"
              f"  호출 {x['n']}  누적 입력 {n(x['cum'])}  출력 {n(x['out'])}  ${x['usd']:.2f}")


def step_label(c):
    if not c["tools"]:
        return "(도구 없음: 답변 뒤 사용자 발언이나 알림)"
    parts = []
    for b in c["tools"]:
        name, inp = b.get("name") or "?", b.get("input") or {}
        if name == "Bash":
            s = inp.get("description") or (inp.get("command") or "")[:50]
        elif name in ("Read", "Edit", "Write"):
            s = Path(inp.get("file_path") or "").name
        elif name in ("Skill", "Agent"):
            s = inp.get("skill") or inp.get("description") or ""
        else:
            s = ""
        parts.append(f"{name}: {s}" if s else name)
    return " + ".join(parts)[:120]


def cmd_carry(a):
    path = find_session(a.session)
    if a.agent:
        subs = subagents(path)
        hits = [k for k in subs if k.startswith(a.agent)]
        if len(hits) != 1:
            sys.exit(f"서브에이전트를 하나로 정하지 못했다: {a.agent} → {len(hits)}개")
        calls, what = calls_of(load(subs[hits[0]]["path"]), main=False), f"서브에이전트 {hits[0]}"
        live = recent(calls)
    elif a.skill:
        runs = measure_runs(path, set(a.skill), a.turns)
        if len(runs) < a.nth:
            sys.exit(f"그 스킬 실행은 {len(runs)}번뿐이다")
        run = runs[a.nth - 1]
        calls, live = run["main"] or run["sub"], run["live"]
        what = f"{run['skill']} 실행 {a.nth}번째 ({kst(run['ts'])}, {'본 대화' if run['main'] else '포크 에이전트'})"
    else:
        calls, what = calls_of(load(path)), "세션 전체(본 대화)"
        live = recent(calls)
    if live:
        print("마지막 호출이 10분 안이다(진행 중일 수 있음). 끝난 뒤 다시 잰 값을 쓴다.")
    if a.list:
        print(f"{what}: 호출 {len(calls)}번. 번호 · 맥락 · 직전 호출보다 늘어난 맥락 · 출력(생각) · 도구 수 · 도구")
        for k, c in enumerate(calls):
            grown = f"{c['ctx'] - calls[k - 1]['ctx']:+,}" if k else ""
            print(f"  #{k + 1:<3} {c['ctx']:>9,} {grown:>9} {c['out']:>7,}({c['think']:,}) {len(c['tools'])}  {step_label(c)}")
        return
    if len(calls) < 2:
        sys.exit("호출이 2번보다 적어 나눌 것이 없다")
    k_n, floor, cum = len(calls), calls[0]["ctx"], sum(c["ctx"] for c in calls)
    steps = []
    for k in range(k_n - 1):
        delta = calls[k + 1]["ctx"] - calls[k]["ctx"]
        steps.append((delta * (k_n - 1 - k), delta, k_n - 1 - k, k + 1, step_label(calls[k])))
    grown = cum - floor * k_n
    print(f"{what}: 호출 {k_n}번, 누적 입력 {n(cum)}")
    print(f"  시작할 때 이미 있던 맥락 {n(floor)} 토큰을 {k_n}번 읽음 = {n(floor * k_n)} ({floor * k_n / cum:.0%})")
    print(f"  이 구간에서 늘어난 맥락을 다시 읽음 = {n(grown)} ({grown / cum:.0%})")
    print(f"  다시 읽은 값이 큰 단계 {a.top}개 (늘어난 토큰 × 그 뒤 호출 수):")
    for carry, delta, later, k, label in sorted(steps, reverse=True)[:a.top]:
        print(f"    #{k:<3} {delta:>+9,} × {later:<3} = {carry:>11,} ({carry / cum:5.1%})  {label}")
    shrink = [s for s in steps if s[1] < -5000]
    if shrink:
        print(f"  맥락이 5,000 토큰 넘게 줄어든 단계 {len(shrink)}개 (압축·정리): " + ", ".join(f"#{s[3]} {s[1]:+,}" for s in shrink[:6]))


ASSIGN = re.compile(r'(?:^|[\s;(])([A-Za-z_]\w*)=(?:"([^"\n]*)"|\'([^\'\n]*)\'|([^\s;"\')]+))')
ROOTS = [(str(STYLE) + "/", "style/"), (str(SKILLS) + "/", "skills/"), (str(VAULT) + "/", "vault/")]
PATH_END = r'([^"\'\n;|&<>*$`]+?\.(?:md|py|tsv|json|sh))'


def expand(cmd):
    home = str(HOME) + "/"
    cmd = re.sub(r"(?<![\w/.])~/", home, cmd).replace("$HOME/", home).replace("${HOME}/", home)
    env = {m.group(1): next(g for g in m.groups()[1:] if g is not None) for m in ASSIGN.finditer(cmd)}
    for _ in range(3):
        for k, v in env.items():
            cmd = cmd.replace("${" + k + "}", v).replace("$" + k + "/", v + "/")
    return cmd


def labels_in(text):
    found = set()
    for root, prefix in ROOTS:
        for m in re.finditer(re.escape(root) + PATH_END, text):
            rel = m.group(1)
            name = rel.rsplit("/", 1)[-1]
            if prefix == "vault/" and name.endswith(".md") and name not in ("SKILL.md", "index-guide.md", "proposals.md", "date-guide.md"):
                rel = rel.split("/", 1)[0] + "/(노트)"
            found.add((prefix + rel, root + m.group(1)))
    return found


def cmd_reads(a):
    refs, sess, sizes, skill_calls, seen = Counter(), {}, {}, Counter(), set()
    cut = (datetime.now(timezone.utc) - timedelta(days=a.days)).strftime("%Y-%m-%dT%H:%M:%S")
    paths = recent_sessions(a.days)
    for p in paths:
        files = [p] + [s["path"] for s in subagents(p).values()]
        for f in files:
            rows = load(f)
            if f == p:
                for inv in invocations(rows, None, human_rows(rows)):
                    if (inv["ts"] or "") >= cut and (inv["skill"], inv["ts"]) not in seen:
                        seen.add((inv["skill"], inv["ts"]))
                        skill_calls[inv["skill"]] += 1
            for c in calls_of(rows, main=(f == p)):
                if (c["ts"] or "") < cut:
                    continue
                for b in c["tools"]:
                    if b.get("id") in seen:
                        continue
                    seen.add(b.get("id"))
                    inp = b.get("input") or {}
                    text = expand(inp.get("command") or "") if b.get("name") == "Bash" else str(inp.get("file_path") or "")
                    for label, full in labels_in(text):
                        refs[label] += 1
                        sess.setdefault(label, set()).add(p.stem)
                        sizes.setdefault(label, Path(full).stat().st_size if "(노트)" not in label and Path(full).is_file() else 0)
    print(f"최근 {a.days}일의 도구 호출 (원본 {len(paths)}개, 서브에이전트 포함, 이어 연 세션의 겹친 줄은 한 번만). 참조는 읽기와 쓰기를 모두 센다.")
    print("  참조  세션  지금 크기(바이트)  파일")
    for label, cnt in refs.most_common(a.top):
        print(f"  {cnt:>4}  {len(sess[label]):>4}  {sizes[label]:>10,}  {label}")
    print("스킬 호출 횟수: " + ", ".join(f"{k} {v}" for k, v in skill_calls.most_common(20)))


MARKS = [("SessionStart 훅이 넣은 글", "SessionStart hook additional context"), ("환경 안내", "\n# Environment"),
         ("새 도구 안내", "The following tools just became available"),
         ("지연 도구 이름 목록", "The following deferred tools are now available"),
         ("에이전트 종류 목록", "Available agent types for the Agent tool"),
         ("스킬 목록", "The following skills are available for use with the Skill tool"),
         ("MCP 서버 안내", "# MCP Server Instructions")]
SKILL_LINE = re.compile(r"^- ([\w.-]+(?::[\w.-]+)*): ")


def first_request(path):
    """세션의 첫 본 대화 요청: 시스템 프롬프트·도구 정의(shape)와 첫 메시지 조각(blob)."""
    blobs, shapes = {}, {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith('{"type":"api-request-blob"'):
                m = re.search(r'"hash":"([0-9a-f]+)"', line[:400])
                if m:
                    blobs[m.group(1)] = line
            elif line.startswith('{"type":"api-request-shape"'):
                r = json.loads(line)
                shapes[r.get("shapeHash")] = r.get("shape") or {}
            elif line.startswith('{"type":"api-request"'):
                r = json.loads(line)
                if str(r.get("querySource", "")).startswith("repl_main_thread"):
                    msgs = [json.loads(blobs[h]).get("message") for h in r.get("tail") or [] if h in blobs]
                    return r, shapes.get(r.get("shapeHash")) or {}, msgs
    return None, {}, []


def first_ctx(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"type":"assistant"' not in line or line.startswith('{"type":"'):
                continue
            r = json.loads(line)
            u = (r.get("message") or {}).get("usage") or {}
            ctx = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
            if ctx and not r.get("isSidechain"):
                return ctx, r.get("timestamp"), r.get("version") or ""
    return 0, None, ""


def compose(shape, msgs):
    """첫 요청을 구성 요소별로 나눈다. 라벨 → [글자 수, 그중 비ASCII(한글 등) 글자 수], 스킬 목록 상세, 도구 크기."""
    parts, skills = {}, Counter()

    def add(label, s):
        v = parts.setdefault(label, [0, 0])
        v[0] += len(s)
        v[1] += sum(1 for ch in s if ord(ch) > 127)

    for b in shape.get("system") or []:
        if isinstance(b, dict):
            add("시스템 프롬프트(하니스)", b.get("text", ""))
    tools = []
    for t in shape.get("tools") or []:
        s = json.dumps(t, ensure_ascii=False)
        tools.append((len(s), t.get("name", "?")))
        add("도구 정의", s)
    mine = set(user_skills())
    for msg in msgs:
        content = (msg or {}).get("content")
        blocks = content if isinstance(content, list) else [{"type": "text", "text": str(content or "")}]
        for b in blocks:
            text = b.get("text", "") if isinstance(b, dict) else ""
            if not text:
                continue
            if "Codebase and user instructions are shown below" in text[:200]:
                for sec in re.split(r"(?=Contents of /)", text):
                    m = re.match(r"Contents of (\S+)", sec)
                    if not m:
                        add("지시 머리말", sec)
                    elif "/memory/" in m.group(1):
                        add("메모리 색인(MEMORY.md)", sec)
                    elif m.group(1).endswith("/.claude/CLAUDE.md"):
                        add("전역 CLAUDE.md", sec)
                    elif m.group(1).endswith("CLAUDE.md"):
                        add("프로젝트 CLAUDE.md", sec)
                    else:
                        add("그 밖의 지시 파일 " + Path(m.group(1)).name, sec)
            elif any(mark in text for _, mark in MARKS):
                pos = sorted((text.find(mark), label) for label, mark in MARKS if mark in text)
                if pos[0][0] > 0:
                    add("그 밖의 시스템 안내", text[:pos[0][0]])
                for j, (at, label) in enumerate(pos):
                    seg = text[at:pos[j + 1][0] if j + 1 < len(pos) else len(text)]
                    add(label, seg)
                    if label == "스킬 목록":
                        cur = None
                        for ln in seg.splitlines():
                            m = SKILL_LINE.match(ln)
                            if m:
                                name = m.group(1)
                                cur = name.split(":")[0] + " 플러그인" if ":" in name else ("사용자 스킬" if name in mine else "내장 스킬")
                                skills[cur + " 수"] += 1
                            if cur:
                                skills[cur] += len(ln) + 1
            elif text.startswith("<system-reminder>\nAs you answer"):
                add("작업 공간 안내(메일·git 상태)", text)
            else:
                add("첫 발언과 그 밖", text)
    return parts, skills, sorted(tools, reverse=True)


def cmd_base(a):
    if a.list:
        print("세션 시작(KST)  첫 호출 토큰  Claude Code  프로젝트  세션")
        for p in recent_sessions(a.days):
            ctx, ts, ver = first_ctx(p) if (a.project or "") in p.parent.name else (0, None, "")
            if ctx:
                print(f"  {kst(ts, '%Y-%m-%d %H:%M')}  {ctx:>8,}  {ver:<8}  {p.parent.name[-24:]}  {p.stem[:8]}")
        return
    if a.session:
        cands = [find_session(a.session)]
    else:
        cands = sorted((p for p in PROJECTS.glob("*/*.jsonl") if (a.project or "") in p.parent.name),
                       key=lambda p: getattr(p.stat(), "st_birthtime", p.stat().st_mtime), reverse=True)[:15]
    for path in cands:
        req, shape, msgs = first_request(path)
        ctx, ts, ver = first_ctx(path)
        if req and ctx:
            break
    else:
        sys.exit("첫 요청 기록(api-request)이 있는 세션을 찾지 못했다")
    parts, skills, tools = compose(shape, msgs)
    total, kor = sum(v[0] for v in parts.values()), sum(v[1] for v in parts.values())
    ratio = ctx / total
    est = lambda v: int(v[0] * ratio)
    print(f"세션 {path.stem[:8]} ({kst(ts, '%Y-%m-%d %H:%M')} 시작, Claude Code {ver}, {path.parent.name[-24:]})")
    print(f"첫 호출 {n(ctx)} 토큰 (실측) / 구성 요소 {n(total)}자 (그중 한글 등 비ASCII {n(kor)}자) → 글자당 {ratio:.2f} 토큰으로 어림")
    for label, v in sorted(parts.items(), key=lambda kv: -est(kv[1])):
        print(f"  약 {est(v):>6,} 토큰  {est(v) / ctx:5.1%}  {v[0]:>7,}자  {label}")
    print(f"  도구 정의 {len(tools)}개 가운데 큰 것: " + ", ".join(f"{nm} {n(sz)}자" for sz, nm in tools[:6]))
    groups = sorted(((v, k) for k, v in skills.items() if not k.endswith(" 수")), reverse=True)
    print("  스킬 목록 안: " + ", ".join(f"{k} {skills[k + ' 수']}개 {n(v)}자" for v, k in groups))
    if a.save:
        g = lambda label: parts.get(label, [0, 0])[0]
        row = {"start_kst": kst(ts), "session": path.stem[:8], "project": path.parent.name[-24:], "cc_version": ver,
               "first_ctx_tokens": ctx, "chars_total": total, "system": g("시스템 프롬프트(하니스)"),
               "tools": g("도구 정의"), "n_tools": len(tools), "claude_md_global": g("전역 CLAUDE.md"),
               "claude_md_project": g("프로젝트 CLAUDE.md"), "memory": g("메모리 색인(MEMORY.md)"),
               "hook": g("SessionStart 훅이 넣은 글"), "deferred_tools": g("지연 도구 이름 목록"),
               "mcp": g("MCP 서버 안내"), "skills_list": g("스킬 목록"),
               "n_skills": sum(v for k, v in skills.items() if k.endswith(" 수")), "agents_list": g("에이전트 종류 목록")}
        row["other"] = total - sum(row[c] for c in ("system", "tools", "claude_md_global", "claude_md_project", "memory",
                                                     "hook", "deferred_tools", "mcp", "skills_list", "agents_list"))
        if any(r["session"] == row["session"] for r in read_tsv(RESEARCH / "base.tsv")):
            print("base.tsv 에 이미 있는 세션이라 더하지 않음")
        else:
            append_tsv(RESEARCH / "base.tsv", BASE_COLS, [row])
            print("base.tsv 에 1줄 더함")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("trend"); p.add_argument("--skill", nargs="+", required=True); p.add_argument("--by", choices=("month", "week"), default="month")
    p.set_defaults(fn=cmd_trend)
    p = sub.add_parser("base"); p.add_argument("--session"); p.add_argument("--save", action="store_true")
    p.add_argument("--list", action="store_true"); p.add_argument("--days", type=int, default=14)
    p.add_argument("--project", help="프로젝트 폴더 이름의 일부"); p.set_defaults(fn=cmd_base)
    p = sub.add_parser("runs"); p.add_argument("--skill", nargs="*"); p.add_argument("--days", type=int, default=30)
    p.add_argument("--session"); p.add_argument("--turns", type=int, default=1); p.add_argument("--save", action="store_true")
    p.set_defaults(fn=cmd_runs)
    p = sub.add_parser("stats"); p.add_argument("--skill", nargs="+", required=True); p.add_argument("--since", help="YYYY-MM-DD[ HH:MM] 부터")
    p.add_argument("--until", help="YYYY-MM-DD[ HH:MM] 전까지"); p.add_argument("--session", nargs="*", help="이 세션(앞 8자)만")
    p.add_argument("--not-session", nargs="*", help="이 세션(앞 8자)은 빼고"); p.add_argument("--model", help="모델 이름의 일부")
    p.add_argument("--not-run", nargs="*", help="시작 시각이 이 값(YYYY-MM-DD HH:MM 의 앞부분)으로 시작하는 실행은 빼고. 멈춘 실행, 요청 종류가 다른 실행 하나를 뺄 때")
    p.add_argument("--ctx-below", type=int, help="시작 맥락이 이 값보다 작은 실행만"); p.add_argument("--ctx-above", type=int, help="시작 맥락이 이 값 이상인 실행만")
    p.set_defaults(fn=cmd_stats)
    p = sub.add_parser("check"); p.add_argument("--session", required=True); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("after"); p.add_argument("--session", required=True); p.add_argument("--skill", nargs="+", required=True)
    p.add_argument("--nth", type=int, default=1); p.add_argument("--n", type=int, default=5); p.add_argument("--width", type=int, default=120)
    p.set_defaults(fn=cmd_after)
    p = sub.add_parser("total"); p.add_argument("--session", required=True); p.add_argument("--top", type=int, default=8); p.set_defaults(fn=cmd_total)
    p = sub.add_parser("carry"); p.add_argument("--session", required=True); p.add_argument("--skill", nargs="*")
    p.add_argument("--nth", type=int, default=1); p.add_argument("--agent"); p.add_argument("--turns", type=int, default=1)
    p.add_argument("--top", type=int, default=12); p.add_argument("--list", action="store_true"); p.set_defaults(fn=cmd_carry)
    p = sub.add_parser("reads"); p.add_argument("--days", type=int, default=14); p.add_argument("--top", type=int, default=40)
    p.set_defaults(fn=cmd_reads)
    import lab
    lab.register(sub, sys.modules[__name__])
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
