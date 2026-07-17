#!/usr/bin/env python3
"""Stage 3: validate an agent-authored cue plan, then compute cue timings.

Usage: validate_time.py words.json plan.json out.srt [--fps 30] [--flags flags.txt]

words.json  — from align.py.
plan.json   — from the agent (Stage 2), a list of cues in order:
  {"words": [first, last],   inclusive index range into words.json
   "text": "What?! No way.", repaired text: verbatim words + punctuation/casing;
                             may contain ONE "\n" (2-line cue, break at a
                             grammar boundary, top line shorter)
   "no_extend": true,        optional: reaction shot follows, don't linger
   "edited": [41]}           optional: indices whose spelling was deliberately fixed

Exit 0: SRT + flags written.
Exit 2: plan rejected — one error per line, addressed by cue number.
        Fix only the named cues and rerun. The plan carries no timestamps;
        all timing below is computed from the aligned words.
"""
import json, re, sys

MIN_DUR, MAX_DUR = 0.833, 5.0
MAX_CPS, TARGET_CPS = 17.0, 15.0   # flag above MAX; extend cues toward TARGET
MAX_LINE_CHARS, MAX_LINES = 25, 2
LEAD, TAIL = 0.12, 0.5
LATE_SLIP = 0.15   # a starving cue may run this far into the next cue's speech

norm = lambda t: re.sub(r"[^\w']", '', t).lower()


def validate(plan, words):
    errors = []
    expect = 0
    for c, cue in enumerate(plan, 1):
        first, last = cue['words']
        if first != expect:
            errors.append(f"cue {c}: words start at {first}, expected {expect} "
                          f"(every word used exactly once, in order)")
        expect = last + 1
        toks = cue['text'].split()
        if len(toks) != last - first + 1:
            errors.append(f"cue {c}: {len(toks)} tokens vs {last-first+1} aligned words")
            continue
        for k, tok in enumerate(toks):
            i = first + k
            if norm(tok) != norm(words[i]['word']) and i not in cue.get('edited', []):
                errors.append(f"cue {c}: word {i} '{words[i]['word']}' rewritten as "
                              f"'{tok}' (verbatim rule; use \"edited\" if intentional)")
        lines = cue['text'].split('\n')
        if len(lines) > MAX_LINES:
            errors.append(f"cue {c}: {len(lines)} lines > {MAX_LINES}")
        for ln in lines:
            if len(ln) > MAX_LINE_CHARS:
                errors.append(f"cue {c}: line '{ln}' is {len(ln)} chars > {MAX_LINE_CHARS}")
    if expect != len(words):
        errors.append(f"plan ends at word {expect-1}, words.json has {len(words)} words")
    return errors


def fmt_ts(t):
    ms = round(t * 1000)
    return f"{ms//3600000:02d}:{ms%3600000//60000:02d}:{ms%60000//1000:02d},{ms%1000:03d}"


def main():
    words_path, plan_path, out_path = sys.argv[1:4]
    argv = sys.argv[4:]
    fps = float(argv[argv.index('--fps') + 1]) if '--fps' in argv else 30
    flags_path = argv[argv.index('--flags') + 1] if '--flags' in argv else None
    gap = 2 / fps + 0.001

    data = json.load(open(words_path))
    words, flags = data['words'], list(data.get('flags', []))
    plan = json.load(open(plan_path))

    errors = validate(plan, words)
    if errors:
        print('\n'.join(errors))
        sys.exit(2)

    out = []
    for i, cue in enumerate(plan):
        first, last = cue['words']
        ws, we = words[first]['start'], words[last]['end']
        start = ws - LEAD
        if out:
            start = max(start, out[-1]['end'] + gap)
        nxt_ws = words[plan[i+1]['words'][0]]['start'] if i + 1 < len(plan) else 1e9
        polite, hard = nxt_ws - LEAD - gap, nxt_ws - gap
        end = min(we + TAIL, start + MAX_DUR, polite)
        nchars = len(cue['text'].replace('\n', ' '))
        need = max(MIN_DUR, nchars / TARGET_CPS)
        if not cue.get('no_extend') and end - start < need:
            end = min(start + need, start + MAX_DUR, hard)
        if end - start < MIN_DUR:   # last resort, even for no_extend
            end = min(start + MIN_DUR, hard + LATE_SLIP)
        if end - start < MIN_DUR - 1e-6:
            flags.append(f"SHORT {end-start:.2f}s (crowded): {cue['text']}")
        if nchars / (end - start) > MAX_CPS + 0.01:
            flags.append(f"CPS {nchars/(end-start):.1f} (fast speech): {cue['text']}")
        out.append({'start': start, 'end': end, 'text': cue['text']})

    with open(out_path, 'w', encoding='utf-8') as f:
        for i, c in enumerate(out, 1):
            f.write(f"{i}\n{fmt_ts(c['start'])} --> {fmt_ts(c['end'])}\n{c['text']}\n\n")
    if flags_path:
        open(flags_path, 'w').write('\n'.join(flags) + '\n')
    print(f"wrote {len(out)} cues -> {out_path}; {len(flags)} flags")
    for fl in flags:
        print(' !', fl)


if __name__ == '__main__':
    main()
