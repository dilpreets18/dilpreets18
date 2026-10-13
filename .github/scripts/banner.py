"""Animated hero banner: a fireball charges, flies across, and bursts into a name."""
import math
import random
import sys

OUT = sys.argv[1]
NAME = "DILPREET SINGH DUA"
SUB = "Solutions Engineer"

W, H = 860, 230
CX, CY = W / 2, 112
DUR = 7.0                    # loop length (s)
T_CHARGE, T_FIRE, T_HIT = 0.0, 1.3, 1.85
T_FADE = 6.4


def k(t):
    return f"{max(0, min(1, t / DUR)):.4f}"


def anim(attr, times, values, extra=""):
    return (f'<animate attributeName="{attr}" dur="{DUR}s" repeatCount="indefinite" '
            f'keyTimes="{";".join(k(t) for t in times)}" values="{";".join(map(str, values))}" {extra}/>')


rng = random.Random(7)
p = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
    "<defs>",
    '<radialGradient id="orb"><stop offset="0" stop-color="#ffffff"/>'
    '<stop offset="0.25" stop-color="#fff3b0"/><stop offset="0.5" stop-color="#ffb020"/>'
    '<stop offset="0.75" stop-color="#ff5a1f" stop-opacity="0.85"/><stop offset="1" stop-color="#c81e1e" stop-opacity="0"/></radialGradient>',
    '<radialGradient id="flash"><stop offset="0" stop-color="#ffffff"/>'
    '<stop offset="0.35" stop-color="#ffd166" stop-opacity="0.8"/><stop offset="0.7" stop-color="#ff5a1f" stop-opacity="0.4"/><stop offset="1" stop-color="#c81e1e" stop-opacity="0"/></radialGradient>',
    '<linearGradient id="trail" x1="0" x2="1"><stop offset="0" stop-color="#c81e1e" stop-opacity="0"/>'
    '<stop offset="0.6" stop-color="#ff5a1f" stop-opacity="0.7"/><stop offset="1" stop-color="#ffd166" stop-opacity="0.95"/></linearGradient>',
    '<linearGradient id="name" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#ffffff"/>'
    '<stop offset="1" stop-color="#ffb347"/></linearGradient>',
    '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4" result="b"/>'
    '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
    "</defs>",
    f'<rect width="{W}" height="{H}" rx="12" fill="#0d1117"/>',
]

# faint background stars
for _ in range(45):
    x, y, r = rng.uniform(10, W - 10), rng.uniform(10, H - 10), rng.uniform(0.5, 1.4)
    p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#8b949e" opacity="{rng.uniform(.15,.5):.2f}"/>')

START_X = 90
# charging particles converging on the orb
for i in range(14):
    a = rng.uniform(0, 2 * math.pi)
    d = rng.uniform(40, 70)
    sx, sy = START_X + math.cos(a) * d, CY + math.sin(a) * d
    t0 = rng.uniform(0.05, 0.6)
    p.append(
        f'<circle r="2" fill="#ffb020" opacity="0">'
        + anim("cx", [0, t0, T_FIRE, DUR], [sx, sx, START_X, START_X])
        + anim("cy", [0, t0, T_FIRE, DUR], [sy, sy, CY, CY])
        + anim("opacity", [0, t0, T_FIRE - 0.05, T_FIRE, DUR], [0, 1, 1, 0, 0])
        + "</circle>"
    )

# trail behind the flying orb
p.append(
    f'<rect y="{CY-9}" height="18" rx="9" fill="url(#trail)" opacity="0">'
    + anim("x", [0, T_FIRE, T_HIT, DUR], [START_X, START_X, CX - 260, CX - 260])
    + anim("width", [0, T_FIRE, T_HIT, T_HIT + 0.15, DUR], [0, 0, 260, 0, 0])
    + anim("opacity", [0, T_FIRE, T_HIT, T_HIT + 0.15, DUR], [0, 0.9, 0.9, 0, 0])
    + "</rect>"
)

# the orb: grows while charging, flies to centre, vanishes on impact
p.append(
    f'<circle r="0" fill="url(#orb)" filter="url(#glow)">'
    + anim("cx", [0, T_FIRE, T_HIT, DUR], [START_X, START_X, CX, CX])
    + anim("cy", [0, DUR], [CY, CY])
    + anim("r", [0, 0.9, 1.05, 1.15, T_FIRE, T_HIT, T_HIT + 0.05, DUR],
           [0, 26, 22, 28, 26, 22, 0, 0])
    + '<animate attributeName="opacity" values="1;0.85;1;0.9;1" dur="0.3s" repeatCount="indefinite"/>'
    + "</circle>"
)

# impact flash and shockwave rings
p.append(
    f'<circle cx="{CX}" cy="{CY}" r="0" fill="url(#flash)">'
    + anim("r", [0, T_HIT, T_HIT + 0.35, DUR], [0, 0, 260, 260])
    + anim("opacity", [0, T_HIT, T_HIT + 0.05, T_HIT + 0.45, DUR], [0, 0, 1, 0, 0])
    + "</circle>"
)
for i, (rmax, delay) in enumerate([(300, 0), (220, 0.12)]):
    p.append(
        f'<ellipse cx="{CX}" cy="{CY}" rx="0" ry="0" fill="none" stroke="#ff8a3d" stroke-width="{3-i}">'
        + anim("rx", [0, T_HIT + delay, T_HIT + delay + 0.6, DUR], [0, 0, rmax, rmax])
        + anim("ry", [0, T_HIT + delay, T_HIT + delay + 0.6, DUR], [0, 0, rmax * 0.35, rmax * 0.35])
        + anim("opacity", [0, T_HIT + delay, T_HIT + delay + 0.6, DUR], [0, 1, 0, 0])
        + "</ellipse>"
    )

# sparks flying outward
for i in range(22):
    a = 2 * math.pi * i / 22 + rng.uniform(-0.1, 0.1)
    d = rng.uniform(120, 260)
    ex, ey = CX + math.cos(a) * d, CY + math.sin(a) * d * 0.55
    p.append(
        f'<circle r="{rng.uniform(1.5,3):.1f}" fill="#ffd166" opacity="0">'
        + anim("cx", [0, T_HIT, T_HIT + 0.7, DUR], [CX, CX, round(ex), round(ex)])
        + anim("cy", [0, T_HIT, T_HIT + 0.7, DUR], [CY, CY, round(ey), round(ey)])
        + anim("opacity", [0, T_HIT, T_HIT + 0.05, T_HIT + 0.7, DUR], [0, 0, 1, 0, 0])
        + "</circle>"
    )

# name slams in with a small shake, then holds and fades for the loop
shake = [0, T_HIT, T_HIT + 0.05, T_HIT + 0.1, T_HIT + 0.15, T_HIT + 0.2, DUR]
p.append(
    '<g><animateTransform attributeName="transform" type="translate" '
    f'dur="{DUR}s" repeatCount="indefinite" keyTimes="{";".join(k(t) for t in shake)}" '
    'values="0,0;0,0;-6,3;5,-2;-3,1;0,0;0,0"/>'
    f'<g transform="translate({CX} {CY + 14})"><g>'
    '<animateTransform attributeName="transform" type="scale" '
    f'dur="{DUR}s" repeatCount="indefinite" keyTimes="{k(0)};{k(T_HIT)};{k(T_HIT+0.25)};1" '
    'values="1.6;1.6;1;1"/>'
    f'<text x="0" y="0" text-anchor="middle" font-family="\'Segoe UI\',Helvetica,Arial,sans-serif" '
    f'font-size="46" font-weight="800" letter-spacing="4" fill="url(#name)" filter="url(#glow)" opacity="0">{NAME}'
    + anim("opacity", [0, T_HIT, T_HIT + 0.15, T_FADE, DUR - 0.1, DUR], [0, 0, 1, 1, 0, 0])
    + "</text></g></g></g>"
)

# subtitle
p.append(
    f'<text x="{CX}" y="{CY + 56}" text-anchor="middle" font-family="\'Segoe UI\',Helvetica,Arial,sans-serif" '
    f'font-size="18" letter-spacing="6" fill="#8b949e" opacity="0">{SUB.upper()}'
    + anim("opacity", [0, T_HIT + 0.5, T_HIT + 0.9, T_FADE, DUR - 0.1, DUR], [0, 0, 1, 1, 0, 0])
    + "</text>"
)

p.append("</svg>")
with open(OUT, "w") as f:
    f.write("\n".join(p))
print("ok")
