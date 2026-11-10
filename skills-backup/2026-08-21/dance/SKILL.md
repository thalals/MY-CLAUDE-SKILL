---
name: dance
description: Use when user invokes /dance to display a fun ASCII dance animation in chat with optional mood (happy, sad, excited, chill, love, angry, party, sleepy). Also triggered when user expresses a mood and wants Claude to dance for them. Shows the terminal command for real animated playback.
---

# Dance Skill

## Overview

채팅창에서 ASCII 댄스 애니메이션을 플립북 스타일로 보여주고, 실제 움직이는 버전을 실행할 수 있는 터미널 명령어를 안내한다. 기분(mood)에 따라 타이틀/댄서/디스코볼/음표/장식/하단 메시지가 전부 달라진다.

실제 스크립트는 `~/dance.sh` 에 있고, mood를 인자로 받는다.

## When to Use

- 사용자가 `/dance` 를 직접 호출했을 때
- 사용자가 `/dance happy`, `/dance sad` 처럼 기분을 명시한 경우
- 사용자가 "춤춰줘", "기분 안 좋아 춤좀", "신나는 거 보여줘" 같이 댄스를 요청할 때
- 사용자가 mood 목록을 물어보면 → 아래 "Mood Catalog" 섹션 안내

## Workflow

1. **`~/dance.sh` 존재 확인 (가장 먼저)**
   - Bash 도구로 `test -f ~/dance.sh && echo exists || echo missing` 실행
   - **없으면** → 아래 "Script Template" 섹션의 절차대로 생성. 사용자에게 "스크립트가 없어서 새로 만들었어요" 한 줄 안내
   - **있으면** → 다음 단계로
2. **기분 결정 (mood selection)**
   - 인자가 명시되면 그대로 사용 (예: `/dance sad` → `sad`)
   - 사용자가 "랜덤", "아무거나", "뭐든", `random` 등을 말하면 → `random` mood 사용 (스크립트가 알아서 8개 중 하나 무작위 선택)
   - 인자가 한국어/자연어면 매핑 (예: "슬퍼" → `sad`, "신나" → `excited`, "사랑해" → `love`, "졸려" → `sleepy`, "빡쳐" → `angry`)
   - 인자가 없으면 → 대화 맥락에서 추론 (사용자 직전 발화의 감정 톤). 맥락도 없으면 `happy` 기본값
   - 사용자가 `list`, `목록`, "뭐 있어?" 등을 요청하면 → Mood Catalog 표시
3. **채팅창에 플립북 출력** — 해당 mood의 프레임 4~6개를 한 번에 출력 (실제 애니메이션은 채팅창에서 렌더링 안 되므로 플립북으로). ANSI 색상 코드는 빼고 **이모지로 톤** 을 살린다.
   - `random` 인 경우 → 채팅창에서도 Bash로 `(MOODS=(happy sad excited chill love angry party sleepy); echo ${MOODS[$RANDOM % 8]})` 같이 무작위 mood 하나 뽑은 뒤 그 mood로 플립북 출력
4. **터미널 실행 명령어 안내** — 항상 마지막에 아래 문구 포함:
   ```
   진짜 움직이는 버전:
   bash ~/dance.sh [mood]
   ```
5. **mood 목록 안내** — 한 줄로 `happy / sad / excited / chill / love / angry / party / sleepy / random` 또는 `bash ~/dance.sh list` 명령 안내

## Script Template

스킬 실행 시 `~/dance.sh` 가 없으면 **다음 우선순위로 복원**한다:

1. **1순위 — 스킬 디렉토리 백업** (가장 최신 보장):
   ```bash
   cp ~/.claude/skills/dance/dance.sh ~/dance.sh && chmod +x ~/dance.sh
   ```

2. **2순위 — iCloud 백업**:
   ```bash
   cp "/Users/hyeongminpark/Library/Mobile Documents/com~apple~CloudDocs/claude/dance.sh" ~/dance.sh && chmod +x ~/dance.sh
   ```

3. **3순위 — 둘 다 없는 경우**:
   사용자에게 "스크립트 백업이 다 없어서 못 만들었어요. 이전 대화 기록에서 복원이 필요해요." 안내 후 일단 채팅 플립북만 보여준다.

**중요:** 절대 인라인으로 새 dance.sh 를 작성하지 말 것. 사용자의 기존 mood 설정/안무가 유실됨. 반드시 백업본 복사로만 복원한다.

## Mood Catalog

각 mood는 **댄서 5명** + **디스코볼** + **음표/별 장식** + **하단 메시지** + **속도** 로 구성. 4~6프레임 반복.

### `happy` 🌈 (기본값) — 0.25초/프레임
- 타이틀: `✨🪩 GENTLE DISCO NIGHT 🪩✨`
- 댄서: `┏(^o^)┓ ┏(•_•)┛ ┗(^_^)┓ ┏(◕‿◕)┛ ┏(❛◡❛)┓`
- 디스코볼: ◉◉◉◉ / ◎◉◎◉ / ◉◎◉◎ / ✦◉✦◉
- 장식: `♪ ♫ ♬ ♩ ♭` + 별 `✦ * ✧`
- 하단: `🎉 PARTY TIME! 🎉`

### `sad` 💧 — 0.55초/프레임 (느림)
- 타이틀: `💧🌧 SAD BLUES NIGHT 🌧💧`
- 댄서: `╮(T_T)╭ ╮(；ω；)╭ ╮(◞‸◟)╭ ╮(╥﹏╥)╭ ╮(；﹏；)╭` (팔 축 늘어짐)
- 디스코볼: ☔☔☔ / 🌧🌧🌧
- 장식: `💧 ☔ 🌧 ☁` + `.` `·` (조용히)
- 하단: `💧 RAINY NIGHT... 💧`
- 동작: 팔 늘어짐 → 가만히 → 고개 숙임 → 가만히 (미니멀)

### `excited` ⚡ — 0.14초/프레임 (빠름)
- 타이틀: `⚡🔥 EXCITED RAVE NIGHT 🔥⚡`
- 댄서: `┏(≧∇≦)┓ ┏(★ω★)┛ ┗(≧▽≦)┓ ┏(✧∀✧)┛ ┏(◕‿◕)┓`
- 디스코볼: ⚡⚡⚡ / 💥💥💥 / 🔥🔥🔥 / ★★★
- 장식: `!!! ♪ ♬ 💥 ⚡ 🔥 ★`
- 하단: `⚡ RAVE ON!!! ⚡`

### `chill` 😎 — 0.45초/프레임 (느긋)
- 타이틀: `😎🌙 CHILL LOUNGE NIGHT 🌙😎`
- 댄서: `~(¬‿¬) ~(•̀ᴗ•́) ~( ͡° ͜ʖ ͡°) ~(⌐■_■) ~(￣ω￣)` (좌우 ~ 스웨이)
- 디스코볼: ☾☾☾ / ✧✧✧ / ◐◐◐ / ◑◑◑
- 장식: `~ ✧ ☾ ♪ ♫`
- 하단: `😎 STAY COOL 😎`

### `love` 💕 — 0.28초/프레임
- 타이틀: `💕💖 LOVE NIGHT 💖💕`
- 댄서: `┏(♡‿♡)┓ ┏(´∀｀)┛ ┗(◕‿◕)┓ ┏(♥‿♥)┛ ┏(˃‿˂)┓`
- 디스코볼: ❤❤❤ / ♡♡♡ / 💕💕💕 / ♥♡♥
- 장식: `❤ ♡ 💕 💖 💗 ✨`
- 하단: `💕 SPREAD THE LOVE 💕`

### `angry` 🔥 — 0.16초/프레임
- 타이틀: `🔥💢 ANGRY MOSH PIT 💢🔥`
- 댄서: `┏(╬ಠ益ಠ)┓ ┏(ಠ益ಠ)┛ ┗(`0´)┓ ┏(¬_¬")┛ ┏(`Д´)┓` (스피드라인 彡彡)
- 디스코볼: 💢💢💢 / 🔥🔥🔥 / ⚡⚡⚡ / 💥💥💥
- 장식: `💢 🔥 ⚡ 💥 !!`
- 하단: `🔥 LET IT OUT! 🔥`

### `party` 🎉 — 0.2초/프레임 (믹스)
- 타이틀: `🎉🪩 MEGA PARTY NIGHT 🪩🎉`
- 댄서: happy + excited + love + chill + cool 의 짬뽕 — `┏(^o^)┓ ┏(≧∇≦)┛ ┗(♡‿♡)┓ ┏(¬‿¬)┛ ┏(★ω★)┓`
- 디스코볼: 🪩🪩🪩 / ★★★★ / ◉◉◉◉ / 🎉🎉🎉
- 장식: `🎉 🪩 🎊 ♪ ♬ ✨ ★`
- 하단: `🎉 MEGA PARTY MODE! 🎉`

### `sleepy` 😴 — 0.7초/프레임 (매우 느림)
- 타이틀: `😴🌙 SLEEPY LULLABY 🌙😴`
- 댄서: `(￣o￣).zZ (∪｡∪).zZ (꒪⌓꒪).zZ (´；ω；\`).z (´-ω-\`).z`
- 디스코볼: 🌙🌙🌙 / ⭐⭐⭐ / ☾☾☾☾ / 💤💤💤
- 장식: `💤 🌙 ☾ zzz ⭐ ✦`
- 하단: `😴 ZZZ... GOOD NIGHT 😴`
- 동작: z 개수만 조금씩 변동 (잠 자고 있음)

## Output Format (채팅창)

ANSI 색상 코드는 채팅창에서 raw escape `[31m` 로 그대로 찍히므로 **이모지로 톤을 표현**한다. 코드 펜스로 감싸도 되고 raw 출력도 OK.

예시 (happy):
```
🌈  H A P P Y   D I S C O  🌈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   ♪  ♫  ♬  ♩  ♭        ← 음표
        🪩 ◉◉◉◉ 🪩        ← 디스코볼

  ┏(^o^)┓  ┏(•_•)┛  ┗(^_^)┓  ┏(◕‿◕)┛  ┏(❛◡❛)┓
  ┗(^o^)┛  ┗(•_•)┓  ┏(^_^)┛  ┗(◕‿◕)┓  ┗(❛◡❛)┛
  ＼(^o^)／ ＼(•_•)／ ＼(^_^)／ ＼(◕‿◕)／ ＼(❛◡❛)／
  ┏(^o^)┛  ┏(•_•)┓  ┗(^_^)┛  ┏(◕‿◕)┓  ┏(❛◡❛)┛
  ┗(^o^)┓  ┗(•_•)┛  ┏(^_^)┓  ┗(◕‿◕)┛  ┗(❛◡❛)┓
  ＼(^o^)／ ＼(•_•)／ ＼(^_^)／ ＼(◕‿◕)／ ＼(❛◡❛)／

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 PARTY TIME! 🎉
```

```
💃 진짜 움직이는 버전:
   bash ~/dance.sh happy

📋 다른 mood 보기:
   bash ~/dance.sh list

📋 사용 가능한 mood: happy / sad / excited / chill / love / angry / party / sleepy
```

## Implementation Hints

**댄서 동작 패턴 (가장 중요):**
- 각 댄서가 매 프레임마다 자기 양쪽 괄호를 다 뒤집어야 함
  - F0: `┏(face)┓` (양팔 위)
  - F1: `┗(face)┛` (양팔 아래)
  - F2: `＼(face)／` (점프/V)
  - 그리고 한쪽만 위인 변형 `┏(face)┛`, `┗(face)┓` 도 섞기
- 5명 댄서 사이에 시작 포즈는 살짝씩 다르게 (한 명은 ┏┓, 한 명은 ┏┛ 등) — "다같이 같은 박자에 움직이지만 자세는 살짝 다른" 웨이브 느낌
- mood별 frame 수: happy/excited/love/party 는 6프레임, sad/chill/angry 는 3~4프레임, sleepy 는 2~3프레임

**채팅창 출력:**
- 한 frame 당 화면을 너무 빽빽하게 채우지 말 것 (15~18줄 이하)
- 댄서가 중앙에 가장 눈에 띄게
- 디스코볼/스피커/관중 등 부수효과는 1~2개만

**스크립트 호출:**
- 채팅창에서 `bash ~/dance.sh <mood>` 를 직접 실행해도 ANSI escape 가 raw 로 찍혀서 보기 안 좋음 → 채팅창엔 플립북, 진짜 실행은 사용자가 터미널에서

## Anti-Patterns

- ❌ 채팅창에서 실제 애니메이션 시도 (clear + sleep 루프) — 안 보임
- ❌ ANSI escape 코드 그대로 출력 — 채팅에선 `[31m` 같은 게 보임
- ❌ 댄서가 프레임 사이에 안 바뀜 (정적) — "춤" 으로 안 보임
- ❌ 댄서 묻힐 정도로 화면 가득 채우기 — 30줄+ 출력 금지
- ❌ mood 무시하고 항상 같은 댄스 — 핵심 가치 훼손
