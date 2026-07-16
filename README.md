# microdrama-automatic-subtitle-repairer

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills)
that repairs machine-generated subtitles for vertical microdramas
(phone-native short dramas): verbatim text with fixed grammar/punctuation,
semantic cue segmentation, and word-accurate audio sync.

## What it does

Given an `.srt` file and its video, the skill runs a five-stage pipeline:

| Stage | Executor | What happens |
|---|---|---|
| 0 Audit | script | measure rule violations in the original SRT |
| 1 Align | WhisperX | force-align the SRT text to the audio → per-word timestamps |
| 2 Compose | the agent | fix grammar/punctuation, group words into cues by semantic rules (reveals/punchlines isolated, no misleading fragments, breaks at performance pauses) |
| 3 Validate & time | script | reject any plan that violates verbatim/length rules; compute all cue timings from word timestamps |
| 4 QC | script + agent | zero-violation audit, flag triage, burned-in preview check |

Design principle: **the agent decides meaning, never milliseconds; the
scripts decide milliseconds, never meaning.** The subtitle text is verbatim —
the pipeline never rewrites dialogue to satisfy a timing rule.

## Install

Copy this folder into your project as
`.claude/skills/microdrama-subtitle-repair/`, then from the project root:

```bash
python3.13 -m venv .venv   # any Python 3.10–3.13
.venv/bin/pip install -r .claude/skills/microdrama-subtitle-repair/requirements.txt
```

Requires ffmpeg on PATH. GPU (NVIDIA CUDA or Apple MPS) is auto-detected.

## Use

Ask Claude Code to fix your subtitles and point it at the SRT + video, e.g.:

> Fix the subtitles in EP01.srt to match EP01.mp4

The display rules (line length, durations, reading speed, semantic
segmentation) live in `references/subtitle-rules.md` — edit that file to
retarget the skill at a different format (e.g. 16:9 two-line subtitles).
