# Security Policy

## Supported versions

Only the [latest release](https://github.com/rotorrest/claude-monitor/releases/latest) is supported. `claudios update` (or `brew upgrade claude-monitor`) gets you there.

## Reporting a vulnerability

Please use [GitHub's private vulnerability reporting](https://github.com/rotorrest/claude-monitor/security/advisories/new) — don't open a public issue for security problems.

## What this tool does (threat model)

- Reads files under your own `~/.claude/` and runs read-only system commands (`ps`, `vm_stat`, `pmset`, `docker stats`).
- Makes exactly one kind of network call: a version check / self-update against `api.github.com` and GitHub release downloads, SHA256-verified. `CLAUDIOS_NO_UPDATE_CHECK=1` disables the check entirely.
- Executes AppleScript only with validated inputs (ttys matching `s\d+`, session IDs matching `[A-Za-z0-9-]+`), and strips control characters from anything read from session files before rendering.

## Pipeline

Every push runs `ruff`, `bandit`, CodeQL, `shellcheck` and a stdlib-only import guard; releases are blocked unless the same gate passes and the tag matches `__version__`.
