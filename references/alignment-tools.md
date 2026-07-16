# Forced Alignment Notes

`scripts/align.py` wraps everything below; read this only when it breaks
or needs replacing.

Task shape: trusted transcript + audio → word timestamps. This is *forced
alignment*, not transcription — never re-transcribe and diff.

## Caveats already handled by align.py

- `whisperx.align()` re-splits batched segments internally, so batch output
  can't be paired back to inputs — align one cue per call and flatten words.
- Digits ("20") get no timestamps from the phoneme model — interpolated
  from neighboring words.
- Untrusted alignments (majority word scores < 0.5, or first word drifted
  > 2 s from the SRT anchor) are discarded; those cues keep original SRT
  timing and get flagged for the Stage 4 ASR diff.

## If WhisperX becomes unavailable

The stable part is wav2vec2 CTC alignment; wrappers come and go. Fallbacks,
in order: `ctc-forced-aligner` (MahmoudAshraf97, lightweight, purpose-built
for text+audio), raw `torchaudio` forced-alignment API (the primitive both
wrappers use), Montreal Forced Aligner (most accurate, heavyweight — conda
plus pronunciation dictionaries, overkill for 2-minute clips). stable-ts was
archived 2026-05-30; do not adopt. aeneas is long unmaintained; avoid.
