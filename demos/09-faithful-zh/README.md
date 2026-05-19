# Demo 9 — 忠实总结（中文正控）

此示例为合成数据，是 demo 3 的中文镜像。一个写得合格的总结应该在此 demo
上输出绝大多数 `exact` 标签和很低的 divergence。如果工具在此 demo 上输出
大量 `reversed` / `fabricated`，说明工具本身在中文语料上 mis-calibrated。

## 期望审计结果

所有论点均应判为 `exact`。期望 divergence ≤ 10%。

## 怎么跑

```bash
summary-doctor demos/09-faithful-zh/summary.txt \
  --original demos/09-faithful-zh/source.txt \
  --lang zh --mock
```
