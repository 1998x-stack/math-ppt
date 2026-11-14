# math-ppt：数学题 → 可编辑 PPT + SRT + 配音时间轴

把数学题图片、参考解析或文字整理为**讲得清楚的数学课程**，输出学生直接观看的 PPT、配音文本、SRT 和逐页时间轴。当前已包含三角函数整数题的 **20 页完整示例**。

## 产物与边界

| 文件 | 用途 |
|---|---|
| `lesson.pptx` | 数学内容优先的可编辑课件，原生 PowerPoint 文字和形状 |
| `lesson.srt` | 完整中文字幕，含逐条起止时间 |
| `voiceover.txt` | 纯净配音文本，与 PPT 演讲者备注一致 |
| `timeline.json` | 每页与每条字幕的对应关系 |
| `lesson.json` | 唯一教案源，供后续修改和批量生产 |

**发布成品不能有**“开头 3 秒抓住数学矛盾”“9:16 竖屏教学”“原题重排”“新增推导”等仅供内部制作使用的文字。这些描述不应进入 PPT 页面、演讲者备注、TTS 配音和 SRT。生成脚本会对常见泄漏关键词做检查。

## 快速运行

使用 Python 3.10+ 与 `python-pptx`：

```bash
git clone https://github.com/1998x-stack/math-ppt.git
cd math-ppt
python -m pip install -r requirements.txt
python scripts/build.py \
  --input examples/tangent-integer-triangle/lesson.json \
  --out examples/tangent-integer-triangle/generated
```

脚本会生成：
```text
generated/
├── lesson.pptx
├── lesson.srt
├── voiceover.txt
└── timeline.json
```

要导出视频用 PNG，可通过 LibreOffice 将 PPTX 转为 PDF，再用 Poppler 的 `pdftoppm` 导出图片。也可以打开 PPT 直接导出每页图片。做字幕、片段和音频对齐时，应以 `timeline.json` 为对应表。

## examples/

示例：[三角形内角的正切值均为整数，求它们的和](examples/tangent-integer-triangle/)。

- [20 页教案 JSON](examples/tangent-integer-triangle/lesson.json)
- [配音纯文本](examples/tangent-integer-triangle/voiceover.txt)
- [SRT 字幕](examples/tangent-integer-triangle/lesson.srt)
- [逐页时间轴](examples/tangent-integer-triangle/timeline.json)
- [原题与数学核查](examples/tangent-integer-triangle/source_verification.md)

答案是 **6**。教案详细讲解最小角不超过 60°、`tan A=1`、剩余两个角为什么是锐角、和角公式、整数因式分解，以及 1、2、4 的迁移判断题。拓展题不会冒充原图片内容。

## 音视频制作流程

```mermaid
flowchart LR
    A[题目与解析] --> B[数学核查]
    B --> C[lesson.json]
    C --> D[PPTX]
    C --> E[纯净旁白与SRT]
    C --> F[逐页时间轴]
    E --> G[TTS配音]
    G --> H[对齐真实音频]
    D --> I[导出PNG]
    F --> H
    H --> J[剪映合成]
    I --> J
    J --> K[手机预览与发布]
```

初次生成的 SRT 时间由文本长度估算，**不等于与真实 TTS 音频精确同步**。配音生成后应采用逐段音频时长或强制对齐结果重新计算时间戳；不能仅仅根据音频总时长同比缩放就称为逐句精准对齐。

本仓库不会自动生成音频，除非额外接入 TTS 服务。音频合成和最终发布需在视频编辑软件中完成或接入对应 API。

## 项目文件

- [SKILL.md](SKILL.md)：完整 Agent 工作规则、成品约束与质量门槛。
- [scripts/build.py](scripts/build.py)：从教案构建 PPTX、字幕和时间轴。
- [references/audio-video-pipeline.md](references/audio-video-pipeline.md)：TTS 音画对齐与剪辑建议。
- [examples/tangent-integer-triangle/](examples/tangent-integer-triangle/)：包含真实可用数据的完整示范。
- [AGENTS.md](AGENTS.md)：维护与校验规则。

后续可以把不同年级和专题加入各自的 `examples/<topic>/` 目录，保持相同的输入输出契约。

## 已发布的真实 example 成品

完整示例目录：[examples/tangent-integer-triangle/](examples/tangent-integer-triangle/)，其中不仅有可复现的教案、逐页配音和 SRT，还包括 CI 自动生成并回写的 [可编辑 PPTX](examples/tangent-integer-triangle/lesson.pptx)、[PDF 预览](examples/tangent-integer-triangle/lesson.pdf) 和 [20 张竖屏图片](examples/tangent-integer-triangle/slides/)。这些二进制产物由 GitHub Actions 发布任务生成，普通 PR 只做验证，不推送文件。


## 一键课件视频：PPT ↔ SRT ↔ 页码 ↔ 语音

最新的标准构建新增 `slide_map.json`；`cue_to_page` 和 `pages[].captions` 负责建立字幕序号与 PPT 页码的机器可读映射，并且对 SRT 文件做哈希校验。SRT 单独不能推导出页面切点。

```bash
# 从教案生成 PPT、SRT、时间轴和逐页字幕映射
python scripts/build.py --input examples/tangent-integer-triangle/lesson.json --out build

# 预先列出 120 条配音任务（不请求网络）
python scripts/srt_to_tts.py --srt build/lesson.srt \
  --slide-map build/slide_map.json --out build/tts --dry-run

# 生成音频（社区 edge-tts 原型；生产环境可换官方 TTS）
pip install edge-tts
python scripts/srt_to_tts.py --srt build/lesson.srt \
  --slide-map build/slide_map.json --out build/tts

# 按真实音频时长校准字幕及切页，拼接 narration.wav
python scripts/retime_tts.py --timeline build/timeline.json \
  --cue-audio-dir build/tts --out build/aligned --assemble

# 接收 PPTX、音频、字幕和页码映射，自动生成竖屏 MP4
python scripts/render_course_video.py \
  --pptx build/lesson.pptx --audio build/aligned/narration.wav \
  --srt build/aligned/lesson.srt --slide-map build/aligned/slide_map.json \
  --out build/final.mp4
```

`render_course_video.py` 默认将字幕烧录进 MP4，同时输出 `final.srt` 和 `final.manifest.json`。传入 `--no-burn-subtitles` 可保留纯画面+配音视频，然后在剪映/CapCut 导入外部 SRT 作为可编辑字幕。合成依赖 `LibreOffice`、`pdftoppm`、`FFmpeg`（含 libass、libx264），不依赖 GUI 实时录屏。注意 PPTX 动画不保留。

完整复现示例：[三角函数20页课程](examples/tangent-integer-triangle/) · [字幕配音与剪映调查](references/srt-tts-capcut-research.md) · [音视频分工流程](examples/tangent-integer-triangle/VIDEO_WORKFLOW.md)。
