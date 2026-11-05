#!/usr/bin/env bash
# 航天云课堂 · 回合保活 + 自愈
#
# 为什么需要它：
#   沙箱在回合结束（agent 完成一次回复）后 5～7 分钟会回收标签页，
#   页面变 about:blank、登录态丢失，播放停止。这不是页面 bug，内存也充足
#   （实测 126G 内存只用 24G，无 OOM）。唯一可靠对策是"把回合占住"：
#   在一次工具调用里持续 sleep，回合不结束，页面就不会被回收。
#
# 用法：
#   ./keepalive.sh              # 540 秒（9 分钟），每 45 秒体检
#   ./keepalive.sh 540 30       # 自定义时长与间隔
#
# 注意：单次工具调用上限 600 秒，DURATION 不要超过 560。
#       要连续跑 30 分钟，就连续调用 3～4 次。

set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
DURATION="${1:-540}"
INTERVAL="${2:-45}"

st() {
  local out
  out="$(timeout 25 agent-browser eval --stdin < "$DIR/status.js" 2>/dev/null | tail -1)"
  if [ -z "$out" ]; then printf '%s' '{"page":"blank","action":"reopen"}'; else printf '%s' "$out"; fi
}
field() { printf '%s' "$1" | node "$DIR/jq.js" "$2"; }
say() { echo "[$(date +%H:%M:%S)] $*"; }

T0=$(date +%s)
ROUND=0
FIX=0
LAST=""

say "保活开始 ${DURATION}s / 每 ${INTERVAL}s"

while :; do
  NOW=$(date +%s)
  [ $((NOW - T0)) -ge "$DURATION" ] && break

  sleep "$INTERVAL"
  ROUND=$((ROUND + 1))

  S="$(st)"
  PAGE="$(field "$S" page)"
  ACTION="$(field "$S" action)"
  PROG="$(field "$S" progress)"
  REQ="$(field "$S" required)"
  T="$(field "$S" time)"
  D="$(field "$S" duration)"
  RATE="$(field "$S" rate)"
  ALIVE="$(field "$S" alive)"

  say "[$ROUND] page=$PAGE action=$ACTION ${PROG:--} ${REQ:--} ${T:--}/${D:--} rate=${RATE:--} alive=$ALIVE"
  LAST="$S"

  if [ "$ACTION" = "holding" ]; then
    :   # 主动暂停，不动
  elif [ "$ACTION" != "none" ]; then
    FIX=$((FIX + 1))
    say "→ 自愈（$ACTION）"
    bash "$DIR/recover.sh" 2>&1 | sed 's/^/    /'
  fi
done

say "保活结束：$ROUND 轮，自愈 $FIX 次"
if [ -n "$LAST" ]; then
  say "末态：page=$(field "$LAST" page) $(field "$LAST" progress) 必修 $(field "$LAST" required) $(field "$LAST" time)/$(field "$LAST" duration)s"
  DC="$(field "$LAST" done_count)"
  [ -n "$DC" ] && say "专题完成度：$DC/$(field "$LAST" total_count)"
fi
