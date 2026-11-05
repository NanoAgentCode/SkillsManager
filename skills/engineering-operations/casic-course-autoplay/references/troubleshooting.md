# 排查表

> 来源环境的历史经验，未在本仓库实站验证。回收时间和命令兼容性以当前环境为准，参见 SKILL.md 的仓库使用约定。

> 大部分情况不用读这里：直接跑 `bash scripts/recover.sh`，它按 `status.js` 的 `action` 字段自动处置。
> 本文用于 `recover.sh` 也搞不定的场景。

## 命令速查

```bash
bash scripts/recover.sh --status    # 体检（page / action / alive / no_video / courses）
bash scripts/recover.sh --list      # 全部课程完成状态表
bash scripts/recover.sh             # 自愈：重开 → 重登 → 回专题 → 进课 → 注入
bash scripts/recover.sh "课程名"     # 指定课程
bash scripts/recover.sh --hold      # 主动暂停（跨刷新有效）
bash scripts/recover.sh --resume    # 解除暂停
bash scripts/recover.sh --restart   # 硬重置浏览器
bash scripts/keepalive.sh 540 45    # 占住回合连续播放（决定效率的关键）
bash scripts/watch.sh 30 0          # 每 30 秒值守（仅回合内有效）
```

## `recover.sh --status` 卡住不返回 / 返回空

`agent-browser` daemon 会瞬时卡死。实测某次卡 **2 分 32 秒**后返回空，而同一页面随后 0.15 秒就正常响应。

现在所有 `st()` 都有 `timeout 25`，超时按 `page:blank / action:reopen` 兜底，`recover.sh` 在重开无效时会自动 `close --all` 硬重置浏览器。

手工判断：

```bash
timeout 25 agent-browser eval --stdin < scripts/status.js   # 空返回 = daemon 卡死
agent-browser tab list                                      # 看标签还在不在
```

处置：

```bash
bash scripts/recover.sh --restart    # close --all → 重开 → 登录 → 进课 → 注入
```

## 说要暂停，其实早就停了

如果你发"暂停"时距离上一回合结束已超过 5～7 分钟，页面多半已被回收，播放本来就停了。`--hold` 在 `blank` 页无意义（写不进 localStorage），脚本现在会直接提示"当前没有播放，无需暂停"。

确认方式：

```bash
agent-browser tab list        # about:blank 即已无播放
ps -eo args | grep -E "[w]atch.sh|[k]eepalive.sh"   # 无残留进程即安全
```

> ⚠️ 但 `recover.sh --restart` 也不一定能挽回：`close --all` 之后如果 `open` 仍超时，说明 daemon 本身需要重建，重试一次通常恢复。

## 页面点不动 / 章节列表在视口外且无法滚动

桌面默认视口（1280×577）下专题页被裁成一屏，`scrollIntoView` 和 `scroll down` 都无效，滚动容器 `clientHeight` 为 0。

```bash
agent-browser set viewport 390 844
```

设置后页面重排，所有坐标结论作废，重新 `snapshot`。

## 登录填了没反应 / `waitForSelector('input')` 超时

页面有 6 个 `input`，4 个是自定义键盘的隐藏镜像（`type=tel`、`id=customKeyboard`）。按顺序取会填进隐藏框。

```bash
agent-browser fill "input[type=text].user" "156xxxxxxxx"
agent-browser fill "input[type=password]" "<密码>"
agent-browser click ".van-checkbox__label"    # 不是 input[type=checkbox]
agent-browser click ".login-btn"
```

用 Playwright 时同理，`input:visible` 才是有效选择器；`waitForSelector('input')` 默认等可见，会直接超时。

## 页面变 `about:blank`（最高频）

**根因不是页面 bug，是回合结束。** agent 完成一次回复后，沙箱在 5～7 分钟内回收标签页和子进程，登录态一起丢。

已排除：内存充足（126G 总 / 24G 用，Chrome RSS 320MB）、无 OOM 记录。同回合启动的 `watch.sh`、`node standalone.js` 也在同一时刻消失，可佐证是环境级回收。

`status.js` 会返回 `page: "blank"`、`action: "reopen"`。处置：

```bash
bash scripts/recover.sh        # 约 20 秒恢复
```

想**减少崩溃频率**，用 `keepalive.sh` 占住回合（见下节）。

## 播放效率只有三成 / 一直推不动

典型症状：用户问一次“进度”→ 恢复 → 播 7 分钟 → 又崩。原因同上，回合一结束就回收。

```bash
bash scripts/keepalive.sh 540 45     # 单次 9 分钟，连续调 3～4 次覆盖 30 分钟
```

实测对比（28 分钟窗口）：一问一恢复推进约 7 分钟内容；占住回合推进约 38 分钟（含 1.5 倍速折算）。

单次工具调用上限 600 秒，`DURATION` 别超过 560。

## 登录后被踢回 `#/login`

1. **开了第二个标签页**。同账号双端互斥，先开的被踢。
   ```bash
   agent-browser tab list && agent-browser tab close
   ```
2. **在手机或别的浏览器登录了同一账号**。这种会让当前端弹"您已在其他终端登录学习"，播放器被替换。
3. Token 过期（长时间空闲）。

三种都走 `recover.sh`；`#/login?redirect=...` 登录后会自动跳回原页。

## 课程页没有播放器（video 为 null）

两种完全不同的情况，别搞混：

| `status.no_video` | 现象 | 处置 |
|---|---|---|
| `notes` | 正文出现"快速笔记"，`.catalog-box li` 数量为 0 | 平台播完一课后的落地页，**注入控制器无效**。回专题页重选课程（`action: back_to_subject`，`recover.sh` 已自动处理） |
| `kicked` | 正文含"您已在其他终端登录学习"，选集列表还在 | 被别的设备顶掉。`recover.sh` 会重新进课并注入 |

v5 的控制器遇到 `notes` 会在连续 10 秒确认后自己回专题页，不用人管。

## 列表显示"需再学 mm:ss"

平台按"有效学习时长"结算，没播够就挂这个标记。这不是被跳过，是没播满。

v4 控制器会自动回补：播到列表最后一集时扫描所有带"需再学"的项，逐个回跳重播，清扫完才离开课程。

手工验证：

```bash
agent-browser eval "(()=>{const lis=[...document.querySelectorAll('.catalog-box li')].filter(li=>li.offsetParent!==null);return lis.map((li,i)=>i+(li.className.includes('active-section')?'*':'')+(/需再学/.test(li.innerText)?'[欠]':'')).join(',')})()"
```

若某集连续多轮都清不掉（`sweeps` 到上限 6），多半是平台要求前置测验或阅读材料，脚本无法自动完成。

## `eval` 报 `Identifier 'x' has already been declared`

页面上下文共享，`const` / `let` 不能重复声明。用 IIFE：

```js
(()=>{ const x = 1; return x })()
```

## `screenshot` 报 "Element not found"

命令是位置参数：`agent-browser screenshot [selector] [path]`，传 `--path` 会被当选择器。

```bash
agent-browser screenshot --screenshot-dir /root/.codebuddy/artifact
```

## 分院弹层点错项

`.nav-item:nth-child(n)` 会命中错误项（弹层内还有标题等兄弟节点）。用文本匹配：

```js
[...document.querySelectorAll('.nav-item')].find(e => e.innerText.trim() === '安全学院').click()
```

## 进度条长时间不动

```bash
agent-browser eval "(()=>{const v=document.querySelector('video');return JSON.stringify({t:Math.round(v.currentTime),paused:v.paused,rate:v.playbackRate,ready:v.readyState})})()"
```

- `paused=true` → `v.play()`
- `rate=1` → 控制器被清了（页面重载），重新注入
- `ready<3` 且位置不动 → 缓冲卡住，点一下当前集重载

平台进度按整段视频结算，`currentTime` 在走但百分比不变属正常。

## 倍速到底生效了吗

别靠肉眼估，做一次定量测量：

```bash
agent-browser eval "(()=>{const v=document.querySelector('video');window.__s0=v.currentTime;window.__w0=Date.now();return 'mark'})()"
sleep 20
agent-browser eval "(()=>{const v=document.querySelector('video');const dt=(Date.now()-window.__w0)/1000;return 'ratio='+((v.currentTime-window.__s0)/dt).toFixed(2)+' rate='+v.playbackRate})()"
```

`ratio` 应等于 `rate`。若 `ratio` 明显偏低，通常是刚注入时页面还在缓冲，等 30 秒再测。

## 会话结束 / 沙箱休眠后播放是否继续

不会，但原因和直觉不同：不是"沙箱睡了才停"，而是**回合结束后 5～7 分钟标签页就被回收**，比休眠更早。

- 已完成学时在服务端，重进后从断点继续，不会丢
- 平台的播放位置记忆甚至会直接续播（实测重开后落在 548/2826 秒，不是 0）
- 想连续播放：`keepalive.sh` 占住回合
- 想真正通宵无人值守：把 `standalone.js` 放到自己的电脑/服务器上配 systemd，别指望 agent 沙箱
