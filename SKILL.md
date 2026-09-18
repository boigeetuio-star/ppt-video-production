---
name: PPT视频制作
description: 从中文口播音频制作商业培训/知识讲解类课件视频（HyperFrames 合成，编辑式排版、词级卡点动画）。当用户提供口播音频/旁白并要求制作课件视频、培训视频、课程视频、知识讲解视频、口播配动画课件、或说"用我的课件模板做视频"时使用。流程含逐词时间戳转写、按口播词绑定页面切换与内容出现时间（30fps 帧级取整、未说到不提前出现）、check/快照/渲染/ffprobe 全量验证。品牌名与配色均为参数，Skill 不内置任何具体品牌或配色信息。
---

# Voiceover Course Video（口播课件视频）

把一段中文口播音频制作成 16:9 商业培训课件视频：1920×1080、30fps、H.264/MP4、时长与音频一致、无字幕。页面与内容出现时间精确绑定到口播词的开始时间。

## 执行前参数（必须向用户确认或取默认）

| 参数 | 说明 | 默认/示例 |
| --- | --- | --- |
| `BRAND_EN` | 左上角英文品牌（可为空则删除该元素） | 用户提供 |
| `BRAND_ZH` | 左侧竖排中文品牌（可为空则删除该元素） | 用户提供 |
| `ACCENT` / `ACCENT_DEEP` / `INK` / `PAPER` | 主色/深主色/深色/浅色四值，由用户提供（不要内置任何具体色值） | 用户提供 |
| `MIN_PAGES` | 页数下限（无硬性限制，按口播内容切分，可为任意页数） | 不限 |
| `FONT_HEAVY` / `FONT_REGULAR` | 标题/正文字体文件（TTF，本地路径） | 用户提供 |
| `OUT_DIR` | 项目目录 | 新视频独立文件夹；修改原地更新 |

## 流程概览

1. **词级转写**：`scripts/transcribe_words.py` 转写逐词时间戳 → `scripts/merge_timeline.py` 融合成段级+词级时间轴。
2. **分页方案**：按口播内容切分（页数不限，避免单页信息过载即可），每页绑定口播词开始时间；先交方案表给用户确认后再开工。
3. **搭建工程**：`hyperframes init` + 字体 + 从 `assets/composition-template.html` 复制脱敏模板，按方案改写每页。
4. **检查**：`npx hyperframes check` 全绿；`npx hyperframes snapshot` 逐页快照目检。
5. **渲染交付**：`npx hyperframes render --quality delivery --fps 30` → ffprobe 核验 → 版本号递增交付（v1/v2/v3…，不得覆盖旧文件）。

## 资源

- `references/workflow.md` — 完整分步流程（转写、分页、工程、动画规则、验证清单）
- `scripts/transcribe_words.py` — faster-whisper 词级转写（CPU，参数化）
- `scripts/merge_timeline.py` — ASR 段级时间轴与 whisper 词级时间融合
- `scripts/build_timeline.py` — 页方案 JSON + 词时间轴 → 每页 data-start/data-duration/内容单元 data-u 绑定表
- `assets/composition-template.html` — 脱敏模板（排版 CSS 全量 + 3 个示例页 + 词级动画引擎），品牌/配色为 CSS 变量占位

## 关键规则（违背即返工）

- **词级卡点**：页面切换与每个内容单元绑定对应口播词的开始时间，`ceil(词开始秒 × 30)/30` 帧级取整；未说到的内容一律不提前出现；完整句子/卡片为一个动画主体，禁止拆字。
- **动画**：0.35–0.4s 短距滑入或淡入，ease-out；禁页面抖动/慢飘/弹跳/大缩放/旋转；转场快速淡入淡出（0.12s），不得提前切页。
- **检查**：交付前 check 全绿（Layout/Contrast/Motion）+ 逐页快照 + ffprobe 时长/分辨率/fps 核验；每页目检文字裁剪、元素重叠、颜色对比（WCAG AA）。
- **版本**：每次修改另存新版本号（_v2/_v3），不得覆盖旧文件。
