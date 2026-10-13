"""Generate an animated snake SVG from the public GitHub contribution calendar.

Reads https://github.com/users/<user>/contributions (the same calendar visitors
see on the profile, including anonymized private contributions) so the snake
always matches the real graph.

Usage: python snake.py <username> <output_dir>
"""
import os
import random
import re
import sys
import urllib.request

USER, OUT = sys.argv[1], sys.argv[2]
CELL, GAP = 11, 3
PITCH = CELL + GAP
STEP = 0.14           # seconds per cell
SNAKE_LEN = 5
PAUSE_STEPS = 12      # pause after the snake leaves the grid

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

# Wandering path: the snake enters from the left, then hunts the active days
# in random order, taking slightly meandering routes, and leaves on the right.
rng = random.Random()
targets = [pos for pos, lvl in cells.items() if lvl > 0]
rng.shuffle(targets)


def inside(c, r):
    return 0 <= c < cols and 0 <= r < 7


pos = (-1, rng.randrange(7))
path = [pos]
for tgt in targets + [(cols, rng.randrange(7))]:
    guard = 0
    while pos != tgt and guard < 500:
        guard += 1
        c, r = pos
        dc = (tgt[0] > c) - (tgt[0] < c)
        dr = (tgt[1] > r) - (tgt[1] < r)
        moves = []
        if dc:
            moves.append((c + dc, r))
        if dr:
            moves.append((c, r + dr))
        if rng.random() < 0.2:  # occasional detour so it looks alive
            moves = [(c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)]
            moves = [m for m in moves if inside(*m) and m not in path[-3:]]
        nxt = rng.choice(moves) if moves else (c + dc, r + dr)
        path.append(nxt)
        pos = nxt

eat_step = {}
for i, p in enumerate(path):
    eat_step.setdefault(p, i)
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
    for i in range(SNAKE_LEN):
        values, times = [], []
        for s in range(total_steps):
            k = min(max(s - i, 0), len(path) - 1)
            x, y = xy(path[k])
            values.append(f"{x},{y}")
            times.append(f"{s / total_steps:.5f}")
        values.append(values[-1])
        times.append("1")
        size = CELL - i  # tail tapers
        pad = i / 2
        opacity = 1 - i * 0.12
        out.append(
            f'<rect width="{size}" height="{size}" x="{pad}" y="{pad}" rx="3" '
            f'fill="{theme["snake"]}" fill-opacity="{opacity:.2f}">'
            f'<animateTransform attributeName="transform" type="translate" '
            f'dur="{dur:.2f}s" repeatCount="indefinite" calcMode="linear" '
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
