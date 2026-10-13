"""Animated hero banner.

An original hooded fighter charges a fireball in his palm and launches it
across a perspective floor. It explodes and the name slams in as 3D extruded
lettering. Pure SVG + SMIL, so it animates inside a GitHub README.

Usage: python banner.py <out.svg>
"""
import math
import random
import sys

OUT = sys.argv[1]
NAME = "DILPREET SINGH DUA"
SUB = "SOLUTIONS ENGINEER"

W, H = 900, 280
HORIZON = 168
VP = (W / 2, HORIZON)
FLOOR_Y = 252                       # where the fighter stands
DUR = 8.0
T_FIRE, T_HIT = 1.7, 2.35
T_FADE = 7.3
PALM = (182, 138)
HIT = (530, 132)
FONT = "'Segoe UI Black','Arial Black','Segoe UI',Helvetica,Arial,sans-serif"

rng = random.Random(11)


def k(t):
    return f"{max(0.0, min(1.0, t / DUR)):.4f}"


def anim(attr, times, values, extra=""):
    return (f'<animate attributeName="{attr}" dur="{DUR}s" repeatCount="indefinite" '
            f'keyTimes="{";".join(k(t) for t in times)}" values="{";".join(map(str, values))}" {extra}/>')


def anim_tf(kind, times, values, extra=""):
    return (f'<animateTransform attributeName="transform" type="{kind}" dur="{DUR}s" '
            f'repeatCount="indefinite" keyTimes="{";".join(k(t) for t in times)}" '
            f'values="{";".join(values)}" {extra}/>')


def limb(a, b, wa, wb, fill="url(#skinLit)"):
    """Tapered capsule from point a to b."""
    (x1, y1), (x2, y2) = a, b
    ang = math.atan2(y2 - y1, x2 - x1) + math.pi / 2
    dx, dy = math.cos(ang), math.sin(ang)
    pts = [(x1 + dx * wa / 2, y1 + dy * wa / 2), (x2 + dx * wb / 2, y2 + dy * wb / 2),
           (x2 - dx * wb / 2, y2 - dy * wb / 2), (x1 - dx * wa / 2, y1 - dy * wa / 2)]
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"
    return (f'<path d="{d}" fill="{fill}"/>'
            f'<circle cx="{x1}" cy="{y1}" r="{wa/2:.1f}" fill="{fill}"/>'
            f'<circle cx="{x2}" cy="{y2}" r="{wb/2:.1f}" fill="{fill}"/>')


def rim(a, b, off=2.2):
    """Warm rim light along the side of a limb facing the fireball."""
    (x1, y1), (x2, y2) = a, b
    return (f'<line x1="{x1+off:.1f}" y1="{y1-off*0.4:.1f}" x2="{x2+off:.1f}" y2="{y2-off*0.4:.1f}" '
            f'stroke="url(#rimGrad)" stroke-width="1.6" stroke-linecap="round" class="rim"/>')


p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']

# ---------------------------------------------------------------- defs
p.append(f"""<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#04060b"/><stop offset="1" stop-color="#101826"/></linearGradient>
<linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#0a0f18"/><stop offset="1" stop-color="#151d2b"/></linearGradient>
<linearGradient id="gridFade" x1="0" y1="{HORIZON}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#2b3a52" stop-opacity="0"/><stop offset="1" stop-color="#34507a" stop-opacity="0.9"/></linearGradient>
<radialGradient id="vignette" cx="0.5" cy="0.5" r="0.75">
  <stop offset="0.6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.65"/></radialGradient>

<linearGradient id="skinLit" x1="30" y1="0" x2="200" y2="0" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#0d1118"/><stop offset="0.55" stop-color="#232a36"/>
  <stop offset="1" stop-color="#6a4a36"/></linearGradient>
<linearGradient id="clothLit" x1="20" y1="0" x2="190" y2="0" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#090c12"/><stop offset="0.6" stop-color="#1c2230"/>
  <stop offset="1" stop-color="#4e3a33"/></linearGradient>
<linearGradient id="cloak" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#05070b"/><stop offset="1" stop-color="#1a1f2b"/></linearGradient>
<linearGradient id="sash" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#7a2a0c"/><stop offset="1" stop-color="#ff8a3d"/></linearGradient>
<linearGradient id="rimGrad" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#ffd38a"/><stop offset="1" stop-color="#ff7a2e"/></linearGradient>

<radialGradient id="core"><stop offset="0" stop-color="#ffffff"/><stop offset="0.35" stop-color="#fff6c2"/>
  <stop offset="0.7" stop-color="#ffc23d"/><stop offset="1" stop-color="#ff8a1f" stop-opacity="0"/></radialGradient>
<radialGradient id="flame"><stop offset="0" stop-color="#ffb020"/><stop offset="0.55" stop-color="#ff5a1f"/>
  <stop offset="0.85" stop-color="#c81e1e" stop-opacity="0.6"/><stop offset="1" stop-color="#7a0f0f" stop-opacity="0"/></radialGradient>
<radialGradient id="halo"><stop offset="0" stop-color="#ff9a3d" stop-opacity="0.55"/>
  <stop offset="1" stop-color="#ff5a1f" stop-opacity="0"/></radialGradient>
<radialGradient id="floorLight"><stop offset="0" stop-color="#ff8a3d" stop-opacity="0.55"/>
  <stop offset="1" stop-color="#ff5a1f" stop-opacity="0"/></radialGradient>
<radialGradient id="flash"><stop offset="0" stop-color="#ffffff"/><stop offset="0.3" stop-color="#ffe08a" stop-opacity="0.9"/>
  <stop offset="0.65" stop-color="#ff6a1f" stop-opacity="0.45"/><stop offset="1" stop-color="#c81e1e" stop-opacity="0"/></radialGradient>
<linearGradient id="tail" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#c81e1e" stop-opacity="0"/><stop offset="0.6" stop-color="#ff5a1f" stop-opacity="0.75"/>
  <stop offset="1" stop-color="#ffd166"/></linearGradient>

<linearGradient id="face" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#ffffff"/><stop offset="0.5" stop-color="#ffe7b0"/><stop offset="1" stop-color="#ffb347"/></linearGradient>

<filter id="fire" x="-60%" y="-60%" width="220%" height="220%">
  <feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="3" result="n">
    <animate attributeName="baseFrequency" dur="0.9s" values="0.06;0.085;0.06" repeatCount="indefinite"/>
  </feTurbulence>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="16" xChannelSelector="R" yChannelSelector="G"/>
  <feGaussianBlur stdDeviation="0.6"/>
</filter>
<filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
  <feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="softGlow" x="-30%" y="-80%" width="160%" height="260%">
  <feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="blur6"><feGaussianBlur stdDeviation="6"/></filter>
<filter id="blur2"><feGaussianBlur stdDeviation="2"/></filter>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>
</defs>""")

p.append('<g clip-path="url(#frame)">')

# ---------------------------------------------------------------- scene
p.append(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
for _ in range(60):
    x, y = rng.uniform(0, W), rng.uniform(0, HORIZON - 6)
    p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(.4,1.3):.1f}" fill="#c9d1d9" '
             f'opacity="{rng.uniform(.1,.55):.2f}"/>')
p.append(f'<rect y="{HORIZON}" width="{W}" height="{H-HORIZON}" fill="url(#floor)"/>')

# perspective grid
grid = []
for i in range(-14, 15):
    xb = VP[0] + i * 95
    grid.append(f"M{VP[0]} {VP[1]} L{xb} {H}")
for j in range(1, 9):
    y = HORIZON + (H - HORIZON) * (j / 8) ** 1.9
    grid.append(f"M0 {y:.1f} L{W} {y:.1f}")
p.append(f'<path d="{" ".join(grid)}" stroke="url(#gridFade)" stroke-width="1" fill="none"/>')
p.append(f'<line x1="0" y1="{HORIZON}" x2="{W}" y2="{HORIZON}" stroke="#ff7a2e" stroke-opacity="0.25"/>')

# fireball light pool travelling across the floor
p.append(
    f'<ellipse cy="{FLOOR_Y+6}" rx="120" ry="16" fill="url(#floorLight)" opacity="0">'
    + anim("cx", [0, T_FIRE, T_HIT, DUR], [PALM[0], PALM[0], HIT[0], HIT[0]])
    + anim("opacity", [0, 0.4, T_FIRE, T_HIT, T_HIT + 0.6, DUR], [0, 0.7, 1, 1, 0, 0])
    + "</ellipse>"
)
# fireball contact shadow on the floor (grows smaller as it rises away)
p.append(
    f'<ellipse cy="{FLOOR_Y+4}" rx="26" ry="5" fill="#000" opacity="0" filter="url(#blur2)">'
    + anim("cx", [0, T_FIRE, T_HIT, DUR], [PALM[0] + 4, PALM[0] + 4, HIT[0], HIT[0]])
    + anim("opacity", [0, 0.6, T_FIRE, T_HIT, T_HIT + 0.05, DUR], [0, 0.35, 0.45, 0.35, 0, 0])
    + "</ellipse>"
)

# ---------------------------------------------------------------- fighter
FX = []
# ground shadow
FX.append(f'<ellipse cx="100" cy="{FLOOR_Y+2}" rx="78" ry="8" fill="#000" opacity="0.6" filter="url(#blur2)"/>')

fighter = []
# whole-body motion: breathing while charging, recoil on launch
fighter.append(anim_tf("translate", [0, 0.8, T_FIRE, T_FIRE + 0.08, T_FIRE + 0.6, DUR],
                       ["0,0", "0,2", "0,2", "-10,1", "0,0", "0,0"]))

# cloak flowing behind (drawn first, furthest back)
cloak_a = "M100 116 C80 122 62 152 50 190 C44 210 28 226 10 232 C30 216 36 200 42 182 C52 152 70 128 94 116 Z"
cloak_b = "M100 116 C78 126 58 156 46 192 C38 214 22 222 4 224 C26 212 34 196 40 180 C50 150 70 128 94 116 Z"
fighter.append(f'<path fill="url(#cloak)" d="{cloak_a}">'
               f'<animate attributeName="d" dur="0.9s" repeatCount="indefinite" values="{cloak_a};{cloak_b};{cloak_a}"/></path>')
# scarf tail
scarf_a = "M106 114 C92 110 76 116 56 108 C66 116 80 122 104 122 Z"
scarf_b = "M106 114 C90 116 74 106 52 112 C64 120 82 124 104 122 Z"
fighter.append(f'<path fill="url(#sash)" d="{scarf_a}">'
               f'<animate attributeName="d" dur="0.55s" repeatCount="indefinite" values="{scarf_a};{scarf_b};{scarf_a}"/></path>')

# back leg (extended behind)
hip_b, knee_b, ankle_b = (96, 178), (70, 212), (44, 244)
fighter.append(limb(hip_b, knee_b, 20, 15, "url(#clothLit)"))
fighter.append(limb(knee_b, ankle_b, 15, 11, "url(#clothLit)"))
fighter.append('<path d="M34 244 C38 238 50 238 54 244 L54 250 L30 252 Z" fill="#0b0e14"/>')

# back arm, chambered fist at the hip
sh_b, el_b, fist_b = (100, 124), (84, 150), (100, 166)
fighter.append(limb(sh_b, el_b, 12, 10))
fighter.append(limb(el_b, fist_b, 10, 9))
fighter.append(f'<circle cx="{fist_b[0]}" cy="{fist_b[1]}" r="6.5" fill="url(#skinLit)"/>')

# torso
fighter.append('<path d="M96 116 C108 110 122 113 126 123 C126 140 120 160 114 178 L90 180 '
               'C88 160 90 136 96 116 Z" fill="url(#clothLit)"/>')
fighter.append('<path d="M126 123 C126 140 120 160 114 178" stroke="url(#rimGrad)" stroke-width="1.6" fill="none" class="rim"/>')
# chest fold
fighter.append('<path d="M104 128 C110 140 112 152 110 168" stroke="#06080c" stroke-opacity="0.6" stroke-width="2" fill="none"/>')
# sash belt with knot
fighter.append('<path d="M89 170 L116 167 L115 177 L89 180 Z" fill="url(#sash)"/>')
fighter.append('<path d="M92 174 L80 186 L86 188 L96 177 Z" fill="#a8401a"/>')

# front leg (bent, forward)
hip_f, knee_f, ankle_f = (108, 178), (142, 202), (150, 244)
fighter.append(limb(hip_f, knee_f, 21, 16, "url(#clothLit)"))
fighter.append(limb(knee_f, ankle_f, 16, 12, "url(#clothLit)"))
fighter.append(rim(hip_f, knee_f, 8))
fighter.append(rim(knee_f, ankle_f, 6))
fighter.append('<path d="M140 244 C146 236 160 238 170 246 L170 251 L140 252 Z" fill="#0b0e14"/>')
fighter.append('<path d="M150 239 C158 239 166 242 170 246" stroke="url(#rimGrad)" stroke-width="1.2" fill="none" class="rim"/>')

# hood and head
fighter.append('<path d="M98 112 C88 100 92 80 108 74 C122 70 134 80 134 94 C134 106 126 114 114 116 '
               'C108 117 102 116 98 112 Z" fill="url(#clothLit)"/>')
fighter.append('<path d="M100 92 C90 96 86 106 84 116 L98 112 Z" fill="#090c12"/>')  # hood drape
fighter.append('<path d="M134 94 C134 106 126 114 114 116" stroke="url(#rimGrad)" stroke-width="1.6" fill="none" class="rim"/>')
fighter.append('<path d="M120 86 C130 86 134 96 131 106 C127 112 118 110 116 102 Z" fill="#05070a"/>')  # face shadow
eye = ('<path d="M122 95 L131 93 L131 96 L123 97 Z" fill="#ffd166" filter="url(#softGlow)">'
       + anim("opacity", [0, 0.5, T_FIRE, T_FIRE + 0.3, DUR], [0.6, 1, 1, 0.7, 0.6]) + "</path>")
fighter.append(eye)

# front arm extended, palm open toward the fireball (rotates on launch)
sh_f, el_f, wr_f = (118, 124), (148, 132), (172, 137)
arm = [anim_tf("rotate", [0, T_FIRE - 0.15, T_FIRE, T_FIRE + 0.6, DUR],
               [f"6 {sh_f[0]} {sh_f[1]}", f"8 {sh_f[0]} {sh_f[1]}", f"-6 {sh_f[0]} {sh_f[1]}",
                f"0 {sh_f[0]} {sh_f[1]}", f"0 {sh_f[0]} {sh_f[1]}"])]
arm.append(limb(sh_f, el_f, 13, 11))
arm.append(limb(el_f, wr_f, 11, 9))
arm.append(rim(sh_f, el_f, 0.5))
arm.append(rim(el_f, wr_f, 0.5))
# open palm with fingers
arm.append('<path d="M170 131 C176 128 182 130 183 134 L186 132 L188 135 L184 138 L187 140 L184 143 '
           'C180 145 172 144 168 140 Z" fill="url(#skinLit)"/>')
arm.append('<path d="M183 134 L186 132 L188 135 L184 138 L187 140" stroke="url(#rimGrad)" stroke-width="1" fill="none" class="rim"/>')
fighter.append("<g>" + "".join(arm) + "</g>")

FX.append("<g>" + "".join(fighter) + "</g>")
p.append("".join(FX))

# rim lights pulse with the fireball's brightness
p.insert(1, '<style>.rim{opacity:.9}</style>')

# ---------------------------------------------------------------- fireball
# charging sparks spiralling into the palm
for i in range(18):
    a = rng.uniform(0, 2 * math.pi)
    d = rng.uniform(34, 70)
    sx, sy = PALM[0] + 12 + math.cos(a) * d, PALM[1] + math.sin(a) * d
    t0 = rng.uniform(0.05, 1.1)
    t1 = min(t0 + 0.45, T_FIRE - 0.02)
    p.append(
        f'<circle r="{rng.uniform(1.2,2.4):.1f}" fill="#ffcf6b" opacity="0">'
        + anim("cx", [0, t0, t1, DUR], [round(sx), round(sx), PALM[0] + 12, PALM[0] + 12])
        + anim("cy", [0, t0, t1, DUR], [round(sy), round(sy), PALM[1], PALM[1]])
        + anim("opacity", [0, t0, t1 - 0.02, t1, DUR], [0, 1, 1, 0, 0])
        + "</circle>"
    )

BX = PALM[0] + 14   # ball sits just in front of the palm


def ball_motion():
    return (anim("cx", [0, T_FIRE, T_HIT, DUR], [BX, BX, HIT[0], HIT[0]])
            + anim("cy", [0, T_FIRE, (T_FIRE + T_HIT) / 2, T_HIT, DUR],
                   [PALM[1], PALM[1], PALM[1] - 10, HIT[1], HIT[1]]))


def ball_size(scale):
    rs = [0, 0.9 * scale, 0.75 * scale, 1.0 * scale, 0.9 * scale, 1.15 * scale, 0, 0]
    return anim("r", [0, 0.7, 0.95, 1.3, T_FIRE, T_HIT - 0.02, T_HIT + 0.02, DUR],
                [f"{r * 30:.1f}" for r in rs])


# flame tail streaming behind while in flight
p.append(
    f'<g filter="url(#fire)"><rect height="34" rx="17" fill="url(#tail)" opacity="0">'
    + anim("y", [0, T_FIRE, (T_FIRE + T_HIT) / 2, T_HIT, DUR],
           [PALM[1] - 17, PALM[1] - 17, PALM[1] - 27, HIT[1] - 17, HIT[1] - 17])
    + anim("x", [0, T_FIRE, T_HIT, DUR], [BX, BX, HIT[0] - 230, HIT[0] - 230])
    + anim("width", [0, T_FIRE, T_HIT, T_HIT + 0.1, DUR], [0, 0, 240, 0, 0])
    + anim("opacity", [0, T_FIRE, T_HIT, T_HIT + 0.1, DUR], [0, 1, 1, 0, 0])
    + "</rect></g>"
)
# halo, flame shell (turbulent), hot core
p.append('<circle r="0" fill="url(#halo)">' + ball_motion() + ball_size(2.2) + "</circle>")
p.append('<g filter="url(#fire)"><circle r="0" fill="url(#flame)">' + ball_motion() + ball_size(1.35)
         + "</circle></g>")
p.append('<circle r="0" fill="url(#core)" filter="url(#glow)">' + ball_motion() + ball_size(0.75)
         + '<animate attributeName="opacity" values="1;0.85;1;0.92;1" dur="0.25s" repeatCount="indefinite"/>'
         + "</circle>")

# ---------------------------------------------------------------- impact
p.append(f'<circle cx="{HIT[0]}" cy="{HIT[1]}" r="0" fill="url(#flash)">'
         + anim("r", [0, T_HIT, T_HIT + 0.4, DUR], [0, 0, 420, 420])
         + anim("opacity", [0, T_HIT, T_HIT + 0.05, T_HIT + 0.55, DUR], [0, 0, 1, 0, 0])
         + "</circle>")
# shockwave rings lying on the floor plane (flattened = perspective)
for i, (rmax, delay, sw) in enumerate([(380, 0, 3), (260, 0.12, 2), (170, 0.22, 1.5)]):
    p.append(f'<ellipse cx="{HIT[0]}" cy="{FLOOR_Y-6}" rx="0" ry="0" fill="none" stroke="#ff8a3d" stroke-width="{sw}">'
             + anim("rx", [0, T_HIT + delay, T_HIT + delay + 0.7, DUR], [0, 0, rmax, rmax])
             + anim("ry", [0, T_HIT + delay, T_HIT + delay + 0.7, DUR], [0, 0, rmax * 0.12, rmax * 0.12])
             + anim("opacity", [0, T_HIT + delay, T_HIT + delay + 0.7, DUR], [0, 0.9, 0, 0])
             + "</ellipse>")
# embers bursting outward
for i in range(30):
    a = rng.uniform(0, 2 * math.pi)
    d = rng.uniform(140, 330)
    ex, ey = HIT[0] + math.cos(a) * d, HIT[1] + math.sin(a) * d * 0.5 + 30
    p.append(f'<circle r="{rng.uniform(1.3,3.2):.1f}" fill="{rng.choice(["#ffd166","#ff9a3d","#fff1c1"])}" opacity="0">'
             + anim("cx", [0, T_HIT, T_HIT + 0.9, DUR], [HIT[0], HIT[0], round(ex), round(ex)])
             + anim("cy", [0, T_HIT, T_HIT + 0.9, DUR], [HIT[1], HIT[1], round(ey), round(ey)])
             + anim("opacity", [0, T_HIT, T_HIT + 0.05, T_HIT + 0.9, DUR], [0, 0, 1, 0, 0])
             + "</circle>")

# ---------------------------------------------------------------- 3D name
NX, NY = W / 2 + 80, 126
DEPTH = 9
name = []
name.append(anim_tf("translate", [0, T_HIT, T_HIT + 0.05, T_HIT + 0.1, T_HIT + 0.15, T_HIT + 0.2, DUR],
                    ["0,0", "0,0", "-7,4", "6,-3", "-3,1", "0,0", "0,0"]))
inner = [anim_tf("scale", [0, T_HIT, T_HIT + 0.22, T_HIT + 0.32, DUR], ["1.7", "1.7", "0.96", "1", "1"])]
text_attrs = (f'x="0" y="0" text-anchor="middle" font-family="{FONT}" font-size="48" '
              f'font-weight="900" letter-spacing="3"')
# extrusion: stacked copies stepping down-right, darkening with depth
for d in range(DEPTH, 0, -1):
    shade = int(40 + (DEPTH - d) * 9)
    col = f"rgb({min(255, shade + 70)},{shade // 2 + 10},{shade // 4})"
    inner.append(f'<text {text_attrs} transform="translate({d * 0.9:.1f} {d * 1.1:.1f})" fill="{col}">{NAME}</text>')
# soft shadow under the letters
inner.append(f'<text {text_attrs} transform="translate(8 16)" fill="#000" opacity="0.55" filter="url(#blur6)">{NAME}</text>')
# front face with bevel highlight
inner.append(f'<text {text_attrs} fill="url(#face)" stroke="#fff6dc" stroke-width="0.8" filter="url(#softGlow)">{NAME}</text>')
name.append(f'<g transform="translate({NX} {NY})"><g>' + "".join(inner) + "</g></g>")
p.append('<g opacity="0">'
         + anim("opacity", [0, T_HIT, T_HIT + 0.12, T_FADE, DUR - 0.15, DUR], [0, 0, 1, 1, 0, 0])
         + "<g>" + "".join(name) + "</g></g>")

# subtitle on a glowing underline
p.append(f'<g opacity="0">'
         + anim("opacity", [0, T_HIT + 0.55, T_HIT + 0.95, T_FADE, DUR - 0.15, DUR], [0, 0, 1, 1, 0, 0])
         + f'<line x1="{NX-150}" y1="{NY+34}" x2="{NX+150}" y2="{NY+34}" stroke="#ff8a3d" stroke-width="1.5" '
           f'opacity="0.7" filter="url(#softGlow)"/>'
         + f'<text x="{NX}" y="{NY+60}" text-anchor="middle" font-family="\'Segoe UI\',Helvetica,Arial,sans-serif" '
           f'font-size="16" font-weight="600" letter-spacing="9" fill="#c9d1d9">{SUB}</text></g>')

p.append(f'<rect width="{W}" height="{H}" fill="url(#vignette)"/>')
p.append("</g>")
p.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="#30363d"/>')
p.append("</svg>")

with open(OUT, "w") as f:
    f.write("\n".join(p))
print("ok")
