---
name: math-ppt
description: >
  Convert math problems/images and source solutions into rigorous, editable
  Chinese teaching PPTX, clean narration text, SRT captions and a time-aligned
  slide plan for video production.
---

# Math PPT Skill · 数学短视频课程生成

## 目标

接受用户的题目图片、文字或 PDF，首先核对来源与完整数学证明，再生成可编辑 PPT、纯净旁白、SRT 与逐页时间轴。输出面向学生/家长的真实数学讲解，不要把分镜制作备注显示给观众。

## 标准作业流程

1. **审题与提取**：逐项提取原题条件、求值对象、原解析、原答案；图像不清楚时标记歧义。把来源事实与教学新增内容分开写入 `source_verification.md`。
2. **严格核算**：验证定义域、符号、单调性区间、除零风险、边界条件与整数解唯一性。不要照抄有漏洞的解答。
3. **详细教学设计**：按“明确条件 → 关键观察 → 为什么成立 → 代数推导 → 结论 → 常见错误 → 迁移练习”拆页；一页只讲一个核心推理。讲具体题时必须解释关键理由，不能为了时长省略必要步骤。
4. **成品纯净规则**：所有可能出现在页面或音频的字段（`title`、`kicker`、`lines`、`formula`、`highlight`、`notes` 等）都只能放学生真正要看到/听到的内容。禁止出现“开头 3 秒”“9:16 竖屏教学”“原题重排”“新增推导”“抓住数学矛盾”“口播脚本”等制作术语。页脚同样检查。
5. **编写 `lesson.json`**：`notes` 必须是教师可以直接朗读的完整中文话语，不要含时码、镜头指令或“第几秒切页”。每页有独立 `title` 和 `notes`，最后给出核对无误的结果。
6. **构建**：运行 `python scripts/build.py --input LESSON.json --out OUTPUT_DIR`。输出 `lesson.pptx`、`lesson.srt`、`voiceover.txt`、`timeline.json`。
7. **四重校验**：检查数学逻辑；检查 PPT 手机端可读性与文字无越界；检查成品没有泄漏制作术语；检查每条字幕文本和旁白完全一致、时间不倒退、页面时间段连续。
8. **实际配音后重新对齐**：初始 `timeline.json` 的 `alignment` 为 `estimated_from_text_not_audio`。如果后续配音由逐条字幕转成语音，采用每段实际时长重新计算 SRT；如果是整段配音，使用 forced alignment。不得把估算时间称为精准同步。
9. **交付示例**：每一种题型在 `examples/<slug>/` 留下完整数据、SRT、时间轴、来源与质量记录，并提供可复现的运行指令。

## 数学示例关键事实

用户提供的题：若三角形三个内角正切值都是整数，求 `tan A + tan B + tan C`。

可设 `A≤B≤C`，`0<A≤60°`，于是 `0<tan A≤√3<2`，整数性得到 `tan A=1`，即 `A=45°`。又 `B+C=135°`，并由角度和定义域推出 `B,C` 都是锐角。记 `b=tan B,c=tan C`，则 `(b+c)/(1-bc)=-1`，所以 `(b-1)(c-1)=2`，结合 `b≤c` 得到 `b=2,c=3`，总和为 **6**。

迁移练习：`1,2,4` 不满足 `tan A+tan B+tan C=tan A tan B tan C`，因此不能作为同一个三角形三个内角的正切值。此练习是新增内容，不冒充原题。

## 命令

```bash
python -m pip install -r requirements.txt
python scripts/build.py --input examples/tangent-integer-triangle/lesson.json \
  --out examples/tangent-integer-triangle/generated
```

参见 [完整示例](examples/tangent-integer-triangle/lesson.json)、[TTS/SRT 工作流](references/audio-video-pipeline.md)。

## 示例仓库与视频交付 QA

每个 `examples/<slug>/` 应提供经 CI 生成并归档的 PPTX、PDF、逐页 PNG、原始 lesson JSON、SRT、voiceover、timeline 与来源核查文档；不可只保留一次性 Actions 构建附件。数学审核不能仅靠 Python 语法和数字枚举。任何受众可见字段（包括页面系列页脚）都不得出现“开头3秒”“9:16竖屏教学”等内部制作说明。PPT 画面字段不得被裁掉：超过可视文本容量时必须构建失败并要求分拆页面。

正式配音完成后，运行 `scripts/retime_tts.py` 测量逐cue音频并拼接 WAV，再用 `scripts/assemble_video.py` 进行音频时长一致性验证和 MP4 组装；单独保留 aligned SRT 供剪映导入，**禁止把估算时间轴当作已精确同步**。


## 字幕、页码、真实音频和 MP4 生成（必备交付）

- 每份 `lesson.json` 构建时，必须输出 `slide_map.json`，其中 `cue_to_page` 明确记录每条字幕在第几页，`pages[].captions` 包含字幕文字及起止时间。不得尝试仅根据 SRT 猜测 PPT 页码；SRT 没有页码字段。
- 生成器基于同一份 `notes` 输出 `lesson.pptx`、`lesson.srt`、`voiceover.txt`、`timeline.json`、`slide_map.json`。页码映射附有 SRT SHA-256，以阻止字幕变化后误用旧映射。
- 如果真实音频尚不存在，`slide_map.json.alignment=estimated_from_text_not_audio`，不能声称已得到可发布音视频。自动合成时必须拒绝此状态，只有 `--allow-estimated` 可显式生成不保证同步的草稿。
- 如果使用按字幕编号生成的真实 TTS 音频，先 `scripts/retime_tts.py --assemble`，得到 WAV、重排后的 SRT、timeline 及 slide map。再执行 `scripts/render_course_video.py --pptx ... --audio ... --srt ... --slide-map ... --out ...`。
- 合成器采用 LibreOffice→PDF→PNG→FFmpeg 的**离线逐页渲染**替代易受桌面尺寸和弹窗影响的 GUI 录屏，生成带语音与烧录字幕的 MP4 和可编辑的 sidecar SRT。它不捕获真实的 PowerPoint 动画、激光笔或教师摄像头。
- 需要通过 `scripts/qa.py`、视频集成测试及至少一次手机端预览；重要数学符号及正式旁白不得混入制作指令。

## SRT→TTS 的可选接口

`scripts/srt_to_tts.py` 提供 `edge-tts` 社区服务原型：先用 `--dry-run` 导出 `tts_jobs.json`，再安装可选依赖 `edge-tts` 生成 `001.mp3` 等逐 cue 配音。该服务不是剪映官方商业 API，不应作为无人值守生产 SLA 的唯一依赖。商用批量生产优先评估火山引擎豆包语音 TTS 2.0 或 Azure Speech 官方接口。需要朗读的公式，应先将 `notes` 写成自然中文，再由 SRT 提供相同的语音文本。详细研究见 `references/srt-tts-capcut-research.md`。
