"""라벨 줄의 값 '위와 같음'(또는 '위와 같다' 로 시작하는 값)을 같은 묶음 바로 앞 기록의 같은 라벨 값으로 바꾼다. 사용: python3 resolve_same.py <staging 루트>
묶음은 한 H2 안에서 빈 줄 없이 이어진 라벨 줄(한 줄 꼴 `- A: x | B: y`, 머리+하위 줄 꼴)이다. 앞 기록에 그 라벨이 없으면 그대로 둔다."""
import re, sys
from pathlib import Path
N = Path(sys.argv[1]); SAME = re.compile(r"^(위와 같음|위와 같다)(?=$|[,.·] )")
done = left = 0
for p in sorted((N / "record").rglob("*.md")):
    if p.name in ("index-guide.md", "SKILL.md", "README.md"): continue
    lines = p.read_text(encoding="utf-8").split("\n"); last = {}; changed = False; code = False
    for i, l in enumerate(lines):
        if l.startswith("```"): code = not code
        if code or l.startswith("#") or not l.strip():
            last = {}; continue
        m = re.match(r"^(\s*)- (.*)$", l)
        if not m:
            last = {}; continue
        ind, rest = m.groups()
        parts = rest.split(" | ") if not ind else [rest]
        out = []
        for part in parts:
            km = re.match(r"^([^:|]{1,20}): (.*)$", part)
            if not km: out.append(part); continue
            k, v = km.groups()
            sm = SAME.match(v)
            if sm and k in last:
                v = last[k] + v[sm.end():]; done += 1; changed = True
            elif sm:
                left += 1
            last[k] = v; out.append(f"{k}: {v}")
        lines[i] = ind + "- " + " | ".join(out)
    if changed: p.write_text("\n".join(lines), encoding="utf-8")
print(f"바꾼 값 {done}개 · 앞 기록이 없어 둔 값 {left}개")
