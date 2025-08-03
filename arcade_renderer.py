##########################################################
# arcade_renderer.py
# Handles rendering, drawing, and visual effects for Arcade
##########################################################

import arcade
import math
import time

class ArcadeRenderer:
    """Handles all rendering and visual effects for Arcade"""
    
    def __init__(self, scene):
        self.scene = scene
        self.render_stats = {
            "sprites_drawn": 0,
            "draw_calls": 0,
            "last_frame_time": 0
        }

    def render_world(self):
        """Render all world objects using the main camera"""
        start_time = time.time()
        
        # Draw all sprite lists in proper order
        sprite_count = 0
        
        # Terrain first (background)
        self.scene.terrain_sprites.draw()
        sprite_count += len(self.scene.terrain_sprites)
        
        # Animals
        self.scene.animal_sprites.draw()
        sprite_count += len(self.scene.animal_sprites)
        
        # Trees
        self.scene.tree_sprites.draw()
        sprite_count += len(self.scene.tree_sprites)
        
        # Bipeds
        self.scene.biped_sprites.draw()
        sprite_count += len(self.scene.biped_sprites)
        
        # Houses
        self.scene.house_sprites.draw()
        sprite_count += len(self.scene.house_sprites)
        
        # Drops (on top)
        self.scene.drop_sprites.draw()
        sprite_count += len(self.scene.drop_sprites)
        
        # Draw selection indicators
        self._draw_selection_indicators()
        
        # Update render stats
        self.render_stats["sprites_drawn"] = sprite_count
        self.render_stats["draw_calls"] = 6  # Number of sprite list draws
        self.render_stats["last_frame_time"] = time.time() - start_time

    def render_ui(self):
        """Render UI elements using the UI camera"""
        # Draw camera info
        arcade.draw_text(
            f"Camera: {self.scene.camera.position} Zoom: {self.scene.zoom_scale:.1f}",
            10, self.scene.window.height - 30,
            arcade.color.WHITE, 14
        )
        
        # Draw terrain info
        arcade.draw_text(
            f"Terrain: {self.scene.terrain_width}x{self.scene.terrain_height}",
            10, self.scene.window.height - 50,
            arcade.color.WHITE, 14
        )
        
        # Draw entity counts
        arcade.draw_text(
            f"Animals: {len(self.scene.animal_sprites)} Bipeds: {len(self.scene.biped_sprites)}",
            10, self.scene.window.height - 70,
            arcade.color.WHITE, 14
        )
        
        # Draw inventory
        if self.scene.inventory:
            inventory_text = "Inventory: " + ", ".join(f"{k}:{v}" for k, v in self.scene.inventory.items())
            arcade.draw_text(
                inventory_text,
                10, self.scene.window.height - 90,
                arcade.color.YELLOW, 12
            )
        
        # Draw simulation mode
        arcade.draw_text(
            f"Mode: {self.scene.simulation_mode.upper()}",
            10, self.scene.window.height - 110,
            arcade.color.CYAN, 12
        )
        
        # Draw render stats
        arcade.draw_text(
            f"Sprites: {self.render_stats['sprites_drawn']} | Frame: {self.render_stats['last_frame_time']*1000:.1f}ms",
            10, self.scene.window.height - 130,
            arcade.color.LIGHT_GRAY, 10
        )
        
        # Draw controls help
        self._draw_controls_help()

    def _draw_selection_indicators(self):
        """Draw selection indicators around selected bipeds"""
        for biped in self.scene.biped_sprites:
            if hasattr(biped, 'selected') and biped.selected:
                # Draw selection circle
                arcade.draw_circle_outline(
                    biped.center_x, biped.center_y, 20,
                    arcade.color.YELLOW, 2
                )
            
            # Draw movement target if moving
            if (hasattr(biped, 'moving') and biped.moving and
                hasattr(biped, 'target_x') and hasattr(biped, 'target_y')):
                # Draw target indicator
                arcade.draw_circle_filled(
                    biped.target_x, biped.target_y, 5,
                    arcade.color.RED
                )
                
                # Draw movement line
                arcade.draw_line(
                    biped.center_x, biped.center_y,
                    biped.target_x, biped.target_y,
                    arcade.color.WHITE, 1
                )

    def _draw_controls_help(self):
        """Draw controls help text"""
        help_text = [
            "Controls:",
            "Left Click + Drag: Move camera",
            "Right Click: Move biped",
            "Mouse Wheel: Zoom",
            "H: Build house",
            "T: Toggle simulation mode",
            "Ctrl+R: Regenerate world",
            "Space: Pause"
        ]
        
        start_y = 150
        for i, text in enumerate(help_text):
            color = arcade.color.WHITE if i == 0 else arcade.color.LIGHT_GRAY
            size = 12 if i == 0 else 10
            arcade.draw_text(
                text,
                self.scene.window.width - 250, start_y - (i * 15),
                color, size
            )

    def update_water_animation(self, dt):
        """Update water animation effects"""
        # Simple water animation - could be enhanced
        self.scene.wave_time += dt * 0.001
        
        # Update any water tiles with animation
        for terrain_sprite in self.scene.terrain_sprites:
            if hasattr(terrain_sprite, 'tile_type') and terrain_sprite.tile_type == 2:  # Water
                # Simple wave animation
                wave_offset = math.sin(self.scene.wave_time * 2 + 
                                     terrain_sprite.center_x * 0.01 + 
                                     terrain_sprite.center_y * 0.01) * 2
                # Could modify sprite position or texture here
                pass

    def draw_debug_info(self, debug_info):
        """Draw debug information overlay"""
        if not debug_info:
            return
        
        # Draw debug background
        arcade.draw_lbwh_rectangle_filled(
            10, 10, 300, 200,
            (0, 0, 0, 128)  # Semi-transparent black
        )
        
        y_offset = 180
        for category, data in debug_info.items():
            # Category header
            arcade.draw_text(
                f"{category.upper()}:",
                15, y_offset,
                arcade.color.YELLOW, 12
            )
            y_offset -= 20
            
            # Category data
            if isinstance(data, dict):
                for key, value in data.items():
                    arcade.draw_text(
                        f"  {key}: {value}",
                        20, y_offset,
                        arcade.color.WHITE, 10
                    )
                    y_offset -= 15
            else:
                arcade.draw_text(
                    f"  {data}",
                    20, y_offset,
                    arcade.color.WHITE, 10
                )
                y_offset -= 15
            
            y_offset -= 5  # Extra space between categories

    def highlight_tile(self, grid_x, grid_y, color=arcade.color.YELLOW):
        """Highlight a specific tile"""
        # Convert grid to isometric coordinates
        iso_x = (grid_x - grid_y) * (64 // 2)  # TILE_WIDTH
        iso_y = (grid_x + grid_y) * (37 // 2)  # TILE_HEIGHT
        
        # Draw highlight
        arcade.draw_circle_outline(iso_x, iso_y, 30, color, 3)

    def draw_grid_overlay(self, alpha=50):
        """Draw grid overlay for debugging"""
        # Draw grid lines
        for y in range(self.scene.terrain_height):
            for x in range(self.scene.terrain_width):
                iso_x = (x - y) * (64 // 2)
                iso_y = (x + y) * (37 // 2)
                
                # Draw tile outline
                points = [
                    (iso_x, iso_y - 18),
                    (iso_x + 32, iso_y),
                    (iso_x, iso_y + 18),
                    (iso_x - 32, iso_y)
                ]
                
                arcade.draw_polygon_outline(points, (255, 255, 255, alpha), 1)

    def draw_path_visualization(self, path, color=arcade.color.GREEN):
        """Draw a path for debugging"""
        if not path or len(path) < 2:
            return
        
        # Convert path to screen coordinates and draw
        screen_points = []
        for grid_x, grid_y in path:
            iso_x = (grid_x - grid_y) * (64 // 2)
            iso_y = (grid_x + grid_y) * (37 // 2)
            screen_points.append((iso_x, iso_y))
        
        # Draw path line
        for i in range(len(screen_points) - 1):
            arcade.draw_line(
                screen_points[i][0], screen_points[i][1],
                screen_points[i+1][0], screen_points[i+1][1],
                color, 2
            )
        
        # Draw waypoints
        for point in screen_points:
            arcade.draw_circle_filled(point[0], point[1], 3, color)

    def get_render_stats(self):
        """Get rendering statistics"""
        return {
            "sprites_drawn": self.render_stats["sprites_drawn"],
            "draw_calls": self.render_stats["draw_calls"],
            "frame_time_ms": self.render_stats["last_frame_time"] * 1000,
            "total_sprite_lists": len(self.scene.sprite_lists),
            "camera_position": self.scene.camera.position if self.scene.camera else (0, 0),
            "zoom_scale": self.scene.zoom_scale
        }

    def set_background_color(self, color):
        """Set the background color"""
        # This would be called in the main draw loop
        # For now, just store the preference
        self.background_color = color

    def create_particle_effect(self, x, y, effect_type="sparkle"):
        """Create a simple particle effect"""
        # Simple implementation - could be enhanced with actual particle system
        if effect_type == "sparkle":
            for _ in range(5):
                offset_x = random.randint(-10, 10)
                offset_y = random.randint(-10, 10)
                arcade.draw_circle_filled(
                    x + offset_x, y + offset_y, 2,
                    arcade.color.YELLOW
                )
        elif effect_type == "explosion":
            for _ in range(8):
                offset_x = random.randint(-20, 20)
                offset_y = random.randint(-20, 20)
                arcade.draw_circle_filled(
                    x + offset_x, y + offset_y, 3,
                    arcade.color.ORANGE
                )

    def fade_in_sprite(self, sprite, duration=1.0):
        """Fade in a sprite over time"""
        # Simple implementation - in a full system this would use tweening
        if hasattr(sprite, 'alpha'):
            sprite.alpha = min(255, sprite.alpha + (255 * duration / 60))  # Assuming 60 FPS

    def fade_out_sprite(self, sprite, duration=1.0):
        """Fade out a sprite over time"""
        if hasattr(sprite, 'alpha'):
            sprite.alpha = max(0, sprite.alpha - (255 * duration / 60))
            if sprite.alpha <= 0:
                sprite.alive = False

    def shake_camera(self, intensity=5, duration=0.5):
        """Shake the camera for dramatic effect"""
        # Simple camera shake - would need to be called each frame during shake
        if hasattr(self, 'shake_timer') and self.shake_timer > 0:
            import random
            offset_x = random.randint(-intensity, intensity)
            offset_y = random.randint(-intensity, intensity)
            
            current_x, current_y = self.scene.camera.position
            self.scene.camera.move_to((current_x + offset_x, current_y + offset_y))
            
            self.shake_timer -= 1/60  # Assuming 60 FPS
        else:
            self.shake_timer = 0

    def zoom_to_position(self, world_x, world_y, target_zoom=2.0, speed=0.1):
        """Smoothly zoom to a specific world position"""
        # Simple zoom animation - would need to be called each frame
        current_zoom = self.scene.zoom_scale
        zoom_diff = target_zoom - current_zoom
        
        if abs(zoom_diff) > 0.01:
            new_zoom = current_zoom + (zoom_diff * speed)
            self.scene.zoom_scale = new_zoom
            
            # Center camera on target position
            screen_center_x = self.scene.window.width // 2
            screen_center_y = self.scene.window.height // 2
            
            self.scene.camera.move_to((world_x - screen_center_x, world_y - screen_center_y))

    def draw_minimap(self, x, y, width, height):
        """Draw a simple minimap"""
        # Draw minimap background
        arcade.draw_lbwh_rectangle_filled(x, y, width, height, (0, 0, 0, 128))
        arcade.draw_lbwh_rectangle_outline(x, y, width, height, arcade.color.WHITE, 2)
        
        # Calculate scale
        scale_x = width / self.scene.terrain_width
        scale_y = height / self.scene.terrain_height
        
        # Draw terrain on minimap
        for terrain_y in range(self.scene.terrain_height):
            for terrain_x in range(self.scene.terrain_width):
                if (terrain_y < len(self.scene.map_data) and 
                    terrain_x < len(self.scene.map_data[0])):
                    tile_type = self.scene.map_data[terrain_y][terrain_x]
                    
                    # Choose color based on tile type
                    if tile_type == 1:  # Grass
                        color = arcade.color.GREEN
                    elif tile_type == 2:  # Water
                        color = arcade.color.BLUE
                    elif tile_type == 4:  # Mountain
                        color = arcade.color.GRAY
                    elif tile_type == 11:  # Desert
                        color = arcade.color.YELLOW
                    else:
                        continue  # Skip void tiles
                    
                    # Draw minimap pixel
                    pixel_x = x + terrain_x * scale_x
                    pixel_y = y + terrain_y * scale_y
                    arcade.draw_lbwh_rectangle_filled(
                        pixel_x, pixel_y, scale_x, scale_y, color
                    )
        
        # Draw bipeds on minimap
        for biped in self.scene.biped_sprites:
            if hasattr(biped, 'grid_x') and hasattr(biped, 'grid_y'):
                pixel_x = x + biped.grid_x * scale_x
                pixel_y = y + biped.grid_y * scale_y
                arcade.draw_circle_filled(pixel_x, pixel_y, 2, arcade.color.CYAN)