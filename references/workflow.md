# 完整工作流（voiceover-course-video）

## Step 1 词级转写

前置：`mediakit-cli video asr-subtitles`（language=cmn-Hans-CN，异步任务 query-task 轮询）产出段级时间轴 JSON，形如
`{"duration": <s>, "subtitles": [{"start_time": <s>, "end_time": <s>, "subtitle_text": "…"}]}`（结果文件可能带 UTF-8 BOM，须按 utf-8-sig 读取）。

```powershell
# 1) faster-whisper 逐词转写（CPU small 模型）
python scripts/transcribe_words.py "<audio.mp3>" words_whisper.json

# 2) 融合：ASR 段级文本 + whisper 词级时间 → timeline_final.json（词级卡点的权威依据）
python scripts/merge_timeline.py asr_result.json words_whisper.json timeline_final.json
```

产物 `timeline_final.json`：`{"duration": s, "segments": [{"text", "start", "end", "words": [{"w","s","e"}]}]}`。
检查 stderr 输出 `empty_words=0`；有 EMPTY 段需重新对齐或人工补词。
注意：ASR 的 `duration` 与音频实测时长（ffprobe）可能略有差异，最终 `data-duration` 以 ffprobe 实测为准。

辅助选词与绑定：`python scripts/build_timeline.py --dump-words timeline_final.json` 打印词流，从中挑选"只在本页口播中出现"的词作为绑定词；页与单元都支持直接给时间（`start_time` / `time`）绕过匹配。同词多页出现时用 `min_time` 或更独特的词/直接给时间。

## Step 2 分页方案（先确认再开工）

把口播内容按语义切分为若干页（页数无硬性下限，以单页信息量适中为准）。方案表每页含：**绑定口播词**（页面切换与标题/要点各自绑定哪几个词）、**文案要点**、**排版形式**、**背景**（深/浅/主色交替）。

每页排版形式尽量不重复，可选：大标题压屏、开放式分栏、引语对比、横向文字带、重点色块、流程横带、编号标题、悬念大字、CTA 色块、清单结尾。
避免重复卡片、大数字、模板化布局。

**先向用户提交完整方案表并确认，确认后才进入 Step 3。**

## Step 3 搭建工程

```powershell
# 新视频：独立文件夹
npx hyperframes init "<项目目录>" --non-interactive --example=blank --skill=general-video
```

- 字体：下载 FONT_HEAVY / FONT_REGULAR 两个 TTF 到 `fonts/`（验证文件头魔数 00 01 00 00）。
- 口播复制为 `media/voiceover.mp3`。
- 从 `assets/composition-template.html` 复制到项目 `index.html`，替换 CSS 变量 `--accent/--accent-deep/--ink/--paper`（品牌色）与 `BRAND_EN/BRAND_ZH` 占位（用户不需要则删除对应元素）。
- 按方案把模板示例 section 复制扩展为实际页数；每页背景类 `pg-dark / pg-light / pg-orange` 交替；根 `data-duration` = 音频时长；`<audio id="vo">` 的 `data-duration` 同步。

### 每页 HTML 模式（词级卡点核心）

```html
<section id="p01" class="clip pg-dark" data-start="0.2" data-duration="1.2">
  <div class="page">
    <div class="grid"></div>
    <div class="brand">BRAND_EN</div>
    <div class="brand-v">BRAND_ZH</div>
    <div class="content">
      <div class="t"  data-u="0"       data-kind="rise">…标题…</div>
      <div class="k"  data-u="0.7667"  data-kind="fade">…副句…</div>
    </div>
    <div class="pageno"><b>01</b><i>/ 21</i></div>
  </div>
</section>
```

- `data-start`/`data-duration`：页面切换时间，来自方案绑定词（`ceil(词开始秒×30)/30`）。
- `data-u`：内容单元出现时间 = 绑定词绝对时间 − 页面 `data-start`（秒，帧级对齐，见 build_timeline.py）。
- 多元素列表（标签组/流程步骤/清单行）各自独立 `data-u`，逐词逐个出现，禁止整组一起出现。
- 完整句子/卡片是一个动画主体（一个元素），禁止拆成多字动画。

### 动画与转场

模板内嵌 GSAP 引擎已实现：页面 0.12s 快速淡入、内容单元 `data-u` 驱动 0.38s ease-out（`rise` 上滑 36px / `slidel` 左入 48px / `slider` 右入 48px / `fade` 淡入）、页面 0.12s 淡出、末页 0.4s 淡出至黑。无需手写动画逻辑，只改 `data-u`/`data-kind`。

## Step 4 检查

```powershell
npx hyperframes check          # lint+runtime+layout+motion+contrast，须 0 error 且 Contrast 全过
npx hyperframes snapshot --at <各页稳定帧,卡点帧>   # 逐页目检
```

常见修复：
- 半透明小字对比度不足 → 提高 alpha 至 ≥0.62（或改深色系），WCAG 3:1（大字 24px+）达标。
- 描边数字（`-webkit-text-stroke` + `color: transparent`）被判不可见 → 补 `-webkit-text-fill-color: rgba(<ink>,0.18)`。
- 动画中间态被采样到低对比 → 该元素出现时间不动，只保证静止态达标即可（check 采样到动画中属正常误报，可改采样点或确认静止态）。

卡点验证帧示例：标签/步骤/清单逐项出现的前后各拍一帧，确认"前一项在、后一项不在"。

## Step 5 渲染与交付

```powershell
npx hyperframes render --quality delivery --fps 30 --output "<项目名>_v<N>.mp4"
ffprobe -v error -show_format -show_streams "<…>.mp4"   # h264 / 1920×1080 / 30fps / 时长≈音频
```

- 版本号：每次修改递增（_v1/_v2/_v3…），不得覆盖旧文件。
- 新视频独立文件夹；修改现有视频原地更新。
- 交付前：check 全绿、逐页快照目检（无裁剪/重叠）、ffprobe 核验、抽 2–3 帧确认音画同步与卡点。
