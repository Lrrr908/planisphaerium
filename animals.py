##########################################################
# animals.py · v2025-07-07 e — IRONCLAD ANCHOR POINT FIX
##########################################################

import math
import random
import pygame
from drop import DropObject

from iso_map import IsoObject, TILE_WIDTH, TILE_HEIGHT
from animal_ai import AnimalAI

STACK_OFFSET = 30

# ────────────────────────────────────────────────────────
# Visual / tuning
# ────────────────────────────────────────────────────────
ENABLE_PSEUDO_3D_SHADING = False
PLANET_LIGHT_ANGLE_DEGREES = 45

# Titan settings
TITAN_CHANCE = 100.0
TITAN_BIG_THRESHOLD = 200
TITAN_COLORS = [
    (255,  50, 200), ( 50, 255, 200), (255, 255,  50),
    (255, 120,  50), (180,  50, 255)
]
REALISTIC_COLORS = [
    (180, 140, 100), (200, 180, 150), ( 90,  60,  30),
    (120,  80,  60), (140, 180,  80)
]

STEP_CYCLE = [(0, 2), (1, 1), (2, 0), (1, 1)]

# Safety caps
MAX_ANIMALS = 500
MAX_DROPS   = 1000

##########################################################
# UTILITY
##########################################################
def _colorize_surface(orig_surf, color):
    surf = pygame.Surface(orig_surf.get_size(), pygame.SRCALPHA)
    w, h = orig_surf.get_size()
    for x in range(w):
        for y in range(h):
            px = orig_surf.get_at((x, y))
            if px.a:
                surf.set_at((x, y), (color[0], color[1], color[2], px.a))
    return surf

def _apply_vertical_gradient(surface, base_color, angle_deg):
    if not ENABLE_PSEUDO_3D_SHADING:
        return surface

    w, h = surface.get_size()
    grad = pygame.Surface((w, h), pygame.SRCALPHA)
    angle_norm = math.cos(math.radians(angle_deg))
    top_b = 1.0 + 0.2 * angle_norm
    bot_b = 1.0 - 0.2 * angle_norm
    for y in range(h):
        f = y / max(1, h - 1)
        b = top_b * (1 - f) + bot_b * f
        shaded = tuple(min(255, max(0, int(c * b))) for c in base_color)
        for x in range(w):
            a = surface.get_at((x, y)).a
            if a:
                grad.set_at((x, y), shaded + (a,))
    return grad

##########################################################
# PIXEL-ANIMAL SPRITE GENERATOR
##########################################################
def create_pixel_animal_frames_with_outline(
    body_color=(200, 100, 100), outline_color=(0, 0, 0),
    shadow_color=(0, 0, 0, 100), num_frames=4,
    width=96, height=80, body_width=18, body_height=12,
    leg_thickness=3, leg_length=8, tail_length=6,
    spike_count=0, head_count=1, head_radius=4,
    has_ears=False,  ear_size=1,
    has_horns=False, horn_length=2,
    has_snout=False, snout_length=2,
    has_wings=False, style_variant="normal"
):
    frames = []
    for i in range(num_frames):
        front_off, back_off = STEP_CYCLE[i % len(STEP_CYCLE)]

        base   = pygame.Surface((width, height), pygame.SRCALPHA)
        shadow = pygame.Surface((width, height), pygame.SRCALPHA)

        body_x = 10 if style_variant == "t_rex" else 4
        if style_variant == "t_rex":
            front_off = max(0, front_off - 1)

        body_y = (height // 2) - (body_height // 2)
        pygame.draw.rect(base, body_color, (body_x, body_y, body_width, body_height))

        # Body shadow
        sh_rect = pygame.Rect(body_x, body_y + body_height + 4, body_width, 4)
        pygame.draw.ellipse(shadow, shadow_color, sh_rect)

        # Spikes
        for s_i in range(spike_count):
            frac = s_i / (spike_count - 1) if spike_count > 1 else 0.5
            sx = int(body_x + frac * body_width)
            sy = body_y
            pygame.draw.polygon(base, body_color,
                                [(sx, sy - 3), (sx - 2, sy), (sx + 2, sy)])

        # Tail
        tail_y = body_y + body_height // 2
        pygame.draw.line(base, body_color,
                         (body_x, tail_y),
                         (body_x - tail_length, tail_y - 2),
                         leg_thickness)

        # Heads
        head_cx = (body_x + body_width // 2) if has_wings else (body_x + body_width + head_radius + 1)
        base_hcy = body_y + body_height // 2 - (8 if style_variant == "long_neck" else 0)
        for h in range(head_count):
            hcy = int(base_hcy + (h - (head_count - 1) / 2) * 2 * head_radius)
            pygame.draw.circle(base, body_color, (head_cx, hcy), head_radius)

            # Eye
            eye_w = max(2, head_radius // 2)
            eye_b = max(1, eye_w // 2)
            eye_c = (head_cx + eye_w, hcy - 1)
            pygame.draw.circle(base, (255, 255, 255), eye_c, eye_w)
            pygame.draw.circle(base, (0, 0, 0), eye_c, eye_b)

            if has_snout:
                pygame.draw.rect(
                    base, body_color,
                    (head_cx + head_radius - 1, hcy - head_radius // 2,
                     snout_length, head_radius))

        # Wings
        if has_wings:
            lt  = (body_x + 1, body_y)
            rt  = (body_x + body_width - 1, body_y)
            lte = (body_x -  8, body_y - 6 - (i % 2) * 2)
            rte = (body_x + body_width + 8, body_y - 6 + (i % 2) * 2)
            pygame.draw.line(base, body_color, lt,  lte, leg_thickness + 1)
            pygame.draw.line(base, body_color, rt,  rte, leg_thickness + 1)

        # Legs
        ly_top = body_y + body_height
        front_add, back_add = front_off, back_off
        if style_variant == "t_rex":
            front_add = max(0, front_off - 1)
            back_add  = back_off + 1
        legs = [
            (body_x + 2,              ly_top + leg_length + back_add),
            (body_x + 5,              ly_top + leg_length + back_add),
            (body_x + body_width - 2, ly_top + leg_length + front_add),
            (body_x + body_width - 5, ly_top + leg_length + front_add),
        ]
        for lx, ly in legs:
            pygame.draw.line(base, body_color, (lx, ly_top), (lx, ly), leg_thickness)

        # Outline
        outline = pygame.Surface((width, height), pygame.SRCALPHA)
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if not (ox or oy):
                    continue
                outline.blit(_colorize_surface(base, outline_color), (ox, oy))
        outline.blit(base, (0, 0))

        # Final frame
        final = pygame.Surface((width, height), pygame.SRCALPHA)
        final.blit(shadow, (0, 0))
        final.blit(_apply_vertical_gradient(outline, body_color,
                                            PLANET_LIGHT_ANGLE_DEGREES), (0, 0))
        frames.append(final)

    return frames

def create_pixel_animal_frames(*a, **kw):
    return create_pixel_animal_frames_with_outline(*a, **kw)

##########################################################
# IRONCLAD ANCHOR POINT CALCULATOR
##########################################################
def calculate_animal_anchor_point(frame):
    """
    IRONCLAD: Find the exact pixel location where the animal appears within its frame.
    This is the KEY to fixing teleporting - we need to know where the animal 
    actually is within the frame, not just assume it's centered.
    """
    if not frame:
        return (0, 0)
        
    width, height = frame.get_size()
    
    # Find all non-transparent pixels
    pixels = []
    for y in range(height):
        for x in range(width):
            pixel = frame.get_at((x, y))
            if pixel.a > 20:  # Non-transparent pixel (with anti-aliasing threshold)
                pixels.append((x, y))
    
    if not pixels:
        return (width // 2, height // 2)  # Fallback to frame center
    
    # Calculate weighted center based on actual pixel density
    # This gives us the visual center of mass of the animal
    total_weight = 0
    weighted_x = 0
    weighted_y = 0
    
    for x, y in pixels:
        # Weight pixels near the center more heavily (body vs extremities)
        weight = frame.get_at((x, y)).a / 255.0  # Use alpha as weight
        weighted_x += x * weight
        weighted_y += y * weight
        total_weight += weight
    
    if total_weight > 0:
        anchor_x = weighted_x / total_weight
        anchor_y = weighted_y / total_weight
    else:
        # Fallback: geometric center of bounding box
        min_x = min(p[0] for p in pixels)
        max_x = max(p[0] for p in pixels)
        min_y = min(p[1] for p in pixels)
        max_y = max(p[1] for p in pixels)
        anchor_x = (min_x + max_x) / 2
        anchor_y = (min_y + max_y) / 2
    
    return (anchor_x, anchor_y)

##########################################################
# 3) ANIMAL UNIT - IRONCLAD POSITIONING
##########################################################
class AnimalUnit(IsoObject):
    def __init__(self, scene, tile_x, tile_y, frames, speed=1.0,
                 territory_radius=5, growth_scale=1.0, growth_rate=0.02,
                 founder_unit=None, species_id=None, can_reproduce=True,
                 titan_mode=True):
        
        # CRITICAL: Animals render below trees - use proper layer offset
        draw_order = (tile_x + tile_y) * 10 + 2  # Layer 2: above terrain, below trees
        super().__init__(grid_x=tile_x, grid_y=tile_y, draw_order=draw_order)
        
        self.scene = scene

        self.x_f, self.y_f = float(tile_x), float(tile_y)

        self.original_frames = frames
        self.scaled_frames   = frames[:]
        
        # IRONCLAD: Pre-calculate anchor points for both directions
        self.anchor_right = calculate_animal_anchor_point(frames[0]) if frames else (0, 0)
        print(f"[ANCHOR] Animal anchor point: {self.anchor_right}")
        
        # PRE-GENERATE both directions with CONSISTENT positioning
        self.frames_right = frames[:]
        self.frames_left = [pygame.transform.flip(f, True, False) for f in frames]
        
        # CRITICAL: Calculate left anchor point after flipping
        if self.frames_left:
            flipped_frame = self.frames_left[0]
            frame_width = flipped_frame.get_width()
            # When flipped, the anchor X coordinate is mirrored across the frame center
            self.anchor_left = (frame_width - self.anchor_right[0], self.anchor_right[1])
        else:
            self.anchor_left = self.anchor_right
        
        print(f"[ANCHOR] Right anchor: {self.anchor_right}, Left anchor: {self.anchor_left}")
        
        self.current_frame   = 0
        self.facing_left     = False

        self.speed            = speed
        self.home_tile        = (tile_x, tile_y)
        self.territory_radius = territory_radius
        self.growth_scale     = growth_scale
        self.growth_rate      = growth_rate
        self.founder_unit     = founder_unit
        self.species_id       = species_id
        self.can_reproduce    = can_reproduce
        self.titan_mode       = titan_mode

        # SIMPLIFIED direction system - just face the direction you're moving
        self.visual_facing_left = False  # What we're actually displaying
        self.direction_lock_timer = 0.0  # Minimal cooldown to prevent rapid flipping
        self.direction_lock_duration = 0.3  # Very short - just prevent rapid flipping

        # Smooth movement variables
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.target_x = float(tile_x)
        self.target_y = float(tile_y)
        self.max_speed = speed
        self.acceleration = 2.0

        # Animation timing
        self.animation_timer = 0.0
        self.animation_speed = 8.0
        
        # IRONCLAD: Fixed screen position - this NEVER changes once calculated
        self.fixed_screen_x = 0
        self.fixed_screen_y = 0
        
        # Movement tracking
        self.path_tiles  = []
        self.path_index  = 0
        self.roam_timer  = 0.0

        # Combat
        self.health          = 10
        self.attack_power    = 3
        self.attack_range    = 1.0
        self.attack_speed    = 0.5
        self.attack_cooldown = 0.0

        self.target_unit = None
        self.mission     = None

        # Behaviour
        self.hunger              = random.uniform(0, 0.5)
        self.energy              = random.uniform(0.5, 1.0)
        self.aggression          = random.uniform(0.0, 1.4)
        self.in_attack_animation = False
        self.attack_anim_timer   = 0.0
        self.diet               = "herbivore"

        # Life / death
        self.alive    = True
        self._is_dead = False

        self.ai = AnimalAI(self)
        
        # CRITICAL: Initialize everything immediately
        self.set_zoom_scale(1.0)
        self.calculate_screen_position(
            scene.map.camera_offset_x,
            scene.map.camera_offset_y,
            scene.zoom_scale
        )

    # ───────────────────────────────────────────────
    # Randomised loot table
    # ───────────────────────────────────────────────
    def _roll_drops(self):
        tbl = {}
        if random.random() < 0.75:
            tbl["meat"] = random.randint(1, 3)
        if random.random() < 0.50:
            tbl["bones"] = random.randint(1, 2)
        if random.random() < 0.40:
            tbl["leather"] = 1
        return tbl

    # ───────────────────────────────────────────────
    # Core update
    # ───────────────────────────────────────────────
    def set_zoom_scale(self, zoom_scale):
        final_zoom = zoom_scale * self.growth_scale
        
        # Update both right and left facing frames
        self.frames_right = [
            pygame.transform.smoothscale(
                f,
                (max(1, int(f.get_width()  * final_zoom)),
                 max(1, int(f.get_height() * final_zoom)))
            )
            for f in self.original_frames
        ]
        
        # Update left frames by flipping the scaled right frames
        self.frames_left = [
            pygame.transform.flip(frame, True, False) 
            for frame in self.frames_right
        ]
        
        # Update scaled_frames for compatibility
        self.scaled_frames = self.frames_right[:]
        
        # IRONCLAD: Scale anchor points to match zoom
        self.scaled_anchor_right = (
            self.anchor_right[0] * final_zoom,
            self.anchor_right[1] * final_zoom
        )
        self.scaled_anchor_left = (
            self.anchor_left[0] * final_zoom,
            self.anchor_left[1] * final_zoom
        )

    def update(self, dt):
        if self._is_dead:
            return

        seconds = dt * 0.001
        if self.growth_scale < 1.0:
            self.growth_scale = min(self.growth_scale + self.growth_rate * seconds, 1.0)

        # Update direction lock timer
        if self.direction_lock_timer > 0:
            self.direction_lock_timer -= seconds

        # REVAMPED MOVEMENT UPDATE - Smooth physics-based movement
        self._update_smooth_movement(seconds)

        self.ai.update(dt)

        # Universal death check
        if self.health <= 0:
            self._die()

    # ───────────────────────────────────────────────
    # REVAMPED MOVEMENT SYSTEM - Simple and smooth
    # ───────────────────────────────────────────────
    def _update_smooth_movement(self, seconds):
        # Update target position based on current path
        if self.path_tiles and self.path_index < len(self.path_tiles):
            self.target_x, self.target_y = self.path_tiles[self.path_index]
            
            # Check if we're close enough to current waypoint to advance
            dist_to_target = math.hypot(self.target_x - self.x_f, self.target_y - self.y_f)
            if dist_to_target < 0.15:
                self.path_index += 1
                if self.path_index < len(self.path_tiles):
                    self.target_x, self.target_y = self.path_tiles[self.path_index]
        
        # Calculate desired velocity towards target
        target_dx = self.target_x - self.x_f
        target_dy = self.target_y - self.y_f
        target_distance = math.hypot(target_dx, target_dy)
        
        if target_distance > 0.01:
            # Normalize direction and scale by max speed
            desired_velocity_x = (target_dx / target_distance) * self.max_speed
            desired_velocity_y = (target_dy / target_distance) * self.max_speed
            
            # SIMPLE DIRECTION LOGIC: Just face the direction you're moving!
            if self.direction_lock_timer <= 0 and abs(desired_velocity_x) > 0.2:
                old_facing = self.visual_facing_left
                
                if desired_velocity_x < -0.1:
                    self.visual_facing_left = True
                elif desired_velocity_x > 0.1:
                    self.visual_facing_left = False
                
                if old_facing != self.visual_facing_left:
                    self.direction_lock_timer = self.direction_lock_duration
                    print(f"Animal {getattr(self, 'species_id', 'unknown')} facing {'LEFT' if self.visual_facing_left else 'RIGHT'}")
            
            # Smooth velocity interpolation
            velocity_diff_x = desired_velocity_x - self.velocity_x
            velocity_diff_y = desired_velocity_y - self.velocity_y
            
            max_accel_this_frame = self.acceleration * seconds
            velocity_change_magnitude = math.hypot(velocity_diff_x, velocity_diff_y)
            
            if velocity_change_magnitude > max_accel_this_frame:
                scale = max_accel_this_frame / velocity_change_magnitude
                velocity_diff_x *= scale
                velocity_diff_y *= scale
            
            self.velocity_x += velocity_diff_x
            self.velocity_y += velocity_diff_y
            
            # Update animation
            current_speed = math.hypot(self.velocity_x, self.velocity_y)
            if current_speed > 0.1:
                self.animation_timer += seconds * self.animation_speed * current_speed
                self.current_frame = int(self.animation_timer) % len(self.scaled_frames)
        else:
            # Gradually stop when no target
            self.velocity_x *= (1.0 - seconds * 5.0)
            self.velocity_y *= (1.0 - seconds * 5.0)
            
            if math.hypot(self.velocity_x, self.velocity_y) < 0.05:
                self.velocity_x = 0.0
                self.velocity_y = 0.0
        
        # Apply velocity to position
        self.x_f += self.velocity_x * seconds
        self.y_f += self.velocity_y * seconds
        
        # Update grid position and draw order
        self.grid_x = int(round(self.x_f))
        self.grid_y = int(round(self.y_f))
        self.draw_order = (self.grid_x + self.grid_y) * 10 + 2
        
        # Update facing for compatibility
        self.facing_left = self.visual_facing_left

    # ───────────────────────────────────────────────
    # Combat and drop spawning (unchanged)
    # ───────────────────────────────────────────────
    def _attack_logic(self, dt):
        if not self.target_unit or not self.target_unit.alive:
            self.mission = None
            return

        dist = math.hypot(
            self.target_unit.x_f - self.x_f,
            self.target_unit.y_f - self.y_f
        )

        if dist <= self.attack_range:
            self.attack_cooldown -= dt * 0.001
            if self.attack_cooldown <= 0:
                self.in_attack_animation = True
                self.attack_anim_timer   = 0.25

                self.target_unit.health -= self.attack_power
                print(f"Animal attacks {self.target_unit} for {self.attack_power} dmg")

                if self.target_unit.health <= 0 and hasattr(self.target_unit, "_die"):
                    self.target_unit._die()

                self.attack_cooldown = 1.0 / self.attack_speed
        else:
            self._move_toward(
                (self.target_unit.grid_x, self.target_unit.grid_y),
                dt
            )

    def _spawn_drops(self, victim):
        drops = victim._roll_drops()
        if not drops:
            return

        for resource, qty in drops.items():
            drop_obj = DropObject(victim.grid_x, victim.grid_y, resource, qty)
            drop_obj.calculate_screen_position(
                self.scene.map.camera_offset_x,
                self.scene.map.camera_offset_y,
                self.scene.zoom_scale
            )
            self.scene.drops.append(drop_obj)
            print(f"Spawned {qty} × {resource} at ({victim.grid_x},{victim.grid_y})")

    def _die(self):
        if self._is_dead:
            return
        self._is_dead = True
        self.alive    = False
        self._spawn_drops(self)

    # ───────────────────────────────────────────────
    # Movement helpers - simple
    # ───────────────────────────────────────────────
    def _move_toward(self, target_tile, dt):
        """Simple move_toward using smooth movement system"""
        self.target_x, self.target_y = target_tile
        self.path_tiles = []
        self.path_index = 0

    def _update_move(self, seconds):
        """Legacy method - now handled by _update_smooth_movement"""
        pass

    # ───────────────────────────────────────────────
    # IRONCLAD SCREEN POSITIONING - The key fix!
    # ───────────────────────────────────────────────
    def calculate_screen_position(self, cam_x, cam_y, zoom_scale=1.0):
        """
        IRONCLAD: Calculate the exact screen position where the animal should appear.
        This position NEVER changes based on facing direction.
        """
        # Standard isometric transformation
        iso_x = (self.x_f - self.y_f) * (TILE_WIDTH // 2) * zoom_scale
        iso_y = (self.x_f + self.y_f) * (TILE_HEIGHT // 2) * zoom_scale
        
        # Add terrain height offset if using layered terrain
        terrain_height_offset = 0
        if hasattr(self.scene, 'use_layered_terrain') and self.scene.use_layered_terrain:
            if hasattr(self.scene, 'terrain'):
                try:
                    terrain_height = self.scene.terrain.get_height_at(self.grid_x, self.grid_y)
                    terrain_height_offset = terrain_height * 16 * zoom_scale
                except:
                    terrain_height_offset = 0
        
        # IRONCLAD: This is where the animal should visually appear on screen
        # This position NEVER changes regardless of facing direction
        self.fixed_screen_x = int(iso_x + cam_x)
        self.fixed_screen_y = int(iso_y + cam_y - terrain_height_offset)
        
        # Set stable position for compatibility
        self.screen_x = self.fixed_screen_x
        self.screen_y = self.fixed_screen_y
        self.stable_screen_x = self.fixed_screen_x
        self.stable_screen_y = self.fixed_screen_y

    def draw(self, surface, tree_images=None, zoom_scale=1.0):
        """
        IRONCLAD DRAWING: Animal always appears at the same screen position
        regardless of facing direction. This is THE fix for teleporting.
        """
        if self._is_dead:
            return

        # Choose the correct frame based on direction
        if self.visual_facing_left:
            if hasattr(self, 'frames_left') and self.frames_left:
                frame_surf = self.frames_left[self.current_frame]
                current_anchor = self.scaled_anchor_left if hasattr(self, 'scaled_anchor_left') else (0, 0)
            else:
                frame_surf = pygame.transform.flip(self.scaled_frames[self.current_frame], True, False)
                current_anchor = (0, 0)  # Fallback
        else:
            if hasattr(self, 'frames_right') and self.frames_right:
                frame_surf = self.frames_right[self.current_frame]
                current_anchor = self.scaled_anchor_right if hasattr(self, 'scaled_anchor_right') else (0, 0)
            else:
                frame_surf = self.scaled_frames[self.current_frame]
                current_anchor = (0, 0)  # Fallback

        if not frame_surf:
            return

        # IRONCLAD POSITIONING: Always position so the animal's anchor point 
        # appears at the fixed screen position, regardless of facing direction
        frame_w, frame_h = frame_surf.get_width(), frame_surf.get_height()
        
        # Calculate where to draw the frame so the animal appears at fixed_screen position
        draw_x = self.fixed_screen_x - current_anchor[0]
        draw_y = self.fixed_screen_y - current_anchor[1] - int(frame_h * 0.8)  # Slight offset for ground level
        
        # Draw the frame at the calculated position
        surface.blit(frame_surf, (draw_x, draw_y))
        
        # DEBUG: Show anchor point (remove this in production)
        if getattr(self.scene, 'debug_mode', False):
            pygame.draw.circle(surface, (255, 0, 0), (self.fixed_screen_x, self.fixed_screen_y), 3)

##########################################################
# 4) ANIMAL MANAGER  — unchanged
##########################################################

class AnimalManager:
    def __init__(self, scene):
        self.scene = scene
        self.animals = []
        self.next_species_id = 1
        self.species_founders = {}
        self.growth_timer = 0.0
        self.GROWTH_INTERVAL = 30.0
        self.GROWTH_MAX_TIMES = 3
        self.growth_count = 0

    def spawn_random_animals(self, override_count=None, override_positions=None):
        if override_positions is not None:
            valid_positions = override_positions
        else:
            valid_positions = []
            for y in range(self.scene.map.height):
                for x in range(self.scene.map.width):
                    if self.scene.forest_map[y][x] > 0:
                        if (x, y) not in self.scene.blocked_tiles:
                            valid_positions.append((x, y))

        if not valid_positions:
            print("No valid tiles to spawn animals.")
            return

        if override_count is not None:
            total_species = override_count
        else:
            if len(valid_positions) < 100:
                total_species = 5
            elif len(valid_positions) < 500:
                total_species = 8
            else:
                total_species = 12

        for _ in range(total_species):
            frames, titan = self._build_random_frames()
            speed = 0.5 if titan else 0.8
            territory = random.randint(5, 10)
            sid = self.next_species_id
            self.next_species_id += 1

            spawn_pos = random.choice(valid_positions)
            founder_animal = AnimalUnit(
                scene=self.scene,
                tile_x=spawn_pos[0],
                tile_y=spawn_pos[1],
                frames=frames,
                speed=speed,
                territory_radius=territory,
                growth_scale=1.0,
                growth_rate=0.02,
                founder_unit=None,
                species_id=sid,
                can_reproduce=True,
                titan_mode=titan
            )
            
            self.animals.append(founder_animal)
            self.species_founders[sid] = founder_animal

    def _build_random_frames(self):
        titan = random.random() < TITAN_CHANCE

        if titan:
            color = random.choice(TITAN_COLORS)
        else:
            if random.random() < 0.5:
                color = random.choice(REALISTIC_COLORS)
            else:
                color = (
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255)
                )

        body_w = random.randint(15, 50)
        body_h = random.randint(8, 20)
        leg_len = random.randint(6, 15)
        tail_len = random.randint(4, 12)
        leg_thick = random.randint(2, 5)
        head_rad = random.randint(3, 10)
        head_count = 1
        if random.random() < 0.1:
            head_count = 2
        has_ears = random.random() < 0.3
        ear_size = random.randint(1, 3)
        has_horns = random.random() < 0.2
        horn_len = random.randint(2, 5)
        has_snout = random.random() < 0.4
        snout_len = random.randint(2, 6)
        has_wings = random.random() < 0.15
        spike_c = 0
        if body_w > 25 and random.random() < 0.4:
            spike_c = random.randint(2, 5)

        style_variants = ["normal", "t_rex", "long_neck"]
        style = random.choice(style_variants)

        if titan:
            w_surf = 300
            h_surf = 300
        elif body_w > 30:
            w_surf = 80 + body_w + tail_len + head_rad + leg_len
            h_surf = 80 + body_h + head_rad
        else:
            w_surf = 60 + body_w + tail_len + head_rad + leg_len
            h_surf = 60 + body_h + head_rad

        frames = create_pixel_animal_frames_with_outline(
            body_color=color,
            outline_color=(0, 0, 0),
            shadow_color=(0, 0, 0, 120),
            num_frames=4,
            width=w_surf,
            height=h_surf,
            body_width=body_w,
            body_height=body_h,
            leg_thickness=leg_thick,
            leg_length=leg_len,
            tail_length=tail_len,
            head_count=head_count,
            head_radius=head_rad,
            has_ears=has_ears,
            ear_size=ear_size,
            has_horns=has_horns,
            horn_length=horn_len,
            has_snout=has_snout,
            snout_length=snout_len,
            has_wings=has_wings,
            spike_count=spike_c,
            style_variant=style
        )
        return frames, titan

    def update(self, dt):
        for a in self.animals:
            a.update(dt)

        # SAFETY: cap animal count
        if len(self.animals) > MAX_ANIMALS:
            print(f"[AnimalManager] Animal cap reached: {len(self.animals)} animals. Skipping doubling.")
            return

        if self.growth_count < self.GROWTH_MAX_TIMES:
            self.growth_timer += dt * 0.001
            if self.growth_timer > self.GROWTH_INTERVAL:
                self.growth_timer = 0.0
                self._double_animals()
                self.growth_count += 1

    def _double_animals(self):
        new_list = []
        for a in self.animals:
            if not a.alive or not a.can_reproduce:
                continue
            sid = a.species_id
            if sid not in self.species_founders:
                continue
            founder = self.species_founders[sid]
            if not founder.alive:
                continue

            nx = a.grid_x + random.randint(-2, 2)
            ny = a.grid_y + random.randint(-2, 2)
            nx = max(0, min(nx, self.scene.map.width - 1))
            ny = max(0, min(ny, self.scene.map.height - 1))

            if (nx, ny) in self.scene.blocked_tiles:
                continue

            if any(
                other.grid_x == nx and other.grid_y == ny
                for other in self.animals
            ):
                continue

            baby_scale = 0.3
            baby_grow = 0.015
            clone = AnimalUnit(
                scene=self.scene,
                tile_x=nx,
                tile_y=ny,
                frames=a.original_frames,
                speed=a.speed,
                territory_radius=a.territory_radius,
                growth_scale=baby_scale,
                growth_rate=baby_grow,
                founder_unit=founder,
                species_id=sid,
                can_reproduce=True,
                titan_mode=a.titan_mode
            )
            
            clone.facing_left = a.facing_left
            new_list.append(clone)

        if len(self.animals) + len(new_list) > MAX_ANIMALS:
            new_list = new_list[: MAX_ANIMALS - len(self.animals)]
            print("[AnimalManager] Animal doubling capped due to max limit.")

        self.animals.extend(new_list)

    def kill_animal(self, animal):
        animal.alive = False
        sid = animal.species_id
        if sid in self.species_founders and self.species_founders[sid] is animal:
            self.species_founders[sid].alive = False

    def calculate_screen_positions(self, cam_x, cam_y, zoom_scale):
        for a in self.animals:
            a.set_zoom_scale(zoom_scale)
            a.calculate_screen_position(cam_x, cam_y, zoom_scale)

    def set_zoom_scale(self, zoom_scale):
        for a in self.animals:
            a.set_zoom_scale(zoom_scale)

    def draw(self, surface, zoom_scale=1.0):
        for a in sorted(self.animals, key=lambda a: a.draw_order):
            a.draw(surface, None, zoom_scale)

    def add_animal(self, animal):
        # CRITICAL: Calculate screen position immediately when adding animals
        animal.calculate_screen_position(
            self.scene.map.camera_offset_x,
            self.scene.map.camera_offset_y,
            self.scene.zoom_scale
        )
        self.animals.append(animal)