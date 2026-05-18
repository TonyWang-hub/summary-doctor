# Contributing to summary-doctor

Thanks for your interest in improving the project. The most valuable contributions are **new demo cases** — real or synthetic (summary, source) pairs that the current backend gets wrong. Each accepted case becomes a regression fixture.

## Quick start

```bash
git clone https://github.com/TonyWang-hub/summary-doctor.git
cd summary-doctor
make install-dev
make test
```

All tests must pass under the mock backend before you open a PR.

## Pull request flow

1. **Open an issue first** if your change is non-trivial (new backend, new label, breaking CLI change). For small fixes you can go straight to a PR.
2. Fork the repo, create a topic branch off `main`, and keep the PR focused — one logical change per PR.
3. Run `make test` locally. Add tests for any new code path.
4. Fill in **all three checklists** in the PR template: tests, redaction, docs. PRs with the redaction checklist unchecked will not be merged.
5. The project will respond on the PR; expect a round of review before merge.

## Submitting a new demo case

Demo cases live under `demos/<NN>-<short-slug>/` and contain three files: `summary.txt`, `source.txt`, and a short `README.md` that states the expected label and a one-line rationale.

Rules for a demo PR:

- Texts must be either authored by you, fully synthetic, or shared under the project license (MIT). No scraped third-party content without permission.
- No private, personal, or proprietary content. No real names, no internal URLs, no API keys, no internal project codenames.
- Add or update a test in `tests/` that asserts the expected label on the new demo.
- Number the directory with the next free index. Keep the slug short and descriptive (e.g. `04-cherrypick-zh`).

If you are not sure whether a case is in scope, open a **Demo case** issue first using the issue template — the project will help shape it before you spend time on a PR.

## Code style

- Standard Python, no formatter is enforced yet. Keep it readable.
- Type hints on public functions are appreciated but not required.
- Keep new dependencies to a minimum; justify any addition in the PR description.

## License

By contributing you agree that your contributions are licensed under the MIT license that covers the project.
