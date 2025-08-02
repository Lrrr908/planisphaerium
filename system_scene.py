# system_scene.py · v2025-07-08 k  (hover-glow & ring-click navigation + LOADING SCREENS)

import os, math, random, pygame
from functools import lru_cache
from typing import List, Tuple, Dict, Optional, TYPE_CHECKING

from scene_manager import Scene
from planet_meta   import PlanetMeta         # single canonical dataclass
from planet_storage import PlanetStorage     # NEW: Centralized storage
if TYPE_CHECKING:                            # IDE hints only
    from planet_scene import PlanetScene


# ───────── constants ────────────────────────────────────
TILE_W, TILE_H       = 64, 32
STARFIELD_DENSITY    = 0.00025
CANVAS_W, CANVAS_H   = 4000, 2500


# ───────── helper funcs ─────────────────────────────────
def load_or_circle(path: str, px: int,
                   color: Tuple[int, int, int]) -> pygame.Surface:
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, (px, px))
    surf = pygame.Surface((px, px), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (px // 2, px // 2), px // 2 - 4)
    return surf


@lru_cache(maxsize=192)
def scale_img(img: pygame.Surface, scale: float) -> pygame.Surface:
    if scale == 1.0: return img
    w, h = img.get_size()
    return pygame.transform.smoothscale(img, (max(1, int(w * scale)),
                                              max(1, int(h * scale))))


# ───────── starfield background ─────────────────────────
class Starfield:
    def __init__(self, w: int, h: int, density: float = STARFIELD_DENSITY):
        self.stars = [(random.randint(0, w),
                       random.randint(0, h),
                       random.randint(180, 255))
                      for _ in range(int(w * h * density))]

    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float, zoom: float):
        par = 0.2 + 0.8 / max(1.0, zoom)
        sw, sh = surf.get_size()
        for x, y, b in self.stars:
            sx = x * par + cam_x * (1 - par)
            sy = y * par + cam_y * (1 - par)
            if -5 <= sx <= sw + 5 and -5 <= sy <= sh + 5:
                surf.set_at((int(sx), int(sy)), (b, b, b))


# ───────── celestial body ───────────────────────────────
class Body:
    def __init__(self,
                 name: str,
                 orbit_r: int,
                 orbit_spd: float,
                 sprite: pygame.Surface,
                 parent: Optional["Body"] = None,
                 meta: Optional[PlanetMeta] = None):
        self.name   = name
        self.meta   = meta
        self.parent = parent
        self.orbit_r   = orbit_r
        self.orbit_spd = orbit_spd
        self.orbit_ang = random.random() * math.tau
        self.sprite_orig   = sprite
        self.sprite_scaled = sprite
        self.gx = self.gy = self.sx = self.sy = 0.0
        self.moons: List["Body"] = []

    def rescale(self, zoom: float):
        self.sprite_scaled = scale_img(self.sprite_orig, zoom)
        for m in self.moons: m.rescale(zoom)


# ───────── system-view scene ────────────────────────────
class SystemScene(Scene):
    SIZE_BUCKETS   = [(60, 60, 64), (100, 100, 96), (200, 200, 128)]
    BUCKET_WEIGHTS = [0.55, 0.35, 0.10]

    def __init__(self, manager, assets_dir: str, planet_storage: Optional[PlanetStorage] = None):
        super().__init__()
        self.manager, self.assets = manager, assets_dir

        self.cam_x, self.cam_y = 960, 512
        self.zoom              = 1.0
        self.dragging          = False
        self.drag_start        = (0, 0)

        self.starfield = Starfield(CANVAS_W, CANVAS_H)
        self.star_img  = load_or_circle(os.path.join(assets_dir, "star.png"),
                                        768, (255, 255, 50))

        # NEW: Use persistent storage
        self.planet_storage = planet_storage or PlanetStorage()
        self.planets = self.planet_storage.load_all_planets()
        
        self.bodies: List[Body] = []
        self._build_system()

        # ring-hover state
        self.hover_planet: Optional[Body] = None

    def reset_hover_state(self):
        """Reset hover state when returning to this scene"""
        self.hover_planet = None
        
    def on_scene_enter(self):
        """Called when this scene becomes active"""
        self.reset_hover_state()

    # ───────── population ───────────────────────────────
    def _build_system(self):
        radii = random.sample(range(30, 111, 10), 9)
        for idx, r in enumerate(radii):
            planet_name = f"Planet-{idx}"
            planet_id = planet_name  # Use consistent naming
            
            # Check if planet already exists
            if planet_id in self.planets:
                planet_meta = self.planets[planet_id]
            else:
                # Create new planet
                tiles_w, tiles_h, px = random.choices(self.SIZE_BUCKETS,
                                                      weights=self.BUCKET_WEIGHTS,
                                                      k=1)[0]
                planet_meta = PlanetMeta(
                    seed=random.getrandbits(32),
                    tiles=(tiles_w, tiles_h),
                    planet_type=self._determine_planet_type()
                )
                self.planets[planet_id] = planet_meta
                
            sprite = load_or_circle(os.path.join(self.assets,
                                                 f"planet_{random.randint(1,9)}.png"),
                                     self._get_pixel_size(planet_meta.tiles),
                                     (random.randint(80,255),
                                      random.randint(80,255),
                                      random.randint(80,255)))
            p = Body(planet_name, r, random.uniform(0.00025, 0.0006),
                     sprite, meta=planet_meta)
            p.rescale(self.zoom)

            roll = random.random()
            if roll < 0.30:
                p.moons.append(self._make_moon(p, 0))
            elif roll < 0.38:
                p.moons += [self._make_moon(p, 0), self._make_moon(p, 1)]

            self.bodies.append(p)

        # optional debris
        for b in range(random.randint(1, 2)):
            debris = load_or_circle(os.path.join(self.assets, "debris_1.png"),
                                    256, (160, 160, 160))
            self.bodies.append(
                Body(f"Debris-{b}", 130 + b * 20, random.uniform(0.0001, 0.00025),
                     debris))

    def _determine_planet_type(self) -> str:
        """Determine planet type based on position and random factors"""
        types = ["terrestrial", "desert", "arctic", "oceanic", "volcanic"]
        weights = [0.4, 0.2, 0.15, 0.15, 0.1]
        return random.choices(types, weights=weights, k=1)[0]
    
    def _get_pixel_size(self, tiles: Tuple[int, int]) -> int:
        """Get sprite pixel size based on tile dimensions"""
        w, h = tiles
        if w <= 60:
            return 64
        elif w <= 100:
            return 96
        else:
            return 128

    def _make_moon(self, planet: Body, idx: int) -> Body:
        sprite = load_or_circle(os.path.join(self.assets, "moon_1.png"), 48, (200,200,200))
        moon_id = f"{planet.name}-M{idx}"
        
        if moon_id in self.planets:
            m_meta = self.planets[moon_id]
        else:
            m_meta = PlanetMeta(
                seed=random.getrandbits(32),
                tiles=(40, 40),
                planet_type="moon"
            )
            self.planets[moon_id] = m_meta
            
        m = Body(f"{planet.name}-Moon{idx+1}",
                 random.randint(4, 10), random.uniform(0.0007, 0.0016),
                 sprite, parent=planet, meta=m_meta)
        m.rescale(self.zoom)
        return m

    # ───────── input ────────────────────────────────────
    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self.dragging = True
                self.drag_start = pygame.mouse.get_pos()

            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self.dragging = False
                self._click(*e.pos)

            elif e.type == pygame.MOUSEMOTION:
                self._update_hover(*e.pos)

            elif e.type == pygame.MOUSEWHEEL:
                self.zoom = max(0.2, min(5.0,
                              self.zoom * (1.1 if e.y > 0 else 1 / 1.1)))
                for b in self.bodies: b.rescale(self.zoom)

            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.running = False

    # hover detection
    def _update_hover(self, mx: int, my: int) -> None:
        self.hover_planet = None
        for p in self.bodies:
            if p.parent:          # skip moons
                continue
            if self._ring_hit(mx, my, p):
                self.hover_planet = p
                return

    # click behaviour - UPDATED FOR LOADING SCREENS
    def _click(self, mx: int, my: int):
        if not self.hover_planet:
            return

        from planet_scene import PlanetScene   # lazy import

        keys   = pygame.key.get_pressed()
        use_moon = keys[pygame.K_m] and self.hover_planet.moons

        target_meta = (self.hover_planet.moons[0].meta
                       if use_moon else self.hover_planet.meta)

        if target_meta:
            # NEW: Get surface from scene manager for loading screen support
            surface = getattr(self.manager, 'surface', None)
            
            # Create planet scene with loading screen support
            planet_scene = PlanetScene(self.assets, target_meta, surface)
            
            # Pass storage reference to planet scene
            planet_scene.planet_storage = self.planet_storage
            
            # Store planet ID for proper saving
            planet_name = self.hover_planet.moons[0].name if use_moon else self.hover_planet.name
            planet_scene.planet_id = planet_name
            
            self.manager.set_scene(planet_scene)

    # ───────── update ───────────────────────────────────
    def update(self, dt: int):
        if self.dragging:
            mx, my = pygame.mouse.get_pos()
            dx, dy = mx - self.drag_start[0], my - self.drag_start[1]
            self.cam_x += dx
            self.cam_y += dy
            self.drag_start = (mx, my)

        # Always update hover state based on current mouse position
        mx, my = pygame.mouse.get_pos()
        self._update_hover(mx, my)

        for b in self.bodies:
            self._tick(b, dt)

    def _tick(self, body: Body, dt: int):
        pgx = body.parent.gx if body.parent else 0
        pgy = body.parent.gy if body.parent else 0
        body.orbit_ang += body.orbit_spd * dt
        body.gx = pgx + body.orbit_r * math.cos(body.orbit_ang)
        body.gy = pgy + body.orbit_r * math.sin(body.orbit_ang)
        body.sx, body.sy = self._to_screen(body.gx, body.gy)
        for m in body.moons:
            self._tick(m, dt)

    # ───────── render ───────────────────────────────────
    def render(self, surf: pygame.Surface):
        surf.fill((5, 5, 20))
        self.starfield.draw(surf, self.cam_x, self.cam_y, self.zoom)

        # star
        star_scaled = scale_img(self.star_img, self.zoom)
        cx, cy = self._to_screen(0, 0)
        surf.blit(star_scaled, (cx - star_scaled.get_width()  // 2,
                                cy - star_scaled.get_height() // 2))

        # orbit rings
        ring_layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        for p in self.bodies:
            if p.parent:
                continue
            glow = (p is self.hover_planet)
            col  = (255, 255, 160, 200) if glow else (200, 200, 200, int(120*self.zoom))
            width = 3 if glow else 1
            pts = [self._to_screen(p.orbit_r * math.cos(math.radians(d)),
                                   p.orbit_r * math.sin(math.radians(d)))
                   for d in range(0, 360, 6)]
            pygame.draw.lines(ring_layer, col, True, pts, width)
        surf.blit(ring_layer, (0, 0))

        # planets & moons
        for p in self.bodies:
            surf.blit(p.sprite_scaled,
                      (p.sx - p.sprite_scaled.get_width()  // 2,
                       p.sy - p.sprite_scaled.get_height() // 2))
            for m in p.moons:
                surf.blit(m.sprite_scaled,
                          (m.sx - m.sprite_scaled.get_width()  // 2,
                           m.sy - m.sprite_scaled.get_height() // 2))

    # ───────── helpers ──────────────────────────────────
    def _ring_hit(self, mx: int, my: int, planet: Body) -> bool:
        """Distance from mouse to star centre minus scaled orbit radius ≤ 4 px."""
        cx, cy = self._to_screen(0, 0)
        dist   = math.hypot(mx - cx, my - cy)
        ring_r = planet.orbit_r * (TILE_W // 2) * self.zoom
        return abs(dist - ring_r) <= 4.0          # 4-pixel tolerance

    def _hit(self, mx: int, my: int, body: Body) -> bool:
        r = body.sprite_scaled.get_width() * 0.5
        return (mx - body.sx) ** 2 + (my - body.sy) ** 2 <= r * r

    def _to_screen(self, gx: float, gy: float) -> Tuple[float, float]:
        sx = (gx - gy) * (TILE_W // 2) * self.zoom + self.cam_x
        sy = (gx + gy) * (TILE_H // 2) * self.zoom + self.cam_y
        return sx, sy