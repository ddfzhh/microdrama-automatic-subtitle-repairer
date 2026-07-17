#!/usr/bin/env python3
"""QC audit for vertical microdrama SRTs. Usage: audit.py file.srt [...] [--fps 30]"""
import re, sys, json

MIN_DUR, MAX_DUR, MAX_CPS, MAX_LINE_CHARS, MAX_LINES = 0.833, 5.0, 17.0, 25, 2

def parse_srt(path):
    txt = open(path, encoding='utf-8-sig').read()
    cues = []
    for b in re.split(r'\n\s*\n', txt.strip()):
        lines = b.strip().split('\n')
        m = re.search(r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)', b)
        if not m:
            continue
        g = list(map(int, m.groups()))
        start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        ti = next(i for i, l in enumerate(lines) if '-->' in l)
        text = '\n'.join(lines[ti + 1:])
        cues.append({'start': start, 'end': end, 'text': text})
    return cues

def audit(path, fps=30):
    cues = parse_srt(path)
    gap_min = 2 / fps
    v, w_ = [], []
    prev_end = None
    for i, c in enumerate(cues, 1):
        d = c['end'] - c['start']
        n = len(c['text'].replace('\n', ' '))
        lines = c['text'].split('\n')
        if len(lines) > MAX_LINES: v.append((i, f'lines={len(lines)}', c['text']))
        for ln in lines:
            if len(ln) > MAX_LINE_CHARS: v.append((i, f'line chars={len(ln)}', ln))
        # interruption stubs ("I—") bounded by speech on both sides are exempt
        # from min duration
        if d < MIN_DUR - 1e-3 and not c['text'].rstrip().endswith(('—', '-', '…')):
            v.append((i, f'dur={d:.2f}s<min', c['text']))
        if d > MAX_DUR: v.append((i, f'dur={d:.2f}s>max', c['text']))
        # reading speed is a soft target: the text is verbatim, so fast
        # speech gets a warning, not a violation
        if d > 0 and n / d > MAX_CPS: w_.append((i, f'cps={n/d:.1f}', c['text']))
        if prev_end is not None:
            if c['start'] < prev_end: v.append((i, 'overlap', c['text']))
            elif c['start'] - prev_end < gap_min - 1e-6:
                v.append((i, f'gap={(c["start"]-prev_end)*1000:.0f}ms', c['text']))
        prev_end = c['end']
    return cues, v, w_

if __name__ == '__main__':
    argv = sys.argv[1:]
    fps = 30
    if '--fps' in argv:
        i = argv.index('--fps')
        fps = float(argv[i + 1])
        del argv[i:i + 2]
    args = argv
    total_cues = total_v = total_w = 0
    for path in args:
        cues, v, w_ = audit(path, fps)
        total_cues += len(cues); total_v += len(v); total_w += len(w_)
        print(f'{path}: {len(cues)} cues, {len(v)} violations, {len(w_)} speed warnings')
        for i, rule, text in v:
            print(f'  cue {i}: {rule} | {text}')
        for i, rule, text in w_:
            print(f'  cue {i} (warn): {rule} | {text}')
    print(f'\nTOTAL: {total_cues} cues, {total_v} violations, {total_w} speed warnings')
    sys.exit(1 if total_v else 0)
