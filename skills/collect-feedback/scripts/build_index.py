"""스타일 색인(index.md)의 '파일 목록' 을 주제 파일에서 다시 만든다.
사용: python3 build_index.py [style 폴더]
- 주제 파일(code/*.md, work/*.md)의 둘째 줄 인용 `> 읽는 때: …` 과 `### ` 제목에서 목록을 만든다. 단일 소스는 주제 파일이다.
- index.md 의 `<!-- files:start -->` 와 `<!-- files:end -->` 사이만 바꾼다.
- 파일마다 크기와 항목 수를 내고, 상한(20KB)을 넘은 파일을 알린다.
"""
import re
import sys
from pathlib import Path

STYLE = Path(sys.argv[1] if len(sys.argv) > 1 else
             "/Users/hyeongminpark/Library/Mobile Documents/com~apple~CloudDocs/claude/style")
LIMIT = 20_000
START, END = "<!-- files:start -->", "<!-- files:end -->"
PAREN = re.compile(r"\s\((?:20\d\d|보강|정정|병합|YAGNI)[^)]*\)\s*$")


def short(title):
    return PAREN.sub("", title).split(" — ")[0].strip()


lines, over = [], []
for path in sorted(STYLE.glob("code/*.md")) + sorted(STYLE.glob("work/*.md")):
    text = path.read_text(encoding="utf-8")
    when = re.search(r"^> 읽는 때: (.+?)\. 색인은", text, re.M)
    if not when:
        sys.exit(f"'> 읽는 때: …. 색인은 `index.md`.' 줄이 없다: {path}")
    titles = [short(t) for t in re.findall(r"^### (.+)$", text, re.M)]
    rel = path.relative_to(STYLE).as_posix()
    size = path.stat().st_size
    lines.append(f"- `{rel}` — {when.group(1)}")
    lines.append("  " + " · ".join(titles))
    print(f"{size:6d}B  {len(titles):2d}항목  {rel}")
    if size > LIMIT:
        over.append(rel)

index = STYLE / "index.md"
text = index.read_text(encoding="utf-8")
if text.count(START) != 1 or text.count(END) != 1:
    sys.exit("index.md 에 files:start / files:end 표시가 하나씩 있어야 한다")
head, rest = text.split(START)
tail = rest.split(END)[1]
index.write_text(head + START + "\n" + "\n".join(lines) + "\n" + END + tail, encoding="utf-8")
print(f"{index.stat().st_size:6d}B  index.md")
if over:
    print("상한 20KB 초과(파일을 나눌 것):", ", ".join(over))
