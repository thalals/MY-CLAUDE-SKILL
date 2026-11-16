# 이 스킬과 도구를 고칠 때

## 고치는 조건과 순서

- 이 스킬(SKILL.md, reference, scripts)은 사용자가 확인한 제안이나 사용자의 직접 지시로만 고친다(`reference/proposals.md`).
- 고친 뒤 `evals/scenarios.md` 의 시나리오(A·B·C·D)를 서브에이전트로 다시 돌려 기대 결과와 비교한다. 어긴 것은 문장을 고치고 다시 돌린다.
- 타임라인·시작·알림 도구를 고치면 `python3 -B "<스킬>/evals/test_session_tools.py"` 로 두 원본 형식, 활동 시각, 기존 알림 이행을 검증한다. 시험은 임시 입력과 별도 상태 파일만 쓴다.
- 스킬 폴더째(SKILL.md, reference, scripts, evals) iCloud `claude/skills/record-obsidian/` 에 백업하고 전역 CLAUDE.md 의 동기화 스크립트를 돌린다.
- 볼트 도구(`record/visit.py`, `build-index.py`, `record-lint.py`)를 고치거나 더하면 `record/index-guide` 와 볼트 루트 지도의 도구 줄을 고친다. 스킬 도구를 더하면 SKILL.md 의 참고 파일과 이 파일에 적는다.

## 크기 원칙

- SKILL.md 는 불러온 뒤 매 호출 다시 읽히고, 대화가 압축되면 앞 5,000 토큰만 다시 붙는다(Claude Code skills 문서). 본 대화가 하는 일만 두고 10KB 안팎을 넘기지 않는다. 이 볼트의 한국어 글은 1 byte 에 0.4~0.6 토큰쯤이다.
- 서브에이전트만 쓰는 절차는 `reference/record-run.md`, 드물게 쓰는 절차는 reference 의 다른 파일에 둔다. 규칙 본문은 볼트 규칙 파일에만 두고 여기에 옮겨 쓰지 않는다.

## 스킬 도구

- `scripts/start.py`: 1단계 시작 출력. 오늘 날짜, daily SKILL 전문, 열린 제안과 마지막 전체 검진, 오늘 날짜 노트의 frontmatter·주제 목록, 이 세션의 기록 범위와 그 뒤 타임라인을 한 번에 낸다. `--session`, `--vault`.
- `scripts/timeline.py`: Claude·Codex 원본(jsonl)의 사용자 발언·명령·질문 답변·도구 거절 KST 시각. `--tools` 는 도구 호출, `--span` 은 날짜별 실제 활동 범위. 경로를 생략하면 현재 디렉터리의 최근 Claude 세션을 읽는다.
- Codex 원본은 `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` 이며 ID 앞부분으로도 찾는다. 주입된 지침·메타 정보와 중복 미러 이벤트는 제외한다.
- `scripts/session_hook.py` 는 Claude 훅 전용이고, 2026-11-11 부터 `~/.claude/settings.json` 에 등록하지 않는다. 기록은 사용자가 명령할 때만 하며, 기록하지 않은 세션을 자동으로 검사하거나 기록할지 묻지 않는다. 등록하면 SessionEnd 는 사용자 발언 3개 이상인 세션의 마지막 실제 활동 시각·원본 경로·종료 시각을 `~/.claude/record-obsidian/pending.tsv` 에 남기고, SessionStart 는 timeline.py 와 같은 기준으로 원본의 마지막 활동을 다시 읽어 daily sessions 의 끝 시각과 분 단위로 비교한다. 예전 4열 목록도 원본을 찾으면 보정하고, 원본이 없으면 기존 시각을 유지한다. 14일 보관 기준은 실제 종료 시각이다. Codex 훅 설치는 포함하지 않는다.
