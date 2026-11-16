"""형식 변환 뒤 사실이 빠지지 않았는지 보는 점검. 사용: python3 verify.py <staging 루트> [<옛 노트 경로> [<새 노트 경로>,…]]

옛 노트는 staging 의 base-*.tgz(변환 전 볼트 사본)에서, 새 노트는 staging 에서 읽는다. 경로는 볼트 루트 기준(예 record/IICombined.Co/OMS/action/shipment.md).
노트 본문에서 백틱 식별자, 대문자_밑줄 이름, 티켓 키, 커밋 sha, 숫자, METHOD 경로, 위키링크 대상을 모아 옛 것이 새 것에 모두 있는지 본다.
지우기로 한 것(목차 절, '> ↑' 지도 줄)은 빼고 센다. 인자가 없으면 base 에 있는 모든 record 노트를 같은 경로끼리 본다.
빠진 것이 있으면 노트마다 한 줄씩 내고 종료 코드 1. 문장 뜻이 바뀌었는지는 이 점검으로 알 수 없다.
"""
import re, sys, tarfile
from pathlib import Path

SPECIAL = {"index-guide.md", "SKILL.md", "README.md"}


def body(t):
    ls = t.split("\n")
    if ls and ls[0] == "---" and "---" in ls[1:]:
        return "\n".join(ls[ls.index("---", 1) + 1:])
    return t


def toks(t):
    t = body(t)
    t = re.sub(r"(?s)\n## 목차\n.*?(?=\n## )", "\n", t)
    t = "\n".join(l for l in t.split("\n") if not l.startswith("> ↑") and not l.startswith("> 절:"))
    links = {m.split("|")[0].strip() for m in re.findall(r"\[\[([^\]]+)\]\]", t)}
    links = {l for l in links if not l.startswith("#")}
    t = re.sub(r"\[\[[^\]]*\]\]", " ", t)
    out = {"`" + x for x in re.findall(r"`([^`\n]+)`", t)}
    plain = t.replace("`", " ")
    out |= set(re.findall(r"\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b", plain))
    out |= set(re.findall(r"\b(?:OMS|IICQA|TEST)-\d+\b", plain))
    out |= set(re.findall(r"\b[0-9a-f]{8}\b", plain))
    out |= {"#" + x for x in re.findall(r"(?<![\w.])\d+(?:[.,]\d+)?(?![\w])", plain)}
    out |= set(re.findall(r"(?:GET|POST|PUT|PATCH|DELETE) /[^\s`,;()·|]+", plain))
    return out, links


def unticked(s):
    """표 칸에서 온 식별자는 변환기가 백틱을 붙였으므로 백틱 유무는 가리지 않는다."""
    return {x.lstrip("`") for x in s}


def main():
    N = Path(sys.argv[1]).resolve()
    tar = tarfile.open(sorted(N.glob("base-*.tgz"))[-1])
    names = set(tar.getnames())
    if len(sys.argv) >= 3:
        old = sys.argv[2]
        pairs = [(old, sys.argv[3].split(",") if len(sys.argv) >= 4 else [old])]
    else:
        pairs = []
        for n in sorted(names):
            if n.startswith("record/") and n.endswith(".md") and Path(n).name not in SPECIAL and not Path(n).name.startswith("._"):
                p = N / n
                sib = sorted(p.parent.glob(p.stem + "-*.md"))
                pairs.append((n, [n] + [str(s.relative_to(N)) for s in sib]))
    bad = 0
    for old, news in pairs:
        if old not in names:
            print(f"옛 노트가 base 에 없다: {old}")
            bad += 1
            continue
        a, la = toks(tar.extractfile(old).read().decode("utf-8"))
        b, lb = set(), set()
        for n in news:
            p = N / n
            if not p.exists():
                print(f"새 노트가 없다: {n}")
                bad += 1
                continue
            x, y = toks(p.read_text(encoding="utf-8"))
            b |= x
            lb |= y
        miss = sorted(unticked(a) - unticked(b))
        lmiss = sorted(la - lb)
        if miss or lmiss:
            bad += 1
            print(f"{old}: 빠진 식별자·숫자 {len(miss)}개 {miss[:12]} · 빠진 링크 {len(lmiss)}개 {lmiss[:6]}")
    print(f"노트 {len(pairs)}개 · 빠진 것이 있는 노트 {bad}개")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
