# 本示例的 PPT ↔ 字幕 ↔ 音频 ↔ 视频对应关系

本示例有 **20 页 PPT、120 条 SRT 字幕**。`slide_map.json` 提供可由机器直接使用的 `cue_to_page` 和每页完整 `captions`。这是由 `timeline.json` 和 `lesson.srt` **一起验证后生成**的，因为单独的 SRT 不具备页码字段。

## 文件角色

- `lesson.pptx`：展示给学生的 20 页课件；可编辑 PPT。
- `lesson.srt`：当前为文本估算时间，**尚未按真实音频重计时**。
- `timeline.json`：页面区间、字幕索引和估算时间源。
- `slide_map.json`：独立、可审计、附字幕 SHA-256 的页码映射。
- `tts_jobs.example.json`：120 条逐条 TTS 任务清单，包含所属页码与文本，但**不包含音频**。

## 从现有示例开始

```bash
python scripts/srt_to_tts.py \
  --srt examples/tangent-integer-triangle/lesson.srt \
  --slide-map examples/tangent-integer-triangle/slide_map.json \
  --out work/tts --dry-run

# 生成真实语音后
python scripts/retime_tts.py \
  --timeline examples/tangent-integer-triangle/timeline.json \
  --cue-audio-dir work/tts --out work/aligned --assemble

python scripts/render_course_video.py \
  --pptx examples/tangent-integer-triangle/lesson.pptx \
  --srt work/aligned/lesson.srt --audio work/aligned/narration.wav \
  --slide-map work/aligned/slide_map.json --out work/course.mp4
```

注意：在没有真实 TTS 文件时，本仓库只保存可复现课程素材，不伪造真实配音或声称完成最终音频视频。工程自动合成采用 **PPTX 离线渲染** 而非 GUI 逐页录屏，能保留准确页面切换，但无法复现幻灯片对象级动画。需要讲解动画时应分拆更多 PPT 页面或使用额外动画渲染器。
