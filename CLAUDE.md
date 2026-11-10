# Global Instructions

## 사용자 스타일 참조 파일

- 스타일 폴더: `/Users/hyeongminpark/Library/Mobile Documents/com~apple~CloudDocs/claude/style/`
- 세션을 시작하면 **`index.md` 만** 읽는다. 읽는 법, 우선순위 테마, 주제 파일 목록(파일 — 읽는 때 — 규칙 제목)이 있다.
- 주제 파일(`code/*.md`, `work/*.md`)은 `index.md` 의 '작업별 최소 세트' 표에서 지금 작업 행의 '반드시' 파일을 작업 전에 읽고, '해당하면' 은 조건이 맞는 것만 읽는다. 폴더 전체를 미리 읽지 않는다.
- 어느 행인지 애매하거나 표에 없는 작업이면 추측하지 말고, 읽을 후보 파일과 추천을 한 줄로 내어 작업 전에 사용자에게 묻는다.
- 서브에이전트에 코드·문서 작업을 맡길 때는 프롬프트에 읽을 주제 파일 경로를 적는다.

## 피드백 수집 규칙

대화 중 사용자가 피드백에 해당하는 발언을 하면, `/collect-feedback` 스킬을 통해 스타일 폴더의 주제 파일에 반영한다.

**호출 시점(트리거)의 단일 소스는 `collect-feedback` 스킬 frontmatter 의 `when_to_use`** — 스킬 목록으로 매 세션 노출되므로 여기에 중복 기재하지 않는다. 트리거 변경은 스킬 파일에서만 한다.

**주의:** `/exit`, `/clear`, `Ctrl+C` 는 CLI가 즉시 처리하므로 피드백 수집 불가. 종료 전 `/collect-feedback` 을 먼저 실행하거나 종료 의사를 메시지로 전달할 것.

세부 수집 대상, 분류 기준, 업데이트 방식은 `collect-feedback` 스킬 참조.

## iCloud 백업 규칙

아래 항목이 생성/수정되면, iCloud 경로에 동일한 내용을 복사하여 복원 데이터를 유지한다.

| 원본 | 백업 대상 | 타이밍 |
|------|-----------|--------|
| `~/.claude/CLAUDE.md` | `iCloud/claude/CLAUDE.md` | 수정 시 즉시 |
| `~/.claude/skills/` | `iCloud/claude/skills/` | 스킬 생성/수정 시 즉시 |

- iCloud 경로: `/Users/hyeongminpark/Library/Mobile Documents/com~apple~CloudDocs/claude/`
- 스킬 백업은 변경된 스킬 디렉토리만 복사 (`cp -r ~/.claude/skills/<skill-name>/ iCloud/claude/skills/<skill-name>/`)
- iCloud 에 복사한 뒤에는 `bash "$HOME/Desktop/hmin/MY-CLAUDE-SKILL/.sync/sync.sh"` 를 실행해 개인 GitHub 저장소(`~/Desktop/hmin/MY-CLAUDE-SKILL`)에도 올린다. 바뀐 것이 없으면 커밋하지 않는다

## 시스템 사전 (Obsidian record)

- 볼트: `/Users/hyeongminpark/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian` (경로에 공백이 있어 따옴표로 감싼다)
- OMS(iic-oms)의 동작, 저장소 밖 호출자·구독자, 상태·불변식, 관장 범위, 결정 이유를 답하거나 코드를 바꾸기 전에 record 를 본다. 입구는 `record/IICombined.Co/OMS/index-guide.md` 이고, 질문에 경로·토픽·env 키·클래스·티켓 키가 있으면 `record/` 를 그 문자열로 먼저 검색한다.
- 믿는 순서: 지금 코드(origin/develop)·실측 > record > daily history > 저장소 docs·auto memory 의 시스템 사실. 서로 다르면 사용자에게 알린다.
- record 노트를 근거로 쓰기 전에 frontmatter `basis` 이후 변경을 본다: `git log --oneline <basis sha>..origin/develop -- <paths>`. 저장소 위치: iic-oms `/Users/hyeongminpark/Desktop/iic/iic-oms`, oms-adapter `/Users/hyeongminpark/Desktop/iic/oms-adapter`
- 지난 작업의 경위는 `daily history/index-guide.md`(시스템별)·`date-guide.md`(날짜별)에서 찾고, 날짜 노트(`daily history/YYYY/MM/YYYY-MM-DD.md`)는 `## ` 줄로 주제를 찾아 그 범위만 읽는다.
- 대화를 기록하거나 record 를 고칠 때는 `record-obsidian` 스킬로 한다. 규칙 본문은 `daily history/SKILL.md`·`record/SKILL.md` 이고, 구조·규칙·스킬을 바꾸자는 제안은 볼트 루트 `proposals.md` 에 올려 사용자 확인을 받은 뒤 반영한다.
- 서브에이전트에 시스템 질문을 맡길 때는 볼트 경로와 입구 경로를 프롬프트에 적는다.
