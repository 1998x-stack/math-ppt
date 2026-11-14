# SRT → TTS → PPT 画面 → MP4：技术选型与限制（2026-11）

## 最重要的原则

- SRT 只携带字幕文字与时间戳，**不携带 PPT 页码，也不携带音频**。
- `timeline.json` 是教案生成的时序源；`slide_map.json` 明确将每条字幕序号映射到 PPT 页码，同时保留完整 SRT 文本和时间戳。
- 文字估算生成的时间戳并不是 TTS 音频的真实时间。应优先逐字幕生成语音，再用 FFprobe 实测并重排 SRT 与 PPT 页时间。
- 离线渲染（LibreOffice→PDF→PNG→FFmpeg）比依赖鼠标、屏幕共享或 UI 录屏更加确定、容易测试；此方法不捕获 PPT 动画、激光笔和教师摄像头。需要这些效果时必须增加独立录屏/渲染能力。

## 剪映 / CapCut 的可验证能力

1. CapCut 官方支持在 **Desktop 和 Web** 导入 SRT（Web 主要支持 SRT，Desktop 也可使用 TXT）；移动端截至 2026 年没有直接导入外部 SRT 的能力。参考：https://www.capcut.com/help/how-to-import-subtitles
2. CapCut 有 Text-to-Speech（文字转语音）功能，通常是先建立文字层，选择该文字层并进行语音生成。参考：https://www.capcut.com/help/text-to-speech-feature
3. CapCut 的字幕导入与 TTS 功能是两个不同操作；不能未经实测承诺“导入一份 SRT 就能通过公开 API 一键生成完整对应语音”。参考：https://www.capcut.com/create/ai-video-generator/capcut-ai-video-captions-voiceover-guide
4. 未查到能直接把本仓库 SRT/PPT 文件无交互提交到剪映内部项目并导出 MP4 的公共、稳定官方 REST API 文档。火山引擎提供商业视频剪辑 Web SDK，但不等于剪映桌面端 API；按其 SDK 文档，需要接入工程与相应服务。参考：https://docs.volcengine.com/docs/video-on-demand/integrate-ai-mediakit-video-edit-web-sdk?lang=zh

## 可编程配音方案

| 方案 | 自动化形式 | 适用场景 | 注意事项 |
|---|---|---|---|
| **火山引擎豆包 TTS 2.0** | 官方 HTTP/WebSocket API | 中文课程规模化、商用集成优先评估 | 需要 API Key、模型开通和费用预算；依据当前 API 文档接入 |
| **Azure Speech** | 官方 Speech SDK | 需要稳定的文本边界/音频边界及多音色 | 需要云资源与密钥；注意配音成本 |
| **edge-tts** | 社区 Python 库调用 Edge 在线配音 | 本地原型、快速验证 | 非正式商业服务 API，可能受网络/限流/策略变更影响 |
| **Piper TTS** | 离线模型 | CPU/本地/隐私或无网络 | 中文可用音色较少，语音自然度与数理公式发音需实测 |

参考：
- 豆包 TTS 2.0：https://console.volcengine.com/ark/region%3Acn-beijing/docs/agent-plan-personal-voice-model
- Azure WordBoundary：https://learn.microsoft.com/azure/ai-services/speech-service/how-to-speech-synthesis
- edge-tts：https://github.com/rany2/edge-tts
- Piper 中文音色：https://github.com/rhasspy/piper/blob/master/VOICES.md

## 数学朗读质量门槛

不要直接把复杂的屏幕公式送给 TTS 朗读。`lesson.json` 的 `notes` 应是能自然念出的中文，例如：

- PPT 显示：`tan(B+C) = (tan B+tan C)/(1−tan B·tan C)`
- 配音文本：`B 加 C 的正切，等于 B 的正切加 C 的正切，除以一减去两者正切的乘积。`

当显示公式与旁白不完全相同时，**旁白与 SRT 必须一致**，同时 `slide_map.json` 仍依赖原始 `timeline.json` 显示页面。

## 完整执行示例

```bash
# 1) 初始教案生成（默认估算时码）
python scripts/build.py --input examples/tangent-integer-triangle/lesson.json --out build/lesson
python scripts/qa.py --input examples/tangent-integer-triangle/lesson.json --out build/lesson

# 2) 仅预览 TTS 任务，不需要联网
python scripts/srt_to_tts.py \
  --srt build/lesson/lesson.srt --slide-map build/lesson/slide_map.json \
  --out build/tts --dry-run

# 3) 可选社区 TTS 方案（真实生成每条配音，需要联网）
python -m pip install edge-tts
python scripts/srt_to_tts.py \
  --srt build/lesson/lesson.srt --slide-map build/lesson/slide_map.json \
  --out build/tts --voice zh-CN-YunxiNeural

# 4) 音频测时，生成已校准的 WAV、字幕和 slide_map.json
python scripts/retime_tts.py --timeline build/lesson/timeline.json \
  --cue-audio-dir build/tts --out build/aligned --assemble

# 5) PPTX、真实 WAV、实际 SRT、实际页码映射一键生成成品 MP4
python scripts/render_course_video.py \
  --pptx build/lesson/lesson.pptx \
  --srt build/aligned/lesson.srt --audio build/aligned/narration.wav \
  --slide-map build/aligned/slide_map.json \
  --out build/final.mp4
```

生成的 `final.mp4` **默认烧录字幕**，同时保存 `final.srt`，可以在剪映中重做字体/校对字幕；如果希望剪映中的字幕保持可编辑，额外传入 `--no-burn-subtitles` 导出纯画面+音频 MP4。

由于配音速度取决于语音模型和朗读内容，初始 `lesson.srt` 的约 5 分钟估算仅用于排版，不作为最终视频时码。
