"""
Planet View
Simple Arcade-based isometric 3D world view - Minecraft Style
"""

import arcade
from arcade import View
from typing import List, Dict, Tuple, Optional, Set
import random
import math

from ..core.constants import *
from ..world.world_generator import WorldGenerator, Block
from ..entities.biped import Biped, BipedJob
from ..entities.animal import Animal, AnimalType
from ..ui.hud import HUD
from ..systems.game_state import GameState
from ..entities.entity import EntityType
from ..systems.pathfinding import Pathfinder

# Isometric constants
TILE_WIDTH = 64
TILE_HEIGHT = 32
BLOCK_HEIGHT = 16

class PlanetView(View):
    """Simple Arcade planet view with isometric 3D Minecraft-style world"""
    
    def __init__(self, game_window):
        super().__init__()
        self.game_window = game_window
        self.game_state = game_window.game_state
        
        # Simple camera system
        self.camera_offset_x = 0
        self.camera_offset_y = 0
        self.zoom_scale = 1.0
        
        # Mouse controls
        self.mouse_dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # World - Single plane for simplicity
        self.grid_width = 15  # Smaller grid for testing
        self.grid_height = 15
        self.grid_blocks = {}  # Simple dict: (x, y) -> block_data
        
        # Pathfinding system
        self.pathfinder = Pathfinder(self.grid_width, self.grid_height)
        
        # Entities (simple dictionaries)
        self.bipeds: List[Dict] = []
        self.animals: List[Dict] = []
        self.houses: List[Dict] = []
        self.selected_entities: Set[str] = set()
        
        # UI
        self.hud = HUD(self)
        
        # Debug
        self.show_debug = False
        self.show_grid = False
        
        # Time counter for effects
        self.time_counter = 0.0
        
        # Initialize
        self.setup_simple_world()
        self.setup_entities()
        
    def setup_simple_world(self):
        """Set up a simple single-plane isometric grid"""
        print("[PlanetView] Generating simple grid...")
        
        # Create a simple grid of blocks
        for grid_x in range(-self.grid_width//2, self.grid_width//2):
            for grid_y in range(-self.grid_height//2, self.grid_height//2):
                # Simple block data
                block_data = {
                    'block_type': 'grass',
                    'layer': 0,  # All blocks on same layer (no stacking)
                    'top_color': arcade.color.GREEN,
                    'left_color': (100, 150, 100),  # Darker green
                    'right_color': (120, 170, 120),  # Medium green
                    'grid_x': grid_x,
                    'grid_y': grid_y,
                    'depth': self.calculate_depth(grid_x, grid_y, 0)
                }
                self.grid_blocks[(grid_x, grid_y)] = block_data
                
        print(f"[PlanetView] Generated {len(self.grid_blocks)} blocks in a single plane")
        
    def setup_entities(self):
        """Set up initial entities on the simple grid"""
        # Create bipeds
        for i in range(3):
            grid_x = random.randint(-5, 5)
            grid_y = random.randint(-5, 5)
            
            iso_x, iso_y = self.grid_to_iso(grid_x, grid_y, 0)
            
            biped = {
                'id': f"biped_{i}",
                'iso_x': iso_x,
                'iso_y': iso_y,
                'grid_x': grid_x,
                'grid_y': grid_y,
                'color': (0, 255, 0),
                'width': 16,
                'height': 24,
                'depth': self.calculate_depth(grid_x, grid_y, 0),
                'job': random.choice(list(BipedJob)).value,
                'health': 100,
                'max_health': 100,
                # Movement and animation properties
                'target_x': grid_x,
                'target_y': grid_y,
                'path': [],
                'path_index': 0,
                'is_moving': False,
                'animation_frame': 0,
                'animation_speed': 0.2,
                'last_animation_time': 0
            }
            self.bipeds.append(biped)
            
        # Create animals
        for i in range(8):
            grid_x = random.randint(-7, 7)
            grid_y = random.randint(-7, 7)
            
            iso_x, iso_y = self.grid_to_iso(grid_x, grid_y, 0)
            
            animal = {
                'id': f"animal_{i}",
                'iso_x': iso_x,
                'iso_y': iso_y,
                'grid_x': grid_x,
                'grid_y': grid_y,
                'color': random.choice([(255, 165, 0), (255, 0, 255), (0, 255, 255), (255, 255, 0)]),
                'radius': random.randint(6, 12),
                'depth': self.calculate_depth(grid_x, grid_y, 0),
                'shape': random.choice(['circle', 'square', 'triangle']),
                'health': 50,
                'max_health': 50,
                # Movement properties
                'target_x': grid_x,
                'target_y': grid_y,
                'path': [],
                'path_index': 0,
                'is_moving': False,
                'move_timer': 0,
                'move_interval': random.uniform(2.0, 5.0)
            }
            self.animals.append(animal)
            
    def grid_to_iso(self, grid_x: int, grid_y: int, height: int = 0) -> Tuple[float, float]:
        """Convert grid coordinates to isometric screen coordinates"""
        iso_x = (grid_x - grid_y) * (TILE_WIDTH // 2)
        iso_y = (grid_x + grid_y) * (TILE_HEIGHT // 2)
        iso_y -= height * BLOCK_HEIGHT  # Height offset
        return iso_x, iso_y
        
    def iso_to_grid(self, iso_x: float, iso_y: float) -> Tuple[int, int]:
        """Convert isometric coordinates to grid coordinates (approximate)"""
        # Simplified reverse conversion
        grid_sum = (iso_y * 2) / TILE_HEIGHT
        grid_diff = (iso_x * 2) / TILE_WIDTH
        grid_x = int((grid_sum + grid_diff) / 2)
        grid_y = int((grid_sum - grid_diff) / 2)
        return grid_x, grid_y
        
    def calculate_depth(self, grid_x: int, grid_y: int, layer: int) -> float:
        """Calculate depth for proper sorting - FIXED FOR CORRECT 3D ORDERING"""
        # For proper 3D stacking:
        # 1) grid_x + grid_y determines back-to-front order (higher = further back = drawn first)
        # 2) layer determines bottom-to-top order (higher = higher up = drawn later)
        # 3) Multiply by large numbers to ensure proper separation
        # FIXED: Lower values = drawn first (back), higher values = drawn last (front)
        # REVERSED: Blocks closer to bottom of screen (viewer) should have LOWER depth values
        return -(grid_x + grid_y) * 10000 + layer * 100
        
    def on_draw(self):
        """Render the scene"""
        self.clear()
        
        # Set background color
        arcade.set_background_color((135, 206, 235))  # Sky blue
        
        # Calculate visible area for culling - smaller margin for performance
        margin = 100  # Reduced from 200
        screen_left = (-self.camera_offset_x - margin) / self.zoom_scale
        screen_right = (-self.camera_offset_x + self.width + margin) / self.zoom_scale
        screen_bottom = (-self.camera_offset_y - margin) / self.zoom_scale
        screen_top = (-self.camera_offset_y + self.height + margin) / self.zoom_scale
        
        # Filter visible blocks
        visible_blocks = []
        for block in self.grid_blocks.values():
            iso_x, iso_y = self.grid_to_iso(block['grid_x'], block['grid_y'], block['layer'])
            if (screen_left <= iso_x <= screen_right and screen_bottom <= iso_y <= screen_top):
                visible_blocks.append(block)
                
        # Sort blocks for proper depth rendering - FIXED DEPTH SORTING
        # Sort by: 1) grid_x + grid_y (back to front), 2) layer (bottom to top)
        # FIXED: Sort by depth in ascending order (back to front)
        visible_blocks.sort(key=lambda b: b['depth'])
        
        # Draw terrain blocks
        blocks_drawn = 0
        for block in visible_blocks:
            self.draw_3d_block(block)
            blocks_drawn += 1
            
        # Collect and sort all entities
        all_entities = []
        for biped in self.bipeds:
            all_entities.append(('biped', biped))
        for animal in self.animals:
            all_entities.append(('animal', animal))
        for house in self.houses:
            all_entities.append(('house', house))
            
        # Sort entities by depth - FIXED ENTITY SORTING
        # FIXED: Sort by depth in ascending order (back to front)
        all_entities.sort(key=lambda e: e[1]['depth'])
        
        # Draw entities
        for entity_type, entity in all_entities:
            self.draw_entity(entity_type, entity)
            
        # Draw HUD
        self.hud.draw()
        
        # Draw debug info
        if self.show_debug:
            self.draw_debug_info(blocks_drawn)
            
        # Draw grid if enabled
        if self.show_grid:
            self.draw_debug_grid()
            
    def draw_3d_block(self, block: Dict):
        """Draw a 3D isometric block - SIMPLIFIED FOR PERFORMANCE"""
        # Get screen position
        iso_x, iso_y = self.grid_to_iso(block['grid_x'], block['grid_y'], block['layer'])
        center_x = iso_x * self.zoom_scale + self.camera_offset_x
        center_y = iso_y * self.zoom_scale + self.camera_offset_y
        
        # Scale dimensions
        tile_w = TILE_WIDTH * self.zoom_scale
        tile_h = TILE_HEIGHT * self.zoom_scale
        block_depth = BLOCK_HEIGHT * self.zoom_scale
        
        # Level of detail - simplify when zoomed out
        if self.zoom_scale < 0.3:
            left = center_x - tile_w//2
            right = center_x + tile_w//2
            bottom = center_y - tile_h//2
            top = center_y + tile_h//2
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, block['top_color'])
            return
            
        # Define diamond points for top face
        top_left = (center_x - tile_w//2, center_y)
        top_right = (center_x + tile_w//2, center_y)
        top_top = (center_x, center_y + tile_h//2)
        top_bottom = (center_x, center_y - tile_h//2)
        
        # Draw faces in correct order for depth: left, right, then top
        # Left face (darkest)
        left_points = [
            top_left,
            top_bottom,
            (top_bottom[0], top_bottom[1] - block_depth),
            (top_left[0], top_left[1] - block_depth)
        ]
        arcade.draw_polygon_filled(left_points, block['left_color'])
        
        # Right face (medium)
        right_points = [
            top_bottom,
            top_right,
            (top_right[0], top_right[1] - block_depth),
            (top_bottom[0], top_bottom[1] - block_depth)
        ]
        arcade.draw_polygon_filled(right_points, block['right_color'])
        
        # Top face (lightest) - drawn last so it's on top
        top_points = [top_top, top_right, top_bottom, top_left]
        arcade.draw_polygon_filled(top_points, block['top_color'])
        
        # Draw outlines when zoomed in - SIMPLIFIED
        if self.zoom_scale > 0.8:
            arcade.draw_polygon_outline(left_points, arcade.color.BLACK, 1)
            arcade.draw_polygon_outline(right_points, arcade.color.BLACK, 1)
            arcade.draw_polygon_outline(top_points, arcade.color.BLACK, 1)
            
    def draw_block_effects(self, x: float, y: float, block: Block, width: float, height: float):
        """Draw special effects for certain block types"""
        if block.block_type == 'water':
            # Water ripple
            ripple_time = self.time_counter * 2
            ripple_offset = math.sin(ripple_time + x * 0.01) * 2
            arcade.draw_circle_filled(x + ripple_offset, y, 2, (255, 255, 255, 100))
            
        elif 'ore' in block.block_type:
            # Ore sparkle
            sparkle_time = self.time_counter * 3
            if math.sin(sparkle_time + x * 0.1) > 0.7:
                color = (255, 255, 255) if 'diamond' in block.block_type else (255, 255, 0)
                arcade.draw_circle_filled(
                    x + random.randint(-int(width//4), int(width//4)),
                    y + random.randint(-int(height//4), int(height//4)),
                    1, color
                )
                
        elif block.block_type == 'leaves':
            # Leaf movement
            sway_time = self.time_counter * 1.5
            sway_offset = math.sin(sway_time + x * 0.02) * 1
            arcade.draw_circle_filled(x + sway_offset, y + height//4, 1, (100, 255, 100))
            
    def draw_entity(self, entity_type: str, entity: Dict):
        """Draw an entity"""
        x = entity['iso_x'] * self.zoom_scale + self.camera_offset_x
        y = entity['iso_y'] * self.zoom_scale + self.camera_offset_y
        
        # Only draw if visible
        if not (-50 <= x <= self.width + 50 and -50 <= y <= self.height + 50):
            return
            
        # Draw selection indicator
        if entity['id'] in self.selected_entities:
            arcade.draw_circle_outline(x, y + 20, 15, arcade.color.YELLOW, 3)
            
        if entity_type == 'biped':
            # Draw biped with Zelda-style character
            self.draw_biped_character(entity, x, y)
            
        elif entity_type == 'animal':
            # Draw animal
            if entity['shape'] == 'circle':
                r = entity['radius'] * self.zoom_scale
                arcade.draw_circle_filled(x, y, r, entity['color'])
                arcade.draw_circle_outline(x, y, r, arcade.color.BLACK, 1)
            elif entity['shape'] == 'square':
                size = entity['radius'] * self.zoom_scale
                left = x - size
                right = x + size
                bottom = y - size
                top = y + size
                arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, entity['color'])
                arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, arcade.color.BLACK)
            elif entity['shape'] == 'triangle':
                size = entity['radius'] * self.zoom_scale
                points = [(x, y + size), (x - size, y - size), (x + size, y - size)]
                arcade.draw_polygon_filled(points, entity['color'])
                arcade.draw_polygon_outline(points, arcade.color.BLACK, 1)
                 
        elif entity_type == 'house':
             # Draw house
             w = entity['width'] * self.zoom_scale
             h = entity['height'] * self.zoom_scale
             left = x - w//2
             right = x + w//2
             bottom = y - h//2
             top = y + h//2
             arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, entity['color'])
             arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, arcade.color.BLACK)
            
    def draw_biped_character(self, biped: Dict, x: float, y: float):
        """Draw a simple biped character with walking animation"""
        scale = self.zoom_scale
        
        # Job colors
        job_colors = {
            'worker': (100, 149, 237),
            'builder': (255, 140, 0),
            'farmer': (34, 139, 34),
            'hunter': (139, 69, 19),
            'scientist': (138, 43, 226),
            'soldier': (220, 20, 60),
        }
        
        job_color = job_colors.get(biped['job'], (0, 255, 0))
        
        # Body
        body_size = 8 * scale
        arcade.draw_circle_filled(x, y, body_size, job_color)
        arcade.draw_circle_outline(x, y, body_size, arcade.color.BLACK, 1)
        
        # Head
        head_size = 6 * scale
        arcade.draw_circle_filled(x, y + body_size + head_size//2, head_size, (255, 220, 177))
        arcade.draw_circle_outline(x, y + body_size + head_size//2, head_size, arcade.color.BLACK, 1)
        
        # Simple eyes
        if scale > 0.5:
            eye_size = 1 * scale
            arcade.draw_circle_filled(x - 2*scale, y + body_size + head_size//2 + 1*scale, eye_size, arcade.color.BLACK)
            arcade.draw_circle_filled(x + 2*scale, y + body_size + head_size//2 + 1*scale, eye_size, arcade.color.BLACK)
            
        # Walking animation - legs
        # Always show animated legs for visual interest
        # Animate legs based on animation frame
        frame = biped['animation_frame']
        leg_offset = 2 * scale
        
        if frame == 0 or frame == 2:
            # Left leg forward, right leg back
            left_leg_y = y - body_size - leg_offset
            right_leg_y = y - body_size + leg_offset
        else:
            # Right leg forward, left leg back
            left_leg_y = y - body_size + leg_offset
            right_leg_y = y - body_size - leg_offset
            
        # Draw legs
        leg_width = 2 * scale
        leg_height = 6 * scale
        
        # Left leg
        arcade.draw_lrbt_rectangle_filled(
            x - 3*scale, x - 3*scale + leg_width,
            left_leg_y, left_leg_y + leg_height,
            (139, 69, 19)  # Brown pants
        )
        
        # Right leg
        arcade.draw_lrbt_rectangle_filled(
            x + 3*scale - leg_width, x + 3*scale,
            right_leg_y, right_leg_y + leg_height,
            (139, 69, 19)  # Brown pants
        )
            
        # Health bar
        if biped['health'] < biped['max_health']:
            bar_width = 20 * scale
            bar_height = 3 * scale
            bar_y = y + body_size + head_size + 8*scale
            
            # Background
            left = x - bar_width//2
            right = x + bar_width//2
            bottom = bar_y - bar_height//2
            top = bar_y + bar_height//2
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, arcade.color.RED)
            
            # Health fill
            health_percent = biped['health'] / biped['max_health']
            fill_width = bar_width * health_percent
            fill_left = x - bar_width//2
            fill_right = fill_left + fill_width
            arcade.draw_lrbt_rectangle_filled(fill_left, fill_right, bottom, top, arcade.color.GREEN)
            
    def draw_debug_info(self, blocks_drawn: int):
        """Draw debug information"""
        y_pos = self.height - 30
        
        arcade.draw_text(f"Camera: ({self.camera_offset_x:.0f}, {self.camera_offset_y:.0f}) Zoom: {self.zoom_scale:.2f}",
                        10, y_pos, arcade.color.WHITE, 12)
        y_pos -= 20
        
        arcade.draw_text(f"Terrain: {self.grid_width}x{self.grid_height} | Blocks: {len(self.grid_blocks)} | Drawn: {blocks_drawn}",
                        10, y_pos, arcade.color.WHITE, 12)
        y_pos -= 20
        
        arcade.draw_text(f"Entities: Bipeds: {len(self.bipeds)} | Animals: {len(self.animals)} | Houses: {len(self.houses)}",
                        10, y_pos, arcade.color.WHITE, 12)
        y_pos -= 20
        
        # Performance
        blocks_percent = (blocks_drawn / len(self.grid_blocks)) * 100 if self.grid_blocks else 0
        color = arcade.color.GREEN if blocks_percent < 50 else arcade.color.YELLOW if blocks_percent < 80 else arcade.color.RED
        arcade.draw_text(f"Rendered: {blocks_percent:.1f}%", 10, y_pos, color, 12)
        
        # Controls
        arcade.draw_text("Controls: Drag=Camera | Right-click=Move | Scroll=Zoom | G=Grid | H=House | R=Regen | D=Debug",
                        10, 10, arcade.color.WHITE, 10)
        
    def draw_debug_grid(self):
        """Draw debug grid"""
        if self.zoom_scale < 0.5:
            return
            
        for grid_y in range(0, min(10, self.grid_height)):
            for grid_x in range(0, min(10, self.grid_width)):
                iso_x, iso_y = self.grid_to_iso(grid_x, grid_y, 0)
                screen_x = iso_x * self.zoom_scale + self.camera_offset_x
                screen_y = iso_y * self.zoom_scale + self.camera_offset_y
                
                if (0 <= screen_x <= self.width and 0 <= screen_y <= self.height):
                    arcade.draw_text(f"{grid_x},{grid_y}", screen_x-10, screen_y, arcade.color.YELLOW, 8)
                    
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Handle mouse press"""
        if x > self.width - HUD_WIDTH:
            self.hud.on_mouse_press(x, y, button, modifiers)
            return
            
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse_dragging = True
            self.last_mouse_x = x
            self.last_mouse_y = y
            self.handle_left_click(x, y, modifiers)
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.handle_right_click(x, y)
            
    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        """Handle mouse release"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse_dragging = False
            
    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """Handle mouse motion"""
        if self.mouse_dragging and x <= self.width - HUD_WIDTH:
            self.camera_offset_x += dx
            self.camera_offset_y += dy
            
    def on_mouse_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float):
        """Handle mouse scroll for zoom"""
        zoom_factor = 1.1 if scroll_y > 0 else 1/1.1
        old_zoom = self.zoom_scale
        self.zoom_scale *= zoom_factor
        self.zoom_scale = max(0.1, min(self.zoom_scale, 3.0))
        
        # Zoom towards mouse position
        world_x = (x - self.camera_offset_x) / old_zoom
        world_y = (y - self.camera_offset_y) / old_zoom
        
        new_screen_x = world_x * self.zoom_scale + self.camera_offset_x
        new_screen_y = world_y * self.zoom_scale + self.camera_offset_y
        
        self.camera_offset_x += x - new_screen_x
        self.camera_offset_y += y - new_screen_y
        
    def on_key_press(self, key, modifiers):
        """Handle key press"""
        if key == arcade.key.G:
            self.show_grid = not self.show_grid
        elif key == arcade.key.D:
            self.show_debug = not self.show_debug
        elif key == arcade.key.H:
            self.build_house()
        elif key == arcade.key.R:
            self.regenerate_world()
            
    def handle_left_click(self, x: float, y: float, modifiers: int):
        """Handle left click for selection"""
        if not modifiers & arcade.key.MOD_SHIFT:
            self.selected_entities.clear()
            
        # Simple entity selection (find closest)
        clicked_entity = self.get_entity_at_screen_pos(x, y)
        if clicked_entity:
            self.selected_entities.add(clicked_entity['id'])
            
    def handle_right_click(self, x: float, y: float):
        """Handle right click for movement"""
        if not self.selected_entities:
            return
            
        # Convert screen to world coordinates
        world_x = (x - self.camera_offset_x) / self.zoom_scale
        world_y = (y - self.camera_offset_y) / self.zoom_scale
        
        # Convert to grid coordinates
        grid_x, grid_y = self.iso_to_grid(world_x, world_y)
        grid_x = max(-self.grid_width//2, min(self.grid_width//2 - 1, grid_x))
        grid_y = max(-self.grid_height//2, min(self.grid_height//2 - 1, grid_y))
        
        # Move selected bipeds using A* pathfinding
        for entity_id in self.selected_entities:
            for biped in self.bipeds:
                if biped['id'] == entity_id:
                    # Use A* pathfinding to move to target
                    self.move_entity_to(biped, grid_x, grid_y)
                    break
                
    def get_entity_at_screen_pos(self, screen_x: float, screen_y: float):
        """Get entity at screen position"""
        # Simple distance check
        for biped in self.bipeds:
            entity_x = biped['iso_x'] * self.zoom_scale + self.camera_offset_x
            entity_y = biped['iso_y'] * self.zoom_scale + self.camera_offset_y
            if abs(screen_x - entity_x) < 20 and abs(screen_y - entity_y) < 20:
                return biped
                
        for animal in self.animals:
            entity_x = animal['iso_x'] * self.zoom_scale + self.camera_offset_x
            entity_y = animal['iso_y'] * self.zoom_scale + self.camera_offset_y
            if abs(screen_x - entity_x) < 15 and abs(screen_y - entity_y) < 15:
                return animal
                
        return None
        
    def build_house(self):
        """Build a house at selected biped location"""
        if not self.selected_entities or not self.bipeds:
            return
            
        # Find first selected biped
        for biped in self.bipeds:
            if biped['id'] in self.selected_entities:
                house = {
                    'id': f"house_{len(self.houses)}",
                    'iso_x': biped['iso_x'],
                    'iso_y': biped['iso_y'] - 30,
                    'grid_x': biped['grid_x'],
                    'grid_y': biped['grid_y'],
                    'width': 48,
                    'height': 48,
                    'color': (139, 69, 19),
                    'depth': biped['depth'] + 1
                }
                self.houses.append(house)
                print(f"House built at ({biped['grid_x']}, {biped['grid_y']})")
                break
                
    def regenerate_world(self):
        """Regenerate the world"""
        print("[PlanetView] Regenerating world...")
        self.setup_simple_world()
        self.setup_entities()
        self.houses.clear()
        self.selected_entities.clear()
        print("[PlanetView] World regenerated!")
        
    def update(self, delta_time: float):
        """Update the view"""
        # Update biped movement and animations
        for biped in self.bipeds:
            # REMOVED: Automatic circular movement - bipeds only move when commanded
            # Only update movement and animation for bipeds that are actually moving
            self.update_entity_movement(biped, delta_time)
            self.update_biped_animation(biped, delta_time)
            
        # Update animal movement with simple direct movement
        for animal in self.animals:
            animal['move_timer'] += delta_time
            
            # Check if it's time to move
            if animal['move_timer'] >= animal['move_interval']:
                animal['move_timer'] = 0
                
                # Pick a new random target and move there immediately
                target_x = random.randint(-self.grid_width//2, self.grid_width//2 - 1)
                target_y = random.randint(-self.grid_height//2, self.grid_height//2 - 1)
                
                # Use simple direct movement
                self.move_entity_to(animal, target_x, target_y)
                print(f"Animal {animal['id']} moved to ({target_x}, {target_y})")
                
        # Update HUD
        self.hud.update(delta_time)
        
        # Update time counter for effects
        self.time_counter += delta_time
        
    # Compatibility methods for HUD
    def get_entity_by_id(self, entity_id: str):
        """Get entity by ID for HUD compatibility"""
        for biped in self.bipeds:
            if biped['id'] == entity_id:
                return SimpleEntity(biped, EntityType.BIPED)
        for animal in self.animals:
            if animal['id'] == entity_id:
                return SimpleEntity(animal, EntityType.ANIMAL)
        return None
        
    def get_all_entities(self):
        """Get all entities for compatibility"""
        entities = []
        for biped in self.bipeds:
            entities.append(SimpleEntity(biped, EntityType.BIPED))
        for animal in self.animals:
            entities.append(SimpleEntity(animal, EntityType.ANIMAL))
        return entities
        
    def move_entity_to(self, entity: Dict, target_x: int, target_y: int):
        """Move an entity to a target position using simple direct movement"""
        print(f"[DEBUG] Moving {entity['id']} from ({entity['grid_x']}, {entity['grid_y']}) to ({target_x}, {target_y})")
        
        # Simple immediate movement - no pathfinding, no interpolation
        entity['grid_x'] = target_x
        entity['grid_y'] = target_y
        
        # Update isometric position immediately
        iso_x, iso_y = self.grid_to_iso(target_x, target_y, 0)
        entity['iso_x'] = iso_x
        entity['iso_y'] = iso_y
        entity['depth'] = self.calculate_depth(target_x, target_y, 0)
        
        # Reset movement state
        entity['is_moving'] = False
        entity['path'] = []
        entity['path_index'] = 0
        
        print(f"[DEBUG] Entity {entity['id']} moved to ({target_x}, {target_y})")
        return True
        
    def update_entity_movement(self, entity: Dict, delta_time: float):
        """Update entity movement - SIMPLIFIED TO DO NOTHING"""
        # No movement updates needed - entities move immediately
        pass

    def update_biped_animation(self, biped: Dict, delta_time: float):
        """Update biped walking animation - SIMPLIFIED AND INDEPENDENT"""
        # Simple independent animation that doesn't interfere with movement
        biped['last_animation_time'] += delta_time
        
        # Always animate slowly, regardless of movement state
        if biped['last_animation_time'] >= 0.3:  # Slower animation
            biped['animation_frame'] = (biped['animation_frame'] + 1) % 4
            biped['last_animation_time'] = 0

class SimpleEntity:
    """Simple entity wrapper for HUD compatibility - FIXED"""
    def __init__(self, data: Dict, entity_type: EntityType):
        self.data = data
        self.entity_type = entity_type
        self.entity_id = data['id']
        
        # Create a stats object for HUD compatibility
        from ..entities.entity import EntityStats
        self.stats = EntityStats(
            health=data.get('health', 100),
            max_health=data.get('max_health', 100),
            energy=data.get('energy', 100),
            max_energy=data.get('max_energy', 100),
            hunger=data.get('hunger', 0),
            max_hunger=data.get('max_hunger', 100)
        )
        
        # Add missing attributes that HUD expects
        self.job = type('Job', (), {'value': data.get('job', 'worker')})()
        self.shape = type('Shape', (), {'value': data.get('shape', 'circle')})()
        self.color = data.get('color', (255, 255, 255))
        self.size = data.get('radius', 10)
        self.state = type('State', (), {'value': 'idle'})()  # Add missing state attribute
        
    def is_alive(self):
        return True
        
    def get_grid_position(self):
        return (self.data['grid_x'], self.data['grid_y'])
        
    def is_at_position(self, x: float, y: float, tolerance: float = 1.0):
        return (abs(self.data['grid_x'] - x) <= tolerance and 
                abs(self.data['grid_y'] - y) <= tolerance)