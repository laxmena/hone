# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2026-03-24

### Fixed
- Report chart no longer skews on error scores (999 / Infinity) — they are replaced with `null` so Chart.js renders a clean gap
- Error iterations now show an orange "Error" badge and auto-expand benchmark output, making failures immediately visible
- Score display shows "Error" instead of raw sentinel values (999.0 / Infinity)

### Improved
- Iteration reasoning is now labeled "Hypothesis" to clarify it is the LLM's plan before the benchmark ran
- Error stdout styled in orange to distinguish from successful output

## [1.2.0] - 2026-03-24

### Added
- `--goal-file` option: pass a file path instead of an inline goal string, enabling rich, multi-line goal descriptions with as much context as needed. Fully backwards-compatible — the positional `GOAL` argument works exactly as before.

## [1.1.0] - 2026-03-23

### Added
- Initial public release with autonomous optimization loop, snapshot strategies (`copy`, `git`), budget cap, dry-run mode, and multi-model support (Claude, OpenAI, Ollama).
