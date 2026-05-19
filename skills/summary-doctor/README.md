# summary-doctor — Claude Code Skill

This folder ships a single `SKILL.md` that teaches Claude Code **when**
to call the `summary-doctor` CLI (or the `audit_summary` MCP tool) on
a faithfulness question.

## Install

### Per-project (recommended)

Drop the folder into your project's `.claude/skills/`:

```bash
mkdir -p .claude/skills
cp -r path/to/summary-doctor/skills/summary-doctor .claude/skills/
```

Claude Code will auto-discover skills under `.claude/skills/<name>/SKILL.md`
on the next session start.

### Per-user (all projects)

```bash
mkdir -p ~/.claude/skills
cp -r path/to/summary-doctor/skills/summary-doctor ~/.claude/skills/
```

### Verify

```bash
claude --skill summary-doctor "audit this summary against the source"
```

If Claude does not pick the skill up, increase the description specificity
or re-check that the file lives at `<root>/summary-doctor/SKILL.md` exactly.

## Prerequisites

The skill assumes the `summary-doctor` CLI is on your `PATH`:

```bash
pip install -e .
# or, once published:
pip install summary-doctor
```

For LLM calls, either:

- Export `ANTHROPIC_API_KEY=...` (Anthropic backend), or
- Have the `claude` CLI authenticated (the skill defaults to
  `--backend claude-cli --model haiku` to reuse the subscription).

## Caveat

`allowed-tools` is enforced by Claude Code and OpenClaw, **silently
ignored** by Agent SDK, Cursor, Codex CLI, Gemini CLI, and Copilot. When
loading this skill from those clients, replicate the restrictions in
the client's own permission system.
