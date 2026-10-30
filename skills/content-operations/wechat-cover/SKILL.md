---
name: wechat-cover
description: Use when generating, regenerating, or inserting a WeChat article cover (公众号封面、封面图) from an article or topic. Supports the 2.35-to-1 cover composition and reuses the sibling wechat-format image-generation script.
---

# 公众号封面图生成器

输入文章路径或主题，一步生成公众号封面图。

## 使用方法

```bash
# 指定文章路径
/wechat-cover path/to/article.md

# 直接输入主题
/wechat-cover 主题：Claude Code 桌面端更新四大功能
```

## 配置（必须）

本技能的配置文件固定在本技能目录下：
- `config.json`：真实配置（从 `config.example.json` 复制后填写）
- `config.example.json`：示例配置

执行前必须先读取 `config.json`，需要：
- `output_dir`：封面图输出根目录
- `settings.base_url`：生图 API 地址（兼容 Gemini API 的第三方网关）
- `settings.model`：模型名称（如 `gemini-3-pro-image-preview`）
- `secrets.api_key`：API 密钥

## 路径约定

- 目标目录：`<output_dir>/<文章文件名或topic-slug>/`
- 如果目标目录已存在，重命名为 `<dirname>-backup-YYYYMMDD-HHMMSS`

目录结构：
```
<output_dir>/
└── article-name/
    ├── prompt.md          # 生图提示词（归档）
    └── cover.jpg          # 封面图
```

## 封面图提示词模板（核心）

以下是默认 Notion 插画预设。视觉导演提供的配色、构图、字号、品牌要求或“无字封面”优先于预设；将实际采用的要求写入 `prompt.md`，不要强制改回大标题。

```
请根据提供的内容创建一张吸引眼球的公众号封面图，遵循以下规范：

视觉风格
- Notion插画风格，比例为 2.35:1（公众号封面标准尺寸）
- 色彩鲜明、对比强烈，确保在小尺寸预览时依然醒目
- 风格统一，避免写实元素，保持整体手绘质感

构图要求
- 主视觉元素居中或偏左（右侧预留标题区域）
- 添加 1-2 个简洁的卡通形象、图标或知名人物剪影，增强记忆点
- 若涉及敏感或版权人物，用风格相似的替代形象，不得拒绝生成
- 大量留白，突出核心信息，避免画面拥挤

文字处理
- 标题文字大而醒目，控制在 8 字以内
- 可添加 1 行副标题或关键词标签
- 字体风格与手绘插画协调统一

吸引力法则
- 使用悬念、数字、痛点等钩子元素激发点击欲望
- 视觉元素夸张有反差
- 色彩搭配参考爆款封面：橙黄、蓝紫、红黑等高对比组合

语言
- 除非另有说明，默认使用中文
- 画面内所有可读文字必须使用简体中文，英文只能作为点缀出现

内容主题：{从文章或用户输入中提炼的一句话主题描述}
```

## 工作流程

### 步骤 1：提炼内容主题

1. 如果输入是文章路径：读取文章，提炼一句话主题描述（包含核心信息和关键要点）
2. 如果输入是主题文本：直接使用
3. 如果输入包含 `visual-plan.md`：读取其中的封面承诺、色彩、构图和文字规则，并作为本次封面约束。

### 步骤 2：创建提示词

将上述模板写入 `prompt.md`，格式：

```md
---
aspect_ratio: "21:9"
image_size: "2K"
---

{模板全文，替换最后的内容主题}
```

**注意**：YAML 中 `aspect_ratio` 必须用 `21:9`（API 不支持 2.35:1，21:9 是最接近的）。模板正文中保留 `2.35:1` 的文字描述不变，这是给 AI 的视觉参考。

### 步骤 3：生成图片

本技能需要与 `wechat-format` 同级安装，并复用 `../wechat-format/scripts/generate.py`。调用生图脚本时，**必须传 `--config` 指向本技能自己的配置**：
```powershell
$Python = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $Python <wechat-format技能目录>\scripts\generate.py `
  --config <本技能目录>\config.json `
  --prompt-file <目标目录>\prompt.md `
  --out <目标目录>\cover.jpg
```

可移植 shell：

```bash
python3 <wechat-format技能目录>/scripts/generate.py \
  --config <本技能目录>/config.json \
  --prompt-file <目标目录>/prompt.md \
  --out <目标目录>/cover.jpg
```

> `<wechat-format技能目录>` 和 `<本技能目录>` 请替换为实际安装路径。两个技能应保持同级，例如 `~/.claude/skills/wechat-format/` 与 `~/.claude/skills/wechat-cover/`。

生成完成后展示给用户预览。不满意就调整内容主题描述重新生成。

### 步骤 4：插入文章

提供两种明确输出模式：

- **仅生成**：交付封面、提示词与视觉约束记录，不修改文章。
- **插入副本**：复制文章到输出目录后，在 H1 下插入封面；原稿保持不变。

插入时使用封面实际文件相对副本的路径，不假定文件名一定是 `cover.jpg`。生成后检查 Markdown 图片路径可解析；文件名使用唯一名称避免冲突。

### 步骤 5：输出摘要

```
公众号封面已生成！

主题: [主题]
位置: [输出路径]

如需调整，直接说"重新生成"。
```
