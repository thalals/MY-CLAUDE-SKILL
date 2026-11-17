#!/usr/bin/env python3
"""평가용 사본을 만든다. 실제 장부를 건드리지 않고, 대화 맥락이 없는 새 세션에서 이 스킬을 돌려 보기 위한 것이다.

  eval_copy.py <프로젝트 폴더> [--name 이름] [--synthetic N]

<프로젝트 폴더>/.claude/skills/<이름>/ 에 이 스킬을 복사하고, 스킬 이름을 바꾸고(사용자 스킬과 이름이 같으면 사용자 스킬이 불린다),
닫기 단계의 백업을 평가 안내로 바꾼다. --synthetic N 은 합성 사실 N개와 합성 방향 N개를 더해 장부가 쌓였을 때를 흉내 낸다.
돌리는 법과 기대 결과는 evals/scenarios.md 에 있다.
"""
import argparse
import random
import re
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
NOTICE = ("평가 사본이다. 장부는 이 스킬 폴더 안에서만 고친다. 다른 스킬, 설정, 볼트, iCloud, 저장소는 건드리지 않고 sync.sh 도 돌리지 않는다."
          " 사용자에게 물을 수 없으니 정할 것은 보고에 남긴다. 보고 끝에 이 스킬을 따르다 걸린 곳을 적는다.")
BACKUP = re.compile(r"그 뒤 스킬 폴더를 iCloud .*?를 돌린다\.")
SKILLS = ["record-obsidian", "collect-feedback", "collect-worklog", "jira", "pr-summary"]
METRICS = [("본 대화 호출", 8, 60), ("시작 맥락", 40000, 600000), ("서브에이전트 호출", 5, 70),
           ("첫 호출 캐시 쓰기", 5000, 500000), ("출력 토큰", 5000, 200000), ("누적 입력", 500000, 30000000)]
CONDS = ["새 세션에서", "오래 쓴 세션에서", "쉬었다가 이어서", "Sonnet 으로", "Opus 로", "주제가 둘인 대화에서", "서브에이전트를 쓰지 않고", "평가 시나리오에서"]
CLOSED = ["보류", "기각", "기각", "보류", "먼저 잰다"]


def synthetic(dest, count, seed=7):
    rnd, R = random.Random(seed), dest / "research"
    fmax = max(int(p.stem[2:]) for p in (R / "findings").glob("F-*.md"))
    dmax = max(int(p.stem[2:]) for p in (R / "directions").glob("D-*.md"))
    for i in range(1, count + 1):
        skill, (metric, lo, hi), cond = rnd.choice(SKILLS), rnd.choice(METRICS), rnd.choice(CONDS)
        v, n, month, day, state = rnd.randint(lo, hi), rnd.randint(3, 40), rnd.randint(6, 10), rnd.randint(1, 28), rnd.choice(CLOSED)
        fid, did, date = f"F-{fmax + i:02d}", f"D-{dmax + i:02d}", f"2026-{month:02d}-{day:02d}"
        (R / "findings" / f"{fid}.md").write_text(
            f"# {fid} {skill} 의 {metric} 중앙값은 {cond} {v:,} 이었다\n- 상태: 유효\n- 갈래: 절차\n- 세기: 관측 반복 ({n}번, 합성 자료)\n- 확인: {date}\n"
            f"- 근거: `stats --skill {skill} --since 2026-{month:02d}-01` → {n}번, {metric} 중앙값 {v:,}.\n"
            f"- 사실: {skill} 을 {cond} 부르면 {metric} 중앙값이 {v:,} 이었다.\n"
            f"- 한계: 평가용으로 만든 합성 항목이다. 실제로 잰 값이 아니다.\n- 다시 볼 때: 쓰지 않는다\n", encoding="utf-8")
        (R / "directions" / f"{did}.md").write_text(
            f"# {did} {skill} 의 {metric} 을 줄인다\n- 상태: {state} ({date})\n- 갈래: 절차\n- 대상: {skill}\n"
            f"- 근거: {fid}({metric} 중앙값 {v:,}). 평가용으로 만든 합성 항목이다.\n- 방법: 합성 항목이라 방법이 없다.\n"
            + ("- 결과: 합성 항목이라 결과가 없다.\n" if state == "기각" else ""), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--name", default="lab-eval")
    ap.add_argument("--synthetic", type=int, default=0)
    a = ap.parse_args()
    dest = Path(a.project).expanduser().resolve() / ".claude" / "skills" / a.name
    if dest.exists():
        sys.exit(f"이미 있다: {dest}")
    shutil.copytree(SKILL, dest, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    md = dest / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    text, k1 = re.subn(r"^name: .*$", f"name: {a.name}", text, count=1, flags=re.M)
    text, k2 = BACKUP.subn(NOTICE, text, count=1)
    text, k3 = re.subn(r"^(# research-efficiency\n)", rf"\1\n> {NOTICE}\n", text, count=1, flags=re.M)
    if not (k1 and k2 and k3):
        sys.exit(f"스킬 본문에서 바꿀 자리를 찾지 못했다(이름 {k1}, 백업 문장 {k2}, 제목 {k3}). 본문이 바뀌었으면 이 도구도 고친다.")
    md.write_text(text, encoding="utf-8")
    if a.synthetic:
        synthetic(dest, a.synthetic)
    print(f"{dest}\n  부르는 법: cd {dest.parents[2]} && claude -p \"/{a.name} <초점>\" ...  (evals/scenarios.md)")


if __name__ == "__main__":
    main()
