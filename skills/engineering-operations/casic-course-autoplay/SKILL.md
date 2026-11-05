---
name: casic-course-autoplay
description: Use when 用户明确要求在航天云课堂（train.casicloud.com 微信端 H5）自动登录、切换分院、进入专题并按倍速顺序刷完课程视频，支持崩溃自愈、欠学时回补、主动暂停与定时汇报。当用户给出该平台账号密码并要求"登录后播放/刷完某专题/安全学院的课程"时使用。
---

# 航天云课堂自动刷课

把「登录 → 切分院 → 找专题 → 进课程 → 倍速连播 → 跨课程续播 → 崩溃自愈」固化成可复用流程。核心是 `scripts/` 下的注入脚本 + 自愈脚本，其余是页面操作。

## 仓库使用约定

- 收录不代表安装依赖或执行操作；用户明确要求后才登录、播放或启动值守。
- Bash 示例从本技能目录执行。Windows 需使用具备 Node.js、agent-browser、GNU timeout 的 Git Bash / WSL；PowerShell 不能直接执行 .sh。独立运行器还需 Playwright 和可用浏览器。
- config.env 已忽略。状态和日志默认应放在仓库 output/casic-course-autoplay/；原脚本保留原有默认路径，独立运行器请显式传 --state。
- 以下关于 5～7 分钟回收、600 秒工具超时、内存和效率的数据均为来源环境历史观察，未在本仓库验证。先检查当前环境，不直接认定回合结束是根因，不默认启动保活循环。
- 页面选择器和服务端学时结算尚未实站验证；以平台完成状态为准。最多回补 6 轮，退出课程不保证学时已完成。

PowerShell 示例（仓库根目录；仅检查语法）：

```powershell
node --check .\skills\engineering-operations\casic-course-autoplay\scripts\standalone.js
```

独立运行器示例（仅在用户明确要求运行后执行，需先创建输出目录）：

```powershell
New-Item -ItemType Directory -Force .\output\casic-course-autoplay | Out-Null
node .\skills\engineering-operations\casic-course-autoplay\scripts\standalone.js --user '<账号>' --pass '<密码>' --url '<专题URL>' --state .\output\casic-course-autoplay\state.json
```

可移植 Shell 示例（仓库根目录）：

```bash
mkdir -p output/casic-course-autoplay
node skills/engineering-operations/casic-course-autoplay/scripts/standalone.js \
  --user '<账号>' --pass '<密码>' --url '<专题URL>' \
  --state output/casic-course-autoplay/state.json
```

## 30 秒上手

```bash
cp config.env.example config.env && vi config.env   # 填专题 URL、账号、密码
bash scripts/recover.sh --status                 # 体检：给出现状和建议动作
bash scripts/recover.sh               # 一键自愈：重开→重登→回专题→进课→注入控制器
bash scripts/recover.sh --list                   # 全部课程完成状态表
bash scripts/keepalive.sh 540 45                 # 占住回合连续播放（这一步决定效率）
```

## 适用场景

- 用户给出 `https://train.casicloud.com/app/wechat/...` 链接 + 手机号 + 密码，要求代其完成专题学习
- 典型诉求："切换安全学院，播放消防专题"、"1.5 倍速顺序播放"、"每 30 分钟汇报"、"第三门结束就暂停"

## 前置检查

```bash
which agent-browser && node -v && agent-browser --version
```

## 第 0 步（关键）：先切移动视口

平台是移动端 H5。桌面视口（1280×577）下专题页被裁成一屏且**无法滚动**，`scrollIntoView` 也无效，看起来像"点不动"。

```bash
agent-browser open "<URL>"
agent-browser set viewport 390 844
```

必须在任何页面判断之前做。视口切换会重排页面，之前的坐标结论全部作废。

## 第 1 步：登录

```bash
agent-browser fill "input[type=text].user" "156xxxxxxxx"
agent-browser fill "input[type=password]" "<密码>"
agent-browser click ".van-checkbox__label"
agent-browser click ".login-btn"
```

要点：

- 页面上有 **6 个 input**，其中 4 个是自定义键盘的隐藏镜像（`type=tel` 的 `#customKeyboard` 等）。按 `input` 顺序取会填到隐藏框里，看起来"填了没反应"。用 `input[type=text].user` 和 `input[type=password]` 这两个**唯一可见**的选择器。
- 协议勾选框是 `van-checkbox`，**没有原生 `input[type=checkbox]`**，`check()` 会失败；点 `.van-checkbox__label` 才有效。
- 登录按钮是 `DIV.login-btn`，不在无障碍树里，只能按 CSS 选择器点。
- 登录成功 hash 变 `#/business-home?...`，底部出现 首页/课程/阅读/我的。

## 第 2 步：切换分院

分院名不在首页正文，藏在顶部标题弹层里。

```bash
agent-browser click ".cur-branch-name"
agent-browser eval "(()=>{const n=[...document.querySelectorAll('.nav-item')].find(e=>e.innerText.trim()==='安全学院');if(!n)return 'nf';n.click();return 'ok'})()"
agent-browser click ".sure-btn"      # 「完成」按钮
```

**不要用 `nth-child`**：业务分院的 `.nav-item` 被嵌套包裹，`nth-child(4)` 会点错项。必须按文本匹配。

## 第 3 步：进入专题与课程

```bash
# 专题卡片上的「我要学」
agent-browser eval "(()=>{const b=[...document.querySelectorAll('*')].filter(e=>e.children.length===0&&e.innerText&&e.innerText.trim()==='我要学');b[0].click();return 'ok'})()"

# 章节列表：每门课是一个 .s-info-right，内含 .sub-left（标题）
agent-browser eval "(()=>{const it=[...document.querySelectorAll('.s-info-right')].find(e=>e.innerText.includes('重大火灾案例警示片（二）'));(it.querySelector('.sub-left')||it).click();return 'ok'})()"
```

课程内视频列表是 `.catalog-box li`，**有一组隐藏的重复节点**，必须过滤：

```js
Array.from(document.querySelectorAll('.catalog-box li')).filter(li => li.offsetParent !== null)
```

点某个 `li` 即切换并播放该集。

## 第 4 步：注入控制器

```bash
agent-browser eval --stdin < scripts/autoplay.js
agent-browser eval --stdin < scripts/status.js
```

`autoplay.js`（v5）行为：

1. 每 **2 秒**把 `playbackRate` 拉回目标值（平台偶尔重置倍速，间隔越短损失越少）
2. 用 `li.active-section` 定位当前集，URL 里的 `/detail/{cid}/{epIdx}` 和时长时间码做兜底
3. 播完切下一集；**到最后一集时先回补所有"需再学"的集**，补完才算本课完成
4. 本课完成 → 回专题页 → 进第一门非"已完成"课程，循环
5. 状态按 `courseId` 存 `localStorage.__casic_state`，刷新/重登后重新注入即续上原集
6. 心跳写 `localStorage.__casic_hb`，外部据此判断控制器死活
7. `stopAfterCourse: true` 时本课结束**只暂停、不跳下一门**
8. 落到 `#/login` 或播放器消失只写标记，绝不乱点页面
9. **课程页既无 `video` 又无选集列表** → 连续 10 秒确认后自动回专题页（平台播完会跳"快速笔记"页，那种页面注入控制器毫无意义）

配置写在注入前：

```bash
agent-browser eval "localStorage.setItem('__casic_cfg', JSON.stringify({rate:1.5,stopAfterCourse:true}));'ok'"
```

> **不要用视频时长 `mm:ss` 定位当前集**。平台显示截断后的整数分钟，1049 秒显示成 `17:28`，按秒反算 `17:29` 必然错配，结果是播完跳回第 1 集。

## 第 5 步：巡检 / 自愈

```bash
bash scripts/recover.sh --status      # 只体检，输出 JSON
bash scripts/recover.sh --list        # 打印全部课程完成状态表
bash scripts/recover.sh               # 自动进第一门未完成课程
bash scripts/recover.sh "课程名"       # 指定课程
bash scripts/recover.sh --hold        # 主动暂停（写 localStorage，跨刷新有效）
bash scripts/recover.sh --resume      # 解除暂停
bash scripts/recover.sh --restart     # 硬重置：关闭浏览器重建，再登录进课
```

`status.js` 的关键字段：

| 字段 | 含义 |
|---|---|
| `page` | `course` / `subject` / `login` / `blank` / `other` |
| `action` | `none` / `reopen` / `relogin` / `enter_course` / `reinject` / `back_to_subject` / `holding` |
| `alive` | **页面内**控制器心跳是否新鲜（>12s 即死）。页面刷新后必为 `false` |
| `no_video` | 课程页无播放器的原因：`notes`（快速笔记页）/ `kicked`（被顶）/ `loading` |
| `courses` | 专题页才有：`[{i,title,done,learning}]` 全量课程状态 |
| `done_count` / `total_count` | 专题完成度 |
| `pending_eps` | 仍标"需再学"的集索引 |
| `progress` / `required` | 课程总进度、必修 x/y |

> `alive` 只看 `window.__ap`，**不能用 localStorage 心跳兜底**。早期版本用兜底，导致页面刷新后仍被判"活着"，`watch.sh` 不触发自愈，卡在专题页一动不动。

`watch.sh` 是"体检 → 异常就 `recover.sh`"的循环，默认 30 秒一轮。

## 第 5.5 步（实战最关键）：占住回合，否则播放等于白干

**现象**：agent 每完成一次回复，回合结束，约 **5～7 分钟**后标签页被清成 `about:blank`，登录态一起丢，播放停止。

**已排除的假设**：

```
内存   126 GB 总量 / 已用 24 GB / 可用 102 GB
Chrome RSS 320 MB
OOM 记录  无
```

不是内存问题，也不是页面 bug——是运行环境在回合空闲后回收标签页和子进程（同回合启动的 `watch.sh`、`node standalone.js` 也在同一时刻消失）。

**后果**：如果"用户问一句 → 恢复 → 播 7 分钟 → 又崩"，实际效率只有 30%。实测对比：

| 方式 | 28 分钟内推进的内容 |
|---|---|
| 一问一恢复 | 约 7 分钟 |
| 占住回合 | 约 38 分钟（含 1.5 倍速折算 3 门课） |

**对策**：

```bash
bash scripts/keepalive.sh 540 45      # 540 秒，每 45 秒体检，异常自动 recover
```

单次工具调用有 600 秒上限，所以 `keepalive.sh` 一次跑 540 秒（9 分钟），循环调用 3～4 次即可覆盖 30 分钟。只要这个调用没返回，回合就不算结束，页面就不会被回收。

要 30 分钟汇报一次，就连续跑 3～4 次 `keepalive.sh`，然后读 `recover.sh --status` 汇报，再继续跑。汇报本身就是回合结束的瞬间，之后仍会崩，下次调用 `recover.sh` 恢复即可（约 20 秒）。

> 该限制只存在于沙箱环境。在真实机器上跑，用 `standalone.js` + systemd 才是正解（见第 6 步）。

## 第 6 步（可选）：脱离 agent 常驻

`scripts/standalone.js` 是 Playwright 版独立运行器：自己起浏览器、自己登录、自己决策，断点存 `state.json`。

```bash
node scripts/standalone.js --user 156xxxxxxxx --pass '***' --url "<专题URL>" \
  --rate 1.5 --chrome /root/.cache/ms-playwright/chromium-<ver>/chrome-linux64/chrome
```

| 参数 | 说明 |
|---|---|
| `--url` | 直达专题，避免首页误点 |
| `--chrome` | 复用已下载的 chromium，跳过 `npx playwright install`（版本对不上时用它救命） |
| `--report` | 进度日志间隔，默认 1800000（30 分钟） |

⚠️ **实测限制**：在沙箱环境里，后台 node 进程扛得过页面崩溃、扛得过登录过期，**但扛不过回合结束**——会话空闲后进程树被回收。所以它适合"在你自己电脑/服务器上常驻"，不适合指望它在 agent 沙箱里通宵跑。

## 坑位清单

- **崩溃根因是回合结束，不是页面 bug**：见第 5.5 步。别去查内存、别去重装浏览器，那都是白费。要连续播放就 `keepalive.sh` 占住回合。
- **`agent-browser` daemon 会瞬时卡死**：实测某次体检卡了 **2 分 32 秒**才返回空，同一页面随后又 0.15 秒正常响应。所有 `st()` 都加了 `timeout 25` 兜底（超时按 `page:blank` 处理），`recover.sh` 重开无效时会自动 `close --all` 硬重置。不加超时会把 `watch.sh` 的 60 秒周期和 `keepalive.sh` 的时长全拖乱。
- **平台播完会跳"快速笔记"页**：`#/study/course/detail/xxx` 但既无 `video` 也无 `.catalog-box li`。这种页面注入控制器无效，`status.js` 会报 `no_video=notes` / `action=back_to_subject`，正确处置是回专题页重选课程。
- **`autopilot_on` 曾长期显示 `false` 却是正常的**：v4 在本课播完后把 `A.on` 置 false，进入下一门没重置。v5 已修（换课/点课时强制 `A.on = true`）。若仍见 false 但 `switches` 在涨，说明只是字段失真。
- **不要开第二个标签页**：同账号双标签触发登录互斥，主标签被踢回 `#/login`，视频中断。
- **不要在手机上登录同一账号**：会弹"您已在其他终端登录学习"，播放器被替换掉，`video` 元素消失。
- `eval` 在同一页面上下文共享作用域，二次执行 `const el = ...` 会报重复声明；一律 IIFE 包裹或挂 `window.__xxx`。
- `agent-browser screenshot` 是位置参数，传 `--path` 会报 "Element not found"，用 `--screenshot-dir <dir>`。
- 页面 `<title>航天云课堂</title>` 会干扰按文本找元素，筛选加 `e.children.length === 0`。
- 首屏封面占满视口、章节列表 `clientHeight = 0`，**这是没切移动视口的信号**，回第 0 步。
- **已完成学时在服务端**，随便崩、随便停，进度不会丢；平台的播放位置记忆甚至能让重进课程时从断点续播（实测重开后直接落在 548/2826 秒）。

## 资源

- `scripts/autoplay.js` — 倍速 + 顺序播放 + 欠学时回补 + 跨课程续播（注入式，v5）
- `scripts/status.js` — 状态快照，含 `action` 建议动作与专题课程清单（v4）
- `scripts/recover.sh` — 一键自愈 / 暂停 / 恢复 / 课程全景表
- `scripts/keepalive.sh` — **占住回合**并自愈，单次 9 分钟，连续调用可覆盖整晚
- `scripts/watch.sh` — 值守循环（回合内有效）
- `scripts/jq.js` — 从 eval 结果里取字段的小工具
- `scripts/standalone.js` — Playwright 独立运行器（需真实机器 + systemd）
- `config.env.example` — 配置模板（复制为 `config.env`，含账号，勿分发）
- `references/troubleshooting.md` — 逐症状排查表
- `references/portability.md` — 换 Playwright/Puppeteer/浏览器 MCP 时的命令映射
