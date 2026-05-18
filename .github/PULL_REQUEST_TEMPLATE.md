<!--
Thanks for sending a PR! Please fill in all three checklists below.
PRs that skip the redaction checklist will not be merged.
-->

## Summary

<!-- One or two sentences. What does this PR change and why? -->

## Type of change

- [ ] Bug fix
- [ ] New feature / new backend / new audit rule
- [ ] New demo case (regression fixture under `demos/`)
- [ ] Docs only
- [ ] Refactor / cleanup (no behavior change)

## Linked issues

<!-- e.g. Closes #12, Refs #34 -->

---

## Checklist — Tests

- [ ] `make test` passes locally.
- [ ] For bug fixes: a regression test is added that fails on `main` and passes on this branch.
- [ ] For new demos: the demo runs under the mock backend and the assertions in `tests/` are updated if needed.
- [ ] For new features: at least one unit test or demo case exercises the new code path.

## Checklist — Redaction & licensing

- [ ] No private, personal, or proprietary content is included in any added file (summary text, source text, logs, issue links, commit messages, screenshots).
- [ ] Any added demo texts are either authored by me, synthetic, or shared with permission under the project license (MIT).
- [ ] No real names, real customer data, internal URLs, API keys, or internal project codenames appear anywhere in the diff.

## Checklist — Documentation

- [ ] If a user-facing CLI flag or output format changed: README.md (and README.zh-CN.md if applicable) is updated.
- [ ] If a new backend was added: `docs/` has at least a short usage note.
- [ ] If behavior changed in a way users would notice: a CHANGELOG entry (or release notes draft) is added.
