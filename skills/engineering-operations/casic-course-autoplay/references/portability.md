# 可移植性说明

> 来源环境的历史经验，未在本仓库实站验证。回收时间和命令兼容性以当前环境为准，参见 SKILL.md 的仓库使用约定。

## 本质是什么

这个 skill 里没有二进制、没有私有 SDK、没有凭证，只有两类东西：

| 类型 | 文件 | 是否与运行时绑定 |
|---|---|---|
| 流程知识 | `SKILL.md`、`references/` | 否，纯文本，任何 agent 都能读 |
| 页面操作脚本 | `scripts/autoplay.js`、`scripts/status.js` | 否，标准 DOM API，浏览器里执行即可 |

绑定发生在**命令层**：SKILL.md 里的 `agent-browser xxx` 需要替换成对方自己的浏览器工具调用。替换后即可运行。

## 依赖矩阵

**必需**

- 一个能执行 JS 的浏览器（headless 即可）
- 能对 DOM 求值：`document.querySelector('video')`、`.click()`、`location.hash = ...`
- 能设置视口为移动尺寸

**不需要**

- 不需要账号密码写进文件（运行时由用户提供）
- 不需要特定语言运行时（Node/Python 均可，JS 直接在页面里跑）
- 不需要视觉模型（流程全走 DOM 选择器），有截图能力更好排查

## 命令映射表

把 SKILL.md 里的命令按此表换掉：

| agent-browser | Playwright | Puppeteer |
|---|---|---|
| `open <url>` | `page.goto(url)` | `page.goto(url)` |
| `set viewport 390 844` | `page.setViewportSize({width:390,height:844})` | `page.setViewport({width:390,height:844})` |
| `eval "<js>"` | `page.evaluate(js)` | `page.evaluate(js)` |
| `eval --stdin < f.js` | `page.evaluate(fs.readFileSync('f.js','utf8'))` | 同左 |
| `click <sel>` | `page.click(sel)` | `page.click(sel)` |
| `type <sel> <text>` | `page.fill(sel, text)` | `page.type(sel, text)` |
| `snapshot -i` | `page.locator('body').ariaSnapshot()` | `page.accessibility.snapshot()` |
| `screenshot` | `page.screenshot({path})` | `page.screenshot({path})` |
| `tab list` / `tab close` | `context.pages()` / `p.close()` | `browser.pages()` |
| `close` | `browser.close()` | `browser.close()` |

浏览器 MCP（如 playwright-mcp、browser-use）通常已封装 `browser_navigate` / `browser_evaluate` / `browser_click`，直接把 SKILL.md 的命令逐条映射到同名工具即可，**核心是把两个 .js 脚本原样注入页面**。

## 平台相关部分（换站需重抓）

以下选择器是 `train.casicloud.com` 当前版本的，平台改版后会失效，需要重新 `snapshot` 抓：

```
.login-btn                    登录按钮
.cur-branch-name              顶部分院切换入口
.nav-item                     分院选项
.s-info-right / .sub-left     专题页课程条目
.catalog-box li               课程内视频列表
video                         播放器
```

`autoplay.js` 的逻辑（倍速锁定、时长反查索引、播完切下一条、跨课程回跳）与站点无关，只依赖上面几个选择器的语义，换站点只需替换选择器常量。

## 不能做什么

- **不能跨站复用**：脚本假设视频在 `<video>` 元素、列表项点击即切集。遇到 iframe 嵌套播放器、Canvas 渲染、DRM（Widevine）的平台需另写。
- **不保证绕过反作弊**：只做“1.5 倍速 + 自动连播”，未修改上报数据。平台若校验有效观看时长、随机弹题、人脸核验，脚本会卡住，需人工介入。
- **状态不跨进程**：控制器挂在页面 `window.__ap` 上，页面刷新或浏览器进程退出即失效，需重新注入。

## 给别人时的最小交付

1. 解开 zip，保留 `SKILL.md` 全文（它是流程主干）
2. 让对方把 `scripts/*.js` 当“注入到页面的代码片段”，不必当命令行脚本
3. 首次运行先跑一遍 `status.js`，确认返回的 `page` / `course` 字段与页面一致，说明选择器仍然有效
4. 若对方 agent 没有 skill 机制，把 `SKILL.md` 直接贴进系统提示或作为任务上下文，效果等同
