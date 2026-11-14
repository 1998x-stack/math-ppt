# 示例：三角形三个内角的正切均为整数

原题：在三角形 ABC 中，tan A、tan B、tan C 都是整数，求三者之和。答案为 **6**。本例包含完整的推导与一道**明确注明属于教学拓展**的迁移题（1、2、4 能否成为三个正切值）。

## 目录与交付

| 文件 | 用途 |
|---|---|
| [lesson.json](lesson.json) | 20 页结构化数学教案，含每页要显示的内容和可直接朗读的教师旁白 |
| [lesson.pptx](lesson.pptx) | 20 页 9:16 可编辑 PowerPoint（由 CI 生成并提交） |
| [lesson.pdf](lesson.pdf) | 手机端预览版（由 CI 生成） |
| [slides/](slides/) | 20 张高清竖屏 PNG，供剪映导入（由 CI 生成） |
| [lesson.srt](lesson.srt) | 对应字幕；**此处是估算时间，不是已对齐真实音频** |
| [voiceover.txt](voiceover.txt) | 用于 TTS 的完整纯净朗读文本 |
| [timeline.json](timeline.json) | 每页起止时间、字幕关联、对齐状态 |
| [source_verification.md](source_verification.md) | 题源、推导审查与新增内容边界 |

## 从教案复现

```bash
pip install -r requirements.txt
python scripts/build.py --input examples/tangent-integer-triangle/lesson.json --out build
python scripts/qa.py --input examples/tangent-integer-triangle/lesson.json --out build
```

上传真实配音后，建议按 SRT cue 顺序切分音频，调用 `python scripts/retime_tts.py --timeline build/timeline.json --cue-audio-dir audio/cues --out aligned --assemble`，使用 `aligned/lesson.srt`、`aligned/timeline.json` 和 `aligned/narration.wav` 合成视频；请勿将估算时间轴当作已经精确配音的结果。

CI 的 `publish-example` 在主分支测试成功后提交 PPT/PDF/PNG 和对应文本，保留原始 `lesson.json` 作为唯一编辑源。


## 字幕到 PPT 的可审计映射

- [slide_map.json](slide_map.json)：20 页与 120 条 SRT 的精确映射，包含 `cue_to_page`、每页字幕列表和 SRT 哈希；
- [tts_jobs.example.json](tts_jobs.example.json)：按字幕切分的语音任务清单；**此 JSON 不包含已生成音频**；
- [VIDEO_WORKFLOW.md](VIDEO_WORKFLOW.md)：从 PPT + SRT + 音频到 MP4 的实际命令与边界；
- 保持 [lesson.srt](lesson.srt) 和 [timeline.json](timeline.json) 的估算时码身份。真实配音产生后请另存 `aligned/`，不要覆盖原始历史。
