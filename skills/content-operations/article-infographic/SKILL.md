---
name: article-infographic
description: Use when turning a finished article into a single-page ImageGen infographic, independently or optionally after wechat-format. Supports landscape and portrait.
---

# 文章信息图

## 输入与范围

读取最终文章正文或路径；wechat-format 交接时读取 manifest 的 `enhanced_markdown`，复用主题、来源台账、输出目录和已选方向，不重新润色文章。

缺正文或方向时合并询问缺项；已提供的不再问。横版 `landscape` 默认 3:2，竖版 `portrait` 默认 2:3；用户尺寸优先，等待方向时可提炼内容。两版都要则分别布局与生成，不旋转或拉伸原图。

独立输出根目录为 `output/article-infographic/<article-slug>/`，集成时沿用 workflow 根目录，用户路径优先。独立交付，不自动插入正文或发布。

## 内容 → 提示词 → 图片

1. 通读成稿，提炼标题、一句结论、通常 3–6 个节点及关系、必要数据和适用边界。提纲为每个节点标注原文章节或短句；核对现有来源台账。保留单位、时间范围、不确定性，不添加成稿未支持的事实或将相关性改成因果。
2. 按关系选择流程、对照、层次、时间线或机制图。横版以左右布局为主，竖版以上下布局为主；精简文字，不堆全文。提示词只包含下列生成规格，无需重复全文或来源台账：

   ```text
   用途：infographic-diagram，中文单页信息图
   方向/目标比例：已选值
   布局：主结构、阅读顺序、节点关系与箭头含义
   逐字文案：标题、结论、节点标签、数据、限定语
   视觉：主题配色、清晰中文、高对比、留白、不透明背景
   约束：仅渲染所列文案，不补造数据；完整呈现，不裁切
   ```

3. 使用环境可用的 ImageGen，优先内置 `image_gen`；存在 imagegen 技能时遵循其操作要求，参数以实际工具为准。不可用或失败则保存提纲与提示词并报告状态，不改用 HTML/截图，不擅自切换需密钥的 CLI/API。
4. 将实际返回图片复制到输出目录，保留真实扩展名。打开图片，对照提纲检查中文、数值、单位、限定语、箭头、裁切和方向。发现问题才用 ImageGen 定向修订，最多两轮；仍有问题标为待修订。

## 产物与验收

每版在 `infographic/` 保存同名前缀的三个文件：`infographic-<orientation>.png`、`infographic-<orientation>-content.md`、`infographic-<orientation>-prompt.md`。图片扩展名以实际格式为准；后续版本加后缀避免覆盖已有交付。

在根目录 manifest.json 新建或更新 `infographic`，保留其他字段。统一使用 variants 数组承载单版或双版：

```text
infographic:
  source_markdown: 实际来源路径（正文输入先归档）
  generator: image_gen
  variants:
    - orientation: landscape | portrait
      target_aspect_ratio: 目标比例
      width / height: 实测像素，未生成时为 null
      content / prompt / image: 相对 manifest 的实际路径，未生成图片为 null
      status: completed | needs_revision | unavailable | failed
      content_checked / visual_checked: 实际完成的检查布尔值
```

仅当图片已保存且内容、视觉检查通过时标为 completed。成稿变化或文章脚本重跑后重新核对图片并更新记录；不沿用旧验收状态。

展示图片，提供图片、提纲、提示词、manifest 链接；文章 HTML 仅在集成流程确实生成时提供。说明未解决的问题，不将图片称为可编辑源文件。
