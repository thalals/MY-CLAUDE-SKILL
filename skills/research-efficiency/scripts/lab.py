#!/usr/bin/env python3
"""연구 장부 도구. efficiency.py 의 하위 명령으로 쓴다(이 파일을 직접 실행하지 않는다).

  status [--brief]                 회차 시작: 쌓인 것, 지난 회차의 인계, 판정 대기 시도, 열린 방향, 다시 볼 사실, 성적, 종합(knowledge.md)
  find 말 ... [--kind F|D|A]       선행 연구 찾기: 모든 말이 들어 있는 항목과, 종합·회차 기록의 줄
  show 번호 ... | --open F|D|A     항목 본문과 그 번호를 인용한 곳
  new F|D|A --title 제목           다음 번호로 항목 파일을 만든다(필수 라벨 뼈대)
  set 번호 라벨 값                 항목의 라벨 한 줄을 바꾸거나 더한다(상태, 우선, 확인 등)
  lint                             장부 점검: 차단(E)이 있으면 종료 코드 1
  index                            index.md 를 다시 쓴다
  close --kind 종류 --focus 초점 --did 한일 --next 다음 [--ids 번호들] [--learned 배운것]
        [--session ID] [--since "YYYY-MM-DD HH:MM"] [--until "YYYY-MM-DD HH:MM"]
                                   회차 닫기: 차단 0 확인 → index.md → 이 회차의 비용을 재서 log.tsv 에 적는다

항목 형식, 상태 말, 점검 번호의 뜻은 reference/ledger.md 에 있다.
"""
import re
import statistics
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
KINDS = {"F": ("findings", "사실"), "D": ("directions", "방향"), "A": ("attempts", "시도")}
STATES = {"F": ("유효", "낡음", "대체됨", "틀림"),
          "D": ("먼저 잰다", "후보", "시도 중", "채택", "기각", "완료", "보류"),
          "A": ("측정 대기", "채택", "실패")}
OPEN = {"F": ("유효",), "D": ("먼저 잰다", "후보", "시도 중"), "A": ("측정 대기",)}
AREAS = ("맥락", "지시", "절차", "효과", "측정", "연구실")
STRENGTHS = ("문서", "관측 1회", "관측 반복", "전후 비교", "통제 비교")
SESSION_KINDS = ("구축", "측정", "판정", "탐색", "적용", "종합")
REQUIRED = {"F": ("상태", "갈래", "세기", "확인", "근거", "사실", "한계", "다시 볼 때"),
            "D": ("상태", "갈래", "대상", "근거", "방법"),
            "A": ("상태", "갈래", "방향", "대상 스킬", "바꾼 때", "필요 횟수", "사전 기준", "바꾼 것", "사전 측정",
                  "예측", "틀렸다고 볼 기준", "품질 확인")}
SKELETON = {"F": ("상태: 유효", "갈래: ", "세기: ", "확인: {today}", "근거: ", "사실: ", "한계: ", "다시 볼 때: "),
            "D": ("상태: 먼저 잰다 ({today})", "갈래: ", "우선: ", "대상: ", "근거: ", "방법: "),
            "A": ("상태: 측정 대기 ({today})", "갈래: ", "방향: ", "대상 스킬: ", "바꾼 때: ", "필요 횟수: ", "사전 기준: ",
                  "바꾼 것: ", "사전 측정: ", "예측: ", "틀렸다고 볼 기준: ", "품질 확인: ", "겹친 변경: ")}
LOG_COLS = ["n", "start_kst", "end_kst", "session", "kind", "focus", "ids", "did", "learned", "next",
            "calls", "sub_calls", "cum_in", "out", "usd", "ref_usd"]
ID = re.compile(r"(?<![\w-])([FDA])-(\d{2,})(?!\d)")
HEAD = re.compile(r"^# ([FDA]-\d{2,}) (.+)$")
LABEL = re.compile(r"^- ([^:\n]{1,30}?): ?(.*)$")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
KNOWLEDGE_MAX_LINES, STALE_DAYS, OPEN_MAX, OPEN_SHOWN, REVIEW_EVERY = 80, 60, 15, 12, 5


def parse(path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    m = HEAD.match(lines[0]) if lines else None
    labels = [(x.group(1).strip(), x.group(2).strip()) for x in map(LABEL.match, lines[1:]) if x]
    return {"path": path, "id": m.group(1) if m else path.stem, "title": m.group(2).strip() if m else "",
            "head_ok": bool(m), "labels": labels, "text": text}


def num(item_id):
    return int(re.sub(r"\D", "", item_id) or 0)


def load_items(E, kind=None):
    out = []
    for k, (folder, _) in KINDS.items():
        if kind in (None, k):
            out += sorted((parse(p) for p in (E.RESEARCH / folder).glob(f"{k}-*.md")), key=lambda it: num(it["id"]))
    return out


def get(it, label):
    return next((v for k, v in it["labels"] if k == label), None)


def state_of(it):
    v = get(it, "상태") or ""
    return next((s for s in sorted(STATES.get(it["id"][0], ()), key=len, reverse=True) if v.startswith(s)), "")


def date_of(it):
    for label in ("확인", "바꾼 때", "상태"):
        m = DATE.search(get(it, label) or "")
        if m:
            return m.group(0)
    return ""


def age_days(it, today):
    d = date_of(it)
    return (today - datetime.strptime(d, "%Y-%m-%d").date()).days if d else None


def refs(text, own=None):
    return sorted({f"{k}-{d}" for k, d in ID.findall(text)} - {own}, key=lambda x: (x[0], num(x)))


def cited_by(E, its):
    """번호 → 그 번호를 인용한 곳(종합, 다른 항목)."""
    by = {}
    for it in its:
        for r in refs(it["text"], it["id"]):
            by.setdefault(r, []).append(it["id"])
    k = E.RESEARCH / "knowledge.md"
    if k.exists():
        for r in refs(k.read_text(encoding="utf-8")):
            by.setdefault(r, []).insert(0, "종합")
    return by


def read_log(E):
    return sorted(E.read_tsv(E.RESEARCH / "log.tsv"), key=lambda r: int(r.get("n") or 0))


def med(rows, col):
    return statistics.median(float(r[col] or 0) for r in rows)


def attempt_runs(it, runs):
    """시도의 '대상 스킬' 과 '바꾼 때' 로 runs.tsv 에서 바꾼 뒤의 실행을 고른다. (모두, 진행 중이 아닌 것)"""
    skill, since = get(it, "대상 스킬") or "", (get(it, "바꾼 때") or "")[:16]
    rows = [r for r in runs if since and r["skill"] == skill and r["start_kst"][:16] >= since]
    return rows, [r for r in rows if "진행 중" not in r.get("note", "")]


def attempt_line(it, runs):
    rows, done = attempt_runs(it, runs)
    s = (f"{it['id']} {it['title']} · 대상 {get(it, '대상 스킬') or '?'} · 바꾼 때 {get(it, '바꾼 때') or '?'}"
         f" · 바꾼 뒤 실행 {len(done)}/{get(it, '필요 횟수') or '?'}번")
    if done:
        m = med(done, "total_ref_usd")
        s += f" · 기준 단가 환산 중앙값 ${m:.2f}"
        try:
            pre = float(get(it, "사전 기준") or "")
            s += f" (사전 ${pre:.2f} 의 {m / pre:.2f}배)"
        except (ValueError, ZeroDivisionError):
            pass
    if len(rows) > len(done):
        s += f" · 진행 중으로 적힌 줄 {len(rows) - len(done)}개는 뺐다"
    return s


def index_text(E, its):
    by = cited_by(E, its)
    out = ["# 장부 목록", "",
           "> 도구가 쓴다(`index`, `close`). 손으로 고치지 않는다. 한 줄은 번호 · 상태 · 갈래 · 날짜 · 제목 · 이 번호를 인용한 곳이다."
           " 본문은 `show 번호`, 찾기는 `find 말`.", ""]
    for k, (folder, name) in KINDS.items():
        rows = [it for it in its if it["id"][0] == k]
        out.append(f"## {name} {len(rows)}개 (`{folder}/`)")
        for it in rows:
            c = by.get(it["id"], [])
            out.append(f"- {it['id']} · {state_of(it) or '상태 없음'} · {get(it, '갈래') or '?'} · {date_of(it) or '?'} · {it['title']}"
                       + (f" · ← {', '.join(c)}" if c else ""))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def problems(E, its):
    """장부 점검. (수준 E|R, 번호, 자리, 말) 목록. 번호의 뜻은 reference/ledger.md."""
    out, R = [], E.RESEARCH
    ids = {it["id"]: it for it in its}
    by = cited_by(E, its)
    today = datetime.now(KST).date()
    add = lambda level, code, where, msg: out.append((level, code, where, msg))
    for it in its:
        k = it["id"][0]
        if not it["head_ok"] or it["path"].stem != it["id"]:
            add("E", "E1", it["path"].name, "첫 줄이 '# 번호 제목' 이 아니거나 번호가 파일 이름과 다르다")
            continue
        for req in REQUIRED[k]:
            vals = [v for l, v in it["labels"] if l == req or (req == "근거" and l.startswith("근거"))]
            if not vals:
                add("E", "E2", it["id"], f"필수 라벨 '{req}' 가 없다")
            elif not any(vals):
                add("E", "E2", it["id"], f"필수 라벨 '{req}' 의 값이 비어 있다")
        st = state_of(it)
        if get(it, "상태") and not st:
            add("E", "E3", it["id"], f"상태 말이 어휘에 없다: {get(it, '상태')[:24]}")
        if get(it, "갈래") and get(it, "갈래") not in AREAS:
            add("E", "E4", it["id"], f"갈래 말이 어휘에 없다: {get(it, '갈래')[:24]}")
        if k == "F" and get(it, "세기") and not get(it, "세기").startswith(STRENGTHS):
            add("E", "E4", it["id"], f"세기 말이 어휘에 없다: {get(it, '세기')[:24]}")
        for r in refs(it["text"], it["id"]):
            if r not in ids:
                add("E", "E5", it["id"], f"장부에 없는 번호를 가리킨다: {r}")
        if k == "A" and st == "측정 대기":
            for label, pat, want in (("바꾼 때", r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", "YYYY-MM-DD HH:MM"),
                                     ("사전 기준", r"\d+(\.\d+)?$", "숫자만"), ("필요 횟수", r"\d+$", "숫자만")):
                if get(it, label) and not re.match(pat, get(it, label)):
                    add("E", "E6", it["id"], f"'{label}' 은 {want} 으로 적는다(도구가 읽는다): {get(it, label)[:24]}")
        if k == "D":
            if st in ("후보", "시도 중") and not any(l.startswith(("틀렸다고 볼 기준", "끝났다고 볼 기준")) for l, _ in it["labels"]):
                add("E", "E7", it["id"], "후보인데 '틀렸다고 볼 기준' 이나 '끝났다고 볼 기준' 이 없다")
            if st in ("채택", "기각", "완료") and not get(it, "결과"):
                add("R", "R6", it["id"], "닫은 방향에 '결과' 줄이 없다")
            basis = " ".join(v for l, v in it["labels"] if l.startswith("근거"))
            if not ID.search(basis) and "선행 없음" not in basis:
                add("R", "R7", it["id"], "근거에 사실·시도 번호가 없다(선행 연구 없이 올린 방향)")
        if k == "A" and st in ("채택", "실패") and not (get(it, "결론") and get(it, "예측 평가")):
            add("R", "R6", it["id"], "판정한 시도에 '결론' 이나 '예측 평가' 줄이 없다")
        if k == "F" and st == "유효":
            age = age_days(it, today)
            if age is not None and age > STALE_DAYS:
                add("R", "R4", it["id"], f"확인한 지 {age}일이다. 다시 재거나 낡음으로 바꾼다")
            if it["id"] not in by:
                add("R", "R3", it["id"], "종합도 다른 항목도 인용하지 않는다")
    kpath = R / "knowledge.md"
    if not kpath.exists():
        add("E", "E8", "knowledge.md", "종합 파일이 없다")
    else:
        klines = kpath.read_text(encoding="utf-8").splitlines()
        if len(klines) > KNOWLEDGE_MAX_LINES:
            add("R", "R1", "knowledge.md", f"{len(klines)}줄이다({KNOWLEDGE_MAX_LINES}줄 이내). 겹치는 문장을 합치고 세부는 사실에 둔다")
        for i, ln in enumerate(klines, 1):
            if ln.startswith("- ") and not ID.search(ln) and "metrics.md" not in ln:
                add("E", "E8", "knowledge.md", f"{i}행에 근거 번호가 없다: {ln[:40]}")
        for r in refs("\n".join(klines)):
            if r not in ids:
                add("E", "E5", "knowledge.md", f"장부에 없는 번호를 가리킨다: {r}")
            elif r[0] == "F" and state_of(ids[r]) != "유효":
                add("R", "R2", "knowledge.md", f"유효하지 않은 사실을 인용한다: {r} [{state_of(ids[r]) or '상태 없음'}]")
    opened = sum(1 for it in its if it["id"][0] == "D" and state_of(it) in OPEN["D"])
    if opened > OPEN_MAX:
        add("R", "R5", "directions", f"열린 방향이 {opened}개다({OPEN_MAX}개 이내). 종합 회차에서 솎는다")
    idx = R / "index.md"
    if not idx.exists() or idx.read_text(encoding="utf-8") != index_text(E, its):
        add("R", "R8", "index.md", "목록이 지금 장부와 다르다. `index` 나 `close` 가 다시 쓴다")
    live = sum(1 for r in E.read_tsv(R / "runs.tsv") if "진행 중" in r.get("note", ""))
    if live:
        add("R", "R9", "runs.tsv", f"진행 중으로 적힌 줄이 {live}개다. 끝난 뒤 `runs --save` 로 다시 잰다")
    log = read_log(E)
    if log and not log[-1].get("next"):
        add("R", "R10", "log.tsv", "지난 회차가 '다음에 할 일' 을 남기지 않았다")
    return out


def status(E, a):
    now, R = datetime.now(KST), E.RESEARCH
    its = load_items(E)
    kinds = {k: [it for it in its if it["id"][0] == k] for k in KINDS}
    runs, base, log = E.read_tsv(R / "runs.tsv"), E.read_tsv(R / "base.tsv"), read_log(E)
    done = [r for r in runs if "진행 중" not in r.get("note", "")]
    count = lambda k: ", ".join(f"{s} {c}" for s, c in Counter(state_of(it) or "상태 없음" for it in kinds[k]).most_common())
    print(f"# 연구실 현황 ({now:%Y-%m-%d %H:%M} KST)")
    print(f"- 장부: {R}")
    print(f"- 쌓인 것: 사실 {len(kinds['F'])}개({count('F')}) · 방향 {len(kinds['D'])}개({count('D')}) · 시도 {len(kinds['A'])}개({count('A')})"
          f" · 회차 {len(log)}번 · 잰 실행 {len(runs)}번 · 첫 호출 스냅숏 {len(base)}개")

    print("\n## 지난 회차")
    if not log:
        print("- 없음. 이번이 첫 회차다.")
    for r in log[-3:][::-1]:
        print(f"- {r['n']}회차 {r['start_kst'][:16]}~{r['end_kst'][11:16]} · {r['kind']} · 초점: {r['focus']}")
        print(f"  한 일: {r['did']}" + (f" (다룬 번호: {r['ids']})" if r["ids"] else ""))
        if r is log[-1]:
            print(f"  다음에 할 일: {r['next'] or '적지 않음'}")
            if r["learned"]:
                print(f"  연구 방법에서 배운 것: {r['learned']}")

    print("\n## 판정 대기 시도")
    waiting = [it for it in kinds["A"] if state_of(it) == "측정 대기"]
    for it in waiting:
        print("- " + attempt_line(it, runs))
    if not waiting:
        print("- 없음")
    adopted = [it for it in kinds["A"] if state_of(it) == "채택"]
    print("\n## 감시 (채택한 시도가 그 뒤에도 유지되는가)")
    for it in adopted:
        print("- " + attempt_line(it, runs))
    if not adopted:
        print("- 채택한 시도 없음")

    opened = [it for it in kinds["D"] if state_of(it) in OPEN["D"]]

    def prio(it):
        m = re.match(r"\d+", get(it, "우선") or "")
        return (int(m.group(0)) if m else 999, num(it["id"]))

    print(f"\n## 열린 방향 {len(opened)}개 (우선 순, 그다음 번호 순)")
    for it in sorted(opened, key=prio)[:OPEN_SHOWN]:
        p = re.match(r"\d+", get(it, "우선") or "")
        print(f"- {it['id']} [{state_of(it)}] {'우선 ' + p.group(0) + ' · ' if p else ''}{get(it, '갈래') or '?'} · {it['title']}")
    if len(opened) > OPEN_SHOWN:
        print(f"- 그 밖 {len(opened) - OPEN_SHOWN}개는 `show --open D` 나 index.md 에서 본다")

    stale = [(it, age_days(it, now.date())) for it in kinds["F"]]
    stale = [(it, age) for it, age in stale if state_of(it) == "낡음" or (state_of(it) == "유효" and age is not None and age > STALE_DAYS)]
    print("\n## 다시 볼 사실")
    for it, age in stale[:8]:
        print(f"- {it['id']} [{state_of(it)}] 확인한 지 {age}일 · {it['title']} · 다시 볼 때: {get(it, '다시 볼 때') or '적지 않음'}")
    if len(stale) > 8:
        print(f"- 그 밖 {len(stale) - 8}개는 `lint` 의 R4 에서 본다")
    if not stale:
        print(f"- 없음 (낡음 상태와, 확인한 지 {STALE_DAYS}일 넘은 유효 사실을 낸다)")

    print("\n## 환경 변화 (지난 회차 뒤의 실행에서 처음 보인 것)")
    news = []
    if log:
        cut = log[-1]["end_kst"][:16]
        for col, label in (("cc_version", "Claude Code"), ("model", "모델")):
            seen = {r[col] for r in runs if r["start_kst"][:16] <= cut}
            news += [f"{label} {v} ({c}번)" for v, c in Counter(r[col] for r in runs if r["start_kst"][:16] > cut and r[col] and r[col] not in seen).items()]
    print("- " + (", ".join(news) + " → 수치를 믿기 전에 `check` 로 도구 합계부터 본다" if news else "없음"))

    print("\n## 스킬별 한 번 값 (기준 단가 환산, 진행 중으로 적힌 줄 제외)")
    c1, c0 = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"), (now - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
    fmt = lambda rs: (f"{len(rs)}번 중앙값 ${med(rs, 'total_ref_usd'):.2f} 합 ${sum(float(r['total_ref_usd'] or 0) for r in rs):.2f}" if rs else "0번")
    for skill in sorted({r["skill"] for r in done if r["start_kst"] >= c0}):
        rs = [r for r in done if r["skill"] == skill]
        print(f"- {skill}: 최근 30일 {fmt([r for r in rs if r['start_kst'] >= c1])} | 그 전 30일 {fmt([r for r in rs if c0 <= r['start_kst'] < c1])}")

    print("\n## 연구실 성적")
    cost = lambda col: sum(float(r[col] or 0) for r in log)
    print(f"- 회차 {len(log)}번에 든 값: 정가 환산 ${cost('usd'):.2f} · 기준 단가 환산 ${cost('ref_usd'):.2f}")
    judged = [get(it, "예측 평가") or "" for it in kinds["A"]]
    states = Counter(state_of(it) for it in kinds["A"])
    print(f"- 시도: 채택 {states['채택']} · 실패 {states['실패']} · 측정 대기 {states['측정 대기']}"
          f" · 예측 평가 {sum(1 for j in judged if j)}개 가운데 맞음 {sum(1 for j in judged if j.startswith('맞음'))}개")
    saved, counted = 0.0, 0
    for it in adopted:
        after = attempt_runs(it, runs)[1]
        try:
            pre = float(get(it, "사전 기준") or "")
        except ValueError:
            continue
        if after:
            saved += (pre - med(after, "total_ref_usd")) * len(after)
            counted += 1
    print("- 채택한 시도로 줄인 값: " + (f"${saved:.2f} (어림. 시도 {counted}개의 (사전 기준 − 채택 뒤 중앙값) × 채택 뒤 실행 수)" if adopted else "채택한 시도 없음"))
    probs = problems(E, its)
    e, r = sum(1 for p in probs if p[0] == "E"), sum(1 for p in probs if p[0] == "R")
    print(f"- 장부 점검: 차단 {e} · 보고 {r}" + (" → `lint` 로 본다" if e or r else ""))

    print("\n## 이번 회차의 시작")
    days = 30
    if log:
        gap = (now - datetime.strptime(log[-1]["end_kst"][:16], "%Y-%m-%d %H:%M").replace(tzinfo=KST)).days
        days = min(30, max(2, gap + 2))
    print(f"- 먼저 `runs --days {days} --save` 로 지난 회차 뒤의 실행을 장부에 옮긴다.")
    since_review = next((i for i, row in enumerate(reversed(log)) if row["kind"] == "종합"), len(log))
    if since_review >= REVIEW_EVERY:
        print(f"- 종합 회차를 권한다. 마지막 종합 뒤 {since_review}회차가 지났다.")
    if not a.brief:
        k = R / "knowledge.md"
        print("\n" + (k.read_text(encoding="utf-8").rstrip() if k.exists() else "knowledge.md 가 없다. `lint` 를 본다."))


def cmd_status(E, a):
    try:
        status(E, a)
    except Exception as e:  # 스킬을 부를 때 이 출력이 본문에 끼워진다. 실패해도 스킬 호출을 멈추지 않는다.
        print(f"현황을 만들다 실패했다({type(e).__name__}: {e}). `lint` 를 돌리고 research/ 의 파일을 직접 본다.")


def cmd_find(E, a):
    terms = [t.lower() for t in a.terms]
    hit = lambda s: all(t in s.lower() for t in terms)
    its = [it for it in load_items(E, a.kind) if hit(it["text"])]
    for it in its:
        print(f"{it['id']} [{state_of(it) or '상태 없음'} · {get(it, '갈래') or '?'}] {it['title']}")
        for ln in [ln for ln in it["text"].splitlines()[1:] if any(t in ln.lower() for t in terms)][:2]:
            print("    " + ln.strip()[:170])
    if not a.kind:
        k = E.RESEARCH / "knowledge.md"
        for ln in (k.read_text(encoding="utf-8").splitlines() if k.exists() else []):
            if ln.startswith("- ") and hit(ln):
                print("종합: " + ln[2:][:190])
        for r in read_log(E):
            if hit(" ".join(r.get(c, "") for c in ("focus", "ids", "did", "learned", "next"))):
                print(f"{r['n']}회차({r['start_kst'][:10]} {r['kind']}): 초점 {r['focus']} · 한 일 {r['did'][:120]}")
    print(f"\n찾은 항목 {len(its)}개. 본문은 `show 번호 ...`. 0개면 말을 바꿔 한 번 더 찾고, 그래도 없으면 '선행 없음' 과 찾은 말을 근거에 적는다.")


def cmd_show(E, a):
    its = load_items(E)
    by = cited_by(E, its)
    if a.open:
        picked = [it for it in its if it["id"][0] == a.open and state_of(it) in OPEN[a.open]]
    elif a.ids:
        want = [x.upper() for x in a.ids]
        picked = [it for it in its if it["id"] in want]
        missing = [w for w in want if w not in {it["id"] for it in picked}]
        if missing:
            print("장부에 없는 번호: " + ", ".join(missing))
    else:
        sys.exit("번호를 주거나 --open F|D|A 를 준다")
    for it in picked:
        print(it["text"].rstrip())
        print(f"(인용한 곳: {', '.join(by.get(it['id'], [])) or '없음'})\n")


def cmd_new(E, a):
    folder = E.RESEARCH / KINDS[a.kind][0]
    folder.mkdir(parents=True, exist_ok=True)
    nums = [int(m.group(1)) for m in (re.match(rf"{a.kind}-(\d+)\.md$", p.name) for p in folder.iterdir()) if m]
    new_id = f"{a.kind}-{max(nums, default=0) + 1:02d}"
    today = datetime.now(KST).strftime("%Y-%m-%d")
    title = re.sub(r"\s+", " ", a.title).strip()
    text = f"# {new_id} {today + ' ' if a.kind == 'A' else ''}{title}\n" + "".join(f"- {s.format(today=today)}\n" for s in SKELETON[a.kind])
    path = folder / f"{new_id}.md"
    with open(path, "x", encoding="utf-8") as fh:
        fh.write(text)
    print(f"{path}\n{text}빈 라벨을 채운다. 라벨의 뜻은 reference/ledger.md 에 있다. 채우기 전에는 lint 가 차단(E2)을 낸다.")


def cmd_set(E, a):
    it = next((x for x in load_items(E) if x["id"] == a.id.upper()), None)
    if it is None:
        sys.exit(f"장부에 없는 번호: {a.id}")
    new = f"- {a.label}: " + re.sub(r"\s+", " ", " ".join(a.value)).strip()
    lines, old = it["text"].splitlines(), None
    for i, ln in enumerate(lines):
        m = LABEL.match(ln)
        if i and m and m.group(1).strip() == a.label:
            old, lines[i] = ln, new
            break
    else:
        lines.append(new)
    it["path"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{it['id']}: " + (f"{old}\n  → {new}" if old else f"더함 {new}"))


def cmd_lint(E, a):
    probs = problems(E, load_items(E))
    for level, title in (("E", "차단"), ("R", "보고")):
        rows = [p for p in probs if p[0] == level]
        print(f"{title} {len(rows)}건")
        for _, code, where, msg in rows:
            print(f"  {code} {where}: {msg}")
    if any(p[0] == "E" for p in probs):
        sys.exit(1)


def cmd_index(E, a):
    text = index_text(E, load_items(E))
    (E.RESEARCH / "index.md").write_text(text, encoding="utf-8")
    print(f"index.md 를 다시 썼다({len(text.splitlines())}줄)")


def utc(kst_text):
    return datetime.strptime(kst_text[:16], "%Y-%m-%d %H:%M").replace(tzinfo=KST).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def cmd_close(E, a):
    its = load_items(E)
    blocks = [p for p in problems(E, its) if p[0] == "E"]
    if blocks:
        for _, code, where, msg in blocks:
            print(f"  {code} {where}: {msg}")
        sys.exit(f"차단 {len(blocks)}건. 고친 뒤 다시 닫는다. 회차 기록은 적지 않았다.")
    known, named = {it["id"] for it in its}, refs(a.ids or "")
    if [x for x in named if x not in known]:
        sys.exit("--ids 에 장부에 없는 번호가 있다: " + ", ".join(x for x in named if x not in known))
    (E.RESEARCH / "index.md").write_text(index_text(E, its), encoding="utf-8")
    path = E.find_session(a.session) if a.session else max(E.PROJECTS.glob("*/*.jsonl"), key=lambda p: p.stat().st_mtime)
    rows = E.load(path)
    if a.since:
        start = a.since[:16]
    else:
        inv = E.invocations(rows, {E.ROOT.name}, E.human_rows(rows))
        start = E.kst(inv[-1]["ts"] if inv else next((r.get("timestamp") for r in rows if r.get("timestamp")), None), "%Y-%m-%d %H:%M")
    end = a.until[:16] if a.until else datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    t0, t1 = utc(start), utc(end)[:-2] + "59"
    inside = lambda c: t0 <= (c["ts"] or "")[:19] <= t1
    m = E.agg([c for c in E.calls_of(rows) if inside(c)])
    s = E.agg([c for sub in E.subagents(path).values() for c in E.calls_of(E.load(sub["path"]), main=False) if inside(c)])
    log, key = read_log(E), (path.stem[:8], start)
    old = next((r for r in log if (r["session"], r["start_kst"]) == key), None)
    clean = lambda x: re.sub(r"\s+", " ", x or "").strip()
    row = {"n": old["n"] if old else max((int(r["n"]) for r in log), default=0) + 1, "start_kst": start, "end_kst": end,
           "session": key[0], "kind": a.kind, "focus": clean(a.focus), "ids": ", ".join(named), "did": clean(a.did),
           "learned": clean(a.learned), "next": clean(a.next), "calls": m["n"], "sub_calls": s["n"],
           "cum_in": m["cum"] + s["cum"], "out": m["out"] + s["out"], "usd": f"{m['usd'] + s['usd']:.2f}", "ref_usd": f"{m['ref'] + s['ref']:.2f}"}
    p = E.RESEARCH / "log.tsv"
    p.unlink(missing_ok=True)
    E.append_tsv(p, LOG_COLS, sorted([r for r in log if r is not old] + [row], key=lambda r: int(r["n"])))
    print(f"{row['n']}회차를 닫았다{'(고쳐 씀)' if old else ''}: 세션 {key[0]} · {start}~{end[11:]} · {a.kind} · 초점 {row['focus']}")
    print(f"  이 회차에 든 것: 본 대화 호출 {m['n']} · 서브에이전트 호출 {s['n']} · 누적 입력 {row['cum_in']:,} · 출력 {row['out']:,}"
          f" · 정가 환산 ${row['usd']} · 기준 단가 환산 ${row['ref_usd']}" + (" · 가격 모르는 모델 있음" if m["unpriced"] + s["unpriced"] else ""))
    print("  닫은 뒤의 호출은 들어가지 않는다. 더 일했으면 같은 명령으로 다시 닫는다. 남은 일은 스킬 본문 '회차' 7단계의 백업이다.")


def register(sub, E):
    def add(name, fn, *args):
        p = sub.add_parser(name)
        for flags, kw in args:
            p.add_argument(*flags, **kw)
        p.set_defaults(fn=lambda a: fn(E, a))

    add("status", cmd_status, (("--brief",), {"action": "store_true"}))
    add("find", cmd_find, (("terms",), {"nargs": "+"}), (("--kind",), {"choices": list(KINDS)}))
    add("show", cmd_show, (("ids",), {"nargs": "*"}), (("--open",), {"choices": list(KINDS)}))
    add("new", cmd_new, (("kind",), {"choices": list(KINDS)}), (("--title",), {"required": True}))
    add("set", cmd_set, (("id",), {}), (("label",), {}), (("value",), {"nargs": "+"}))
    add("lint", cmd_lint)
    add("index", cmd_index)
    add("close", cmd_close, (("--kind",), {"required": True, "choices": SESSION_KINDS}), (("--focus",), {"required": True}),
        (("--did",), {"required": True}), (("--next",), {"required": True}), (("--ids",), {}), (("--learned",), {}),
        (("--session",), {}), (("--since",), {}), (("--until",), {}))
