##########################################################
# unit_manager.py  ·  v2025-07-07a   ⟨auto-HUD unlock⟩
# --------------------------------------------------------
# • Bipeds, selection, movement, simple combat
# • Spawns loot when they kill animals
# • Picks up any DropObject on the same tile and adds it
#   to the biped's inventory dict
# • NEW: automatically unlocks the matching BP-button in
#   the HUD whenever a unit is added
##########################################################

import math
from typing import List, Optional, Dict

import pygame

from iso_map import IsoObject, TILE_WIDTH, TILE_HEIGHT, STACK_OFFSET
from mission_types import UnitMission
from drop import DropObject                   # drop ⟶ loot spawn / pickup


##########################################################
# 1)  Helper – simple pixel-art biped frames
##########################################################
def create_biped_frames(
    body_color=(204, 255, 229),
    num_frames: int = 3,
    width: int = 32,
    height: int = 48,
    head_radius: int = 5,
    head_offset_y: int = 10,
    torso_width: int = 4,
    torso_height: int = 7,
    torso_offset_y: int = 14,
    arm_thickness: int = 2,
    arm_length: int = 8,
    arm_offset_y: int = 16,
    leg_thickness: int = 2,
    leg_offset_y: int = 20,
    leg_spacing: int = 6,
    leg_length: int = 8,
) -> List[pygame.Surface]:
    frames: List[pygame.Surface] = []
    for i in range(num_frames):
        surf = pygame.Surface((width, height), pygame.SRCALPHA)

        # head
        pygame.draw.circle(surf, body_color, (width // 2, head_offset_y), head_radius)

        # torso
        torso_x = width // 2 - torso_width // 2
        pygame.draw.rect(surf, body_color, (torso_x, torso_offset_y, torso_width, torso_height))

        # arms
        shoulder = (width // 2, arm_offset_y)
        la_end = (shoulder[0] - arm_length, shoulder[1] + (i % 2) * 2)
        ra_end = (shoulder[0] + arm_length, shoulder[1] - (i % 2) * 2)
        pygame.draw.line(surf, body_color, shoulder, la_end, arm_thickness)
        pygame.draw.line(surf, body_color, shoulder, ra_end, arm_thickness)

        # legs
        hip = (width // 2, leg_offset_y)
        ll_end = (hip[0] - leg_spacing + (i % 2) * 2, hip[1] + leg_length)
        rl_end = (hip[0] + leg_spacing - (i % 2) * 2, hip[1] + leg_length)
        pygame.draw.line(surf, body_color, hip, ll_end, leg_thickness)
        pygame.draw.line(surf, body_color, hip, rl_end, leg_thickness)

        frames.append(surf)
    return frames


##########################################################
# 2)  Screen-px → iso tile helper
##########################################################
def screen_to_tile(mx, my, cam_x, cam_y, zoom):
    iso_x = mx - cam_x
    iso_y = my - cam_y
    tw = (TILE_WIDTH // 2) * zoom
    th = (TILE_HEIGHT // 2) * zoom
    tx = (iso_y / th + iso_x / tw) / 2.0
    ty = (iso_y / th - iso_x / tw) / 2.0
    return int(round(tx)), int(round(ty))


##########################################################
# 3)  BipedUnit
##########################################################
class BipedUnit(IsoObject):
    def __init__(self, scene, tile_x: int, tile_y: int,
                 frames: List[pygame.Surface], speed: float = 2.0):
        self.scene = scene
        
        # Bipeds render with position-based draw order
        draw_order = (tile_x + tile_y) * 10 + 2.5  # Layer 2.5: above animals, below trees
        
        super().__init__(
            grid_x     = tile_x,
            grid_y     = tile_y,
            draw_order = draw_order
        )

        # position
        self.x_f, self.y_f = float(tile_x), float(tile_y)

        # graphics
        self.original_frames = frames
        self.scaled_frames   = frames[:]
        self.current_frame   = 0
        self.facing_left     = False

        # movement & combat
        self.speed           = speed
        self.mission         = UnitMission.IDLE
        self.target_unit     = None
        self.path_tiles: List[tuple[int,int]] = []
        self.path_index      = 0

        self.health          = 100
        self.attack_power    = 100
        self.attack_range    = 1.5
        self.attack_speed    = 1.0
        self.attack_cooldown = 0.0
        self.attack_repath_timer = 0.0

        # loot & inventory
        self.drops           = {"meat": 1, "leather": 2}
        self.inventory: Dict[str, int] = {}

        # Enhanced movement tracking for layered terrain
        self.destination_x = None
        self.destination_y = None
        self.moving = False
        self.move_progress = 0.0
        self.next_tile_x = None
        self.next_tile_y = None

        # Enhanced biped properties
        self.unit_id = f"biped_{tile_x}_{tile_y}_{hash(self)}"
        self.color = (204, 255, 229)  # Default color
        self.creation_time = 0
        self.last_command_time = 0
        self.max_health = 100
        self.mission_data = {}
        self.selected = False
        self.facing_direction = "down"
        self.animation_time = 0.0

        # misc
        self.is_selected     = False
        self.alive           = True

    # ---------- zoom ----------
    def set_zoom_scale(self, zoom: float):
        self.scaled_frames = [
            pygame.transform.smoothscale(
                fr,
                (max(1, int(fr.get_width()  * zoom)),
                 max(1, int(fr.get_height() * zoom)))
            )
            for fr in self.original_frames
        ]

    # ---------- path helpers ----------
    def set_path(self, path):
        if path:
            self.path_tiles = path
            self.path_index = 0
            self.moving = True
            if self.mission != UnitMission.ATTACK:
                self.mission = UnitMission.MOVE
        else:
            self.path_tiles = []
            self.path_index = 0
            self.moving = False
            if self.mission != UnitMission.ATTACK:
                self.mission = UnitMission.IDLE

    # ---------- main update ----------
    def update(self, dt_ms: int):
        if not self.alive:
            return

        if self.mission == UnitMission.ATTACK:
            self._attack_logic(dt_ms)
        elif self.mission == UnitMission.MOVE or self.moving:
            self._update_path_move(dt_ms * 0.001)

        # Always check for drops after moving / acting
        self._check_pickup_drops()

    # ---------- combat ----------
    def _attack_logic(self, dt_ms: int):
        if not self.target_unit or not self.target_unit.alive:
            self.mission = UnitMission.IDLE
            return

        dist = math.hypot(self.target_unit.x_f - self.x_f,
                          self.target_unit.y_f - self.y_f)

        if dist <= self.attack_range:
            self.attack_cooldown -= dt_ms * 0.001
            if self.attack_cooldown <= 0:
                self.target_unit.health -= self.attack_power
                if self.target_unit.health <= 0:
                    self.target_unit.alive = False
                    self._spawn_drops(self.target_unit)
                self.attack_cooldown = 1.0 / self.attack_speed
        else:
            # chase if out of range
            self.attack_repath_timer += dt_ms * 0.001
            if self.attack_repath_timer >= 3.0 or not self.path_tiles:
                self.attack_repath_timer = 0.0
                path = self.scene.find_path(
                    int(round(self.x_f)), int(round(self.y_f)),
                    int(round(self.target_unit.x_f)), int(round(self.target_unit.y_f))
                )
                if path:
                    self.set_path(path)
            self._update_path_move(dt_ms * 0.001)

    # ---------- loot spawn ----------
    def _spawn_drops(self, victim):
        if not hasattr(victim, "drops"):
            return
        for res, qty in victim.drops.items():
            drop = DropObject(victim.grid_x, victim.grid_y, res, qty)
            drop.calculate_screen_position(
                self.scene.map.camera_offset_x,
                self.scene.map.camera_offset_y,
                self.scene.zoom_scale,
            )
            self.scene.drops.append(drop)

    # ---------- pickup ----------
    def _check_pickup_drops(self):
        if not self.scene.drops:
            return
        for drop in list(self.scene.drops):
            if drop.grid_x == self.grid_x and drop.grid_y == self.grid_y:
                # personal stash
                self.inventory[drop.resource_type] = self.inventory.get(drop.resource_type,0)+drop.quantity
                # shared stash for HUD
                if not hasattr(self.scene, "inventory"):
                    self.scene.inventory = {}
                self.scene.inventory[drop.resource_type] = (
                    self.scene.inventory.get(drop.resource_type,0)+drop.quantity
                )
                self.scene.drops.remove(drop)

    # ---------- movement ----------
    def _update_path_move(self, seconds: float):
        if not self.path_tiles or self.path_index >= len(self.path_tiles):
            if self.mission == UnitMission.MOVE or self.moving:
                self.mission = UnitMission.GUARD
                self.moving = False
            return

        tx, ty = self.path_tiles[self.path_index]
        dx, dy = tx - self.x_f, ty - self.y_f
        dist   = math.hypot(dx, dy)

        if dist < 0.01:
            self.x_f, self.y_f = tx, ty
            self.path_index += 1
            if self.path_index < len(self.path_tiles):
                self.current_frame = (self.current_frame + 1) % len(self.scaled_frames)
            else:
                # Reached the end of the path
                self.moving = False
                if self.mission == UnitMission.MOVE:
                    self.mission = UnitMission.IDLE
            return

        max_move = self.speed * seconds
        ratio = min(1.0, max_move / dist)
        self.x_f += dx * ratio
        self.y_f += dy * ratio

        if abs(dx) > 0.001:
            self.facing_left = dx < 0

        self.grid_x, self.grid_y = int(round(self.x_f)), int(round(self.y_f))
        self.draw_order = (self.grid_x + self.grid_y) * 10 + 2.5  # Layer 2.5: above animals, below trees

    # ---------- iso → screen ----------
    def calculate_screen_position(self, cam_x, cam_y, zoom):
        # Standard isometric calculation
        iso_x = (self.x_f - self.y_f) * (TILE_WIDTH // 2) * zoom
        iso_y = (self.x_f + self.y_f) * (TILE_HEIGHT // 2) * zoom
        
        # CRITICAL: Add terrain height offset for layered terrain
        terrain_height_offset = 0
        if hasattr(self.scene, 'use_layered_terrain') and self.scene.use_layered_terrain:
            if hasattr(self.scene, 'terrain'):
                try:
                    terrain_height = self.scene.terrain.get_height_at(self.grid_x, self.grid_y)
                    terrain_height_offset = terrain_height * 16 * zoom  # 16 pixels per height level
                except:
                    terrain_height_offset = 0
        
        self.screen_x = iso_x + cam_x
        self.screen_y = iso_y + cam_y - terrain_height_offset

    # ---------- draw ----------
    def draw(self, surface, _trees=None, zoom_scale=1.0):
        if not self.alive or not self.scaled_frames:
            return

        frame = self.scaled_frames[self.current_frame]
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)

        w, h = frame.get_size()
        
        # Draw shadow at ground level
        shadow = pygame.Surface((int(w * 0.6), int(h * 0.15)), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60), shadow.get_rect())
        shadow_x = int(self.screen_x - shadow.get_width() // 2)
        shadow_y = int(self.screen_y - shadow.get_height() // 2)
        surface.blit(shadow, (shadow_x, shadow_y))

        # Draw biped just above the shadow (much smaller offset)
        small_offset = int(h * 0.1)  # Small offset instead of STACK_OFFSET
        draw_x = self.screen_x - w // 2
        draw_y = shadow_y - h + small_offset  # Position relative to shadow
        
        # Draw outline
        mask = pygame.mask.from_surface(frame)
        outline = mask.to_surface(setcolor=(0, 0, 0), unsetcolor=(0, 0, 0, 0))
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if ox or oy:
                    surface.blit(outline, (draw_x + ox, draw_y + oy))

        surface.blit(frame, (draw_x, draw_y))

        if self.is_selected or getattr(self, 'selected', False):
            off   = int(5 * zoom_scale)
            tri_h = int(6 * zoom_scale)
            tri_w = int(4 * zoom_scale)
            apex  = (int(self.screen_x), int(draw_y - off))
            pygame.draw.polygon(surface, (0, 255, 0),
                                [apex,
                                 (apex[0] - tri_w, apex[1] - tri_h),
                                 (apex[0] + tri_w, apex[1] - tri_h)])


##########################################################
# 4)  UnitManager
##########################################################
class UnitManager:
    def __init__(self, scene):
        self.scene = scene
        self.units: List[BipedUnit] = []
        self.selected_unit: Optional[BipedUnit] = None

    # ----------------------------------------------------
    #  add_unit  ← NEW unlock-logic here
    # ----------------------------------------------------
    def add_unit(self, unit: BipedUnit):
        """Adds a unit and unlocks the matching HUD slot."""
        self.units.append(unit)

        if hasattr(self.scene, "hud"):
            self.scene.hud.unlock_biped(len(self.units) - 1)

    # ----------------------------------------------------
    #  Selection helpers
    # ----------------------------------------------------
    def select_unit_by_index(self, idx: int) -> bool:
        if 0 <= idx < len(self.units):
            if self.selected_unit:
                self.selected_unit.is_selected = False
                self.selected_unit.selected = False
            self.selected_unit = self.units[idx]
            self.selected_unit.is_selected = True
            self.selected_unit.selected = True
            return True
        return False

    def select_unit_at(self, pos) -> bool:
        mx, my = pos
        zoom   = self.scene.zoom_scale
        offset = int(STACK_OFFSET * zoom)
        for u in reversed(self.units):
            if not u.scaled_frames:
                continue
            fr = u.scaled_frames[u.current_frame]
            rect = pygame.Rect(
                u.screen_x - fr.get_width() // 2,
                (u.screen_y - fr.get_height()) - offset,
                fr.get_width(), fr.get_height()
            )
            if rect.collidepoint(mx, my):
                return self.select_unit_by_index(self.units.index(u))
        return False

    # ----------------------------------------------------
    #  Right-click orders (unchanged)
    # ----------------------------------------------------
    def handle_right_click(self, event):
        mx, my = event.pos
        zoom   = self.scene.zoom_scale
        offset = int(STACK_OFFSET * zoom)

        # 1) Click another biped → select
        for u in reversed(self.units):
            if not u.scaled_frames:
                continue
            fr = u.scaled_frames[u.current_frame]
            rect = pygame.Rect(
                u.screen_x - fr.get_width() // 2,
                (u.screen_y - fr.get_height()) - offset,
                fr.get_width(), fr.get_height()
            )
            if rect.collidepoint(mx, my):
                return self.select_unit_by_index(self.units.index(u))

        # 2) Issue orders if one is selected
        if not self.selected_unit:
            return

        # attack animal?
        target = None
        for a in reversed(self.scene.animal_manager.animals):
            if not a.alive or not a.scaled_frames:
                continue
            fr = a.scaled_frames[a.current_frame]
            rect = pygame.Rect(
                a.screen_x - fr.get_width() // 2,
                (a.screen_y - fr.get_height()) - offset,
                fr.get_width(), fr.get_height()
            )
            if rect.collidepoint(mx, my):
                target = a
                break

        if target:
            u = self.selected_unit
            u.target_unit = target
            u.mission = UnitMission.ATTACK
            u.attack_repath_timer = 0.0
            path = self.scene.find_path(
                int(round(u.x_f)), int(round(u.y_f)),
                int(round(target.x_f)), int(round(target.y_f))
            )
            if path:
                u.set_path(path)
            return

        # otherwise: move order
        tx, ty = screen_to_tile(
            mx, my,
            self.scene.map.camera_offset_x,
            self.scene.map.camera_offset_y,
            zoom
        )
        tx = max(0, min(tx, self.scene.map.width  - 1))
        ty = max(0, min(ty, self.scene.map.height - 1))
        path = self.scene.find_path(
            int(round(self.selected_unit.x_f)),
            int(round(self.selected_unit.y_f)),
            tx, ty
        )
        if path:
            self.selected_unit.set_path(path)
            self.selected_unit.destination_x = tx
            self.selected_unit.destination_y = ty

    # ----------------------------------------------------
    #  Boiler-plate update/draw
    # ----------------------------------------------------
    def handle_events(self, _events):
        pass

    def update(self, dt_ms: int):
        # 1) normal per-unit update
        for u in self.units:
            u.update(dt_ms)

        # 2) build new list of only living units
        alive_units = [u for u in self.units if getattr(u, "alive", True)]
        if len(alive_units) != len(self.units):
            # something died – reset list & HUD
            self.units = alive_units

            if self.selected_unit and not getattr(self.selected_unit, "alive", True):
                self.selected_unit = None

            if hasattr(self.scene, "hud"):
                self.scene.hud.refresh_bipeds(len(self.units))

    def calculate_screen_positions(self, cam_x, cam_y, zoom):
        for u in self.units:
            u.calculate_screen_position(cam_x, cam_y, zoom)

    def draw_units(self, surface, zoom=1.0):
        for u in sorted(self.units, key=lambda x: x.draw_order):
            u.draw(surface, None, zoom)