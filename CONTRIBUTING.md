# Contributing

Thanks for stopping by! This is a small, sharp tool — contributions that keep it that way are very welcome.

## Ground rules

- **Zero dependencies is a feature.** Python stdlib only — CI enforces it. PRs adding dependencies won't be merged.
- **macOS is the target.** Terminal/iTerm2/Cursor/VS Code integrations are AppleScript/`open -a` based on purpose.
- **Screenshots use demo data.** Never commit output generated with `--live` (it contains your real project names). `python3 tools/screenshot.py docs/demo.svg` uses fictional sessions by default.

## Dev loop

```bash
git clone https://github.com/rotorrest/claude-monitor && cd claude-monitor
python3 src/claudios.py -w        # run from source
```

Before pushing:

```bash
ruff check src/ .github/scripts/ tools/
bandit -ll -r src/
python3 .github/scripts/stdlib_guard.py src/claudios.py src/claude_notify.py
shellcheck install.sh
```

CI runs the same checks plus a macOS smoke test.

## Releasing (maintainers)

1. Bump `__version__` in `src/claudios.py`.
2. `git tag vX.Y.Z && git push origin vX.Y.Z`.
3. The pipeline runs the security gate, builds the assets and publishes the release. Update the tap formula (`rotorrest/homebrew-tap`) if the `TAP_GITHUB_TOKEN` secret isn't configured.

## Good first issues

Check the [roadmap in the README](README.md#roadmap-features-proudly-stolen) — every unchecked item links to the tool that inspired it.
