# drop.py  ·  v2025-07-06c
# ─────────────────────────────────────────────────────────
#  Resource drops (meat, leather, ore, etc.)
#  • renders a bright icon + quantity label
#  • scales & re-positions correctly when the camera zooms
#  • lightweight “bob” animation so it pops visually
# ─────────────────────────────────────────────────────────

import math
import pygame
from iso_map import IsoObject, TILE_WIDTH, TILE_HEIGHT

STACK_OFFSET = 30          # vertical lift so the drop isn’t buried in the tile
BOB_SPEED    = 0.004       # radians / ms  → tweak for faster / slower bob
BOB_HEIGHT   = 6           # pixels peak-to-peak at 100 % zoom


class DropObject(IsoObject):
    # -----------------------------------------------------
    # ctor
    # -----------------------------------------------------
    def __init__(self, grid_x: int, grid_y: int,
                 resource_type: str, quantity: int):

        super().__init__(
            grid_x      = grid_x,
            grid_y      = grid_y,
            draw_order  = (grid_x + grid_y) * 10 + 9        # on top of units/trees
        )

        self.resource_type = resource_type
        self.quantity      = quantity
        self.alive         = True
        self.hovered       = False

        # logic position (float for sub-tile accuracy)
        self.x_f = float(grid_x)
        self.y_f = float(grid_y)

        # helper state
        self.zoom_scale = 1.0
        self._bob_phase = 0.0   # radians

    # -----------------------------------------------------
    # external callbacks
    # -----------------------------------------------------
    def set_zoom_scale(self, zoom: float):
        self.zoom_scale = max(0.05, zoom)

    def update(self, dt_ms: int):
        """Tiny sinusoidal bob so the item draws attention."""
        self._bob_phase = (self._bob_phase + dt_ms * BOB_SPEED) % (math.tau)

    # -----------------------------------------------------
    # math helpers
    # -----------------------------------------------------
    def calculate_screen_position(self, cam_x, cam_y, zoom_scale=1.0):
        self.zoom_scale = zoom_scale       # keep in sync
        iso_x = (self.x_f - self.y_f) * (TILE_WIDTH // 2) * zoom_scale
        iso_y = (self.x_f + self.y_f) * (TILE_HEIGHT // 2) * zoom_scale

        # camera + bob
        self.screen_x = iso_x + cam_x
        base_y        = iso_y + cam_y
        bob_offset    = math.sin(self._bob_phase) * (BOB_HEIGHT * zoom_scale * 0.5)
        self.screen_y = base_y - STACK_OFFSET * zoom_scale + bob_offset

    def get_rect(self) -> pygame.Rect:
        r = int(9 * self.zoom_scale)               # clickable radius
        return pygame.Rect(
            int(self.screen_x) - r,
            int(self.screen_y) - r,
            r * 2,
            r * 2
        )

    # -----------------------------------------------------
    # render
    # -----------------------------------------------------
    def draw(self, surface, _tree_images=None, zoom_scale=1.0):
        if not self.alive:
            return

        # colour per resource
        colour_map = {
            "meat":    (210,  55,  55),
            "leather": (139,  69,  19),
            "metal":   (180, 180, 180),
            "bones":   (140, 140, 140),            
        }
        colour = colour_map.get(self.resource_type, (255, 215,   0))

        # icon
        radius = int(7 * zoom_scale)
        pygame.draw.circle(
            surface, colour,
            (int(self.screen_x), int(self.screen_y)),
            max(3, radius)
        )

        # quantity text (always upright, no outline for brevity)
        font = pygame.font.SysFont("Arial", max(12, int(14 * zoom_scale)))
        txt  = font.render(f"×{self.quantity}", True, (0, 0, 0))
        tw, th = txt.get_size()
        surface.blit(txt, (self.screen_x - tw // 2,
                           self.screen_y - radius - th - 2))
