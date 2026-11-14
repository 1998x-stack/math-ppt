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