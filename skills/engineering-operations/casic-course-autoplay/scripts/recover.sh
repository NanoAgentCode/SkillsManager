#!/usr/bin/env bash
# 航天云课堂 · 一键自愈
#
# 场景：页面被清成 about:blank、掉登录、播放器被顶掉、控制器心跳停止。
# 一条命令完成：重开页面 → 重登 → 回专题 → 进课 → 重新注入控制器。
#
# 用法：
#   ./recover.sh                 # 自动进第一门未完成课程
#   ./recover.sh "违规动火作业"   # 指定课程（标题包含即可）
#   ./recover.sh --status        # 只体检，输出 JSON
#   ./recover.sh --list          # 打印全部课程完成状态表
#   ./recover.sh --hold          # 置为主动暂停（本课播完不再跳下一门）
#   ./recover.sh --resume        # 解除暂停
#
# 依赖：bash、agent-browser、node；配置见 ../config.env

set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
CFG="$DIR/../config.env"
[ -f "$CFG" ] && . "$CFG"

SUBJECT_URL="${SUBJECT_URL:-}"
CASIC_USER="${CASIC_USER:-}"
CASIC_PASS="${CASIC_PASS:-}"

st() { agent-browser eval --stdin < "$DIR/status.js" 2>/dev/null | tail -1; }
field() { printf '%s' "$1" | node "$DIR/jq.js" "$2"; }
say() { echo "[$(date +%H:%M:%S)] $*"; }

# 带超时的体检。daemon 偶尔会卡死（实测卡 2 分半后自行恢复），
# 不设上限会把 watch/keepalive 的周期全拖乱。
FALLBACK='{"page":"blank","action":"reopen","alive":false,"no_video":null,"courses":null,"done_count":null,"total_count":null}'
ST_TO=0
st2() {
  local out
  out="$(timeout "${ST_TIMEOUT:-25}" agent-browser eval --stdin < "$DIR/status.js" 2>/dev/null | tail -1)"
  if [ -z "$out" ]; then ST_TO=1; printf '%s' "$FALLBACK"; else ST_TO=0; printf '%s' "$out"; fi
}

S="$(st2)"
if [ "${1:-}" = "--status" ]; then
  printf '%s\n' "$S"
  exit 0
fi

# ---- 课程全景表（专题页才有数据，否则先回专题页）----
if [ "${1:-}" = "--list" ]; then
  PAGE="$(field "$S" page)"
  if [ "$PAGE" != "subject" ]; then
    say "当前不在专题页（page=$PAGE），先回专题页"
    [ -n "$SUBJECT_URL" ] && agent-browser open "$SUBJECT_URL" >/dev/null 2>&1 && sleep 7
    S="$(st2)"
  fi
  printf '%s' "$S" | node "$DIR/jq.js" courses | node -e '
    let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{
      let a=[];try{a=JSON.parse(s)}catch(e){}
      if(!Array.isArray(a)||!a.length){console.log("（未取到课程列表，可能不在专题页）");return}
      let done=0;
      a.forEach(c=>{if(c.done)done++;
        console.log(String(c.i+1).padStart(2)+"  "+(c.done?"[OK]":c.learning?"[..]":"[  ]")+"  "+c.title);
      });
      console.log("—— 已完成 "+done+"/"+a.length+" ——");
    });'
  exit 0
fi

# ---- 硬重置：daemon 卡死 / 标签无响应时用（eval 超时返回空即属此类）----
if [ "${1:-}" = "--restart" ]; then
  say "关闭浏览器并重建"
  agent-browser close --all >/dev/null 2>&1
  sleep 2
  [ -n "$SUBJECT_URL" ] && agent-browser open "$SUBJECT_URL" >/dev/null 2>&1
  agent-browser set viewport 390 844 >/dev/null 2>&1
  sleep 8
  S="$(st2)"; PAGE="$(field "$S" page)"
  say "重启后 page=$PAGE"
  # 不 exit：继续走登录/进课/注入，一条命令到位
fi

# ---- 0. 主动暂停 / 解除暂停（状态写 localStorage，跨刷新有效）----
if [ "${1:-}" = "--hold" ]; then
  PG="$(field "$S" page)"
  if [ "$PG" = "blank" ] || [ "$PG" = "other" ]; then
    say "页面已空（page=$PG），当前没有播放，无需暂停"
    exit 0
  fi
  agent-browser eval "(()=>{if(window.__apTimer){clearInterval(window.__apTimer);window.__apTimer=null}if(window.__ap){window.__ap.on=false;window.__ap.hold=true}const v=document.querySelector('video');if(v&&!v.paused)v.pause();let h={};try{h=JSON.parse(localStorage.getItem('__casic_hb'))||{}}catch(e){}h.hold=true;h.ts=Date.now();localStorage.setItem('__casic_hb',JSON.stringify(h));return 'held'})()" 2>/dev/null | tail -1
  say "已置为暂停态"
  exit 0
fi
if [ "${1:-}" = "--resume" ]; then
  PG="$(field "$S" page)"
  if [ "$PG" = "blank" ] || [ "$PG" = "other" ]; then
    say "页面已空，无法写入解除标记，直接跑 recover.sh 即可"
    exit 0
  fi
  agent-browser eval "(()=>{let h={};try{h=JSON.parse(localStorage.getItem('__casic_hb'))||{}}catch(e){}h.hold=false;localStorage.setItem('__casic_hb',JSON.stringify(h));return 'resumed'})()" 2>/dev/null | tail -1
  say "已解除暂停态"
  S="$(st2)"
fi

PAGE="$(field "$S" page)"
ACTION="$(field "$S" action)"
say "体检：page=$PAGE action=$ACTION"

if [ "$ACTION" = "holding" ]; then
  say "处于主动暂停，跳过自愈（需要继续请用 --resume）"
  exit 0
fi

# ---- 1. 页面没了 ----
if [ "$PAGE" = "blank" ] || [ "$PAGE" = "other" ]; then
  [ -z "$SUBJECT_URL" ] && { say "缺少 SUBJECT_URL，无法重开"; exit 2; }
  say "重开专题页"
  agent-browser open "$SUBJECT_URL" >/dev/null 2>&1
  agent-browser set viewport 390 844 >/dev/null 2>&1
  sleep 8
  S="$(st2)"; PAGE="$(field "$S" page)"
  # 重开无效（通常是 daemon 卡死，eval 返回空）→ 关掉整个浏览器重来
  if [ "$PAGE" = "blank" ] || [ -z "$PAGE" ] || [ "$ST_TO" = "1" ]; then
    say "重开无效（ST_TO=$ST_TO），硬重置浏览器"
    agent-browser close --all >/dev/null 2>&1
    sleep 2
    agent-browser open "$SUBJECT_URL" >/dev/null 2>&1
    agent-browser set viewport 390 844 >/dev/null 2>&1
    sleep 10
    S="$(st2)"; PAGE="$(field "$S" page)"
    say "硬重置后 page=$PAGE"
  fi
fi

# ---- 2. 掉登录 ----
if [ "$PAGE" = "login" ]; then
  [ -z "$CASIC_USER" ] && { say "缺少账号，无法重登"; exit 2; }
  say "重新登录"
  agent-browser fill "input[type=text].user" "$CASIC_USER" >/dev/null 2>&1
  agent-browser fill "input[type=password]" "$CASIC_PASS" >/dev/null 2>&1
  agent-browser click ".van-checkbox__label" >/dev/null 2>&1
  agent-browser click ".login-btn" >/dev/null 2>&1
  sleep 9
  S="$(st2)"; PAGE="$(field "$S" page)"
  say "登录后 page=$PAGE"
fi

# ---- 2.5 平台播完会跳"快速笔记"页：无 video、无选集，注入无效，只能回专题页 ----
if [ "$ACTION" = "back_to_subject" ] || { [ "$PAGE" = "course" ] && [ -z "$(field "$S" duration)" ] && [ "$(field "$S" no_video)" = "notes" ]; }; then
  say "检测到无播放器页面（$PAGE/no_video=$(field "$S" no_video)），回专题页"
  [ -z "$SUBJECT_URL" ] && { say "缺少 SUBJECT_URL，无法回专题页"; exit 2; }
  agent-browser open "$SUBJECT_URL" >/dev/null 2>&1
  agent-browser set viewport 390 844 >/dev/null 2>&1
  sleep 8
  S="$(st2)"; PAGE="$(field "$S" page)"
  say "回专题页后 page=$PAGE 已完成 $(field "$S" done_count)/$(field "$S" total_count)"
fi

# ---- 3. 在专题页：进课 ----
TITLE="${1:-}"
case "$TITLE" in --*) TITLE="";; esac
if [ "$PAGE" = "subject" ]; then
  if [ -n "$TITLE" ]; then
    R=$(agent-browser eval "(()=>{const its=[...document.querySelectorAll('.s-info-right')];const it=its.find(e=>e.innerText.includes('$TITLE'));if(!it)return 'nf';(it.querySelector('.sub-left')||it).click();return 'ok'})()" 2>/dev/null | tail -1)
    say "按标题进课：$R"
  else
    R=$(agent-browser eval "(()=>{const its=[...document.querySelectorAll('.s-info-right')];const it=its.find(e=>e.innerText.indexOf('已完成')===-1);if(!it)return 'all-done';(it.querySelector('.sub-left')||it).click();return 'ok'})()" 2>/dev/null | tail -1)
    say "进第一门未完成课程：$R"
    [ "$R" = "all-done" ] && { say "专题已全部完成"; exit 0; }
  fi
  sleep 8
  S="$(st2)"; PAGE="$(field "$S" page)"
  # 点一次没进去（列表还在渲染时常见）→ 重试一次
  if [ "$PAGE" = "subject" ] && [ -n "${R:-}" ] && [ "$R" != "nf" ] && [ "$R" != "all-done" ]; then
    say "仍在专题页，重试进课"
    agent-browser eval "(()=>{const its=[...document.querySelectorAll('.s-info-right')];const it=its.find(e=>e.innerText.indexOf('已完成')===-1);if(!it)return 'all-done';(it.querySelector('.sub-left')||it).click();return 'ok'})()" >/dev/null 2>&1
    sleep 8
    S="$(st2)"; PAGE="$(field "$S" page)"
    say "重试后 page=$PAGE"
  fi
fi

# ---- 4. 在课程页：注入控制器 ----
if [ "$PAGE" = "course" ]; then
  OUT=$(agent-browser eval --stdin < "$DIR/autoplay.js" 2>/dev/null | tail -1)
  say "注入控制器：$OUT"
  sleep 5
  S="$(st2)"
  say "状态：$(printf '%s' "$S" | node "$DIR/jq.js" progress) 必修 $(printf '%s' "$S" | node "$DIR/jq.js" required) $(printf '%s' "$S" | node "$DIR/jq.js" time)/$(printf '%s' "$S" | node "$DIR/jq.js" duration)s rate=$(printf '%s' "$S" | node "$DIR/jq.js" rate) alive=$(printf '%s' "$S" | node "$DIR/jq.js" alive)"
else
  say "当前不在课程页（page=$PAGE），未注入"
fi
