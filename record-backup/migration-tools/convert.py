"""record 노트를 LLM 전용 형식으로 옮기는 1회용 변환기 (1단계, 결정적). 사용: python3 convert.py <볼트 루트> [--dry] [--report 파일]

하는 일 (노트 본문의 사실 문장은 건드리지 않는다)
  1. `## 목차` 절 삭제 — 절 목록은 build-index.py 가 머리의 `> 절:` 줄로 만든다
  2. `> ↑ …` 지도 줄 삭제
  3. 표 → 라벨 줄. 칸마다 `<머리>: <값>`, 한 행이 400자 이하면 한 줄(` | ` 로 잇는다), 넘는 행이 있는 표는 행마다 머리 줄 + 하위 줄
  4. 표 칸의 식별자(METHOD 경로, /v 경로, oms.·pim. 토픽, 클래스 이름)에 백틱 — lint 가 표 칸에서 보던 식별자를 그대로 본다
  5. 위키링크 별칭 삭제. 대상 경로·헤딩에 없는 말이 든 별칭은 링크 뒤 괄호로 남긴다
  6. `## 관련` 의 `- 노트: [[a]](설명), [[b]]` 줄을 링크마다 한 줄(`- [[a]] — 설명`)로 나눔
  7. 지도 줄의 `키워드:` 를 노트 frontmatter `keywords` 로 옮김

두 번 돌려도 결과가 같다. git 과 볼트 밖 파일은 건드리지 않는다.
"""
import re, sys
from pathlib import Path

LINE_CAP = 400
SPECIAL = {"index-guide.md", "SKILL.md", "README.md"}
IDENT = re.compile(
    r"\b(?:GET|POST|PUT|PATCH|DELETE) /[^\s,;()·]+"
    r"|(?<![\w/])/v\d[^\s,;()·]*"
    r"|\b(?:local\.)?(?:oms|pim)\.[a-z0-9][a-z0-9.\-]*[a-z0-9]"
    r"|\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]+)+(?:\.[a-zA-Z_]\w*)*"
    r"|\b[A-Z][a-z0-9]+\.[a-z]\w*(?:\.[a-zA-Z_]\w*)*"
)
LINK = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]")
SEP_ROW = re.compile(r"^\|[\s:|-]+\|?$")


def split_fm(text):
    lines = text.split("\n")
    if lines and lines[0] == "---" and "---" in lines[1:]:
        end = lines.index("---", 1)
        return lines[: end + 1], lines[end + 1 :]
    return [], lines


def tick(cell):
    """표 칸의 식별자에 백틱. 이미 백틱 안에 있는 것은 두지 않는다(표 칸에는 원래 백틱이 없다)."""
    if "`" in cell:
        return cell
    return IDENT.sub(lambda m: f"`{m.group(0)}`", cell)


def norm(s):
    return re.sub(r"[\s·#/|()\[\]_\-.,'\"`]+", "", s).lower()


def trivial_alias(target, alias):
    """별칭이 대상 경로·헤딩에 이미 있는 말뿐인가."""
    if target.startswith("daily history/"):
        return True
    t = norm(target)
    parts = [x for x in re.split(r"[\s·#/|()]+", alias) if x]
    if all(norm(x) in t for x in parts if norm(x)):
        return True
    generic = {"지도", "노트", "scope", "glossary", "skill", "record", "readme", "이", "폴더의", "목적", "의", "가이드", "daily", "history", "볼트", "제안", "oms", "tms", "쪽"}
    ko = {"어댑터": "omsadapter", "교환": "exchange", "반품": "returns", "흐름": "flow", "클레임": "claim", "정책": "policy", "기능": "action", "도메인": "domain", "용어": "glossary", "연동": "system", "출고": "shipment", "재고": "stock", "관장": "scope", "범위": "scope", "카카오": "kakao", "ssg": "ssg", "주문": "order", "프로모션": "promotion"}
    return all(norm(x) in t or norm(x) in generic or ko.get(norm(x), "~") in t for x in parts if norm(x))


def strip_aliases(line, kept):
    def rep(m):
        target, alias = m.group(1), m.group(2)
        if trivial_alias(target, alias):
            return f"[[{target}]]"
        kept.append((target, alias))
        return f"[[{target}]]({alias})"
    return LINK.sub(rep, line)


def table_to_records(rows):
    """rows: 표 줄 목록(머리, 구분, 데이터…). 라벨 줄 목록을 돌려준다."""
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head, data = cells[0], [c for r, c in zip(rows[1:], cells[1:]) if not SEP_ROW.match(r)]
    recs = []
    for row in data:
        row = (row + [""] * len(head))[: len(head)]
        recs.append([(h, tick(c)) for h, c in zip(head, row) if c])
    inline = [" | ".join(f"{h}: {c}" for h, c in rec) for rec in recs]
    if all(len(x) + 2 <= LINE_CAP for x in inline):
        return [f"- {x}" for x in inline], "inline"
    out = []
    for rec in recs:
        if not rec:
            continue
        out.append(f"- {rec[0][0]}: {rec[0][1]}")
        out += [f"  - {h}: {c}" for h, c in rec[1:]]
    return out, "block"


def convert(text, keywords):
    fm, body = split_fm(text)
    rep = {"tables_inline": 0, "tables_block": 0, "rows": 0, "nav": [], "alias_kept": [], "rel_dropped": [], "toc": 0}
    # frontmatter: 별칭 삭제(sources), keywords 삽입
    fm = [strip_aliases(l, rep["alias_kept"]) for l in fm]
    if keywords and not any(l.startswith("keywords:") for l in fm):
        have = set()
        ai = next((i for i, l in enumerate(fm) if l.startswith("aliases:")), None)
        if ai is not None:
            j = ai + 1
            while j < len(fm) and re.match(r"^\s+-\s", fm[j]):
                have.add(re.sub(r"^\s+-\s+", "", fm[j]).strip().strip('"'))
                j += 1
            pkg = next((l.split(":", 1)[1].strip() for l in fm if l.startswith("package:")), "")
            extra = [k for k in keywords if k not in have and k != pkg]
            if extra:
                fm.insert(j, "keywords: [" + ", ".join('"' + k.replace('"', "'") + '"' for k in extra) + "]")
    out, i, sec, code = [], 0, None, False
    while i < len(body):
        l = body[i]
        if l.startswith("```"):
            code = not code
            out.append(l)
            i += 1
            continue
        if code:
            out.append(l)
            i += 1
            continue
        if l.startswith("## "):
            sec = l[3:].strip()
            if sec == "목차":
                rep["toc"] += 1
                i += 1
                while i < len(body) and not body[i].startswith("## "):
                    i += 1
                continue
        if l.startswith("> ↑"):
            rep["nav"].append(l)
            i += 1
            continue
        if l.startswith("|"):
            j = i
            while j < len(body) and body[j].startswith("|"):
                j += 1
            rows = body[i:j]
            if len(rows) >= 2 and SEP_ROW.match(rows[1]):
                recs, kind = table_to_records(rows)
                rep["tables_" + kind] += 1
                rep["rows"] += len([r for r in rows[2:]])
                out += [strip_aliases(x, rep["alias_kept"]) for x in recs]
                i = j
                continue
        l = strip_aliases(l, rep["alias_kept"])
        if sec == "관련" and re.match(r"^- (노트|기능 노트|관련 노트):", l):
            items = re.findall(r"\[\[([^\]]+)\]\](?:\(([^()]*)\))?", l)
            rest = re.sub(r"\[\[[^\]]+\]\](?:\([^()]*\))?", "", l.split(":", 1)[1])
            if items and not re.sub(r"[\s,·.]+", "", rest):
                out += [f"- [[{t}]]" + (f" — {h}" if h else "") for t, h in items]
                rep["rel_split"] = rep.get("rel_split", 0) + 1
                i += 1
                continue
        out.append(l)
        i += 1
    cleaned = out
    final = []
    for x in cleaned:
        if x.strip() == "" and final and final[-1].strip() == "":
            continue
        final.append(x)
    return "\n".join(fm + final), rep


def map_keywords(record):
    """지도 줄 '- [[경로|이름]] — 설명. 키워드: a, b' 에서 노트 경로 → 키워드 목록."""
    kw = {}
    for ig in record.rglob("index-guide.md"):
        for l in ig.read_text(encoding="utf-8").split("\n"):
            m = re.match(r"^\s*- \[\[([^\]|#]+)(?:\|[^\]]*)?\]\].*?키워드:\s*(.+)$", l)
            if m:
                for k in [x.strip().rstrip(".") for x in m.group(2).split(",") if x.strip()]:
                    kw.setdefault(m.group(1), [])
                    if k not in kw[m.group(1)]:
                        kw[m.group(1)].append(k)
    return kw


def main():
    V = Path(sys.argv[1]).resolve()
    dry = "--dry" in sys.argv
    record = V / "record"
    kw = map_keywords(record)
    tot = {"before": 0, "after": 0, "inline": 0, "block": 0, "rows": 0, "toc": 0, "nav": 0, "rel": 0}
    kept, dropped, navs = [], [], []
    for p in sorted(record.rglob("*.md")):
        if p.name in SPECIAL:
            continue
        rel = p.relative_to(V).with_suffix("").as_posix()
        text = p.read_text(encoding="utf-8")
        new, rep = convert(text, kw.get(rel, []))
        tot["before"] += len(text.encode())
        tot["after"] += len(new.encode())
        tot["inline"] += rep["tables_inline"]
        tot["block"] += rep["tables_block"]
        tot["rows"] += rep["rows"]
        tot["toc"] += rep["toc"]
        tot["nav"] += len(rep["nav"])
        tot["rel"] += len(rep["rel_dropped"])
        kept += [(rel, t, a) for t, a in rep["alias_kept"]]
        dropped += [(rel, l) for l in rep["rel_dropped"]]
        navs += [(rel, l) for l in rep["nav"]]
        if new != text and not dry:
            p.write_text(new, encoding="utf-8")
    print(f"노트 bytes {tot['before']:,} → {tot['after']:,} ({(tot['after'] - tot['before']) * 100 / tot['before']:+.1f}%)")
    print(f"표 한 줄 꼴 {tot['inline']}개 · 머리+하위 줄 꼴 {tot['block']}개 · 행 {tot['rows']}개 · 목차 삭제 {tot['toc']} · 지도 줄 삭제 {tot['nav']} · 관련 줄 삭제 {tot['rel']}")
    print(f"괄호로 남긴 별칭 {len(kept)}개")
    for rel, t, a in kept:
        print(f"  {rel}: [[{t}]]({a})")
    if "--report" in sys.argv:
        rp = Path(sys.argv[sys.argv.index("--report") + 1])
        rp.write_text("\n".join([f"NAV {r}: {l}" for r, l in navs] + [f"REL {r}: {l}" for r, l in dropped]), encoding="utf-8")
        print(f"삭제한 줄 목록: {rp}")


if __name__ == "__main__":
    main()
