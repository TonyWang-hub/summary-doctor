# summary-doctor

> **你看到的 AI 总结可能在撒谎。这个工具能抓出"反转 / 编造 / 选择性引用"——给出引证，不下判决。**

[English](README.md) | 简体中文

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)](docs/ROADMAP.md)
[![PRs: welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#贡献)

<p align="center">
  <img src="docs/demo.gif" alt="summary-doctor 跑完 9 个 demo（mock 模式）——正控停在 0% 偏差，反转 / 编造 demo 全部出警告标签" width="820">
</p>

公开演讲、访谈、文章的 LLM 自动总结正在社交平台上海量传播。在 LLM 忠实度（faithfulness）的相关研究和大量轶事样本里，**有相当一部分的"AI 总结"与原文存在偏差**——有时甚至直接反转演讲者的观点。

目前还没有开源工具能把一篇总结里的每一条论点逐一映射回原文段落，并按"忠实度类别"打标签。**这个项目就是来做这件事的。**

```
┌──────────────────────────────────────────────────────────────┐
│   AI 总结                       原文                          │
│      │                          │                            │
│      └────────┬─────────────────┘                            │
│               ▼                                              │
│      summary-doctor  →  每条论点的标签 + 引用段              │
│                                                              │
│  exact · softened · reversed · fabricated                    │
│  精确匹配 · 弱化 · 反转 · 编造                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 为什么是"引证，不是判决"

我们**不**判断一篇总结是"真"还是"假"。工具的输出是一张映射表：每条论点配一段从原文摘出来的引用 + 一个 4 类标签 + 一个置信度。**最终判断交给读者。**

这样设计的原因：

1. "LLM 审计 LLM" 存在同源偏见。给出**引证**而不是**判决**，绕开了"谁审计审计员"的问题。
2. `fabricated`（编造）标签可能误报——如果原文获取不完整（付费墙、OCR 失败、长文截断），工具会找不到匹配段。此时读者看到"未找到匹配"也能自己判断。

完整设计取舍见 [`docs/SPEC.md`](docs/SPEC.md)。

---

## 安装

```bash
pip install -e .                  # 核心
pip install -e '.[anthropic]'     # 含 Anthropic SDK
```

需要 Python 3.10+。

### 复用 Claude Code 订阅（不需要 API key）

如果你已经订阅 Claude Code，可以直接复用订阅的鉴权和额度，无需单独申请
Anthropic API key。先确认 `claude --version` 在终端能跑通，然后：

```bash
summary-doctor demos/02-softening-zh/summary.txt \
  --original demos/02-softening-zh/source.txt \
  --lang zh \
  --backend claude-cli \
  --model haiku
```

底层走 `claude -p` 命令行调用。每次审计的边际成本归到你订阅的常规用量里，
不会单独走 API 计费。难判断的 reversed / softened 边界场景可以换
`--model opus` 提精度。

---

## 30 秒上手

```bash
# 1. 用自带 demo 跑通流程（不需要 API key）
summary-doctor demos/02-softening-zh/summary.txt \
  --original demos/02-softening-zh/source.txt \
  --lang zh --mock

# 2. 接 Anthropic Claude 做真审计
export ANTHROPIC_API_KEY=sk-ant-...
summary-doctor demos/02-softening-zh/summary.txt \
  --original demos/02-softening-zh/source.txt \
  --lang zh
```

输出：

```
[ok] report: summary-audit-20260518-211103.md
[ok] json:   summary-audit-20260518-211103.md.json
[summary] 3 claims · divergence 50% · reversed 1 · fabricated 0
```

Markdown 报告对每条论点都会给出：

```markdown
### Claim 3 — `reversed` (confidence 75)

**Summary claim:**
> 工具采纳率是衡量教育 AI 改造成功与否的关键指标。

**Matched source paragraph:**
> 最后她强调："工具采纳率不是结果，学生学习成效才是结果。
> 70% 的 AI 教育改造项目失败在错把过程指标当结果指标。"

**Rationale:** Polarity mismatch with strong keyword overlap (5/6).
```

---

## 4 类标签

| 标签 | 定义 |
|------|------|
| `exact` 精确 | 总结的论点在原文里基本是逐字支持的 |
| `softened` 弱化 | 总结保留了方向但丢了限定词或强度 |
| **`reversed` 反转** | 总结颠倒或矛盾于原文的立场 |
| **`fabricated` 编造** | 总结里的论点在原文里完全没有支撑 |

`reversed` 和 `fabricated` 是真正需要警觉的两类标签。

---

## 它不是什么

- 它**不是**真假判断器。它是**引证映射器**。
- 它**不是**实时信息流审计工具。
- 它**不是**作者 / 出版方信誉评分系统——那是另一个问题。

`--mock` backend 是一个启发式的"流程跑通器"，**不是**精度校准过的检测器。真审计请用 Anthropic backend。详见 [`docs/MOCK-LIMITS.md`](docs/MOCK-LIMITS.md)。

---

## Mock vs Anthropic — 怎么选？

| 使用场景 | Backend | 理由 |
|---|---|---|
| CI 冒烟测试 | `mock` | 无需 API key，结果稳定 |
| 个人快速检查 | `mock` | 离线、免费 |
| 发布前对比总结 | `anthropic` Haiku 4.5 | 廉价的校准检测 |
| 反转 / 弱化的边界判断 | `anthropic` Opus 4.7 | 精度最高 |
| 多语言原文 | `anthropic`（任一） | mock 没有跨语言对齐 |

两种 backend 在自带 demo 上的精度对比见 [`docs/EVALUATION.md`](docs/EVALUATION.md)；Anthropic 模式的 prompt 设计见 [`docs/PROMPT-ENGINEERING.md`](docs/PROMPT-ENGINEERING.md)。

**Prompt 缓存 (v0.2.2)**：`anthropic` backend 自动缓存 prompt 前缀（默认 `--cache-ttl 5m`，nightly/CI 用 `1h`），所以同一 source 第二次 audit 大幅省 token。`--no-cache` 可关。`claude-cli` backend **不**会跨 invocation 缓存用户 prompt 内容——详见 [`docs/EVALUATION.md`](docs/EVALUATION.md#cache-performance-v022) 实证。

---

## 工作原理（5 阶段流水线）

```
[1 输入]  →  [2 抽取正文]  →  [3 拆论点]  →  [4 映射+分类]  →  [5 生成报告]
   ↓             ↓                ↓              ↓                  ↓
 url/file     纯文本           论点列表       带标签的对    Markdown + JSON
```

阶段 3、4 会调 LLM（默认 Anthropic Claude）；阶段 1、2、5 是确定性的。完整状态机、失败路径、不做的功能见 [`docs/SPEC.md`](docs/SPEC.md)。

---

## 自带 demo

14 个示例在 [`demos/`](demos/)。所有 demo 均为**合成数据**——如有雷同纯属巧合。

| Demo | 语言 | 设计意图 |
|------|------|---------|
| `01-reversal-en` | English | 反转论点 + 编造论点（GPU supply 烟雾弹）|
| `02-softening-zh` | 中文 | 弱化限定词 + 一条反转 |
| `03-faithful-en` | English | 正控——应该绝大多数是 `exact` |
| `04-cherry-picking-en` | English | 选择性引用——丢限定词导致弱化 |
| `05-causal-inversion-zh` | 中文 | 因果倒置（X→Y 说成 Y→X）|
| `06-scope-creep-en` | English | 范围扩大——窄结论说成普遍规律 |
| `07-temporal-error-en` | English | 年份 / 日期被编造 |
| `08-fabricated-stats-zh` | 中文 | 数字统计凭空捏造 |
| `09-faithful-zh` | 中文 | 中文正控——demo 3 的镜像 |
| `10-quote-out-of-context-en` | English | 整句被原样引用，但紧随其后的限定条件被删除，结论被反转 |
| `11-number-exaggeration-zh` | 中文 | 单一数字被夸大 10×（"8%" → "80%"），下游推论链次生反转 |
| `12-cross-language-en-zh` | EN → 中文 | 跨语言边界用例（v0.2 前瞻；mock backend 会显著漏报）|
| `13-academic-peer-review-en` | English | 行业场景：学术 peer review 总结——方向反转 + 编造引用 + 范围扩大（丢"仅 early-career"限定）|
| `14-legal-mata-style-en` | English | 行业场景：法院 sanctions order 总结——编造判例引用 + 处置反转（原文 "sanctioned" 被总结成 "exonerated"）|

---

## MCP server

`summary-doctor` 自带一个 MCP（Model Context Protocol）server，任何
MCP 客户端（Claude Desktop、Cursor、Cline、Zed、Continue.dev、ChatGPT
Desktop、Codex CLI 等）都能把它作为工具直接调用。Server 是 5 阶段流水线
的薄封装——零行为分叉。

```bash
pip install -e '.[mcp,anthropic]'
summary-doctor-mcp        # 启动 FastMCP（stdio，客户端会自动连）
```

暴露三个 tool：

| Tool | 用途 |
|---|---|
| `audit_summary` | 跑完整审计流水线，返回 Markdown 报告 |
| `get_demo` | 返回自带 demo 的 summary + source + 期望标签，不烧 token |
| `list_labels` | 返回 4 类标签的定义、适用场景、对应行动建议 |

### Claude Desktop 配置

`~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "summary-doctor": {
      "command": "summary-doctor-mcp",
      "env": { "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}" }
    }
  }
}
```

Cursor（`~/.cursor/mcp.json`）用同样的 `mcpServers` 结构。**Zed** 用的是
`context_servers`（不是 `mcpServers`）；**Continue.dev** 是数组、每条要带
`name` 字段；**Cline** 有自己独立的 settings JSON。可直接复制粘贴的 config
片段见 [`docs/launch/research/D-ecosystem-integration.md`](docs/launch/research/D-ecosystem-integration.md)
§1.6。

---

## Claude Code Skill

[`skills/summary-doctor/SKILL.md`](skills/summary-doctor/SKILL.md) 教
Claude Code（或任何支持
[SKILL.md](https://code.claude.com/docs/en/skills) 的 agent）**何时**应该
触发 summary-doctor CLI / MCP 工具。安装：

```bash
mkdir -p ~/.claude/skills
cp -r skills/summary-doctor ~/.claude/skills/
```

也可以放到单个项目的 `.claude/skills/` 下做项目级 scope。具体步骤和
`allowed-tools` 在非 Claude 客户端（Cursor / Codex CLI / Gemini CLI 等）
被静默忽略的注意事项见
[`skills/summary-doctor/README.md`](skills/summary-doctor/README.md)。

---

## 路线图

- v0.1（本版本）：CLI、5 阶段流水线、Claude backend、3 个 demo。
- v0.2：中英跨语言对齐、长文分片、音视频 ASR、MCP server、Claude Code Skill。
- v0.3：浏览器扩展、批量审计。

详见 [`docs/ROADMAP.md`](docs/ROADMAP.md)。

---

## 使用场景 & 合规对照

- [使用场景](docs/USE-CASES.md)：学术同行评议 / 法律案例摘要 / AI 新闻总结
- [合规对照](docs/COMPLIANCE.md)：EU AI Act、NIST AI RMF、SEC、中国《生成式人工智能服务管理暂行办法》

---

## 自审计（已上线）

为了让这个项目对自己也诚实，`summary-doctor` 可以指向仓库自己的
README。提供三个 target，按成本 / 精度递增：

```bash
make self-audit-mock   # 启发式 mock backend，CI 友好，无需鉴权
make self-audit        # claude-cli + haiku，复用 Claude Code 订阅鉴权
make self-audit-opus   # claude-cli + opus，慢但 reversed / softened 边界更准
```

自审计是 dogfood 冒烟测试，不是精度校准过的 benchmark——具体数字
怎么读、不能读出什么，详见 [`docs/SELF-AUDIT.md`](docs/SELF-AUDIT.md)；
mock backend 的已知局限见 [`docs/MOCK-LIMITS.md`](docs/MOCK-LIMITS.md)。

---

## 贡献

现阶段最有价值的 PR：

1. **其他语言**的公开 demo 案例（低资源语言尤其欢迎）。
2. Anthropic backend **误判反例**——它把 `reversed` 打给了一条原文实际支持的论点。这类样本能用来校准 prompt。
3. v0.3 浏览器扩展原型。

除 typo 或新 demo 之外的改动请先开 issue 讨论。

---

## License

[MIT](LICENSE)
