# galaxy_scene.py
import pygame
import math
import random
import os

from scene_manager import Scene

TILE_WIDTH = 64
TILE_HEIGHT = 32

class SolarSystemData:
    def __init__(self, name, orbit_radius, orbit_speed):
        """
        name          : name of this system
        orbit_radius  : distance from black hole in 'grid' units
        orbit_speed   : how fast it orbits (radians/frame or scaled by dt)
        """
        self.name = name
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.orbit_angle = 0.0

        # 'gx, gy' = grid coords for isometric transform
        self.gx = 0.0
        self.gy = 0.0

        # 'sx, sy' = final screen coords
        self.sx = 0.0
        self.sy = 0.0

        self.sprite = None

class GalaxyScene(Scene):
    def __init__(self, manager, assets_dir):
        """
        manager   : the SceneManager for switching scenes if needed
        assets_dir: path to images (e.g., /.../assets/images)
        """
        super().__init__()
        self.manager = manager
        self.assets_dir = assets_dir

        # The black hole center in grid coords => (0,0)
        # We'll isometrically transform it in 'render'.
        self.bh_gx = 0
        self.bh_gy = 0

        # Camera offset in screen coords (for panning/dragging)
        self.cam_x = 960
        self.cam_y = 512

        # (1) Randomly pick one of black_hole_{1..3}.png
        bh_choice = random.randint(1, 3)
        bh_filename = f"black_hole_{bh_choice}.png"
        bh_path = os.path.join(self.assets_dir, bh_filename)
        self.black_hole_img = None
        if os.path.exists(bh_path):
            self.black_hole_img = pygame.image.load(bh_path).convert_alpha()
        else:
            # fallback: a big circle ~256×256
            tmp_surf = pygame.Surface((256,256), pygame.SRCALPHA)
            pygame.draw.circle(tmp_surf, (0,0,0), (128,128), 120)
            self.black_hole_img = tmp_surf

        # We'll define some random solar systems orbiting the black hole
        # orbit_radius in [40..100] => smaller orbits.
        self.systems = []
        system_count = random.randint(3, 6)  # e.g. 3..6 systems
        for i in range(system_count):
            r = random.randint(10, 50)
            # slow-ish orbit speeds
            spd = random.uniform(0.00002, 0.00006)
            sname = f"System-{i}"
            sys_data = SolarSystemData(sname, r, spd)

            # (2) Randomly pick one of solar_system_{1..3}.png
            sol_choice = random.randint(1, 3)
            sol_filename = f"solar_system_{sol_choice}.png"
            star_path = os.path.join(self.assets_dir, sol_filename)
            if os.path.exists(star_path):
                sys_data.sprite = pygame.image.load(star_path).convert_alpha()
            else:
                # fallback: ~128×128 circle
                surf = pygame.Surface((128,128), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255,255,0), (64,64), 50)
                sys_data.sprite = surf

            self.systems.append(sys_data)

        self.dragging = False
        self.last_mouse_pos = (0, 0)

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self.dragging = True
                self.last_mouse_pos = pygame.mouse.get_pos()

            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self.dragging = False
                # Check if user clicked on a system
                mx, my = e.pos
                clicked_sys = self.detect_system_click(mx, my)
                if clicked_sys:
                    print(f"Clicked on {clicked_sys.name}, would switch to PlanetScene here")
                    # from planet_scene import PlanetScene
                    # new_scene = PlanetScene(self.assets_dir)
                    # self.manager.set_scene(new_scene)

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.running = False

    def detect_system_click(self, mx, my):
        """
        Checks if the user clicked near any solar system's screen coords.
        We'll say ~64 is a clickable radius for 128×128 sprites.
        """
        for sys_data in self.systems:
            dx = mx - sys_data.sx
            dy = my - sys_data.sy
            dist = math.hypot(dx, dy)
            if dist < 64:
                return sys_data
        return None

    def update(self, dt):
        # If dragging, move the camera offset
        if self.dragging:
            mx, my = pygame.mouse.get_pos()
            dx = mx - self.last_mouse_pos[0]
            dy = my - self.last_mouse_pos[1]
            self.cam_x += dx
            self.cam_y += dy
            self.last_mouse_pos = (mx, my)

        # Orbit update in 'grid' coords
        for sys_data in self.systems:
            sys_data.orbit_angle += sys_data.orbit_speed * dt
            gx = sys_data.orbit_radius * math.cos(sys_data.orbit_angle)
            gy = sys_data.orbit_radius * math.sin(sys_data.orbit_angle)
            sys_data.gx = gx
            sys_data.gy = gy

            # isometric transform => screen coords
            sx = (gx - gy) * (TILE_WIDTH // 2) + self.cam_x
            sy = (gx + gy) * (TILE_HEIGHT // 2) + self.cam_y
            sys_data.sx = sx
            sys_data.sy = sy

    def render(self, surface):
        surface.fill((10,10,40))

        # black hole at (0,0) in grid coords => transform
        bh_sx = (0 - 0)*(TILE_WIDTH//2) + self.cam_x
        bh_sy = (0 + 0)*(TILE_HEIGHT//2) + self.cam_y

        # draw black hole
        if self.black_hole_img:
            cx = bh_sx - self.black_hole_img.get_width()//2
            cy = bh_sy - self.black_hole_img.get_height()//2
            surface.blit(self.black_hole_img, (cx, cy))
        else:
            # fallback circle
            pygame.draw.circle(surface, (0,0,0),
                (int(bh_sx), int(bh_sy)), 120)

        # draw elliptical orbits + system sprites
        for sys_data in self.systems:
            orbit_points = []
            # sample the orbit in steps of 10° => 36 segments
            for deg in range(0, 360, 10):
                rad = math.radians(deg)
                ogx = sys_data.orbit_radius * math.cos(rad)
                ogy = sys_data.orbit_radius * math.sin(rad)
                ox_sx = (ogx - ogy)*(TILE_WIDTH//2) + self.cam_x
                ox_sy = (ogx + ogy)*(TILE_HEIGHT//2) + self.cam_y
                orbit_points.append((ox_sx, ox_sy))
            if len(orbit_points) > 2:
                pygame.draw.lines(surface, (180,180,180), True, orbit_points, 1)

            # draw the system sprite
            sx = sys_data.sx
            sy = sys_data.sy
            w = sys_data.sprite.get_width()
            h = sys_data.sprite.get_height()
            surface.blit(sys_data.sprite, (sx - w//2, sy - h//2))
