#!/usr/bin/env bash
# 航天云课堂 · 值守循环
#
# 每 30 秒体检一次，发现崩溃/掉登录/控制器死亡就自动跑 recover.sh。
# 跑在自己的回合内有效；回合结束后沙箱休眠，循环也会停（这是环境限制，不是脚本问题）。
#
# 用法：
#   ./watch.sh            # 默认 30 秒一轮，无限循环
#   ./watch.sh 60 12      # 60 秒一轮，跑 12 轮（约 12 分钟）
#   ./watch.sh 30 0       # 无限循环并每轮追加日志到 watch.log
#
# 日志：scripts/watch.log

set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
INTERVAL="${1:-30}"
ROUNDS="${2:-0}"
LOG="$DIR/watch.log"
TITLE="${3:-}"

st() {
  local out
  out="$(timeout 25 agent-browser eval --stdin < "$DIR/status.js" 2>/dev/null | tail -1)"
  if [ -z "$out" ]; then printf '%s' '{"page":"blank","action":"reopen"}'; else printf '%s' "$out"; fi
}
field() { printf '%s' "$1" | node "$DIR/jq.js" "$2"; }
log() { echo "[$(date '+%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "值守启动 interval=${INTERVAL}s rounds=${ROUNDS:-inf}"
n=0
while :; do
  n=$((n + 1))
  S="$(st)"
  PAGE="$(field "$S" page)"
  ACTION="$(field "$S" action)"
  PROG="$(field "$S" progress)"
  REQ="$(field "$S" required)"
  T="$(field "$S" time)"
  D="$(field "$S" duration)"
  RATE="$(field "$S" rate)"

  log "page=$PAGE action=$ACTION ${PROG:-–} ${REQ:-–} ${T:-–}/${D:-–} rate=${RATE:-–}"

  if [ "$ACTION" = "holding" ]; then
    log "主动暂停中，值守空转（--resume 后自动恢复）"
  elif [ "$ACTION" != "none" ] || [ "$PAGE" = "blank" ] || [ "$PAGE" = "login" ]; then
    log "→ 触发自愈（$ACTION）"
    bash "$DIR/recover.sh" "$TITLE" 2>&1 | tee -a "$LOG" | sed 's/^/    /'
  fi

  if [ "$ROUNDS" != "0" ] && [ "$n" -ge "$ROUNDS" ]; then
    log "值守结束（$n 轮）"
    break
  fi
  sleep "$INTERVAL"
done
