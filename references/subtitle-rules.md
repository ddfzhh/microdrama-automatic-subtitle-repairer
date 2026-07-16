# Vertical Microdrama Subtitle Rules

One on-screen text unit = one **cue**.

## Rule zero: the text is verbatim

The subtitle text must match the provided SRT word-for-word. Only grammar,
spelling, punctuation, and casing may be fixed. Never trim, condense,
paraphrase, or reorder words — not even to satisfy a timing rule. When
verbatim text and a timing rule conflict (fast dialogue), the text wins and
the cue is flagged in the QC report.

## What lives where

The SRT file carries only text, line breaks, and timecodes — no styling.
Character-per-line limits are enforced by where the line breaks are placed
in the SRT; how large the text renders is the renderer's decision (the
platform app, or our burn-in style below). The limits and the text size are
calibrated together: 25 chars × 2 lines at ~3.75%-height type fills the
9:16 phone safe area without touching the UI columns.

## Hard rules (QC must pass with zero violations)

- ≤ 2 lines per cue; 1 line preferred — use the 2nd line only when one
  line cannot hold the semantic unit
- ≤ 25 characters per line (including spaces)
- The internal line break of a 2-line cue falls at a grammar boundary
  (same never-break list as cue breaks); prefer the top line shorter
- Duration: 0.833 s min, 5 s max
- Gap between cues: ≥ 2 frames (≥ 83 ms @ 24 fps, ≥ 67 ms @ 30 fps)
- No overlapping cues; strictly chronological

Exception: an interruption stub (a cut-off utterance ending in "—", e.g.
"I—") may run under the minimum duration when it is bounded by adjacent
speech on both sides.

## Targets

- 3–6 words per line typical; a 2-line cue is still ONE thought, never two
  thoughts stacked to save a cue
- Reading speed ≤ 17 CPS (target 15). This is a target, not a hard rule:
  the text is verbatim, so when the actors speak faster than 17 CPS the cue
  simply flags over-speed in the QC report — never fix it by cutting words.
  Timing should always extend such cues into every millisecond of available
  silence first.
- Duration sweet spot: 1–3 s
- Cue in-time: ≤ 120 ms before the first spoken word
- Cue out-time: ≤ 500 ms after the last word; extend into silence to meet
  min duration / CPS, never into the next cue

## Text

- Full punctuation, sentence casing
- Keep terminal periods
- Keep spoken register: "gonna", "ya", curses, interjections stay
- Numbers 1–10 as words, 11+ as digits
- Ellipsis only for genuine trailing off or interruption
- No speaker labels, no SFX captions

## Break points

Priority: sentence end > clause boundary (after comma; before "but/and/
because/so") > phrase boundary.

Never break: article/adjective + noun, subject + verb, verb + particle,
parts of a name.

Test: each cue read alone must make sense.

## Semantic segmentation (editorial judgment — decide while composing cues)

These require understanding the scene; character/duration math cannot catch
them. A cue's in-time comes from its own first word, so isolating words
into their own cue is what delays them on screen until they are spoken.

1. **One thought per cue.** Never bundle the start of a new thought onto
   the tail of the previous one, even if it fits.
2. **Isolate reveals.** A twist, name reveal, verdict, or key fact gets its
   own cue so it appears at the moment it is spoken — never on screen while
   the setup is still being said. ("Luke..." | "I am your father.")
3. **Isolate punchlines.** Setup and punchline never share a cue; the joke
   dies if the audience reads ahead of the delivery.
4. **No misleading fragments.** A cue must not read as a complete statement
   that the continuation then contradicts or reverses. "He's guilty |
   of nothing." asserts the opposite of the sentence — break elsewhere.
   (Different from the "makes sense alone" test: the fragment makes sense,
   but the *wrong* sense.)
5. **Cut at performance pauses.** If the actor pauses mid-sentence for
   effect (visible as a gap in the word timestamps), break the cue at the
   pause and end the first part with "…" — the text must not outrun the
   performance. Conversely, don't add "…" where there is no real pause.
6. **Keep rhetorical question and answer apart.** "You know what they
   say?" | "A street fight ends only one way." — even within one speaker's
   turn.
7. **Match delivery rhythm on repetition.** Parallel or repeated phrasing
   ("20 damn years. 20 years behind a rock.") splits where the delivery
   beats, one beat per cue.
8. **Keep quoted speech intact.** Don't split inside a quoted phrase if it
   can stay whole.
9. **Don't linger into a reaction.** If a line is followed by a silent
   reaction shot, the cue ends with the speech rather than stretching
   across the reaction — the audience should watch the face, not re-read
   the line. Mark such cues `"no_extend": true` in the plan.

## Rendering (previews/delivery)

**Text size: ~3.75% of video height** (BBC subtitle guidance for 9:16
video; 2% is too small to read on a phone, 8% is the error ceiling).
That is 72 px on 1080×1920, 48 px on 720×1280. At this size ~25
characters span the phone safe column (center ~83% of frame width, clear
of the right-side button stack).

Position: bottom-center, baseline ~15–20% up from the bottom edge (clear
of the progress bar / caption dead zone). White text, thin dark outline,
no box.

ffmpeg burn-in style (libass FontSize is relative to PlayResY=288, so 11
≈ 3.75% of height at any resolution; MarginV leaves room for 2 lines):
`force_style='FontName=Arial,FontSize=11,Bold=1,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=1,Shadow=0,MarginV=50,Alignment=2'`
After burning, frame-check a maximum-length 2-line cue: each line must
render unwrapped and inside the safe column.
