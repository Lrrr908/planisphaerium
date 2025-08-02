# Vegetation.py
# ---------------------------------------------------------------
# Procedural more-realistic trees, palms, oaks & cacti for Universe Game
# ---------------------------------------------------------------

import pygame
import random
import math
from oaktree import TreeCfg, build_tree, jitter
import colorsys


# ---------------------------------------------------------------
# Pure-Python Perlin 1D implementation (no C deps)
# ---------------------------------------------------------------
_perm = list(range(256))
random.shuffle(_perm)
_perm += _perm

def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)

def _grad(hash, x):
    g = hash & 15
    grad = 1 + (g & 7)       # gradient 1–8
    if g & 8:
        grad = -grad
    return grad * x

def pnoise1(x):
    """
    1D Perlin noise in [-1,1].
    """
    xi = int(math.floor(x)) & 255
    xf = x - math.floor(x)
    u  = _fade(xf)
    a  = _perm[xi]
    b  = _perm[xi + 1]
    return ((1 - u) * _grad(a, xf) +
            u       * _grad(b, xf - 1))


# ---------------------------------------------------------------
# 1) Style presets (add "cactus")
# ---------------------------------------------------------------
TREE_STYLES = {
    "pine": {
        "max_half":     20,
        "freq":         0.05,
        "palette": [
            ( 30,  60,  30),
            ( 60, 120,  60),
            (100, 180, 100),
        ],
        "trunk_colors": ((100, 70, 40), ( 60, 40, 20)),
    },
    "oak": {
        "max_radius":   16,
        "freq":         0.04,
        "palette": [
            ( 50, 100,  50),
            ( 80, 140,  80),
            (110, 180, 110),
        ],
        "leaf_density": 350,
        "trunk_colors": (( 90, 70, 50), ( 50, 30, 20)),
    },
    "palm": {
        "frond_count":  10,
        "frond_length": 24,
        "frond_width":   6,
        "palette": [
            (100, 160,  80),
            (120, 200, 100),
        ],
        "trunk_colors": ((120, 80, 40), ( 80, 50, 30)),
    },
    "cactus": {
        "height":       60,
        "width":        8,
        "arm_offset":   0.5,    # 50% up from base
        "arm_length":  20,
        "arm_width":    6,
        "palette": [
            ( 34, 139,  34),    # dark green
            ( 50, 205,  50),    # light green
        ],
        "spine_color":  (200, 200, 200),
        "spine_density": 0.02,  # chance per pixel of a spine
    },
}


# ---------------------------------------------------------------
# 2) Pine generator (now with random structure + hue shifts)
# ---------------------------------------------------------------
def generate_pine(scale, params):
    # dimensions
    W = int(50 * scale)
    H = int(80 * scale)
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    cx = W // 2

    # random trunk hue shift
    base_trunk_top, base_trunk_bot = params["trunk_colors"][1], params["trunk_colors"][0]
    hue_shift_tr = random.uniform(-0.5, 0.5)
    trunk_top = shift_hue(base_trunk_top, hue_shift_tr)
    trunk_bot = shift_hue(base_trunk_bot, hue_shift_tr)

    # draw trunk (taller stump)
    stump_h = int(H * random.uniform(0.2, 0.35))
    trunk_w = max(4, int(8 * scale * random.uniform(0.8, 1.2)))
    pygame.draw.rect(
        surf, trunk_bot,
        (cx - trunk_w // 2, H - stump_h, trunk_w, stump_h)
    )
    pygame.draw.rect(
        surf, trunk_top,
        (cx - trunk_w // 4, H - stump_h, trunk_w // 2, stump_h)
    )

    # foliage region
    FH = H - stump_h
    max_half = params["max_half"] * scale * random.uniform(0.8, 1.2)

    # structural variation
    total_circles = int((FH * max_half) / random.uniform(3, 6))
    freq          = params["freq"] * random.uniform(0.8, 1.2)

    # hue shift for foliage
    palette = params["palette"]
    hue_shift_ld = random.uniform(-0.5, 0.5)
    leaf_palette = [shift_hue(c, hue_shift_ld) for c in palette]

    circle_radius = max(1, int(2 * scale))
    for _ in range(total_circles):
        dy = random.uniform(0, FH)
        t  = dy / FH
        half_w = max_half * (1 - t)
        offset = pnoise1(dy * freq) * (4 * scale)
        x = int(cx + random.uniform(-half_w, half_w) + offset)
        y = int(dy)
        if 0 <= x < W and 0 <= y < FH:
            # pick color biased by height
            idx = min(len(leaf_palette) - 1, int(t * len(leaf_palette)))
            color = leaf_palette[idx]
            pygame.draw.circle(surf, color, (x, y), circle_radius)

    return surf





def shift_hue(rgb, shift):
    # rgb in 0–255 range; shift in [–1, 1], returns 0–255 tuple
    r, g, b = [v / 255.0 for v in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    h = (h + shift) % 1.0
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return (int(r2 * 255), int(g2 * 255), int(b2 * 255))

# ---------------------------------------------------------------
# 3) Oak generator
# ---------------------------------------------------------------
def generate_oak(scale, params):
    # canvas size: twice the max_radius
    W = int(params["max_radius"] * 5 * scale)
    H = W
    cx = W // 2
    ground_y = H - 1

    # wildly shift trunk hue
    base_trunk_in, base_trunk_out = params["trunk_colors"]
    hue_shift_trunk = random.uniform(-0.5, 0.5)
    trunk_in  = shift_hue(base_trunk_in,  hue_shift_trunk)
    trunk_out = shift_hue(base_trunk_out, hue_shift_trunk)

    # wildly shift leaf hue
    base_leaf_in, base_leaf_out = params["palette"][0], params["palette"][-1]
    hue_shift_leaf = random.uniform(-0.5, 0.5)
    leaf_in  = shift_hue(base_leaf_in,  hue_shift_leaf)
    leaf_out = shift_hue(base_leaf_out, hue_shift_leaf)

    # randomize structure parameters
    primary_ct     = random.randint(1, 3)
    primary_len    = max(10, int(params["max_radius"] * scale * random.uniform(0.8, 1.2)))
    primary_fan    = random.randint(10, 40)
    primary_thk    = max(1, int(primary_len * random.uniform(0.2, 0.4)))
    fork_spread    = random.randint(20, 80)
    fog_dots       = int(params["leaf_density"] * random.uniform(0.5, 1.0))
    fog_r_min      = random.randint(2, 5)
    fog_r_max      = fog_r_min + random.randint(1, 4)
    cluster_dots   = int(params["leaf_density"] * random.uniform(0.1, 0.3))
    cluster_sz     = max(16, int(28 * scale * random.uniform(0.8, 1.2)))
    cluster_spread = random.randint(4, 12)

    cfg = TreeCfg(
        trunk_h       = max(1, int(2   * scale * random.uniform(0.8,1.2))),
        trunk_w       = max(1, int(2   * scale * random.uniform(0.8,1.2))),
        root_spread   = int(38 * scale * random.uniform(0.8,1.2)),
        col_btm       = trunk_in,
        col_top       = trunk_out,

        primary_ct    = primary_ct,
        primary_len   = primary_len,
        primary_fan   = primary_fan,
        primary_thk   = primary_thk,

        fork_split    = (3, 5),
        fork_spread   = fork_spread,
        len_shrink    = (0.6, 0.9),
        thk_shrink    = (0.5, 0.8),
        min_len       = 5,
        wiggle        = random.uniform(1.0, 3.0),

        crown_pad     = random.uniform(0.7, 1.0),
        fog_dots      = fog_dots,
        fog_r         = (fog_r_min, fog_r_max),
        fog_alpha     = random.randint(50, 200),
        leaf_col_in   = leaf_in,
        leaf_col_out  = leaf_out,

        cluster_sz     = cluster_sz,
        cluster_dots   = cluster_dots,
        cluster_spread = cluster_spread,
        dot_r          = (1, random.randint(2, 4)),
    )

    # build and return the procedurally unique oak
    return build_tree(W, H, cx, ground_y, cfg, scale)


# ---------------------------------------------------------------
# 4) Palm generator (thick fronds with highlight)
# ---------------------------------------------------------------
def generate_palm(scale, params):
    W = int(40 * scale)
    H = int(70 * scale)
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    cx = W // 2

    # trunk
    trunk_h = int(14 * scale)
    trunk_w = max(4, int(6 * scale))
    top_c, bot_c = params["trunk_colors"]
    pygame.draw.rect(surf, bot_c, (cx - trunk_w//2, H - trunk_h, trunk_w, trunk_h))
    pygame.draw.rect(surf, top_c, (cx - trunk_w//4, H - trunk_h, trunk_w//2, trunk_h))

    # fronds
    frond_len = params["frond_length"] * scale
    frond_w   = max(1, int(params["frond_width"] * scale))
    for i in range(params["frond_count"]):
        angle = (i / float(params["frond_count"])) * 2 * math.pi
        dx, dy = math.cos(angle), math.sin(angle)
        x0, y0 = cx, H - trunk_h
        x1 = int(cx + dx * frond_len)
        y1 = int((H - trunk_h) - dy * frond_len)
        # base line
        pygame.draw.line(surf, params["palette"][0], (x0, y0), (x1, y1), frond_w)
        # highlight
        hl_w = max(1, frond_w // 2)
        pygame.draw.line(surf, params["palette"][-1], (x0, y0), (x1, y1), hl_w)

    return surf


# ---------------------------------------------------------------
# 5) Cactus generator
# ---------------------------------------------------------------
def generate_cactus(scale, params):
    height     = int(params["height"] * scale)
    width      = int(params["width"] * scale)
    arm_len    = int(params["arm_length"] * scale)
    arm_w      = int(params["arm_width"] * scale)
    W          = width + arm_len * 2
    H          = height
    surf       = pygame.Surface((W, H), pygame.SRCALPHA)
    cx         = W // 2
    c1, c2     = params["palette"]
    spine_c    = params["spine_color"]
    density    = params["spine_density"]

    # draw column with vertical gradient
    for y in range(H):
        t = y / max(1, H - 1)
        col = (
            int(c2[0] * (1 - t) + c1[0] * t),
            int(c2[1] * (1 - t) + c1[1] * t),
            int(c2[2] * (1 - t) + c1[2] * t),
        )
        x0 = cx - width // 2
        x1 = cx + width // 2
        pygame.draw.line(surf, col, (x0, y), (x1, y))

    # arms at half-height
    arm_y = H - int(params["arm_offset"] * H)
    # left arm
    pygame.draw.rect(
        surf,
        c1,
        (cx - width//2 - arm_len, arm_y - arm_w//2, arm_len, arm_w)
    )
    # right arm
    pygame.draw.rect(
        surf,
        c1,
        (cx + width//2,       arm_y - arm_w//2, arm_len, arm_w)
    )

    # spines on column
    for y in range(0, H, max(4, int(4*scale))):
        for x in range(cx - width//2, cx + width//2):
            if random.random() < density:
                surf.set_at((x, y), spine_c)
    # spines on arms
    for x in range(cx - width//2 - arm_len, cx + width//2 + arm_len):
        if random.random() < density:
            surf.set_at((x, arm_y), spine_c)

    return surf


# ---------------------------------------------------------------
# 6) Unified API
# ---------------------------------------------------------------
def generate_sprite(species="pine", scale=1):
    params = TREE_STYLES.get(species, TREE_STYLES["pine"])
    if species == "pine":
        return generate_pine(scale, params)
    elif species == "oak":
        return generate_oak(scale, params)
    elif species == "palm":
        return generate_palm(scale, params)
    elif species == "cactus":
        return generate_cactus(scale, params)
    # fallback
    return generate_pine(scale, TREE_STYLES["pine"])


# ---------------------------------------------------------------
# 7) Spawner helper for the scene
# ---------------------------------------------------------------
def spawn_vegetation(planet, position, scale=1, group=None, species=None):
    """
    planet.seed → deterministic species if not provided
    position → (screen_x, screen_y) midbottom of sprite
    scale → sprite scaling factor
    group → optional pygame.sprite.Group
    """
    rng = random.Random(planet.seed)
    species = species or rng.choice(list(TREE_STYLES.keys()))
    image   = generate_sprite(species=species, scale=scale)
    sprite  = pygame.sprite.Sprite()
    sprite.image = image
    sprite.rect  = image.get_rect(midbottom=position)
    sprite.grid_x, sprite.grid_y = None, None
    if group:
        group.add(sprite)
    return sprite
