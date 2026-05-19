# M4 — Skill manual dogfood · runbook for the maintainer

> The AI agent that ran M0–M3 cannot drive a Claude Code session. This
> milestone needs **you** (the human maintainer) to do five things and
> paste the result back so we can close the gate.
>
> Estimated time: **5 minutes**.

## Why this step exists

`skills/summary-doctor/SKILL.md` was written and tested for structural
correctness in M1 (12/12 pytest passed). What we still do not know:

1. Does Claude Code actually load the manifest from `~/.claude/skills/`
   or a project-local `.claude/skills/`?
2. Are the **trigger keywords** in the manifest's `description` strong
   enough that Claude Code surfaces the Skill on an in-domain prompt?
3. When the Skill is loaded, does Claude propose calling
   `summary-doctor` with sensible arguments?

These three questions can only be answered by a live Claude Code
session.

## The 5 steps

### Step 1 — install the Skill locally

Pick **one** of these (either works):

**Option A — global (all your Claude Code sessions see it)**:

```bash
mkdir -p ~/.claude/skills
cp -r /Users/tony/Documents/work/ai/cloud_gh_project/summary-doctor/skills/summary-doctor ~/.claude/skills/
```

**Option B — project-local (only inside `summary-doctor/`)**:

```bash
cd /Users/tony/Documents/work/ai/cloud_gh_project/summary-doctor
mkdir -p .claude/skills
ln -s "$PWD/skills/summary-doctor" .claude/skills/summary-doctor
```

Verify:

```bash
ls -la ~/.claude/skills/summary-doctor/SKILL.md       # for option A
# or
ls -la .claude/skills/summary-doctor/SKILL.md         # for option B
```

The file should resolve. If it does not, the Skill cannot be discovered.

### Step 2 — start a fresh Claude Code session

Open a new Claude Code window/tab. **Do not** reuse a long-running one
— Skill discovery happens at session start.

### Step 3 — send the trigger prompt

Paste exactly this into Claude Code:

> I have an AI-generated summary of a talk and the original transcript.
> Can you audit whether the summary is faithful to the source?
>
> Summary: "The speaker argued that AI agents do not increase
> communication overhead, and that this fact essentially overturns
> Brooks' law."
>
> Source: "Every additional agent in the loop is one more participant
> whose intent and state must be kept in sync with humans and with other
> agents. The number of communication channels therefore continues to
> grow, and in some configurations the overhead is greater than a
> pure-human team."

### Step 4 — observe what Claude does

Three possible outcomes:

| Outcome | What it means | Score |
|---|---|---|
| **A** — Claude mentions or invokes `summary-doctor` (CLI or MCP) and proposes an audit | Skill discovery + trigger keywords both work. ✅ | M4 PASS |
| **B** — Claude does the audit *manually* but does not mention the Skill | Skill is installed but trigger keywords are too weak. ⚠️ partial — file v0.2.2 issue to tune triggers | M4 PASS-with-finding |
| **C** — Claude does not perform the audit at all | Skill not loaded OR prompt was off-axis. Re-check install path; if path is correct → trigger keywords need a rewrite | M4 FAIL — file v0.2.2 issue |

### Step 5 — paste the result back

Replace the placeholder below with the actual session transcript (you
can truncate, but keep enough that the outcome is verifiable) and save
the file as:

`spec-kit/v0.2.1-dogfood/artifacts/skill-session.md`

Template:

```markdown
# M4 — Skill session transcript

Date (UTC): <fill in>
Claude Code version: <`claude --version`>
Install path used: ~/.claude/skills/summary-doctor (option A)  -or-
                    <repo>/.claude/skills/summary-doctor (option B)
Outcome: A / B / C  (from the table above)

## Transcript

User:
> ...trigger prompt from Step 3...

Claude (paraphrased OK):
> ...what Claude actually did...

## Notes

- ...anything that surprised you
```

## What I (the AI agent) will do after you paste

1. Read `artifacts/skill-session.md` and write `M4-assessment.md` —
   does the transcript meet the gate criteria?
2. If outcome was A or B, mark M4 ✅ and move to M5.
3. If outcome was C, open a GitHub issue `v0.2.2: tune Skill trigger
   keywords` with the failing transcript attached, then still mark
   M4 ✅ (because the gate is *evidence captured*, not *Skill
   triggered* — Constitution §1).

## If you cannot run this step right now

That is also fine. Per the plan:

> If the human Skill dogfood is impossible / not run, M4 downgrades to
> "Skill manifest validated by structural lint only" and the gap is
> documented honestly in `CHANGELOG.md`. (Spec §4 failure-path row.)

In that case, paste a one-line acknowledgement into
`artifacts/skill-session.md`:

```
M4 SKIPPED — human did not run the dogfood. Structural lint passed in M1
(12/12 pytest tests including build_server_constructs_when_mcp_present
and tools_registered_with_expected_names).
```

…and we move directly to M5 with that line documented in the CHANGELOG.
