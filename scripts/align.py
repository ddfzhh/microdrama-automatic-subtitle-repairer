#!/usr/bin/env python3
"""Stage 1: force-align an original SRT against its audio.

Usage: align.py input.srt audio.wav words.json

Aligns each SRT cue's text (verbatim, as provided) to the audio and writes
one flat word list with global indices:

  {"words": [{"i": 0, "word": "Hey", "start": 12.1, "end": 12.3, "score": 0.9}, ...],
   "flags": ["...spans where alignment was untrusted..."]}

Alignment is per-cue: whisperx.align() re-splits batched segments internally,
so batch output cannot be paired back to inputs. Words the aligner cannot
time (digits like "20") get times interpolated from their neighbors. When a
cue's alignment is untrustworthy (mostly low scores, or drifted far from the
SRT anchor), its words are spread evenly over the original SRT cue span
instead, and the span is flagged for Stage 4 verification.
"""
import json, re, sys

MIN_SCORE, MAX_DRIFT = 0.5, 2.0


def parse_srt(path):
    txt = open(path, encoding='utf-8-sig').read()
    cues = []
    for b in re.split(r'\n\s*\n', txt.strip()):
        lines = b.strip().split('\n')
        m = re.search(r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)', b)
        if not m:
            continue
        g = list(map(int, m.groups()))
        ti = next(i for i, l in enumerate(lines) if '-->' in l)
        cues.append({'start': g[0]*3600 + g[1]*60 + g[2] + g[3]/1000,
                     'end': g[4]*3600 + g[5]*60 + g[6] + g[7]/1000,
                     'text': ' '.join(lines[ti+1:])})
    return cues


def interpolate_times(words, span_start, span_end):
    """Fill missing start/end by spreading each untimed run evenly between
    its timed neighbors."""
    n, i = len(words), 0
    while i < n:
        if words[i].get('start') is not None:
            i += 1
            continue
        j = i
        while j < n and words[j].get('start') is None:
            j += 1
        prev_end = words[i-1]['end'] if i > 0 else span_start
        nxt_start = words[j]['start'] if j < n else span_end
        step = max(nxt_start - prev_end, 0) / (j - i)
        for k in range(j - i):
            words[i+k]['start'] = prev_end + k * step
            words[i+k]['end'] = prev_end + (k+1) * step
            words[i+k]['score'] = words[i+k].get('score') or 0.0
        i = j
    return words


def pick_device():
    """Fastest available backend: NVIDIA CUDA > Apple MPS > CPU."""
    import torch
    if torch.cuda.is_available():
        return 'cuda'
    if torch.backends.mps.is_available():
        return 'mps'
    return 'cpu'


def main():
    srt_path, wav_path, out_path = sys.argv[1:4]
    cues = parse_srt(srt_path)

    import whisperx
    device = pick_device()
    print(f"device: {device}")
    audio = whisperx.load_audio(wav_path)
    try:
        model_a, meta = whisperx.load_align_model(language_code='en', device=device)
    except Exception:
        device = 'cpu'   # accelerator lacks an op or memory — CPU always works
        model_a, meta = whisperx.load_align_model(language_code='en', device=device)

    all_words, flags = [], []
    for cue in cues:
        try:
            res = whisperx.align([cue], model_a, meta, audio, device,
                                 return_char_alignments=False)
        except Exception:
            if device == 'cpu':
                raise
            device = 'cpu'
            model_a, meta = whisperx.load_align_model(language_code='en', device=device)
            res = whisperx.align([cue], model_a, meta, audio, device,
                                 return_char_alignments=False)
        words = [w for s in res['segments'] for w in s['words']]
        if not words:
            flags.append(f"NO ALIGNMENT — anchor timing, verify "
                         f"{cue['start']:.1f}-{cue['end']:.1f}s: {cue['text']}")
            words = [{'word': w} for w in cue['text'].split()]
        low = [w for w in words if (w.get('score') or 0) < MIN_SCORE]
        drift = abs((words[0].get('start') or cue['start']) - cue['start'])
        if len(low) > len(words) / 2 or drift > MAX_DRIFT:
            reason = (f"LOW CONFIDENCE ({len(low)}/{len(words)} words <{MIN_SCORE})"
                      if len(low) > len(words) / 2 else f"DRIFT {drift:.1f}s")
            flags.append(f"{reason} — anchor timing, verify "
                         f"{cue['start']:.1f}-{cue['end']:.1f}s: {cue['text']}")
            for w in words:
                w['start'] = w['end'] = None
        words = interpolate_times(words, cue['start'], cue['end'])
        all_words.extend(words)

    for i, w in enumerate(all_words):
        w['i'] = i
        w['word'] = w['word'].strip()
    json.dump({'words': all_words, 'flags': flags},
              open(out_path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f"{len(all_words)} words -> {out_path}; {len(flags)} flags")
    for f in flags:
        print(' !', f)


if __name__ == '__main__':
    main()
