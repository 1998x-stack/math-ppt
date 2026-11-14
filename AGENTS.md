# AGENTS.md

- 先看用户来源、再核对数学，不得把未看到的原题内容当成事实。
- 页面的所有文字和 notes 都是面向观众的成品；内部制作提示只写进 SKILL 和 references。
- 一个完整数学推导可以有 15–25 页，不能为了缩短视频时长删除关键的逻辑前提。
- notes 是旁白的单一事实来源；SRT、voiceover、timeline 必须从 notes 同步构建。
- 尚未生成 TTS 时只能声称估算字幕时间；真实音频出来后必须校准。
- 每增加一种题型，必须创建可复现的 examples/ 目录，包含题目、lesson.json、lesson.srt、voiceover.txt、timeline.json、来源说明。
- 数学结果、页面文字、字幕和生成文件必须在提交前完成测试。

- 必须验证 `slide_map.json` 的 SRT 哈希、字幕序号和完整页码覆盖。只给 SRT 无法推导 PPT 页码，禁止自动猜测。
- 视频发布前，必须按真实音频重排 SRT 并生成 `per_cue_measured_audio` 的 `slide_map.json`。除非仅生成明确标记的草稿，否则不允许跳过。
- 自动 MP4 用离线渲染；不能冒称保留动画/讲台鼠标笔迹。必须通过短视频集成测试；测试用静音只用于验证管线，不能称为真人或 TTS 配音。
