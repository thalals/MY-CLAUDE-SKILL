#!/bin/bash
# iCloud claude 폴더를 이 저장소로 복사하고, 바뀐 것이 있으면 커밋·push 한다.
# 사용: .sync/sync.sh [--no-push]
set -euo pipefail
SRC="$HOME/Library/Mobile Documents/com~apple~CloudDocs/claude"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO/.sync/sync.log"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

# 여러 세션의 훅이 동시에 돌면 하나만 실행한다
LOCK="$REPO/.sync/.lock"
mkdir "$LOCK" 2>/dev/null || exit 0
trap 'rmdir "$LOCK"' EXIT

[ -d "$SRC" ] || { log "중단: 원본 폴더가 없다"; exit 1; }
# iCloud 가 내려받지 않은 파일(.icloud 자리 표시)이 있으면 삭제로 오인하지 않게 멈춘다
if find "$SRC" -name "*.icloud" -not -path "*/.Trash/*" | grep -q .; then
  log "중단: 내려받지 않은 iCloud 파일이 있다"; exit 1
fi

rsync -a --delete --exclude-from="$REPO/.sync/exclude.txt" "$SRC/" "$REPO/"
cd "$REPO"
git add -A
if git diff --cached --quiet; then exit 0; fi

# 비밀값처럼 보이는 내용이 새로 들어오면 커밋하지 않는다
PATTERN='(gh[opsu]_[A-Za-z0-9]{20,}|xox[bap]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|ntn_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|(password|passwd|secret|token|api[_-]?key)["'"'"' ]*[:=] *["'"'"']?[A-Za-z0-9+/_=-]{16,})'
if git diff --cached -U0 | grep -E '^\+' | grep -Eiq "$PATTERN"; then
  git reset -q
  log "중단: 비밀값으로 보이는 내용이 있어 커밋하지 않았다"; exit 2
fi

COUNT=$(git diff --cached --name-only | wc -l | tr -d ' ')
git commit -q -m "sync: $(date '+%Y-%m-%d %H:%M') (${COUNT} files)"
log "커밋: ${COUNT} files"
if [ "${1:-}" != "--no-push" ]; then
  git push -q origin main && log "push 완료" || { log "push 실패"; exit 3; }
fi
