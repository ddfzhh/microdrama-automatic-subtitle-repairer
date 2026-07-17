# Burn-in Style Spec (only when the user asks for a burned video)

Base: 1080×1920 (9:16). Other resolutions scale everything proportionally
by video height.

| Property | Value |
|---|---|
| Font | Arial (English). For Chinese subtitles use Microsoft YaHei — Arial falls back to a random system CJK font |
| Size | 72 px (≈3.75% of height) |
| Weight | Bold |
| Color | Pure white |
| Outline | 5 px black |
| Shadow | 2 px black |
| Alignment | Bottom center |
| Bottom margin | 360 px |
| Left / right margin | 150 px each |
| Max subtitle width | 780 px (~72.2% of frame width) |
| Chars per line | ≤ 24 (matches the cue hard rule) |
| Safe area | Clear of the platform's bottom button bar and right-side control column |

## How to burn

Convert the SRT to ASS with this exact style, then burn. force_style
approximations drift across resolutions; a real ASS header does not.

```
[Script Info]
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: SafeTikTok,Arial,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&H99000000,1,0,0,0,100,100,0,0,1,5,2,2,150,150,360,1
```

```bash
# 1. convert (static_ffmpeg writes the [Events] from the SRT)
.venv/bin/static_ffmpeg -y -i out.srt out.ass
# 2. replace the generated [Script Info]/[V4+ Styles] header with the block
#    above (keep the generated [Events] section; set the Style name on each
#    Dialogue line to SafeTikTok)
# 3. burn, thread-capped
.venv/bin/static_ffmpeg -y -i video.mp4 -vf "ass=out.ass" -threads 4 -c:a copy burned.mp4
```

Frame-check after burning: a maximum-length two-line cue must render
unwrapped, inside the 780 px width, clear of the safe-area exclusions.
