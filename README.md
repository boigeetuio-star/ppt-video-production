# voiceover-course-video

从中文口播音频制作 16:9 商业培训课件视频的 HyperFrames Skill。

**能力**：口播音频 → 逐词时间戳转写 → 分页方案（≥18 页编辑式排版）→ HyperFrames 合成（页面与内容按口播词开始时间 30fps 帧级卡点）→ check/快照/渲染/ffprobe 全量验证。

## 内容

| 路径 | 说明 |
| --- | --- |
| `SKILL.md` | 触发说明、参数表、流程概览、关键规则 |
| `references/workflow.md` | 完整分步流程（转写、分页、工程、动画、验证） |
| `scripts/transcribe_words.py` | faster-whisper 逐词转写 |
| `scripts/merge_timeline.py` | ASR 段级时间轴 × 词级时间融合 |
| `scripts/build_timeline.py` | 页方案 → 每页 `data-start/data-duration/data-u` 词级绑定表 |
| `assets/composition-template.html` | 脱敏模板：21 种排版样式库 + 3 示例页 + 词级动画引擎 |

## 使用

品牌名与配色均为参数（`BRAND_EN` / `BRAND_ZH` / `--accent` / `--accent-deep` / `--ink` / `--paper`），Skill 不内置任何个人或品牌信息。详见 `SKILL.md`。

## 依赖

Node 22+、FFmpeg、HyperFrames CLI（`npx hyperframes`）、`faster-whisper`、`zhconv`、mediakit-cli。
