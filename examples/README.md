# examples：数学短视频课件完整示例库

本目录**不只包含教案 JSON**。每个示例应保留来源说明、逐页可编辑课件、SRT、配音稿、时间轴、PDF和逐页渲染 PNG，让任何人都能复现和用于后续 TTS/剪映合成。

| 示例 | 核心知识 | 已发布材料 |
|---|---|---|
| [tangent-integer-triangle](tangent-integer-triangle/) | 三角形内角和、正切单调性、和角公式与整数因式分解 | 20页PPTX、PDF、20张PNG、SRT、旁白、timeline、source验证 |

## 新增示例目录规范

```text
examples/<problem-slug>/
├── README.md                 # 原题、教学对象、复现方式
├── lesson.json               # 编辑源：PPT画面与逐页notes
├── source_verification.md    # 题源及数学复核与教学新增内容
├── lesson.pptx               # 由CI生成并提交
├── lesson.pdf                # CI生成的预览
├── slides/slide-01.png ...   # 与timeline的image字段一致
├── lesson.srt                # 默认估算时码，不冒称已对齐音频
├── voiceover.txt             # 纯净配音稿
└── timeline.json             # 每页与cue映射
```

提交新题时先完成数学验证和 `lesson.json`，检查制作术语没有进入课件/音频；CI 构建、严查并提交可以直接观看的示例产物。需保持估算 SRT 与真实配音校准后的 SRT 区分，音画同步的版本应放到单独的导出目录，避免覆盖原始教案产物。
