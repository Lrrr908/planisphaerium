##########################################################
# arcade_planet_scene.py - Arcade 3.3.2 Planet Scene
# Standalone version that works without external modules initially
##########################################################

import arcade
import random
import time
import math
from typing import List, Tuple, Optional
from planet_meta import PlanetMeta
from planet_storage import PlanetStorage

# Constants
TILE_WIDTH = 64
TILE_HEIGHT = 37
STACK_OFFSET = 10

##########################################################
# Main ArcadePlanetScene Class
##########################################################

class ArcadePlanetScene(arcade.View):
    """
    Main Arcade planet scene class - standalone version.
    This version works without external modules and can be gradually enhanced.
    """
    
    def __init__(self, assets_dir: str, meta: PlanetMeta, planet_storage: PlanetStorage):
        super().__init__()
        
        # Core scene properties
        self.assets_dir = assets_dir
        self.meta = meta
        self.planet_storage = planet_storage
        
        # Initialize random seed for deterministic generation
        random.seed(self.meta.seed)
        
        # Arcade-specific properties
        self.camera = None
        self.ui_camera = None
        self.camera_offset_x = 0
        self.camera_offset_y = 0
        
        # Scene configuration
        self.zoom_scale = 1.0
        self.simulation_mode = "realtime"
        self.use_layered_terrain = True
        self.mining_mode = False
        
        # Sprite lists for efficient rendering
        self.terrain_sprites = arcade.SpriteList()
        self.animal_sprites = arcade.SpriteList()
        self.biped_sprites = arcade.SpriteList()
        self.tree_sprites = arcade.SpriteList()
        self.house_sprites = arcade.SpriteList()
        self.drop_sprites = arcade.SpriteList()
        
        # All sprite lists for easy iteration
        self.sprite_lists = [
            self.terrain_sprites,
            self.animal_sprites,
            self.biped_sprites,
            self.tree_sprites,
            self.house_sprites,
            self.drop_sprites
        ]
        
        # Terrain data
        self.terrain_width = meta.tiles[0]
        self.terrain_height = meta.tiles[1]
        self.terrain_data = []
        
        # Game state
        self.blocked_tiles = set()
        self.tree_tiles = set()
        self.drops = []
        self.inventory = {}
        self.wave_time = 0.0
        self.wave_speed = 5.0
        self.wave_spacing = 3.0
        self.house_built = False
        
        # Input state
        self.mouse_dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # Auto-save tracking
        self._last_auto_save = time.time()
        self._last_validation = time.time()
        self._last_cleanup = time.time()
        
        print(f"[ArcadePlanetScene] Initialized with terrain {self.terrain_width}x{self.terrain_height}")

    def setup(self):
        """Set up the scene - called by Arcade after __init__"""
        # Disable camera system for now to avoid window reference issues
        self.camera = None
        self.ui_camera = None
        print("[ArcadePlanetScene] Camera system disabled - drawing without camera")
        
        # Initialize world state
        self._initialize_world_state()

    def _initialize_world_state(self):
        """Initialize world state - generate new for now"""
        print(f"[ArcadePlanetScene] Generating new world for seed {self.meta.seed}")
        self._generate_new_world()

    def _generate_new_world(self):
        """Generate a simple new world"""
        print("[ArcadePlanetScene] Generating simple terrain...")
        
        # Generate simple terrain data
        self._generate_terrain()
        
        # Create terrain sprites
        self._create_terrain_sprites()
        
        # Spawn some entities
        self._spawn_entities()
        
        print(f"[ArcadePlanetScene] Generated {len(self.terrain_sprites)} terrain tiles")

    def _generate_terrain(self):
        """Generate terrain data with height variations for stacked blocks"""
        self.terrain_data = []
        for y in range(self.terrain_height):
            row = []
            for x in range(self.terrain_width):
                # Enhanced terrain generation with height
                tile_type = 1  # Default grass
                height = 1     # Default height
                
                # Create some height variations for mountains
                if random.random() < 0.05:  # 5% chance for mountains
                    height = random.randint(2, 4)
                    tile_type = 4  # Stone for mountains
                elif random.random() < 0.1:
                    tile_type = 2  # Water
                elif random.random() < 0.05:
                    tile_type = 3  # Dirt
                    
                row.append({
                    'type': tile_type,
                    'height': height,
                    'x': x,
                    'y': y
                })
            self.terrain_data.append(row)

    def _create_terrain_sprites(self):
        """Create Arcade sprites for terrain with stacked blocks"""
        self.terrain_sprites.clear()
        
        for y in range(self.terrain_height):
            for x in range(self.terrain_width):
                tile_data = self.terrain_data[y][x]
                
                # Create stacked blocks for each height level
                for layer in range(tile_data['height']):
                    # Calculate isometric position
                    iso_x = (x - y) * (TILE_WIDTH // 2)
                    iso_y = (x + y) * (TILE_HEIGHT // 2)
                    
                    # Add height offset for stacking (stepped pyramid effect)
                    height_offset = layer * 16  # 16 pixels per block height
                    iso_y -= height_offset  # Subtract to make higher blocks appear above
                    
                    # Create terrain sprite for this layer
                    terrain_sprite = ArcadeTerrainSprite(
                        tile_data['type'],
                        iso_x,
                        iso_y,
                        layer  # Pass layer as height
                    )
                    terrain_sprite.parent = self
                    self.terrain_sprites.append(terrain_sprite)

    def _spawn_entities(self):
        """Spawn some initial entities"""
        # Spawn some animals
        for i in range(5):
            x = random.randint(0, self.terrain_width - 1)
            y = random.randint(0, self.terrain_height - 1)
            
            iso_x = (x - y) * (TILE_WIDTH // 2)
            iso_y = (x + y) * (TILE_HEIGHT // 2)
            
            animal = ArcadeAnimalSprite(iso_x, iso_y)
            animal.parent = self
            self.animal_sprites.append(animal)
            
        # Spawn some bipeds
        for i in range(3):
            x = random.randint(0, self.terrain_width - 1)
            y = random.randint(0, self.terrain_height - 1)
            
            iso_x = (x - y) * (TILE_WIDTH // 2)
            iso_y = (x + y) * (TILE_HEIGHT // 2)
            
            biped = ArcadeBipedSprite(iso_x, iso_y, f"BP{i+1}")
            biped.parent = self
            self.biped_sprites.append(biped)

    def _center_camera(self):
        """Center camera on the terrain"""
        center_x = (self.terrain_width - self.terrain_height) * (TILE_WIDTH // 2) // 2
        center_y = (self.terrain_width + self.terrain_height) * (TILE_HEIGHT // 2) // 2
        
        # Position camera so terrain center appears at screen center
        self.camera.position = (center_x - self.window.width // 2, 
                               center_y - self.window.height // 2)

    ##########################################################
    # Arcade View Interface Methods
    ##########################################################

    def on_draw(self):
        """Render the scene"""
        self.clear()
        
        # Draw all sprites with camera offset
        self._draw_sprites_with_offset()
        
        # Draw UI elements
        self._draw_ui()

    def _draw_sprites_with_offset(self):
        """Draw all sprites with camera offset applied"""
        # Only draw sprites that are visible on screen
        screen_left = -self.camera_offset_x / self.zoom_scale - 100
        screen_right = (-self.camera_offset_x + self.window.width) / self.zoom_scale + 100
        screen_bottom = -self.camera_offset_y / self.zoom_scale - 100
        screen_top = (-self.camera_offset_y + self.window.height) / self.zoom_scale + 100
        
        # Draw terrain sprites (most expensive, so cull them)
        visible_terrain = 0
        for sprite in self.terrain_sprites:
            if (screen_left <= sprite.center_x <= screen_right and 
                screen_bottom <= sprite.center_y <= screen_top):
                sprite.draw()
                visible_terrain += 1
        
        # Draw other sprites (fewer, so no culling needed)
        for sprite in self.animal_sprites:
            sprite.draw()
            
        for sprite in self.biped_sprites:
            sprite.draw()
            
        for sprite in self.tree_sprites:
            sprite.draw()
            
        for sprite in self.house_sprites:
            sprite.draw()
            
        for sprite in self.drop_sprites:
            sprite.draw()

    def _draw_ui(self):
        """Draw UI elements"""
        # Draw camera info
        camera_pos = (self.camera_offset_x, self.camera_offset_y)
        arcade.draw_text(
            f"Camera: {camera_pos} Zoom: {self.zoom_scale:.1f}",
            10, self.window.height - 30,
            arcade.color.WHITE, 14
        )
        
        # Draw terrain info
        arcade.draw_text(
            f"Terrain: {self.terrain_width}x{self.terrain_height} (3D Stacked Blocks)",
            10, self.window.height - 50,
            arcade.color.WHITE, 14
        )
        
        # Draw entity counts
        arcade.draw_text(
            f"Animals: {len(self.animal_sprites)} Bipeds: {len(self.biped_sprites)}",
            10, self.window.height - 70,
            arcade.color.WHITE, 14
        )
        
        # Draw controls info
        arcade.draw_text(
            "Controls: Left drag = move, Scroll = zoom, Right click = move biped, H = build house",
            10, 10,
            arcade.color.WHITE, 12
        )

    def on_update(self, delta_time: float):
        """Update all game systems"""
        # Update wave animation time
        self.wave_time += delta_time * 0.001
        
        # Update all sprite lists
        for sprite_list in self.sprite_lists:
            sprite_list.update()
        
        # Simple cleanup check
        if time.time() - self._last_cleanup > 30.0:
            self._cleanup_dead_entities()
            self._last_cleanup = time.time()

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse press events"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._handle_left_click(x, y, modifiers)
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self._handle_right_click(x, y, modifiers)

    def _handle_left_click(self, x: int, y: int, modifiers: int):
        """Handle left mouse button clicks"""
        # Start dragging the map
        self.mouse_dragging = True
        self.last_mouse_x = x
        self.last_mouse_y = y
        print(f"[ArcadePlanetScene] Started dragging at ({x}, {y})")

    def _handle_right_click(self, x: int, y: int, modifiers: int):
        """Handle right mouse button clicks"""
        # Convert screen to world coordinates and move a biped there
        if self.biped_sprites:
            world_x, world_y = self._screen_to_world(x, y)
            
            # Move first biped to clicked location
            biped = self.biped_sprites[0]
            biped.center_x = world_x
            biped.center_y = world_y
            print(f"Moved biped to ({world_x:.1f}, {world_y:.1f})")

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse button up events"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse_dragging = False
            print(f"[ArcadePlanetScene] Stopped dragging at ({x}, {y})")

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        """Handle mouse motion events"""
        # Handle camera dragging
        if self.mouse_dragging:
            # Move camera in same direction as mouse movement (corrected)
            self.camera_offset_x += dx
            self.camera_offset_y += dy
            self.last_mouse_x = x
            self.last_mouse_y = y
            print(f"[Camera] Offset: ({self.camera_offset_x:.1f}, {self.camera_offset_y:.1f})")

    def on_key_press(self, key: int, modifiers: int):
        """Handle keyboard input"""
        if key == arcade.key.ESCAPE:
            print("[ArcadePlanetScene] Escape pressed")
            
        elif key == arcade.key.H:
            self._build_house()
            
        elif key == arcade.key.T:
            self._toggle_simulation_mode()
            
        elif key == arcade.key.R and (modifiers & arcade.key.MOD_CTRL):
            self._regenerate_world()
            
        elif key == arcade.key.SPACE:
            print("[ArcadePlanetScene] Pause toggled")

    def on_key_release(self, key: int, modifiers: int):
        """Handle key release events"""
        pass

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """Handle mouse wheel zoom events"""
        zoom_factor = 1.1 if scroll_y > 0 else 1/1.1
        self._zoom_camera(zoom_factor, x, y)

    ##########################################################
    # Helper Methods
    ##########################################################

    def _screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        # Apply camera offset and zoom
        world_x = (screen_x - self.camera_offset_x) / self.zoom_scale
        world_y = (screen_y - self.camera_offset_y) / self.zoom_scale
        return world_x, world_y

    def _world_to_screen(self, world_x: float, world_y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates"""
        # Apply camera offset and zoom
        screen_x = world_x * self.zoom_scale + self.camera_offset_x
        screen_y = world_y * self.zoom_scale + self.camera_offset_y
        return screen_x, screen_y

    def _zoom_camera(self, zoom_factor: float, anchor_x: float, anchor_y: float):
        """Zoom camera with anchor point"""
        old_zoom = self.zoom_scale
        self.zoom_scale *= zoom_factor
        self.zoom_scale = max(0.1, min(self.zoom_scale, 5.0))
        
        # Calculate the world position under the mouse cursor (before zoom)
        world_x = (anchor_x - self.camera_offset_x) / old_zoom
        world_y = (anchor_y - self.camera_offset_y) / old_zoom
        
        # Calculate where this world point should appear on screen after zoom
        new_screen_x = world_x * self.zoom_scale + self.camera_offset_x
        new_screen_y = world_y * self.zoom_scale + self.camera_offset_y
        
        # Adjust camera offset to keep the world point under the mouse
        self.camera_offset_x += anchor_x - new_screen_x
        self.camera_offset_y += anchor_y - new_screen_y
        
        print(f"Zoom: {self.zoom_scale:.2f} at ({anchor_x:.1f}, {anchor_y:.1f})")

    def _build_house(self):
        """Build a house at the first biped's location"""
        if self.house_built or not self.biped_sprites:
            return
            
        biped = self.biped_sprites[0]
        house = ArcadeHouseSprite(biped.center_x, biped.center_y)
        house.parent = self
        self.house_sprites.append(house)
        self.house_built = True
        print(f"House built at ({biped.center_x:.1f}, {biped.center_y:.1f})")

    def _toggle_simulation_mode(self):
        """Toggle simulation mode"""
        if self.simulation_mode == "paused":
            self.simulation_mode = "realtime"
            print("[ArcadePlanetScene] Switched to REALTIME simulation")
        else:
            self.simulation_mode = "paused"
            print("[ArcadePlanetScene] Switched to PAUSED simulation")

    def _regenerate_world(self):
        """Regenerate the world"""
        print("[ArcadePlanetScene] Regenerating world...")
        
        # Clear all sprites
        for sprite_list in self.sprite_lists:
            sprite_list.clear()
        
        # Regenerate
        self._generate_new_world()
        print("[ArcadePlanetScene] World regeneration complete")

    def _cleanup_dead_entities(self):
        """Clean up dead entities"""
        # Simple cleanup - remove sprites marked as dead
        for sprite_list in self.sprite_lists:
            dead_sprites = [s for s in sprite_list if hasattr(s, 'alive') and not s.alive]
            for sprite in dead_sprites:
                sprite_list.remove(sprite)

    ##########################################################
    # State Management (Simplified)
    ##########################################################

    def save_before_exit(self):
        """Save state before exiting"""
        if self.planet_storage and hasattr(self, 'meta'):
            # TODO: Implement proper state serialization
            print("[ArcadePlanetScene] Saving state...")
            # For now, just print
            pass

    def on_hide_view(self):
        """Called when leaving this view"""
        self.save_before_exit()

    ##########################################################
    # Debug Methods
    ##########################################################

    def get_debug_info(self):
        """Get debug information"""
        return {
            "scene": {
                "simulation_mode": self.simulation_mode,
                "use_layered_terrain": self.use_layered_terrain,
                "mining_mode": self.mining_mode,
                "zoom_scale": self.zoom_scale,
                "camera_position": self.camera.position if self.camera else (0, 0),
            },
            "entities": {
                "bipeds": len(self.biped_sprites),
                "animals": len(self.animal_sprites),
                "terrain_tiles": len(self.terrain_sprites),
                "houses": len(self.house_sprites),
            },
            "sprite_lists": {
                "total_sprites": sum(len(sl) for sl in self.sprite_lists),
            }
        }


##########################################################
# Arcade Sprite Classes
##########################################################

class ArcadeTerrainSprite(arcade.Sprite):
    """Terrain tile sprite for Arcade - 3D Minecraft-style blocks with texture caching"""
    
    # Class-level texture cache for 3D blocks
    _texture_cache = {}
    
    def __init__(self, tile_type: int, x: float, y: float, height: int = 0):
        super().__init__()
        self.tile_type = tile_type
        self.height = height
        self.center_x = x
        self.center_y = y
        
        # Set appearance based on tile type
        self._set_appearance()
        
    def _set_appearance(self):
        """Set sprite appearance based on tile type"""
        # Get Minecraft-style colors for this tile type
        self.top_color, self.left_color, self.right_color = self._get_minecraft_colors(self.tile_type)
        
        # Set dimensions
        self.width = TILE_WIDTH
        self.height = TILE_HEIGHT
        self.block_depth = 16  # Depth for 3D effect
        
        # Create or get cached texture
        self.texture = self._get_cached_texture()

    def _get_minecraft_colors(self, tile_type: int):
        """Get Minecraft-style colors for top, left, and right faces"""
        color_map = {
            1: ((50, 160, 50), (101, 67, 33), (85, 55, 25)),      # Grass: green top, dirt sides  
            2: ((64, 164, 223), (45, 140, 190), (35, 120, 170)),  # Water: blue variations
            3: ((134, 96, 67), (110, 75, 50), (90, 60, 40)),      # Dirt: brown variations
            4: ((130, 130, 130), (105, 105, 105), (85, 85, 85)),  # Stone: gray variations
            5: ((32, 137, 203), (25, 110, 170), (20, 90, 140)),   # Deep water: darker blue
            11: ((247, 233, 163), (210, 195, 135), (180, 165, 115)), # Desert: sandy variations
        }
        return color_map.get(tile_type, ((50, 160, 50), (101, 67, 33), (85, 55, 25)))

    def _darken_color(self, color, factor: float):
        """Darken a color by the given factor"""
        return (
            max(0, int(color[0] * (1 - factor))),
            max(0, int(color[1] * (1 - factor))),
            max(0, int(color[2] * (1 - factor)))
        )
    
    def _get_cached_texture(self):
        """Get or create cached texture for this tile type"""
        cache_key = f"terrain_{self.tile_type}"
        
        if cache_key not in self._texture_cache:
            # Create new texture
            texture = self._create_3d_block_texture()
            self._texture_cache[cache_key] = texture
            print(f"[TextureCache] Created 3D texture for tile type {self.tile_type}")
        
        return self._texture_cache[cache_key]
    
    def _create_3d_block_texture(self):
        """Create a texture for the 3D block using PIL"""
        try:
            from PIL import Image, ImageDraw
            
            # Calculate texture size (enough to fit the 3D block)
            texture_width = int(self.width + self.block_depth)
            texture_height = int(self.height + self.block_depth)
            
            # Create PIL image with transparency
            image = Image.new('RGBA', (texture_width, texture_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Calculate center position
            center_x = texture_width // 2
            center_y = texture_height // 2
            
            # Draw the three faces of the 3D block
            # 1. LEFT FACE (parallelogram)
            left_points = [
                (center_x - self.width//2, center_y),
                (center_x, center_y + self.height//2),
                (center_x, center_y + self.height//2 + self.block_depth),
                (center_x - self.width//2, center_y + self.block_depth)
            ]
            draw.polygon(left_points, fill=self.left_color)
            
            # 2. RIGHT FACE (parallelogram)
            right_points = [
                (center_x, center_y + self.height//2),
                (center_x + self.width//2, center_y),
                (center_x + self.width//2, center_y + self.block_depth),
                (center_x, center_y + self.height//2 + self.block_depth)
            ]
            draw.polygon(right_points, fill=self.right_color)
            
            # 3. TOP FACE (diamond/rhombus)
            top_points = [
                (center_x, center_y - self.height//2),
                (center_x + self.width//2, center_y),
                (center_x, center_y + self.height//2),
                (center_x - self.width//2, center_y)
            ]
            draw.polygon(top_points, fill=self.top_color)
            
            # Draw outlines
            draw.polygon(left_points, outline=self._darken_color(self.left_color, 0.2), width=1)
            draw.polygon(right_points, outline=self._darken_color(self.right_color, 0.2), width=1)
            draw.polygon(top_points, outline=self._darken_color(self.top_color, 0.3), width=1)
            
            # Convert to Arcade texture
            texture = arcade.Texture(f"terrain_{self.tile_type}")
            texture.image = image
            return texture
            
        except ImportError:
            # Fallback to simple colored rectangle if PIL not available
            print("[TextureCache] PIL not available, using simple rectangles")
            return None
    


    def draw(self):
        """Draw the terrain sprite using cached 3D texture"""
        # Apply camera offset and zoom
        scene = getattr(self, 'parent', None)
        if scene and hasattr(scene, 'camera_offset_x'):
            offset_x = scene.camera_offset_x
            offset_y = scene.camera_offset_y
            zoom_scale = scene.zoom_scale
        else:
            offset_x = offset_y = 0
            zoom_scale = 1.0
            
        # Apply zoom to position and size
        zoomed_x = self.center_x * zoom_scale + offset_x
        zoomed_y = self.center_y * zoom_scale + offset_y
        
        if self.texture:
            # Use cached 3D texture (fast)
            zoomed_width = self.texture.width * zoom_scale
            zoomed_height = self.texture.height * zoom_scale
            
            arcade.draw_texture_rectangle(
                zoomed_x, zoomed_y,
                zoomed_width, zoomed_height,
                self.texture
            )
        else:
            # Fallback to simple colored rectangle
            zoomed_width = self.width * zoom_scale
            zoomed_height = self.height * zoom_scale
            
            arcade.draw_lbwh_rectangle_filled(
                zoomed_x - zoomed_width//2,
                zoomed_y - zoomed_height//2,
                zoomed_width, zoomed_height,
                self.top_color
            )


class ArcadeAnimalSprite(arcade.Sprite):
    """Animal sprite for Arcade"""
    
    def __init__(self, x: float, y: float, color=(255, 165, 0)):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.color = color
        self.alive = True
        self.radius = 10

    def update(self, delta_time: float = 0.0):
        """Update animal behavior"""
        # Simple random movement
        if random.random() < 0.01:  # 1% chance per frame to move
            self.center_x += random.randint(-2, 2)
            self.center_y += random.randint(-2, 2)

    def draw(self):
        """Draw the animal sprite as a colored circle"""
        # Apply camera offset and zoom
        scene = getattr(self, 'parent', None)
        if scene and hasattr(scene, 'camera_offset_x'):
            offset_x = scene.camera_offset_x
            offset_y = scene.camera_offset_y
            zoom_scale = scene.zoom_scale
        else:
            offset_x = offset_y = 0
            zoom_scale = 1.0
            
        # Apply zoom to position and size
        zoomed_x = self.center_x * zoom_scale + offset_x
        zoomed_y = self.center_y * zoom_scale + offset_y
        zoomed_radius = self.radius * zoom_scale
            
        arcade.draw_circle_filled(
            zoomed_x, zoomed_y,
            zoomed_radius, self.color
        )


class ArcadeBipedSprite(arcade.Sprite):
    """Biped (unit) sprite for Arcade"""
    
    def __init__(self, x: float, y: float, name: str, color=(0, 255, 0)):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.name = name
        self.color = color
        self.alive = True
        self.selected = False
        self.width = 16
        self.height = 24

    def update(self, delta_time: float = 0.0):
        """Update biped behavior"""
        # Simple idle animation or behavior
        pass

    def draw(self):
        """Draw the biped sprite as a colored rectangle"""
        # Apply camera offset and zoom
        scene = getattr(self, 'parent', None)
        if scene and hasattr(scene, 'camera_offset_x'):
            offset_x = scene.camera_offset_x
            offset_y = scene.camera_offset_y
            zoom_scale = scene.zoom_scale
        else:
            offset_x = offset_y = 0
            zoom_scale = 1.0
            
        # Apply zoom to position and size
        zoomed_x = self.center_x * zoom_scale + offset_x
        zoomed_y = self.center_y * zoom_scale + offset_y
        zoomed_width = self.width * zoom_scale
        zoomed_height = self.height * zoom_scale
            
        arcade.draw_lbwh_rectangle_filled(
            zoomed_x - zoomed_width//2, 
            zoomed_y - zoomed_height//2,
            zoomed_width, zoomed_height,
            self.color
        )


class ArcadeHouseSprite(arcade.Sprite):
    """House sprite for Arcade"""
    
    def __init__(self, x: float, y: float):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.width = 48
        self.height = 48
        self.color = (139, 69, 19)  # Brown color for house

    def draw(self):
        """Draw the house sprite as a colored rectangle"""
        # Apply camera offset and zoom
        scene = getattr(self, 'parent', None)
        if scene and hasattr(scene, 'camera_offset_x'):
            offset_x = scene.camera_offset_x
            offset_y = scene.camera_offset_y
            zoom_scale = scene.zoom_scale
        else:
            offset_x = offset_y = 0
            zoom_scale = 1.0
            
        # Apply zoom to position and size
        zoomed_x = self.center_x * zoom_scale + offset_x
        zoomed_y = self.center_y * zoom_scale + offset_y
        zoomed_width = self.width * zoom_scale
        zoomed_height = self.height * zoom_scale
            
        arcade.draw_lbwh_rectangle_filled(
            zoomed_x - zoomed_width//2, 
            zoomed_y - zoomed_height//2,
            zoomed_width, zoomed_height,
            self.color
        )


##########################################################
# Example usage and testing
##########################################################

def create_test_meta():
    """Create test planet meta for testing"""
    class TestMeta:
        def __init__(self):
            self.seed = 12345
            self.tiles = (50, 50)  # Small world for testing
            self.state = None
    return TestMeta()

def create_test_storage():
    """Create test planet storage for testing"""
    class TestStorage:
        def save_planet(self, planet_id, meta):
            print(f"Saving planet {planet_id}")
        
        def load_planet(self, planet_id):
            print(f"Loading planet {planet_id}")
            return None
    return TestStorage()


# For standalone testing
if __name__ == "__main__":
    class TestWindow(arcade.Window):
        def __init__(self):
            super().__init__(1024, 768, "Arcade Planet Scene Test")
            
        def setup(self):
            meta = create_test_meta()
            storage = create_test_storage()
            
            planet_scene = ArcadePlanetScene("assets", meta, storage)
            planet_scene.setup()
            self.show_view(planet_scene)
    
    window = TestWindow()
    window.setup()
    arcade.run()