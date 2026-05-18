# Demo 2 — Softening + reversal（中文）

此示例为合成数据。如有雷同纯属巧合。

## 期望审计结果

| 总结中的论点 | 期望标签 | 原因 |
|---|---|---|
| "AI 助教能提升中小学课堂效率" | **softened** | 原文有"前提是任课教师对学科知识有深入了解"等多重限定，总结全部丢失 |
| "建议先小范围试点，再横向推广" | exact | 原文一致 |
| "工具采纳率是衡量教育 AI 改造成功与否的关键指标" | **reversed** | 原文实际是"工具采纳率不是结果，学生学习成效才是结果"——总结直接反转 |

## 怎么跑

```bash
summary-doctor demos/02-softening-zh/summary.txt \
  --original demos/02-softening-zh/source.txt \
  --lang zh --mock
```
