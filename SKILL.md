---
name: microdrama-subtitle-repair
description: >-
  Repair and re-master subtitles for vertical microdramas (short dramas made
  for phones). Takes any SRT file(s) plus the matching video(s) and produces
  verbatim, correctly punctuated, semantically segmented, audio-synced
  subtitles that follow vertical-drama display rules. Use this
  skill whenever the user has SRT/subtitle files with bad grammar, bad line
  breaks, cues that are too long/short/fast, or subtitles out of sync with
  dialogue audio — including any mention of "fix subtitles", "subtitle
  timing", "captions look bad", "re-align SRT", or delivering microdrama /
  short-drama / ReelShort-style episodes.
---

# Microdrama Subtitle Repair

Input: one or more `.srt` files, each with the video it belongs to (any
video format ffmpeg reads; caption-free preferred, but only the audio track
is used). Ask the user to point out the SRT file(s) and matching video(s);
if a pairing is ambiguous, confirm it with the user before starting.

The SRT words are the final script. Fix only grammar, spelling, punctuation,
and casing. Never trim, condense, paraphrase, or reorder words — when a
timing rule and the verbatim text conflict, the text wins and the cue is
flagged.

Division of labor — do not blur it:
- **You (the agent)** decide what each cue says and which words belong
  together: meaning, never milliseconds.
- **The scripts** decide when cues appear and disappear, and prove your plan
  legal: milliseconds, never meaning.

Read `references/subtitle-rules.md` before Stage 2. It is the output spec.

## Setup (once per project, from the project root)

```bash
python3.13 -m venv .venv   # any Python 3.10–3.13; NOT 3.14+
.venv/bin/pip install -r .claude/skills/microdrama-subtitle-repair/requirements.txt
```

ffmpeg must be on PATH. Run all scripts with `.venv/bin/python`.

This runs on the user's personal machine — keep it responsive. Prefix
long CPU-bound commands (ASR verification passes, preview burns) with
`nice -n 15`, give ffmpeg burns `-threads 4`, and cap CPU inference
threads (`OMP_NUM_THREADS=4`, faster-whisper `cpu_threads=4`). GPU
alignment needs no cap. Slightly slower is fine; a frozen machine is not.

Windows: the venv executables live at `.venv\Scripts\python` and
`.venv\Scripts\static_ffmpeg` (not `bin/`); install ffmpeg with
`winget install ffmpeg`; run the burn command from `cmd` or wrap the
`-vf` argument in double quotes for PowerShell.

Pilot ONE episode end-to-end, get the user's approval on the SRT and
preview, then batch the rest.

## Workflow (per episode; `S` = this skill's `scripts/` dir)

### Stage 0 — Baseline audit

```bash
ffprobe -v error -select_streams v -show_entries stream=r_frame_rate -of csv=p=0 video.mp4  # e.g. 30/1
.venv/bin/python S/audit.py original.srt --fps <measured fps>
```

Use the measured fps in every `--fps` below (it sets the minimum gap).

Record the violation count — Stage 4 must reduce it to zero.

### Stage 1 — Align (tool)

```bash
ffmpeg -y -i video.mp4 -vn -ac 1 -ar 16000 ep.wav
.venv/bin/python S/align.py original.srt ep.wav words.json
```

`words.json` holds one timestamp per word (`{"i","word","start","end","score"}`)
plus flags for spans where alignment was untrusted and the original SRT
timing was kept.

### Stage 2 — Compose the cue plan (you)

Read `words.json` and `references/subtitle-rules.md`, then write `plan.json`:
an ordered list of cues, each an object:

```json
{"words": [12, 17], "text": "I am your father.", "no_extend": true}
```

- `words`: inclusive index range into `words.json`. Every word used exactly
  once, in order.
- `text`: the repaired cue — the same words with punctuation, casing, and
  spelling fixed. May contain one `\n` for a 2-line cue (see the rules file
  for line limits and break placement). List any spelling-fixed indices in
  `"edited": [i, ...]` and log each fix to `changes_EPxx.md`.
- `no_extend` (optional): set when a silent reaction follows the cue, so
  the timer won't stretch it over the reaction.
- Never write timestamps. Group words by the semantic rules first, grammar
  break points second, length limits third. Use gaps between word
  timestamps to find the actor's pauses.

### Stage 3 — Validate & time (script)

```bash
.venv/bin/python S/validate_time.py words.json plan.json out.srt --fps 30 --flags flags.txt
```

Exit 2 = plan rejected, one error per line addressed by cue number — fix
only the named cues in `plan.json` and rerun. Exit 0 = SRT written with all
timing computed (lead/tail, silence extension, minimum-duration rescues,
frame gaps).

### Stage 4 — QC + visual check

1. `audit.py` on the output: zero violations required (allowed exceptions:
   interruption stubs "I—" and flagged crowded cues; speed warnings are
   report-only because text is verbatim).
2. Act on each line of `flags.txt`:
   - **LOW CONFIDENCE (alignment kept)**: transcribe that span with plain
     ASR using word timestamps and diff against the SRT text. Text differs
     → report the discrepancy to the user; never rewrite the words. Text
     matches → the alignment's timing is trustworthy (the low score was
     music/noise, and a matching transcript means the aligner had the right
     words); as a cross-check, compare the ASR's word times (clip offset +
     word time) against the cue times — if they disagree by > ~300 ms,
     report the span to the user.
   - **DRIFT / NON-MONOTONIC / NO ALIGNMENT (anchor timing)**: these cues
     inherited the ORIGINAL SRT timing, which may carry the source's sync
     errors. Do the same ASR text-diff, and additionally watch these spans
     in the burned preview for early/late cues — a still frame cannot catch
     a sync error.
   - **SHORT (crowded)**: acceptable only when boxed in by speech on both
     sides; list in the QC report.
   - **CPS (fast speech)**: list in the QC report, no action.
3. Burn a preview. Frame-check the longest cue for line wrap, AND
   sync-check every flagged span by watching the preview clip around it —
   layout is verifiable from stills, sync is not (system ffmpeg often
   lacks libass — use the venv's `static_ffmpeg`; style is in the rules
   file):
   ```bash
   .venv/bin/static_ffmpeg -y -i video.mp4 -vf "subtitles=out.srt:force_style='<style>'" -c:a copy preview.mp4
   ```
4. Deliver to a new output folder (never overwrite sources): the SRT, the
   change log, and a QC report (before/after violation counts, accepted
   exceptions, flag resolutions).

## Failure modes

- Aligner distrusts music/SFX-heavy spans → they fall back to original SRT
  timing automatically; your job is the ASR diff in Stage 4.
- Transcript doesn't match the audio → alignment cannot fix wrong words;
  report to the user, never rewrite.
- Two speakers overlap → keep cues sequential; never put two speakers'
  words in one cue.
