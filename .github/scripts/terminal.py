"""Build an animated terminal SVG that types out commands line by line."""
import sys
from xml.sax.saxutils import escape

OUT = sys.argv[1]

LINES = [
    ("cmd", "whoami"),
    ("out", "Dilpreet Singh Dua · Solutions Engineer · Indore, IN"),
    ("cmd", "cat focus.txt"),
    ("out", "Designing solutions that connect people, products & APIs"),
    ("cmd", "ls toolkit/"),
    ("dir", "apis/  integrations/  cloud/  demos/  ai-workflows/"),
    ("cmd", './solve --input "messy requirements"'),
    ("ok",  "✔ requirements → architecture → working demo"),
    ("cmd", "echo $FUN_FACT"),
    ("out", "Debugging at 2 AM hits different"),
]

FS = 14            # font size
CW = FS * 0.62     # approx monospace char width
LH = 24            # line height
PAD_X, TOP = 22, 62
PROMPT = "dilpreet@github:~$ "
TYPE = 0.055       # seconds per typed char
PRE_CMD = 0.45     # pause before typing a command
POST_CMD = 0.35    # pause before output appears
HOLD = 5.0         # pause at the end before looping

W = 760
H = TOP + LH * (len(LINES) + 1) + 16

C = {
    "bg": "#0d1117", "bar": "#161b22", "border": "#30363d",
    "prompt": "#3fb950", "cmd": "#e6edf3", "out": "#8b949e",
    "dir": "#58a6ff", "ok": "#3fb950", "title": "#8b949e",
}

# Timeline: for each line, (start, end) of reveal.
events, t = [], 0.6
for kind, text in LINES:
    if kind == "cmd":
        t += PRE_CMD
        start = t
        t += TYPE * len(text)
        events.append((start, t))
        t += POST_CMD
    else:
        events.append((t, t))
        t += 0.15
cursor_at = t
total = t + HOLD


def kt(sec):
    return f"{min(max(sec / total, 0), 1):.5f}"


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'Liberation Mono\',monospace" font-size="{FS}">',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{C["bg"]}" stroke="{C["border"]}"/>',
    f'<path d="M0.5 36 V10.5 a10 10 0 0 1 10 -10 H{W-10.5} a10 10 0 0 1 10 10 V36 Z" fill="{C["bar"]}"/>',
    f'<line x1="0.5" y1="36" x2="{W-0.5}" y2="36" stroke="{C["border"]}"/>',
    '<circle cx="22" cy="18" r="6" fill="#ff5f56"/><circle cx="42" cy="18" r="6" fill="#ffbd2e"/>'
    '<circle cx="62" cy="18" r="6" fill="#27c93f"/>',
    f'<text x="{W/2}" y="23" text-anchor="middle" fill="{C["title"]}" font-size="12">dilpreet@github: ~</text>',
    "<defs>",
]

prompt_w = len(PROMPT) * CW
for i, ((kind, text), (start, end)) in enumerate(zip(LINES, events)):
    y = TOP + i * LH
    x0 = PAD_X + (prompt_w if kind == "cmd" else 0)
    full = len(text) * CW + 12
    if kind == "cmd":
        n = len(text)
        times = ["0", kt(start)] + [kt(start + TYPE * (k + 1)) for k in range(n)] + ["1"]
        widths = ["0", "0"] + [f"{(k + 1) * CW:.1f}" for k in range(n - 1)] + [f"{full:.1f}", f"{full:.1f}"]
    else:
        times = ["0", kt(start), "1"]
        widths = ["0", f"{full:.1f}", f"{full:.1f}"]
    parts.append(
        f'<clipPath id="c{i}"><rect x="{x0}" y="{y - FS - 2}" height="{LH}" width="0">'
        f'<animate attributeName="width" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" '
        f'keyTimes="{";".join(times)}" values="{";".join(widths)}"/></rect></clipPath>'
    )
parts.append("</defs>")

for i, ((kind, text), (start, _)) in enumerate(zip(LINES, events)):
    y = TOP + i * LH
    if kind == "cmd":
        # prompt appears when the command starts
        parts.append(
            f'<text x="{PAD_X}" y="{y}" fill="{C["prompt"]}" opacity="0">{escape(PROMPT.rstrip())}'
            f'<animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="0;{kt(start - PRE_CMD + 0.05)};1" values="0;1;1"/></text>'
        )
        parts.append(
            f'<text x="{PAD_X + prompt_w}" y="{y}" fill="{C["cmd"]}" clip-path="url(#c{i})">{escape(text)}</text>'
        )
    else:
        parts.append(f'<text x="{PAD_X}" y="{y}" fill="{C[kind]}" clip-path="url(#c{i})">{escape(text)}</text>')

# final prompt with blinking cursor
y = TOP + len(LINES) * LH
appear = kt(cursor_at)
parts.append(
    f'<g opacity="0"><animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite" '
    f'calcMode="discrete" keyTimes="0;{appear};1" values="0;1;1"/>'
    f'<text x="{PAD_X}" y="{y}" fill="{C["prompt"]}">{escape(PROMPT.rstrip())}</text>'
    f'<rect x="{PAD_X + prompt_w}" y="{y - FS + 2}" width="{CW:.1f}" height="{FS + 2}" fill="{C["cmd"]}">'
    f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite" calcMode="discrete"/>'
    f"</rect></g>"
)
parts.append("</svg>")

with open(OUT, "w") as f:
    f.write("\n".join(parts))
print(f"total {total:.1f}s, size {W}x{H}")
