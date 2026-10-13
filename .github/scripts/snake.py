"""Generate an animated snake SVG from the public GitHub contribution calendar.

Reads https://github.com/users/<user>/contributions (the same calendar visitors
see on the profile, including anonymized private contributions) so the snake
always matches the real graph.

Usage: python snake.py <username> <output_dir>
"""
import os
import re
import sys
import urllib.request

USER, OUT = sys.argv[1], sys.argv[2]
CELL, GAP = 11, 3
PITCH = CELL + GAP
STEP = 0.045          # seconds per cell
SNAKE_LEN = 5
PAUSE_STEPS = 25      # pause after the snake leaves the grid

THEMES = {
    "github-snake.svg": {
        "empty": "#ebedf0", "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "snake": "#8250df", "text": "#57606a",
    },
    "github-snake-dark.svg": {
        "empty": "#161b22", "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "snake": "#a371f7", "text": "#8b949e",
    },
}

req = urllib.request.Request(
    f"https://github.com/users/{USER}/contributions",
    headers={"User-Agent": "snake-generator"},
)
html = urllib.request.urlopen(req, timeout=30).read().decode()

cells = {}  # (col, row) -> level
for td in re.findall(r"<td[^>]*data-date[^>]*>", html):
    m = re.search(r'id="contribution-day-component-(\d+)-(\d+)"', td)
    lvl = re.search(r'data-level="(\d)"', td)
    if m and lvl:
        row, col = int(m.group(1)), int(m.group(2))
        cells[(col, row)] = int(lvl.group(1))

if not cells:
    sys.exit("No contribution cells found; GitHub page format may have changed.")

cols = max(c for c, _ in cells) + 1

# Serpentine path: down column 0, up column 1, and so on.
path = []
for c in range(cols):
    rows = range(7) if c % 2 == 0 else range(6, -1, -1)
    path.extend((c, r) for r in rows)

eat_step = {pos: i for i, pos in enumerate(path)}
total_steps = len(path) + SNAKE_LEN + PAUSE_STEPS
dur = total_steps * STEP
W, H = cols * PITCH + 20, 7 * PITCH + 20


def xy(pos):
    c, r = pos
    return 10 + c * PITCH, 10 + r * PITCH


def build(theme):
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    ]
    for pos, level in sorted(cells.items()):
        x, y = xy(pos)
        color = theme["levels"][level]
        rect = f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"'
        if level > 0 and pos in eat_step:
            t = (eat_step[pos] + 1) / total_steps
            rect += (
                f'><animate attributeName="fill" dur="{dur:.2f}s" repeatCount="indefinite" '
                f'calcMode="discrete" keyTimes="0;{t:.5f}" '
                f'values="{color};{theme["empty"]}"/></rect>'
            )
        else:
            rect += "/>"
        out.append(rect)

    # Snake segments, each trailing the head by i steps.
    off = (-PITCH * 2, -PITCH * 2)
    for i in range(SNAKE_LEN):
        values, times = [], []
        for s in range(total_steps):
            k = s - i
            if 0 <= k < len(path):
                x, y = xy(path[k])
            else:
                x, y = off
            values.append(f"{x},{y}")
            times.append(f"{s / total_steps:.5f}")
        size = CELL - i  # tail tapers
        pad = i / 2
        opacity = 1 - i * 0.12
        out.append(
            f'<rect width="{size}" height="{size}" x="{pad}" y="{pad}" rx="3" '
            f'fill="{theme["snake"]}" fill-opacity="{opacity:.2f}">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'dur="{dur:.2f}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{";".join(times)}" values="{";".join(values)}"/></rect>'
        )
    out.append("</svg>")
    return "\n".join(out)


os.makedirs(OUT, exist_ok=True)
for name, theme in THEMES.items():
    with open(os.path.join(OUT, name), "w") as f:
        f.write(build(theme))

active = sum(1 for v in cells.values() if v > 0)
print(f"Wrote snake SVGs: {len(cells)} cells, {active} active days")
