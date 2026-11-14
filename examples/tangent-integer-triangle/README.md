# 示例：三角形的三个内角正切均为整数

用户提供的原题是：三角形 ABC 中，三个内角 A、B、C 的正切均为整数，求 `tan A + tan B + tan C`。原题给出的答案为 **6**。

本目录不是空占位；它保存完整的可复现输入和视频制作素材：

- `lesson.json`：20 页数学讲义与逐页完整口播，每一页对应一个可编辑 PPT 页面。
- `lesson.srt`：与教案旁白对应的中文字幕，逐条包含起止时间。
- `voiceover.txt`：供语音合成直接朗读的纯净旁白。
- `timeline.json`：每页 PPT 的时间段及所对应字幕编号。
- `source_verification.md`：来源、原题推导和新增练习的界限。

在仓库根目录执行：

```bash
pip install -r requirements.txt
python scripts/build.py --input examples/tangent-integer-triangle/lesson.json \
  --out examples/tangent-integer-triangle/generated
```

生成的二进制 PPT 会写到 `generated/lesson.pptx`，不会和可版本管理的原始教案混淆。初始 SRT 时间是文本估算值，生成真实 TTS 后要重新对齐。