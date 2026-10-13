"""Render the animated hero banner as an animated WebP.

An original hooded fighter charges a fireball, launches it across a
perspective floor, it explodes, and the name rises from the blast as burning
3D letters. Everything is procedural: noise-driven fire, particle sparks and
smoke, dynamic lighting from the fireball, bloom and camera shake.

Usage: python banner_render.py <out.webp>
Requires: numpy, scipy, pillow
"""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

OUT = sys.argv[1]
NAME = "DILPREET SINGH DUA"
SUB = "SOLUTIONS  ENGINEER"
FONT_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"

W, H = 900, 280
SS = 3                     # supersampling for crisp shapes
FPS = 20
DUR = 7.0
NF = int(DUR * FPS)
HORIZON = 150
FLOOR = 258
T_FIRE, T_HIT = 1.5, 2.1
T_NAME = 2.25
T_FADE0, T_FADE1 = 6.15, 6.9
HIT = np.array([590.0, 124.0])

rng = np.random.default_rng(42)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


# ------------------------------------------------------------------ helpers
def smooth_noise(h, w, scale, octaves=4, seed=0):
    """Perfectly tileable fractal noise (FFT-filtered white noise), range 0..1."""
    r = np.random.default_rng(seed)
    white = r.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1
    cutoff = 1.0 / scale
    spectrum = 1.0 / (f ** 1.6) * np.exp(-(f / (cutoff * 2 ** octaves)) ** 2)
    spectrum[f < cutoff * 0.25] *= 0.3
    out = np.real(np.fft.ifft2(np.fft.fft2(white) * spectrum)).astype(np.float32)
    return (out - out.min()) / (out.max() - out.min())


NOISE = smooth_noise(256, 256, 64, 5, 1)          # tiling-ish noise texture
NOISE2 = smooth_noise(256, 256, 32, 4, 2)
FOLDS = ndi.zoom(smooth_noise(H // 4, W, 10, 3, 5), (4, 1), order=1, mode="grid-wrap")  # stretched = cloth folds


def sample(noise, u, v):
    return ndi.map_coordinates(noise, [v % 256, u % 256], order=1, mode="wrap")


HEAT_STOPS = np.array([
    [0.00, 0.00, 0.00, 0.00],
    [0.18, 0.35, 0.02, 0.01],
    [0.38, 1.10, 0.18, 0.02],
    [0.58, 1.60, 0.55, 0.06],
    [0.78, 2.00, 1.20, 0.30],
    [1.00, 2.60, 2.30, 1.80],
], np.float32)


def heat(t):
    """Map temperature 0..1+ to HDR fire colour."""
    t = np.clip(t, 0, 1.2)
    out = np.zeros(t.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(t, HEAT_STOPS[:, 0], HEAT_STOPS[:, c + 1])
    return out * np.clip(t / 1.0, 1, 1.2)[..., None]


def blur(img, s):
    if img.ndim == 3:
        return np.stack([ndi.gaussian_filter(img[..., c], s) for c in range(img.shape[2])], -1)
    return ndi.gaussian_filter(img, s)


def cubic(p0, p1, p2, p3, n=14):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def path_points(d):
    """Tiny SVG path parser for absolute M/L/C/Z."""
    import re
    toks = re.findall(r"[MLCZ]|-?\d*\.?\d+", d)
    pts, i, cur, cmd = [], 0, None, None
    while i < len(toks):
        if toks[i] in "MLCZ":
            cmd = toks[i]
            i += 1
            if cmd == "Z":
                continue
        if cmd in ("M", "L"):
            cur = np.array([float(toks[i]), float(toks[i + 1])])
            pts.append(cur)
            i += 2
        elif cmd == "C":
            p1 = np.array([float(toks[i]), float(toks[i + 1])])
            p2 = np.array([float(toks[i + 2]), float(toks[i + 3])])
            p3 = np.array([float(toks[i + 4]), float(toks[i + 5])])
            pts.extend(cubic(cur, p1, p2, p3)[1:])
            cur = p3
            i += 6
    return np.array(pts)


def tf(pts):
    """Fighter design space -> banner space (scale up, stand on the floor)."""
    pts = np.asarray(pts, np.float32)
    return np.stack([18 + pts[..., 0] * 1.22, FLOOR - (252 - pts[..., 1]) * 1.22], -1)


def rot(pts, c, deg):
    a = math.radians(deg)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]], np.float32)
    return (np.asarray(pts) - c) @ R.T + c


def raster(polys=(), circles=(), lines=()):
    im = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(im)
    for poly in polys:
        d.polygon([(float(x) * SS, float(y) * SS) for x, y in poly], fill=255)
    for (cx, cy, r) in circles:
        d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=255)
    for (a, b, w) in lines:
        d.line([(a[0] * SS, a[1] * SS), (b[0] * SS, b[1] * SS)], fill=255, width=max(1, int(w * SS)))
    im = im.resize((W, H), Image.BOX)
    return np.asarray(im, np.float32) / 255.0


def capsule(a, b, wa, wb):
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    v = b - a
    n = np.array([-v[1], v[0]]) / (np.linalg.norm(v) + 1e-6)
    poly = [a + n * wa / 2, b + n * wb / 2, b - n * wb / 2, a - n * wa / 2]
    return poly, [(a[0], a[1], wa / 2), (b[0], b[1], wb / 2)]


def over(dst_rgb, src_rgb, alpha):
    return dst_rgb * (1 - alpha[..., None]) + src_rgb * alpha[..., None]


def splat(buf, x, y, r, color, sharp=1.0):
    """Additive gaussian blob."""
    x0, x1 = int(max(0, x - 3 * r)), int(min(W, x + 3 * r + 1))
    y0, y1 = int(max(0, y - 3 * r)), int(min(H, y + 3 * r + 1))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * (r * sharp) ** 2))
    buf[y0:y1, x0:x1] += g[..., None] * np.asarray(color, np.float32)


def splat_alpha(rgb, x, y, r, color, a):
    x0, x1 = int(max(0, x - 3.6 * r)), int(min(W, x + 3.6 * r + 1))
    y0, y1 = int(max(0, y - 3.6 * r)), int(min(H, y + 3.6 * r + 1))
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * r * r)) * a
    rgb[y0:y1, x0:x1] = rgb[y0:y1, x0:x1] * (1 - g[..., None]) + np.asarray(color) * g[..., None]


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ static scene
sky = np.zeros((H, W, 3), np.float32)
g = np.clip(YY / HORIZON, 0, 1)[..., None]
sky[:] = (1 - g) * np.array([0.008, 0.010, 0.022]) + g * np.array([0.03, 0.035, 0.07])
floor_mask = (YY >= HORIZON).astype(np.float32)
fg = np.clip((YY - HORIZON) / (H - HORIZON), 0, 1)[..., None]
sky = sky * (1 - floor_mask[..., None]) + floor_mask[..., None] * (
    (1 - fg) * np.array([0.02, 0.025, 0.045]) + fg * np.array([0.035, 0.045, 0.075]))
# horizon haze
sky += np.exp(-((YY - HORIZON) / 10) ** 2)[..., None] * np.array([0.06, 0.04, 0.05])

# perspective grid
vp = (W / 2, HORIZON)
lines = []
for i in range(-16, 17):
    lines.append(((vp[0], vp[1]), (vp[0] + i * 90, H + 40), 1.0))
for j in range(1, 10):
    y = HORIZON + (H - HORIZON) * (j / 9) ** 2.1
    lines.append(((0, y), (W, y), 1.0))
grid = raster(lines=lines) * floor_mask * np.clip((YY - HORIZON) / 60, 0, 1)
GRID_COL = np.array([0.10, 0.18, 0.34], np.float32)

stars_xy = rng.uniform([0, 0], [W, HORIZON - 8], (90, 2))
stars_b = rng.uniform(0.15, 0.9, 90)
stars_ph = rng.uniform(0, 2 * math.pi, 90)

# ------------------------------------------------------------------ fighter geometry (design space)
CLOAK_A = "M100 116 C80 122 62 152 50 190 C44 210 28 226 10 232 C30 216 36 200 42 182 C52 152 70 128 94 116 Z"
CLOAK_B = "M100 116 C78 126 58 156 46 192 C38 214 22 222 4 224 C26 212 34 196 40 180 C50 150 70 128 94 116 Z"
SCARF_A = "M106 114 C92 110 76 116 56 108 C66 116 80 122 104 122 Z"
SCARF_B = "M106 114 C90 116 74 106 52 112 C64 120 82 124 104 122 Z"
TORSO = "M96 116 C108 110 122 113 126 123 C126 140 120 160 114 178 L90 180 C88 160 90 136 96 116 Z"
HOOD = "M98 112 C88 100 92 80 108 74 C122 70 134 80 134 94 C134 106 126 114 114 116 C108 117 102 116 98 112 Z"
HOOD_DRAPE = "M100 92 C90 96 86 106 84 116 L98 112 Z"
FACE = "M120 86 C130 86 134 96 131 106 C127 112 118 110 116 102 Z"
SASH = "M89 170 L116 167 L115 177 L89 180 Z"
KNOT = "M92 174 L80 186 L86 188 L96 177 Z"
BOOT_B = "M34 244 C38 238 50 238 54 244 L54 250 L30 252 Z"
BOOT_F = "M140 244 C146 236 160 238 170 246 L170 251 L140 252 Z"
PALM = "M170 131 C176 128 182 130 183 134 L186 132 L188 135 L184 138 L187 140 L184 143 C180 145 172 144 168 140 Z"
SH_F = np.array([118.0, 124.0])

PALM_POS = tf([186, 136])
BALL0 = PALM_POS + np.array([20.0, -1.0])


def lerp_path(a, b, u):
    pa, pb = path_points(a), path_points(b)
    return pa * (1 - u) + pb * u


def fighter_layers(t):
    """Return list of (mask, albedo, emissive) layers back-to-front, plus offset."""
    # body motion
    if t < T_FIRE:
        off = np.array([0.0, 2.0 * smoothstep(0, 0.8, t) + 0.6 * math.sin(t * 9)])
        arm_deg = 7 + 1.5 * math.sin(t * 14) * smoothstep(0.6, 1.4, t)
    else:
        u = t - T_FIRE
        off = np.array([-11.0 * math.exp(-u * 7) * min(1, u * 25), 1.0 * math.exp(-u * 5)])
        arm_deg = -8 * math.exp(-u * 5) * min(1, u * 25) if u < 0.6 else 0
    flutter = 0.5 + 0.5 * math.sin(t * 2 * math.pi / 0.9)
    sflutter = 0.5 + 0.5 * math.sin(t * 2 * math.pi / 0.55)

    def T(p):
        return tf(p) + off

    cloth = np.array([0.075, 0.085, 0.11])
    dark = np.array([0.045, 0.055, 0.085])
    glove = np.array([0.11, 0.085, 0.075])
    sash = np.array([0.85, 0.28, 0.06])

    layers = []
    layers.append((raster(polys=[T(lerp_path(CLOAK_A, CLOAK_B, flutter))]), dark, 0.0))
    layers.append((raster(polys=[T(lerp_path(SCARF_A, SCARF_B, sflutter))]), sash, 0.15))
    # back leg + boot
    p1, c1 = capsule(T([96, 178]), T([70, 212]), 24, 18)
    p2, c2 = capsule(T([70, 212]), T([44, 244]), 18, 13)
    layers.append((raster(polys=[p1, p2, T(path_points(BOOT_B))], circles=c1 + c2), cloth * 0.8, 0.0))
    # back arm chambered
    p1, c1 = capsule(T([100, 124]), T([84, 150]), 14, 12)
    p2, c2 = capsule(T([84, 150]), T([100, 166]), 12, 11)
    fist = T([100, 166])
    layers.append((raster(polys=[p1, p2], circles=c1 + c2 + [(fist[0], fist[1], 8.5)]), glove, 0.0))
    # torso, hood
    layers.append((raster(polys=[T(path_points(TORSO))]), cloth, 0.0))
    layers.append((raster(polys=[T(path_points(SASH)), T(path_points(KNOT))]), sash, 0.12))
    # front leg + boot
    p1, c1 = capsule(T([108, 178]), T([142, 202]), 25, 19)
    p2, c2 = capsule(T([142, 202]), T([150, 244]), 19, 14)
    layers.append((raster(polys=[p1, p2, T(path_points(BOOT_F))], circles=c1 + c2), cloth * 0.95, 0.0))
    layers.append((raster(polys=[T(path_points(HOOD)), T(path_points(HOOD_DRAPE))]), cloth * 1.05, 0.0))
    layers.append((raster(polys=[T(path_points(FACE))]), np.array([0.005, 0.006, 0.01]), 0.0))
    # front arm (rotates about shoulder)
    def R(p):
        return T(rot(np.asarray(p, np.float32), SH_F, arm_deg))
    p1, c1 = capsule(R([118, 124]), R([148, 132]), 15, 13)
    p2, c2 = capsule(R([148, 132]), R([172, 137]), 13, 11)
    layers.append((raster(polys=[p1, p2, R(path_points(PALM))], circles=c1 + c2), glove, 0.0))
    eye = T(np.array([[122, 95], [131, 93], [131, 96], [123, 97]]))
    return layers, eye, off


def shade_layer(mask, albedo, emissive, lights, ambient_dir=np.array([-0.6, -0.8])):
    """Lambert + rim lighting using normals estimated from the layer mask."""
    soft = ndi.gaussian_filter(mask, 2.2)
    gy, gx = np.gradient(soft)
    nx, ny = -gx, -gy
    nl = np.sqrt(nx * nx + ny * ny) + 1e-4
    edge = np.clip(nl * 6, 0, 1)
    nx, ny = nx / nl * edge, ny / nl * edge
    col = np.zeros((H, W, 3), np.float32)
    folds = 0.72 + 0.56 * FOLDS
    albedo = albedo[None, None, :] * folds[..., None]
    # cool moonlight ambient
    amb = 0.55 + 0.45 * np.clip(nx * ambient_dir[0] + ny * ambient_dir[1], 0, 1)
    col += albedo * amb[..., None] * np.array([0.55, 0.65, 0.95]) * 0.9
    for (lx, ly, inten, lcol, rad) in lights:
        dx, dy = lx - XX, ly - YY
        d = np.sqrt(dx * dx + dy * dy) + 1e-3
        fall = inten / (1 + (d / rad) ** 2)
        facing = np.clip((nx * dx + ny * dy) / d, 0, 1)
        col += (albedo * 0.6 + 0.4 * folds[..., None]) * (fall * (0.25 + 1.6 * facing ** 1.5))[..., None] * lcol * 0.9
    col += albedo * emissive * 2.0
    return col


# ------------------------------------------------------------------ name masks
fb = ImageFont.truetype(FONT_BLACK, 47 * SS)
fs = ImageFont.truetype(FONT_SEMI, 15 * SS)


def text_mask(text, font, cx, cy, spacing=0):
    im = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(im)
    # manual letter spacing
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * SS * (len(text) - 1)
    x = cx * SS - total / 2
    asc, desc = font.getmetrics()
    y = cy * SS - (asc + desc) / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=font, fill=255)
        x += w + spacing * SS
    return np.asarray(im.resize((W, H), Image.BOX), np.float32) / 255.0


NAME_C = (585, 116)
face = text_mask(NAME, fb, *NAME_C, spacing=2)
extr = np.zeros_like(face)
EXT_N = 9
side_layers = []
for dpx in range(EXT_N, 0, -1):
    m = ndi.shift(face, (dpx * 0.75, dpx * 0.45), order=1)
    side_layers.append((dpx, m))
extr = np.max([m for _, m in side_layers], axis=0)
sub = text_mask(SUB, fs, NAME_C[0], NAME_C[1] + 50, spacing=7)
# top edges of letters feed the flames
face_top = np.clip(face - ndi.shift(face, (3, 0), order=1), 0, 1)
face_grad_y = np.clip((YY - (NAME_C[1] - 32)) / 64, 0, 1)

# ------------------------------------------------------------------ particles
class P:
    __slots__ = ("x", "y", "vx", "vy", "life", "age", "r", "kind", "heat")

    def __init__(self, x, y, vx, vy, life, r, kind, heat=1.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.age, self.r, self.kind, self.heat = life, 0.0, r, kind, heat


particles = []
fire_buf = np.zeros((H, W), np.float32)
DT = 1.0 / FPS
frames = []

ball_path = lambda u: BALL0 * (1 - u) + HIT * u + np.array([0, -26 * 4 * u * (1 - u)])

# run one warm-up cycle so the loop is seamless for the lingering effects
for cycle in range(1):
    particles.clear()
    fire_buf[:] = 0
    for f in range(NF):
        t = f / FPS
        rec = True
        emis = np.zeros((H, W, 3), np.float32)         # additive light / fire
        lights = []

        # ---------------- fireball state
        ball = None
        if t < T_FIRE:
            grow = smoothstep(0.05, 1.3, t)
            ball = (BALL0[0], BALL0[1], 6 + 20 * grow + 2.5 * math.sin(t * 23), 0.6 + 0.6 * grow)
        elif t < T_HIT:
            u = (t - T_FIRE) / (T_HIT - T_FIRE)
            u = u * u * (1.6 - 0.6 * u)
            pos = ball_path(u)
            ball = (pos[0], pos[1], 26 + 4 * math.sin(t * 30), 1.25)

        if ball is not None:
            bx, by, br, bi = ball
            lights.append((bx, by, 1.5 * bi, np.array([1.0, 0.55, 0.2]), 90))
            # procedural fire sphere
            dx, dy = XX - bx, YY - by
            d = np.sqrt(dx * dx + dy * dy)
            sel = d < br * 2.6
            ang = np.arctan2(dy[sel], dx[sel])
            n = sample(NOISE, ang * 40 + 128, d[sel] * 0.9 - t * 90)
            n2 = sample(NOISE2, XX[sel] * 1.5 - t * 60, YY[sel] * 1.5 + t * 120)
            moving = t >= T_FIRE
            # flames lick backwards (left) while flying, upward while charging
            dirx = -1.0 if moving else 0.0
            diry = 0.0 if moving else -1.0
            stretch = 1 + 0.9 * np.clip((dx[sel] * dirx + dy[sel] * diry) / (d[sel] + 1e-3), 0, 1)
            radius = br * stretch * (0.75 + 0.6 * n) * (0.9 + 0.25 * n2)
            temp = np.clip(1.15 - d[sel] / radius, 0, None) * 1.25 * bi
            temp = np.clip(temp + np.exp(-(d[sel] / (br * 0.45)) ** 2) * 0.9 * bi, 0, 1.25)
            col = heat(temp)
            emis[sel] += col
            # halo
            emis += (np.exp(-(d / (br * 2.8)) ** 2) * 0.35 * bi)[..., None] * np.array([1.0, 0.45, 0.12])
            # emit particles
            if moving:
                for _ in range(10):
                    particles.append(P(bx + rng.normal(0, 6), by + rng.normal(0, 8),
                                       rng.uniform(-180, -40), rng.normal(-30, 40),
                                       rng.uniform(0.25, 0.6), rng.uniform(5, 11), "flame"))
                for _ in range(2):
                    particles.append(P(bx - 10, by + rng.normal(0, 8), rng.uniform(-60, -10),
                                       rng.uniform(-50, -15), rng.uniform(0.8, 1.6), rng.uniform(5, 9), "smoke"))
            else:
                if t > 0.15:
                    for _ in range(3):
                        a = rng.uniform(0, 2 * math.pi)
                        rr = rng.uniform(40, 80)
                        sx, sy = bx + math.cos(a) * rr, by + math.sin(a) * rr
                        particles.append(P(sx, sy, (bx - sx) * 2.4, (by - sy) * 2.4, 0.4, 1.3, "inspark"))
                for _ in range(2):
                    particles.append(P(bx + rng.normal(0, 5), by - br * 0.5, rng.normal(0, 15),
                                       rng.uniform(-90, -50), rng.uniform(0.2, 0.4), rng.uniform(4, 7), "flame"))

        # ---------------- explosion
        te = t - T_HIT
        shake = np.zeros(2)
        if te >= 0:
            if te < DT * 1.01:
                for _ in range(95):
                    a = rng.uniform(0, 2 * math.pi)
                    sp = rng.uniform(150, 720)
                    particles.append(P(HIT[0], HIT[1], math.cos(a) * sp, math.sin(a) * sp * 0.75 - 60,
                                       rng.uniform(0.5, 1.4), rng.uniform(0.9, 2.0), "spark"))
                for _ in range(45):
                    a = rng.uniform(0, 2 * math.pi)
                    sp = rng.uniform(30, 160)
                    particles.append(P(HIT[0] + math.cos(a) * 20, HIT[1] + math.sin(a) * 14,
                                       math.cos(a) * sp, math.sin(a) * sp * 0.6 - 40,
                                       rng.uniform(1.6, 3.2), rng.uniform(14, 26), "smoke"))
            # fireball volume
            if te < 1.4:
                R = 250 * (1 - math.exp(-te * 6))
                hs = max(0.0, 1.55 * math.exp(-te * 2.2) - 0.15)
                dx, dy = XX - HIT[0], (YY - HIT[1]) * 1.25
                d = np.sqrt(dx * dx + dy * dy)
                sel = d < R * 1.5 + 2
                if sel.any() and hs > 0:
                    n = sample(NOISE, XX[sel] * 0.9 + 37, YY[sel] * 0.9 + te * 140)
                    n2 = sample(NOISE2, XX[sel] * 2.2, YY[sel] * 2.2 + te * 260)
                    rr = R * (0.55 + 0.65 * n) * (0.85 + 0.3 * n2)
                    temp = np.clip(1 - d[sel] / (rr + 1e-3), 0, 1) ** 0.8 * hs
                    # hollow out as it burns (ring of fire)
                    temp *= 1 - 0.55 * smoothstep(0.25, 1.0, te) * np.clip(1 - d[sel] / (R * 0.6), 0, 1)
                    emis[sel] += heat(temp) * 1.35
                lights.append((HIT[0], HIT[1], 3.0 * math.exp(-te * 3.5), np.array([1.0, 0.6, 0.25]), 260))
                # shockwave ring on the floor plane + in the air
                sr = 700 * te
                ring = np.exp(-((np.sqrt((XX - HIT[0]) ** 2 + ((YY - HIT[1]) * 1.6) ** 2) - sr) / 6) ** 2)
                emis += (ring * 0.9 * math.exp(-te * 5))[..., None] * np.array([1.0, 0.8, 0.55])
                fr = 520 * te
                fring = np.exp(-((np.sqrt((XX - HIT[0]) ** 2 + ((YY - (FLOOR - 4)) * 7) ** 2) - fr) / 5) ** 2) * floor_mask
                emis += (fring * 1.2 * math.exp(-te * 3.5))[..., None] * np.array([1.0, 0.5, 0.15])
                # flash
                fl = np.exp(-np.sqrt((XX - HIT[0]) ** 2 + (YY - HIT[1]) ** 2) / 260)
                emis += (fl * math.exp(-te * 12) * 1.3)[..., None] * np.array([1.0, 0.8, 0.55])
                shake = rng.normal(0, 7 * math.exp(-te * 8), 2)
            # scorch glow lingering on the floor
            scorch = np.exp(-(((XX - HIT[0]) / 170) ** 2 + ((YY - (FLOOR - 2)) / 12) ** 2)) * floor_mask
            emis += (scorch * 0.5 * math.exp(-te * 0.6))[..., None] * np.array([1.0, 0.35, 0.08])

        # ---------------- name burning
        reveal = np.zeros((H, W), np.float32)
        fade = 1 - smoothstep(T_FADE0, T_FADE1, t)
        if t >= T_NAME:
            rr = (t - T_NAME) * 700
            dn = np.sqrt((XX - HIT[0]) ** 2 + ((YY - HIT[1]) * 2.2) ** 2)
            edge_noise = sample(NOISE2, XX * 3, YY * 3) * 60
            reveal = np.clip((rr - dn + edge_noise) / 25, 0, 1)
        live = reveal * fade
        # flame simulation rising off the letters
        src = (face_top * 1.15 + face * 0.32) * live
        src *= rng.uniform(0.55, 1.25, (H, W)).astype(np.float32)
        wob = sample(NOISE2, XX * 2 + t * 40, YY * 2 + t * 200) - 0.5
        fire_buf = ndi.shift(fire_buf, (-2.2, 0), order=1, mode="constant")
        fire_buf = ndi.map_coordinates(fire_buf, [YY, XX + wob * 2.4], order=1, mode="constant")
        fire_buf = ndi.gaussian_filter(fire_buf, (0.7, 0.9))
        cool = 0.865 + 0.09 * sample(NOISE, XX * 4, YY * 4 + t * 300)
        fire_buf = np.maximum(fire_buf * cool, src)

        # ---------------- update + draw particles
        smoke_layer = []
        alive = []
        for p in particles:
            p.age += DT
            if p.age >= p.life:
                continue
            k = p.age / p.life
            if p.kind == "spark":
                p.vx *= 0.93
                p.vy = p.vy * 0.93 + 520 * DT
                if p.y > FLOOR + 6 and p.vy > 0:
                    p.vy *= -0.35
                    p.vx *= 0.6
            elif p.kind == "flame":
                p.vx *= 0.9
                p.vy -= 160 * DT
            elif p.kind == "smoke":
                p.vx *= 0.96
                p.vy = p.vy * 0.97 - 22 * DT
                p.r += 18 * DT
            elif p.kind == "inspark":
                pass
            p.x += p.vx * DT
            p.y += p.vy * DT
            alive.append(p)
            if p.kind == "spark":
                hcol = heat(np.array(1.05 - 0.75 * k))
                for s in range(9):  # continuous motion streak
                    splat(emis, p.x - p.vx * DT * s * 0.07, p.y - p.vy * DT * s * 0.07,
                          p.r, hcol * (1 - s * 0.09) * 0.45)
            elif p.kind == "flame":
                hcol = heat(np.array(max(0.0, 1.0 - k * 1.1)))
                splat(emis, p.x, p.y, p.r * (1 - 0.4 * k), hcol * 0.6)
            elif p.kind == "inspark":
                splat(emis, p.x, p.y, 1.6, np.array([2.0, 1.4, 0.6]) * (0.4 + k))
            elif p.kind == "smoke":
                smoke_layer.append(p)
        particles[:] = alive

        if not rec:
            continue

        # ---------------- compose
        img = sky.copy()
        tw = 0.6 + 0.4 * np.sin(t * 3 + stars_ph)
        for (sx, sy), b, w in zip(stars_xy, stars_b, tw):
            xi, yi = int(sx), int(sy)
            img[yi, xi] += b * w * 0.6

        # light map for floor/grid
        lightmap = np.zeros((H, W, 3), np.float32)
        for (lx, ly, inten, lcol, rad) in lights:
            dd = np.sqrt((XX - lx) ** 2 + ((YY - ly) * 0.8) ** 2)
            lightmap += (inten / (1 + (dd / rad) ** 2))[..., None] * lcol
        img += (grid[..., None] * (GRID_COL + lightmap * 0.55)) * 0.9
        img += floor_mask[..., None] * lightmap * 0.12

        # fighter
        layers, eye, off = fighter_layers(t)
        fmask = np.zeros((H, W), np.float32)
        for m, alb, em in layers:
            fmask = np.maximum(fmask, m)
        # contact shadow
        sh = np.exp(-(((XX - (tf([100, 0])[0] + off[0])) / 95) ** 2 + ((YY - FLOOR - 1) / 5) ** 2))
        img *= (1 - 0.75 * sh)[..., None]
        if ball is not None:
            bsh = np.exp(-(((XX - ball[0]) / 30) ** 2 + ((YY - FLOOR) / 4) ** 2))
            img *= (1 - 0.4 * bsh)[..., None]
        for m, alb, em in layers:
            img = over(img, shade_layer(m, alb, em, lights), m)
        # glowing eye
        ex, ey = eye.mean(0)
        splat(emis, ex, ey, 2.2, np.array([2.4, 1.6, 0.5]))
        splat(emis, ex, ey, 6, np.array([0.5, 0.25, 0.05]))

        # smoke (alpha, lit by fire)
        for p in smoke_layer:
            k = p.age / p.life
            a = 0.42 * (1 - k) * min(1, p.age * 4)
            glow = 0.0
            for (lx, ly, inten, lcol, rad) in lights:
                glow += inten / (1 + ((p.x - lx) ** 2 + (p.y - ly) ** 2) / rad ** 2)
            c = np.array([0.05, 0.05, 0.06]) + np.array([0.5, 0.2, 0.06]) * min(glow, 1.5) * 0.5
            splat_alpha(img, p.x, p.y, p.r, c, a)

        # name: extrusion sides, then molten face
        if live.max() > 0:
            for dpx, m in side_layers:
                shade = 0.10 + 0.25 * (1 - dpx / EXT_N)
                col = np.array([0.55, 0.12, 0.03]) * shade
                img = over(img, np.broadcast_to(col, img.shape), m * live)
            flick = 0.85 + 0.3 * sample(NOISE, XX * 3 + t * 50, YY * 3)
            hot = (1 - face_grad_y)[..., None] * np.array([2.2, 1.7, 0.9]) + \
                face_grad_y[..., None] * np.array([1.9, 0.6, 0.08])
            cracks = sample(NOISE2, XX * 5, YY * 5 + t * 30)
            hot = hot * (flick * (0.75 + 0.5 * (cracks > 0.55)))[..., None]
            img = over(img, hot * 0.55, face * live)
            emis += hot * (face * live)[..., None] * 0.35
        emis += heat(fire_buf * 1.05) * 0.95

        # subtitle
        if t >= T_NAME + 0.5:
            sa = smoothstep(T_NAME + 0.5, T_NAME + 1.0, t) * fade
            img = over(img, np.broadcast_to(np.array([0.78, 0.8, 0.86]), img.shape), sub * sa)
            line = np.exp(-((YY - (NAME_C[1] + 35)) / 1.2) ** 2) * np.clip(1 - np.abs(XX - NAME_C[0]) / 180, 0, 1)
            emis += (line * sa * 0.9)[..., None] * np.array([1.0, 0.45, 0.12])

        # ---------------- bloom, tone map, shake
        hdr = img + emis
        bright = np.clip(hdr - 0.75, 0, None)
        hdr += blur(bright, 4) * 0.55 + blur(bright, 14) * 0.45
        # vignette
        vig = 1 - 0.55 * np.clip(((XX - W / 2) / (W * 0.62)) ** 2 + ((YY - H / 2) / (H * 0.85)) ** 2, 0, 1)
        hdr *= vig[..., None]
        ldr = 1 - np.exp(-hdr * 1.25)
        ldr = np.clip(ldr, 0, 1) ** (1 / 1.12)
        out = (ldr * 255).astype(np.uint8)
        if np.any(shake):
            sy_, sx_ = int(round(shake[1])), int(round(shake[0]))
            pad = np.pad(out, ((abs(sy_), abs(sy_)), (abs(sx_), abs(sx_)), (0, 0)), mode="edge")
            out = pad[abs(sy_) - sy_: abs(sy_) - sy_ + H, abs(sx_) - sx_: abs(sx_) - sx_ + W]
        frames.append(Image.fromarray(out, "RGB"))
        if f % 20 == 0:
            print("frame", f, flush=True)

frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=int(1000 / FPS),
               loop=0, quality=82, method=6)
# also dump a contact sheet for review
sheet_t = [0.6, 1.3, 1.8, 2.15, 2.35, 2.7, 3.4, 5.0]
sheet = Image.new("RGB", (W * 2, H * 4))
for i, tt in enumerate(sheet_t):
    sheet.paste(frames[min(NF - 1, int(tt * FPS))], ((i % 2) * W, (i // 2) * H))
sheet.save(OUT.rsplit(".", 1)[0] + "_sheet.png")
print("done", len(frames), "frames")
