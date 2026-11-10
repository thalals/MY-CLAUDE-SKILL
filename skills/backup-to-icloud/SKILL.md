---
name: backup-to-icloud
description: Use when ~/.claude/CLAUDE.md or ~/.claude/skills/ is created/modified, or when user invokes /backup-to-icloud — syncs local Claude config changes to iCloud backup
---

# Backup to iCloud

`~/.claude/CLAUDE.md` 와 `~/.claude/skills/` 를 iCloud 백업 폴더와 동기화한다.

## 호출 시점

- 사용자가 `/backup-to-icloud` 으로 직접 호출
- `~/.claude/CLAUDE.md` 를 수정한 직후 자동 실행
- `~/.claude/skills/<skill>/` 를 생성/수정한 직후 자동 실행

## 백업 대상

| 원본 | 백업 대상 |
|------|-----------|
| `~/.claude/CLAUDE.md` | `iCloud/claude/CLAUDE.md` |
| `~/.claude/skills/<skill>/` | `iCloud/claude/skills/<skill>/` |

iCloud 경로: `~/Library/Mobile Documents/com~apple~CloudDocs/claude/`

## 백업 대상 외

- `style/` — iCloud 가 source-of-truth (CLAUDE.md 가 iCloud 경로를 직접 참조). 로컬 복사본 없음.

## 실행 절차

1. **변경 사항 탐지**
   - CLAUDE.md: `diff ~/.claude/CLAUDE.md "$ICLOUD/CLAUDE.md"` 로 비교
   - skills: `diff -rq ~/.claude/skills "$ICLOUD/skills"` 로 한 번에 전체 비교
   - `$ICLOUD` = `~/Library/Mobile Documents/com~apple~CloudDocs/claude`
2. **변경 요약 출력** — 무엇이 다른지(추가/수정/iCloud-only) 사용자에게 표시
3. **복사 실행** — 변경된 항목만 복사
   - CLAUDE.md 변경: `cp ~/.claude/CLAUDE.md "$ICLOUD/CLAUDE.md"`
   - 새/수정된 스킬: `cp -R ~/.claude/skills/<name>/ "$ICLOUD/skills/<name>/"`
4. **검증** — 복사 후 `diff` 결과가 비어있는지 확인 (실패 시 즉시 중단/보고)
5. **GitHub 동기화** — 복사한 항목이 있으면 `bash "$HOME/Desktop/hmin/MY-CLAUDE-SKILL/.sync/sync.sh"` 를 실행한다. iCloud `claude` 폴더를 개인 저장소에 복사해 바뀐 것만 커밋·push 한다. 검증이 실패했으면 실행하지 않는다
6. **결과 보고** — 복사된 항목 목록과 저장소의 `.sync/sync.log` 마지막 줄

## 규칙

- **iCloud-only 항목은 삭제하지 않는다** — 다른 머신에서 백업한 스킬일 수 있음. 변경 요약에만 노출.
- **백업 전 변경 사항을 사용자에게 먼저 알린다** — "아무것도 안 묻고 덮기"는 금지.
- **검증 실패 시 즉시 중단** — diff 가 비어있지 않으면 보고하고 종료.
- **이 스킬 자체가 수정되면 본인도 백업 대상** (`backup-to-icloud/SKILL.md`).

## 주의: 경로 하드코딩

CLAUDE.md 와 일부 스킬에 `/Users/hmin/...` 같은 하드코딩된 경로가 포함될 수 있다. iCloud 백업에도 그대로 복사되며, 다른 사용자명의 머신에서 복원 시 경로 치환이 필요하다. 이 스킬은 치환을 수행하지 않는다 — 복원 시점의 책임.
