# PPT、SRT 与 TTS 语音制作规范

## 标准数据流

`lesson.json` 的 `notes` 是唯一旁白源。生成器从同一份 `notes` 同时创建：

- PPT 的 speaker notes
- 可供 TTS 读取的 `voiceover.txt`
- 逐条 `lesson.srt`
- 包含每页开始/结束时间和 cue 编号的 `timeline.json`

**不要**在这些观众可听见的字段中写“开头 3 秒”“第几页切镜头”“9:16 竖屏教学”等制作提示。制作信息只写在技术文档。

## 初始 SRT 估算与真正同步

初始 `timeline.json` 有标记 `alignment=estimated_from_text_not_audio`：按照文字长度估算片段时长。这足够用来排课件与视频分镜，但**不代表与尚未生成的音频精确同步**。

推荐两种配音路径：

1. **逐 cue TTS**：把 `lesson.srt` 的每条字幕单独生成语音片段，按 001.wav、002.wav 等编号保存。利用 `ffprobe` 测量实际片段时长，再用 `scripts/retime_tts.py` 重新生成 SRT 和逐页时间表。最终拼接音频时保留相同顺序及停顿。
2. **整段语音 TTS**：使用 `voiceover.txt` 生成完整音频，再用 forced alignment / ASR 强制对齐得到实际起止时间。仅根据整体音频长短缩放所有字幕，不能保证逐句同步。

## 组合视频

PPT 每页导出 1080×1920 PNG，按最终 `timeline.json` 中的页时长安排到视频轨。将校准后的字幕与音频导入剪映/CapCut，核对数学符号、字幕安全区、语速与画面切页点。若只需草稿，可用 FFmpeg 把连续 PNG 结合音轨生成 MP4。

TTS、FFmpeg 或发布平台权限都属于外部依赖；本仓库的核心构建程序不会在没有音频的情况下冒称已完成配音或视频发布。

## 从校准后的 TTS 直接组装 MP4（可选）

```bash
python scripts/retime_tts.py --timeline build/timeline.json \\
  --cue-audio-dir audio/cues --out aligned --pause-ms 80 --assemble
python scripts/assemble_video.py --timeline aligned/timeline.json \\
  --slides-dir examples/tangent-integer-triangle/slides \\
  --audio aligned/narration.wav --output aligned/lesson.mp4
```

`assemble_video.py` 只接受已完成音频计时的时间轴；估算时间轴需要显式使用 `--allow-estimated`（仅用于草稿）。它还会检查音频总时长与时间轴误差是否超过300毫秒。SRT 不会烧录进视频，请在剪映中导入 `aligned/lesson.srt` 以便保持编辑能力。
