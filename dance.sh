#!/usr/bin/env bash
# 🪩 Gentle Disco Night - 춤추는 터미널 애니메이션 🪩
# 사용법: bash ~/dance.sh [mood]
#   mood: happy(기본) | sad | excited | chill | love | angry | party | sleepy
#   목록: bash ~/dance.sh list

MOOD="${1:-happy}"

# ───────────── Colors ─────────────
RED=$'\e[31m'; GRN=$'\e[32m'; YEL=$'\e[33m'; BLU=$'\e[34m'
MAG=$'\e[35m'; CYN=$'\e[36m'; WHT=$'\e[97m'; GRY=$'\e[90m'
BOLD=$'\e[1m'; DIM=$'\e[2m'; RST=$'\e[0m'
PINK=$'\e[95m'; ORG=$'\e[38;5;208m'; PUR=$'\e[38;5;141m'
NAVY=$'\e[38;5;25m'; TEAL=$'\e[38;5;44m'; CRIM=$'\e[38;5;160m'

# ───────────── Mood 목록 표시 ─────────────
show_mood_list() {
  echo ""
  echo "  ${MAG}${BOLD}🪩  Dance Mood 목록  🪩${RST}"
  echo "  ${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}"
  echo ""
  printf "    ${YEL}%-10s${RST} 🌈  %s   ${DIM}예: ${RED}┏(^o^)┓${RST}\n"        "happy"   "밝고 신나는 디스코 (기본값)"
  printf "    ${BLU}%-10s${RST} 💧  %s          ${DIM}예: ${NAVY}╮(T_T)╭${RST}\n" "sad"     "비 내리는 슬픈 분위기"
  printf "    ${ORG}%-10s${RST} ⚡  %s         ${DIM}예: ${RED}┏(≧∇≦)┓${RST}\n"  "excited" "격렬한 레이브 파티"
  printf "    ${TEAL}%-10s${RST} 😎  %s         ${DIM}예: ${PUR}┏(¬‿¬)┓${RST}\n"   "chill"   "여유로운 라운지"
  printf "    ${PINK}%-10s${RST} 💕  %s         ${DIM}예: ${RED}┏(♡‿♡)┓${RST}\n" "love"    "사랑 가득 핑크 무드"
  printf "    ${RED}%-10s${RST} 🔥  %s           ${DIM}예: ${CRIM}┏(ಠ益ಠ)┓${RST}\n" "angry"   "분노의 모쉬핏"
  printf "    ${MAG}%-10s${RST} 🎉  %s         ${DIM}예: ${YEL}┏(★ω★)┓${RST}\n" "party"   "모든 게 다 있는 메가 파티"
  printf "    ${PUR}%-10s${RST} 😴  %s         ${DIM}예: ${NAVY}(∪｡∪)zZ${RST}\n"  "sleepy"  "졸린 자장가 모드"
  echo ""
  printf "    ${WHT}${BOLD}%-10s${RST} 🎲  %s         ${DIM}매번 다른 mood${RST}\n" "random" "8가지 중 무작위로 하나"
  echo ""
  echo "  ${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}"
  echo ""
  echo "  ${BOLD}사용법:${RST}  ${CYN}bash ~/dance.sh ${YEL}[mood]${RST}"
  echo "  ${BOLD}예:${RST}     ${CYN}bash ~/dance.sh ${YEL}party${RST}"
  echo "  ${BOLD}목록:${RST}    ${CYN}bash ~/dance.sh ${YEL}list${RST}"
  echo ""
}

case "$MOOD" in
  list|--list|-l|help|--help|-h|\?)
    show_mood_list
    exit 0
    ;;
  random|rand|랜덤|?)
    MOODS=(happy sad excited chill love angry party sleepy)
    MOOD="${MOODS[$((RANDOM % ${#MOODS[@]}))]}"
    echo ""
    echo "  ${MAG}${BOLD}🎲 랜덤 선택: ${YEL}${MOOD}${RST}${MAG}${BOLD}!${RST}"
    sleep 1
    ;;
esac

# ───────────── Mood profiles ─────────────
case "$MOOD" in
  happy)
    TITLE_LINE="${MAG}${BOLD}║${YEL}   ✨🪩  G E N T L E   D I S C O   N I G H T  🪩✨       ${MAG}${BOLD}║${RST}"
    PARTY_MSG="${MAG}${BOLD}              🎉 PARTY TIME! 🎉${RST}"
    SPEED=0.25
    dancers=(
      "${RED}┏(^o^)┓${RST}  ${ORG}┏(•_•)┛${RST}  ${YEL}┗(^_^)┓${RST}  ${GRN}┏(◕‿◕)┛${RST}  ${CYN}┏(❛◡❛)┓${RST}"
      "${RED}┗(^o^)┛${RST}  ${ORG}┗(•_•)┓${RST}  ${YEL}┏(^_^)┛${RST}  ${GRN}┗(◕‿◕)┓${RST}  ${CYN}┗(❛◡❛)┛${RST}"
      "${RED}＼(^o^)／${RST} ${ORG}＼(•_•)／${RST} ${YEL}＼(^_^)／${RST} ${GRN}＼(◕‿◕)／${RST} ${CYN}＼(❛◡❛)／${RST}"
      "${RED}┏(^o^)┛${RST}  ${ORG}┏(•_•)┓${RST}  ${YEL}┗(^_^)┛${RST}  ${GRN}┏(◕‿◕)┓${RST}  ${CYN}┏(❛◡❛)┛${RST}"
      "${RED}┗(^o^)┓${RST}  ${ORG}┗(•_•)┛${RST}  ${YEL}┏(^_^)┓${RST}  ${GRN}┗(◕‿◕)┛${RST}  ${CYN}┗(❛◡❛)┓${RST}"
      "${RED}＼(^o^)／${RST} ${ORG}＼(•_•)／${RST} ${YEL}＼(^_^)／${RST} ${GRN}＼(◕‿◕)／${RST} ${CYN}＼(❛◡❛)／${RST}"
    )
    balls=(
      "${MAG}│ ◉◉◉◉ │${RST}"
      "${YEL}│ ◎◉◎◉ │${RST}"
      "${CYN}│ ◉◎◉◎ │${RST}"
      "${PINK}│ ✦◉✦◉ │${RST}"
    )
    notes=(
      "${PINK}♪${RST}  ${CYN}♫${RST}  ${YEL}♬${RST}  ${GRN}♩${RST}  ${MAG}♭${RST}"
      "${CYN}♫${RST}  ${YEL}♬${RST}  ${GRN}♩${RST}  ${MAG}♭${RST}  ${PINK}♪${RST}"
      "${YEL}♬${RST}  ${GRN}♩${RST}  ${MAG}♭${RST}  ${PINK}♪${RST}  ${CYN}♫${RST}"
      "${GRN}♩${RST}  ${MAG}♭${RST}  ${PINK}♪${RST}  ${CYN}♫${RST}  ${YEL}♬${RST}"
    )
    stars=(
      "${YEL}✦${RST}   ${CYN}*${RST}    ${PINK}✧${RST}    ${YEL}*${RST}   ${CYN}✦${RST}    ${PINK}✧${RST}"
      "${CYN}*${RST}    ${PINK}✧${RST}    ${YEL}*${RST}   ${CYN}✦${RST}   ${PINK}✧${RST}     ${YEL}✦${RST}"
      "${PINK}✧${RST}    ${YEL}✦${RST}   ${CYN}*${RST}    ${PINK}✧${RST}   ${YEL}*${RST}    ${CYN}✦${RST}"
      "${YEL}*${RST}   ${CYN}✦${RST}    ${PINK}✧${RST}    ${YEL}*${RST}   ${CYN}*${RST}   ${PINK}✧${RST}"
    )
    ;;
  sad)
    TITLE_LINE="${BLU}${BOLD}║${NAVY}   💧🌧  S A D   B L U E S   N I G H T  🌧💧         ${BLU}${BOLD}║${RST}"
    PARTY_MSG="${BLU}${BOLD}              💧 RAINY NIGHT... 💧${RST}"
    SPEED=0.55
    dancers=(
      "${NAVY}╮(T_T)╭${RST}  ${BLU}╮(；ω；)╭${RST}  ${PUR}╮(◞‸◟)╭${RST}  ${TEAL}╮(╥﹏╥)╭${RST}  ${GRY}╮(；﹏；)╭${RST}"
      "${NAVY} (T_T) ${RST}  ${BLU} (；ω；) ${RST}  ${PUR} (◞‸◟) ${RST}  ${TEAL} (╥﹏╥) ${RST}  ${GRY} (；﹏；) ${RST}"
      "${NAVY}╭(T_T)╮${RST}  ${BLU}╭(；ω；)╮${RST}  ${PUR}╭(◞‸◟)╮${RST}  ${TEAL}╭(╥﹏╥)╮${RST}  ${GRY}╭(；﹏；)╮${RST}"
      "${NAVY} (T_T) ${RST}  ${BLU} (；ω；) ${RST}  ${PUR} (◞‸◟) ${RST}  ${TEAL} (╥﹏╥) ${RST}  ${GRY} (；﹏；) ${RST}"
    )
    balls=(
      "${BLU}│ ☔☔☔ │${RST}"
      "${NAVY}│ 🌧🌧🌧 │${RST}"
      "${PUR}│ ☔☁☔ │${RST}"
      "${GRY}│ ☁☔☁ │${RST}"
    )
    notes=(
      "${BLU}💧${RST}  ${NAVY}☔${RST}  ${PUR}🌧${RST}  ${GRY}☁${RST}  ${BLU}💧${RST}"
      "${NAVY}☔${RST}  ${PUR}🌧${RST}  ${GRY}☁${RST}  ${BLU}💧${RST}  ${NAVY}☔${RST}"
      "${PUR}🌧${RST}  ${GRY}☁${RST}  ${BLU}💧${RST}  ${NAVY}☔${RST}  ${PUR}🌧${RST}"
    )
    stars=(
      "${BLU}.${RST}   ${NAVY}·${RST}    ${GRY}.${RST}    ${BLU}·${RST}   ${PUR}.${RST}    ${NAVY}·${RST}"
      "${NAVY}·${RST}    ${BLU}.${RST}    ${GRY}·${RST}   ${PUR}.${RST}   ${BLU}·${RST}     ${NAVY}.${RST}"
      "${GRY}.${RST}    ${PUR}·${RST}   ${BLU}.${RST}    ${NAVY}·${RST}   ${BLU}.${RST}    ${PUR}·${RST}"
    )
    ;;
  excited)
    TITLE_LINE="${ORG}${BOLD}║${YEL}   ⚡🔥  E X C I T E D   R A V E   N I G H T  🔥⚡        ${ORG}${BOLD}║${RST}"
    PARTY_MSG="${ORG}${BOLD}              ⚡ RAVE ON!!! ⚡${RST}"
    SPEED=0.14
    dancers=(
      "${RED}┏(≧∇≦)┓${RST}  ${ORG}┏(★ω★)┛${RST}  ${YEL}┗(≧▽≦)┓${RST}  ${CRIM}┏(✧∀✧)┛${RST}  ${MAG}┏(◕‿◕)┓${RST}"
      "${RED}┗(≧∇≦)┛${RST}  ${ORG}┗(★ω★)┓${RST}  ${YEL}┏(≧▽≦)┛${RST}  ${CRIM}┗(✧∀✧)┓${RST}  ${MAG}┗(◕‿◕)┛${RST}"
      "${RED}＼(≧∇≦)／${RST} ${ORG}＼(★ω★)／${RST} ${YEL}＼(≧▽≦)／${RST} ${CRIM}＼(✧∀✧)／${RST} ${MAG}＼(◕‿◕)／${RST}"
      "${RED}┏(≧∇≦)┛${RST}  ${ORG}┏(★ω★)┓${RST}  ${YEL}┗(≧▽≦)┛${RST}  ${CRIM}┏(✧∀✧)┓${RST}  ${MAG}┏(◕‿◕)┛${RST}"
      "${RED}┗(≧∇≦)┓${RST}  ${ORG}┗(★ω★)┛${RST}  ${YEL}┏(≧▽≦)┓${RST}  ${CRIM}┗(✧∀✧)┛${RST}  ${MAG}┗(◕‿◕)┓${RST}"
      "${RED}٩(≧∇≦)۶${RST} ${ORG}٩(★ω★)۶${RST} ${YEL}٩(≧▽≦)۶${RST} ${CRIM}٩(✧∀✧)۶${RST} ${MAG}٩(◕‿◕)۶${RST}"
    )
    balls=(
      "${RED}│ ⚡⚡⚡ │${RST}"
      "${YEL}│ 💥💥💥 │${RST}"
      "${ORG}│ 🔥🔥🔥 │${RST}"
      "${MAG}│ ★★★★ │${RST}"
    )
    notes=(
      "${RED}!!!${RST}   ${YEL}♪${RST}   ${ORG}!!!${RST}   ${MAG}♬${RST}   ${RED}!!!${RST}"
      "${YEL}♬${RST}    ${RED}!!!${RST}   ${MAG}♪${RST}    ${ORG}!!!${RST}   ${YEL}♬${RST}"
      "${ORG}!!!${RST}   ${MAG}♪${RST}    ${RED}!!!${RST}   ${YEL}♬${RST}    ${RED}!!!${RST}"
    )
    stars=(
      "${YEL}⚡${RST}   ${ORG}★${RST}    ${RED}💥${RST}    ${YEL}⚡${RST}   ${MAG}🔥${RST}    ${RED}★${RST}"
      "${RED}🔥${RST}   ${YEL}⚡${RST}    ${MAG}★${RST}    ${ORG}💥${RST}   ${RED}⚡${RST}    ${YEL}🔥${RST}"
      "${MAG}★${RST}    ${RED}💥${RST}   ${YEL}⚡${RST}    ${ORG}🔥${RST}   ${MAG}★${RST}    ${YEL}⚡${RST}"
    )
    ;;
  chill)
    TITLE_LINE="${TEAL}${BOLD}║${PUR}   😎🌙  C H I L L   L O U N G E   N I G H T  🌙😎        ${TEAL}${BOLD}║${RST}"
    PARTY_MSG="${TEAL}${BOLD}              😎 STAY COOL 😎${RST}"
    SPEED=0.45
    dancers=(
      "${TEAL}~(¬‿¬)${RST}   ${CYN}~(•̀ᴗ•́)${RST}   ${PUR}~( ͡° ͜ʖ ͡°)${RST}   ${BLU}~(⌐■_■)${RST}   ${MAG}~(￣ω￣)${RST}"
      "${TEAL} (¬‿¬) ${RST}  ${CYN} (•̀ᴗ•́) ${RST}  ${PUR} ( ͡° ͜ʖ ͡°) ${RST}  ${BLU} (⌐■_■) ${RST}  ${MAG} (￣ω￣) ${RST}"
      "${TEAL}(¬‿¬)~${RST}   ${CYN}(•̀ᴗ•́)~${RST}   ${PUR}( ͡° ͜ʖ ͡°)~${RST}   ${BLU}(⌐■_■)~${RST}   ${MAG}(￣ω￣)~${RST}"
      "${TEAL} (¬‿¬) ${RST}  ${CYN} (•̀ᴗ•́) ${RST}  ${PUR} ( ͡° ͜ʖ ͡°) ${RST}  ${BLU} (⌐■_■) ${RST}  ${MAG} (￣ω￣) ${RST}"
    )
    balls=(
      "${PUR}│ ☾☾☾☾ │${RST}"
      "${TEAL}│ ✧✧✧✧ │${RST}"
      "${CYN}│ ◐◐◐◐ │${RST}"
      "${BLU}│ ◑◑◑◑ │${RST}"
    )
    notes=(
      "${TEAL}~${RST}   ${PUR}♪${RST}   ${CYN}☾${RST}   ${MAG}~${RST}   ${BLU}♫${RST}"
      "${PUR}♫${RST}   ${TEAL}~${RST}   ${MAG}♪${RST}   ${CYN}☾${RST}   ${TEAL}~${RST}"
      "${CYN}☾${RST}   ${BLU}~${RST}   ${TEAL}♫${RST}   ${PUR}~${RST}   ${MAG}♪${RST}"
    )
    stars=(
      "${TEAL}✧${RST}   ${PUR}·${RST}    ${CYN}✦${RST}    ${MAG}~${RST}   ${BLU}✧${RST}    ${TEAL}·${RST}"
      "${PUR}·${RST}    ${TEAL}✧${RST}    ${MAG}~${RST}   ${CYN}✦${RST}   ${TEAL}·${RST}     ${PUR}✧${RST}"
      "${CYN}✦${RST}    ${MAG}~${RST}   ${BLU}·${RST}    ${PUR}✧${RST}   ${TEAL}✦${RST}    ${CYN}~${RST}"
    )
    ;;
  love)
    TITLE_LINE="${PINK}${BOLD}║${RED}   💕💖  L O V E   N I G H T   💖💕                ${PINK}${BOLD}║${RST}"
    PARTY_MSG="${PINK}${BOLD}              💕 SPREAD THE LOVE 💕${RST}"
    SPEED=0.28
    dancers=(
      "${PINK}┏(♡‿♡)┓${RST}  ${MAG}┏(´∀｀)┛${RST}  ${RED}┗(◕‿◕)┓${RST}  ${PINK}┏(♥‿♥)┛${RST}  ${CRIM}┏(˃‿˂)┓${RST}"
      "${PINK}┗(♡‿♡)┛${RST}  ${MAG}┗(´∀｀)┓${RST}  ${RED}┏(◕‿◕)┛${RST}  ${PINK}┗(♥‿♥)┓${RST}  ${CRIM}┗(˃‿˂)┛${RST}"
      "${PINK}＼(♡‿♡)／${RST} ${MAG}＼(´∀｀)／${RST} ${RED}＼(◕‿◕)／${RST} ${PINK}＼(♥‿♥)／${RST} ${CRIM}＼(˃‿˂)／${RST}"
      "${PINK}┏(♡‿♡)┛${RST}  ${MAG}┏(´∀｀)┓${RST}  ${RED}┗(◕‿◕)┛${RST}  ${PINK}┏(♥‿♥)┓${RST}  ${CRIM}┏(˃‿˂)┛${RST}"
      "${PINK}┗(♡‿♡)┓${RST}  ${MAG}┗(´∀｀)┛${RST}  ${RED}┏(◕‿◕)┓${RST}  ${PINK}┗(♥‿♥)┛${RST}  ${CRIM}┗(˃‿˂)┓${RST}"
      "${PINK}♡(♡‿♡)♡${RST} ${MAG}♡(´∀｀)♡${RST} ${RED}❤(◕‿◕)❤${RST} ${PINK}♡(♥‿♥)♡${RST} ${CRIM}❤(˃‿˂)❤${RST}"
    )
    balls=(
      "${RED}│ ❤❤❤❤ │${RST}"
      "${PINK}│ ♡♡♡♡ │${RST}"
      "${MAG}│ 💕💕💕 │${RST}"
      "${CRIM}│ ♥♡♥♡ │${RST}"
    )
    notes=(
      "${RED}❤${RST}   ${PINK}♡${RST}   ${MAG}💕${RST}   ${CRIM}💖${RST}   ${RED}❤${RST}"
      "${PINK}♡${RST}   ${MAG}💕${RST}   ${RED}❤${RST}    ${PINK}♡${RST}   ${CRIM}💖${RST}"
      "${MAG}💕${RST}  ${CRIM}💖${RST}  ${PINK}♡${RST}   ${RED}❤${RST}    ${MAG}💕${RST}"
    )
    stars=(
      "${PINK}💕${RST}   ${RED}✨${RST}    ${MAG}♡${RST}    ${PINK}💖${RST}   ${CRIM}✨${RST}    ${RED}❤${RST}"
      "${RED}❤${RST}    ${PINK}💖${RST}    ${MAG}✨${RST}   ${PINK}♡${RST}   ${CRIM}💕${RST}     ${MAG}♡${RST}"
      "${MAG}♡${RST}    ${CRIM}💗${RST}   ${RED}❤${RST}    ${PINK}💕${RST}   ${MAG}♡${RST}    ${PINK}💖${RST}"
    )
    ;;
  angry)
    TITLE_LINE="${RED}${BOLD}║${CRIM}   🔥💢  A N G R Y   M O S H   P I T  💢🔥           ${RED}${BOLD}║${RST}"
    PARTY_MSG="${RED}${BOLD}              🔥 LET IT OUT! 🔥${RST}"
    SPEED=0.16
    dancers=(
      "${RED}┏(╬ಠ益ಠ)┓${RST} ${CRIM}┏(ಠ益ಠ)┛${RST}  ${ORG}┗(\`0´)┓${RST}   ${RED}┏(¬_¬\")┛${RST} ${CRIM}┏(\`Д´)┓${RST}"
      "${RED}┗(╬ಠ益ಠ)┛${RST} ${CRIM}┗(ಠ益ಠ)┓${RST}  ${ORG}┏(\`0´)┛${RST}   ${RED}┗(¬_¬\")┓${RST} ${CRIM}┗(\`Д´)┛${RST}"
      "${RED}彡(╬ಠ益ಠ)彡${RST} ${CRIM}彡(ಠ益ಠ)彡${RST} ${ORG}彡(\`0´)彡${RST}  ${RED}彡(¬_¬\")彡${RST} ${CRIM}彡(\`Д´)彡${RST}"
      "${RED}＼(╬ಠ益ಠ)／${RST} ${CRIM}＼(ಠ益ಠ)／${RST} ${ORG}＼(\`0´)／${RST}  ${RED}＼(¬_¬\")／${RST} ${CRIM}＼(\`Д´)／${RST}"
    )
    balls=(
      "${RED}│ 💢💢💢 │${RST}"
      "${ORG}│ 🔥🔥🔥 │${RST}"
      "${CRIM}│ ⚡⚡⚡ │${RST}"
      "${YEL}│ 💥💥💥 │${RST}"
    )
    notes=(
      "${RED}💢${RST}  ${ORG}🔥${RST}  ${CRIM}⚡${RST}  ${RED}!!${RST}  ${ORG}💥${RST}"
      "${ORG}🔥${RST}  ${RED}💢${RST}  ${CRIM}💥${RST}  ${ORG}⚡${RST}  ${RED}🔥${RST}"
      "${CRIM}⚡${RST}  ${RED}💥${RST}  ${ORG}🔥${RST}  ${CRIM}💢${RST}  ${RED}!!${RST}"
    )
    stars=(
      "${RED}💢${RST}   ${ORG}🔥${RST}    ${CRIM}⚡${RST}    ${RED}💥${RST}   ${ORG}🔥${RST}    ${CRIM}💢${RST}"
      "${ORG}🔥${RST}   ${RED}💢${RST}    ${CRIM}💥${RST}   ${ORG}⚡${RST}   ${RED}🔥${RST}     ${CRIM}💢${RST}"
      "${CRIM}⚡${RST}    ${RED}🔥${RST}   ${ORG}💢${RST}    ${CRIM}💥${RST}   ${RED}💢${RST}    ${ORG}🔥${RST}"
    )
    ;;
  party)
    TITLE_LINE="${MAG}${BOLD}║${YEL}   🎉🪩  M E G A   P A R T Y   N I G H T  🪩🎉         ${MAG}${BOLD}║${RST}"
    PARTY_MSG="${MAG}${BOLD}              🎉 MEGA PARTY MODE! 🎉${RST}"
    SPEED=0.2
    dancers=(
      "${RED}┏(^o^)┓${RST}   ${ORG}┏(≧∇≦)┛${RST}  ${YEL}┗(♡‿♡)┓${RST}   ${GRN}┏(¬‿¬)┛${RST}  ${CYN}┏(★ω★)┓${RST}"
      "${RED}┗(^o^)┛${RST}   ${ORG}┗(≧∇≦)┓${RST}  ${YEL}┏(♡‿♡)┛${RST}   ${GRN}┗(¬‿¬)┓${RST}  ${CYN}┗(★ω★)┛${RST}"
      "${RED}＼(^o^)／${RST}  ${ORG}＼(≧∇≦)／${RST} ${YEL}＼(♡‿♡)／${RST}  ${GRN}＼(¬‿¬)／${RST} ${CYN}＼(★ω★)／${RST}"
      "${RED}┏(^o^)┛${RST}   ${ORG}┏(≧∇≦)┓${RST}  ${YEL}┗(♡‿♡)┛${RST}   ${GRN}┏(¬‿¬)┓${RST}  ${CYN}┏(★ω★)┛${RST}"
      "${RED}┗(^o^)┓${RST}   ${ORG}┗(≧∇≦)┛${RST}  ${YEL}┏(♡‿♡)┓${RST}   ${GRN}┗(¬‿¬)┛${RST}  ${CYN}┗(★ω★)┓${RST}"
      "${RED}٩(^o^)۶${RST}  ${ORG}٩(≧∇≦)۶${RST} ${YEL}٩(♡‿♡)۶${RST}  ${GRN}٩(¬‿¬)۶${RST} ${CYN}٩(★ω★)۶${RST}"
    )
    balls=(
      "${YEL}│ 🪩🪩🪩 │${RST}"
      "${MAG}│ ★★★★ │${RST}"
      "${PINK}│ ◉◉◉◉ │${RST}"
      "${CYN}│ 🎉🎉🎉 │${RST}"
      "${ORG}│ ✦◉✦◉ │${RST}"
    )
    notes=(
      "${PINK}♪${RST}  ${CYN}♫${RST}  ${YEL}♬${RST}  ${GRN}♩${RST}  ${MAG}🎉${RST}"
      "${CYN}🎊${RST} ${YEL}♬${RST}  ${MAG}♪${RST}  ${RED}🎉${RST} ${PINK}♫${RST}"
      "${MAG}🪩${RST}  ${ORG}♬${RST}  ${PINK}🎶${RST} ${YEL}♪${RST}  ${CYN}🎊${RST}"
      "${GRN}♩${RST}  ${MAG}🎉${RST} ${PINK}♪${RST}  ${CYN}🪩${RST} ${YEL}♬${RST}"
    )
    stars=(
      "${YEL}✨${RST}   ${PINK}🎊${RST}    ${MAG}★${RST}    ${CYN}🎉${RST}   ${GRN}✨${RST}    ${ORG}★${RST}"
      "${PINK}🎉${RST}   ${MAG}★${RST}    ${YEL}🎊${RST}    ${ORG}✨${RST}   ${CYN}★${RST}    ${PINK}🎉${RST}"
      "${CYN}★${RST}    ${YEL}🎉${RST}   ${PINK}✨${RST}    ${MAG}🎊${RST}   ${ORG}★${RST}    ${YEL}✨${RST}"
    )
    ;;
  sleepy)
    TITLE_LINE="${PUR}${BOLD}║${NAVY}   😴🌙  S L E E P Y   L U L L A B Y   🌙😴           ${PUR}${BOLD}║${RST}"
    PARTY_MSG="${PUR}${BOLD}              😴 ZZZ... GOOD NIGHT 😴${RST}"
    SPEED=0.7
    dancers=(
      "${PUR}(￣o￣).zZ${RST}  ${NAVY}(∪｡∪).zZ${RST}  ${BLU}(꒪⌓꒪).zZ${RST}  ${GRY}(´；ω；\`).z${RST} ${PUR}(´-ω-\`).z${RST}"
      "${PUR}(￣o￣)zz${RST}   ${NAVY}(∪｡∪)zz${RST}   ${BLU}(꒪⌓꒪)zz${RST}   ${GRY}(´；ω；\`)z${RST}  ${PUR}(´-ω-\`)z${RST}"
      "${PUR}(￣o￣)..z${RST}  ${NAVY}(∪｡∪)..z${RST}  ${BLU}(꒪⌓꒪)..z${RST}  ${GRY}(´；ω；\`)..${RST} ${PUR}(´-ω-\`)..${RST}"
      "${PUR}(￣o￣)z${RST}    ${NAVY}(∪｡∪)z${RST}    ${BLU}(꒪⌓꒪)z${RST}    ${GRY}(´；ω；\`).${RST}  ${PUR}(´-ω-\`).${RST}"
    )
    balls=(
      "${YEL}│ 🌙🌙🌙 │${RST}"
      "${PUR}│ ⭐⭐⭐ │${RST}"
      "${NAVY}│ ☾☾☾☾ │${RST}"
      "${BLU}│ 💤💤💤 │${RST}"
    )
    notes=(
      "${PUR}💤${RST}  ${NAVY}🌙${RST}  ${BLU}zzz${RST}  ${YEL}⭐${RST}  ${PUR}💤${RST}"
      "${NAVY}🌙${RST}  ${BLU}zzz${RST}  ${PUR}💤${RST}  ${YEL}⭐${RST}  ${NAVY}☾${RST}"
      "${BLU}zzz${RST} ${YEL}⭐${RST}  ${NAVY}🌙${RST}  ${PUR}💤${RST}  ${BLU}zzz${RST}"
    )
    stars=(
      "${YEL}⭐${RST}   ${PUR}✦${RST}    ${NAVY}🌙${RST}   ${YEL}⭐${RST}   ${PUR}✧${RST}    ${NAVY}☾${RST}"
      "${PUR}✦${RST}   ${YEL}⭐${RST}    ${PUR}✧${RST}    ${NAVY}🌙${RST}   ${YEL}⭐${RST}    ${PUR}✦${RST}"
      "${NAVY}☾${RST}   ${PUR}✦${RST}    ${YEL}⭐${RST}    ${PUR}✧${RST}    ${YEL}⭐${RST}   ${NAVY}🌙${RST}"
    )
    ;;
  *)
    echo ""
    echo "  ${RED}❌ 알 수 없는 mood: ${BOLD}$MOOD${RST}"
    show_mood_list
    exit 1
    ;;
esac

# Ctrl+C 누르면 깔끔하게 종료
trap 'tput cnorm; clear; echo "${PINK}${BOLD}  ✨ 즐거우셨나요? Bye! ✨${RST}"; exit 0' INT
tput civis  # 커서 숨김

# ───────────── 메인 루프 ─────────────
i=0
while true; do
  clear
  d=$((i % ${#dancers[@]}))
  b=$((i % ${#balls[@]}))
  n=$((i % ${#notes[@]}))
  s=$((i % ${#stars[@]}))

  echo ""
  echo "${MAG}${BOLD}╔══════════════════════════════════════════════════════════╗${RST}"
  echo "${TITLE_LINE}"
  echo "${MAG}${BOLD}╚══════════════════════════════════════════════════════════╝${RST}"
  echo ""
  echo "          ${stars[$s]}"
  echo "                ${MAG}╭──────╮${RST}"
  echo "                ${balls[$b]}    ${PINK}<- 디스코볼${RST}"
  echo "                ${MAG}╰──┬───╯${RST}"
  echo "                   ${MAG}│${RST}"
  echo "        ${notes[$n]}"
  echo ""
  echo "${PUR}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}"
  echo ""
  echo "        ${dancers[$d]}"
  echo ""
  echo "${PUR}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}"
  echo ""
  echo "       ${ORG}▓▓▓▓▓▓▓▓▓▓ ${YEL}M  A  I  N    S  T  A  G  E ${ORG}▓▓▓▓▓▓▓▓▓▓${RST}"
  echo "       ${ORG}░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░${RST}"
  echo ""
  echo "${PARTY_MSG}"
  echo ""
  echo "         ${WHT}프레임 ${BOLD}#${i}${RST}   ${DIM}mood: ${BOLD}${MOOD}${RST}   ${PINK}[Ctrl+C 종료]${RST}"
  echo ""

  i=$((i + 1))
  sleep "$SPEED"
done
