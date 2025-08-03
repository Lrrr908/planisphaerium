##########################################################
# arcade_utilities.py
# Utility functions and helper methods for Arcade planet scene
##########################################################

import arcade
import math

# Constants
TILE_WATER = 2
TILE_WATERSTACK = 5
TILE_MOUNTAIN = 4
TILE_DESERT = 11
TILE_WIDTH = 64
TILE_HEIGHT = 37

class ArcadeUtilities:
    """Collection of utility functions for Arcade planet scene operations"""
    
    def __init__(self, scene):
        self.scene = scene

    def is_water_tile(self, gx: int, gy: int) -> bool:
        """Convenience check for the two water tile IDs."""
        if (0 <= gy < len(self.scene.map_data) and 
            0 <= gx < len(self.scene.map_data[0])):
            return self.scene.map_data[gy][gx] in (TILE_WATER, TILE_WATERSTACK)
        return False

    def is_valid_position(self, x, y):
        """Check if a position is within map bounds and valid"""
        if not hasattr(self.scene, 'map_data'):
            return False
            
        if x < 0 or y < 0:
            return False
            
        if y >= len(self.scene.map_data) or x >= len(self.scene.map_data[0]):
            return False
            
        return self.scene.map_data[y][x] != -1

    def get_tile_type_at(self, x, y):
        """Get tile type at given coordinates"""
        if not self.is_valid_position(x, y):
            return -1
            
        return self.scene.map_data[y][x]

    def propagate_zoom(self):
        """Propagate zoom scale to all objects that need it"""
        # For Arcade, zoom is typically handled by the camera
        # This method can be used for any custom zoom-dependent logic
        print(f"[ArcadeUtilities] Propagating zoom scale: {self.scene.zoom_scale}")
        
        # Update any zoom-dependent properties on sprites
        for sprite_list in self.scene.sprite_lists:
            for sprite in sprite_list:
                if hasattr(sprite, 'set_zoom_scale'):
                    sprite.set_zoom_scale(self.scene.zoom_scale)

    def calculate_distance(self, x1, y1, x2, y2):
        """Calculate distance between two points"""
        return math.hypot(x2 - x1, y2 - y1)

    def get_neighbors(self, x, y, include_diagonals=True):
        """Get neighboring coordinates"""
        neighbors = []
        
        if include_diagonals:
            offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        else:
            offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dx, dy in offsets:
            nx, ny = x + dx, y + dy
            if self.is_valid_position(nx, ny):
                neighbors.append((nx, ny))
        
        return neighbors

    def find_nearest_valid_position(self, target_x, target_y, max_search_radius=10):
        """Find the nearest valid position to a target coordinate"""
        if self.is_valid_position(target_x, target_y) and (target_x, target_y) not in self.scene.blocked_tiles:
            return target_x, target_y
        
        # Spiral search outward
        for radius in range(1, max_search_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:  # Only check perimeter
                        test_x, test_y = target_x + dx, target_y + dy
                        if (self.is_valid_position(test_x, test_y) and 
                            (test_x, test_y) not in self.scene.blocked_tiles):
                            return test_x, test_y
        
        return None

    def get_biome_at(self, x, y):
        """Get biome type at given coordinates"""
        tile_type = self.get_tile_type_at(x, y)
        
        biome_map = {
            1: "grassland",
            2: "water",
            3: "dirt",
            4: "mountain",
            5: "deep_water",
            11: "desert"
        }
        
        return biome_map.get(tile_type, "unknown")

    def is_shoreline(self, x, y):
        """Check if position is on shoreline (land adjacent to water)"""
        if self.is_water_tile(x, y):
            return False
            
        # Check if any neighbors are water
        for nx, ny in self.get_neighbors(x, y, include_diagonals=False):
            if self.is_water_tile(nx, ny):
                return True
        
        return False

    def get_area_tiles(self, center_x, center_y, radius):
        """Get all tiles within a given radius of center point"""
        tiles = []
        
        for y in range(center_y - radius, center_y + radius + 1):
            for x in range(center_x - radius, center_x + radius + 1):
                if self.calculate_distance(center_x, center_y, x, y) <= radius:
                    if self.is_valid_position(x, y):
                        tiles.append((x, y))
        
        return tiles

    def count_tile_types_in_area(self, center_x, center_y, radius):
        """Count different tile types in an area"""
        tile_counts = {}
        area_tiles = self.get_area_tiles(center_x, center_y, radius)
        
        for x, y in area_tiles:
            tile_type = self.get_tile_type_at(x, y)
            tile_counts[tile_type] = tile_counts.get(tile_type, 0) + 1
        
        return tile_counts

    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        # Get camera position
        camera_x, camera_y = self.scene.camera.position if self.scene.camera else (0, 0)
        
        # Standard isometric projection
        iso_x = (world_x - world_y) * (TILE_WIDTH // 2) * self.scene.zoom_scale
        iso_y = (world_x + world_y) * (TILE_HEIGHT // 2) * self.scene.zoom_scale
        
        # Convert to screen coordinates
        screen_x = iso_x - camera_x
        screen_y = iso_y - camera_y
        
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        # Get camera position
        camera_x, camera_y = self.scene.camera.position if self.scene.camera else (0, 0)
        
        # Remove camera offset
        world_x = screen_x + camera_x
        world_y = screen_y + camera_y
        
        # Convert from isometric to grid coordinates
        grid_x = int((world_x / (TILE_WIDTH // 2) + world_y / (TILE_HEIGHT // 2)) / 2 / self.scene.zoom_scale)
        grid_y = int((world_y / (TILE_HEIGHT // 2) - world_x / (TILE_WIDTH // 2)) / 2 / self.scene.zoom_scale)
        
        return grid_x, grid_y

    def clamp_to_map_bounds(self, x, y):
        """Clamp coordinates to map boundaries"""
        if not hasattr(self.scene, 'map_data'):
            return x, y
            
        map_width = len(self.scene.map_data[0])
        map_height = len(self.scene.map_data)
        
        x = max(0, min(x, map_width - 1))
        y = max(0, min(y, map_height - 1))
        
        return x, y

    def get_map_bounds(self):
        """Get map boundaries"""
        if not hasattr(self.scene, 'map_data'):
            return 0, 0, 0, 0
            
        return 0, 0, len(self.scene.map_data[0]), len(self.scene.map_data)

    def get_camera_bounds(self):
        """Get camera view boundaries in world coordinates"""
        # Get screen corners
        screen_corners = [
            (0, 0),
            (self.scene.window.width, 0),
            (self.scene.window.width, self.scene.window.height),
            (0, self.scene.window.height)
        ]
        
        # Convert to world coordinates
        world_bounds = []
        for screen_x, screen_y in screen_corners:
            world_x, world_y = self.screen_to_world(screen_x, screen_y)
            world_bounds.append((world_x, world_y))
        
        # Find bounding box
        min_x = min(x for x, y in world_bounds)
        max_x = max(x for x, y in world_bounds)
        min_y = min(y for x, y in world_bounds)
        max_y = max(y for x, y in world_bounds)
        
        return min_x, min_y, max_x, max_y

    def is_in_camera_view(self, world_x, world_y, margin=5):
        """Check if world coordinates are visible in camera view"""
        min_x, min_y, max_x, max_y = self.get_camera_bounds()
        
        return (min_x - margin <= world_x <= max_x + margin and 
                min_y - margin <= world_y <= max_y + margin)

    def calculate_buildability_score(self, x, y, building_size=1):
        """Calculate how suitable a location is for building"""
        if not self.is_valid_position(x, y):
            return 0
            
        score = 100
        
        # Penalty for water
        if self.is_water_tile(x, y):
            return 0
        
        # Check surrounding area
        for dy in range(-building_size, building_size + 1):
            for dx in range(-building_size, building_size + 1):
                test_x, test_y = x + dx, y + dy
                
                if not self.is_valid_position(test_x, test_y):
                    score -= 20
                    continue
                
                if self.is_water_tile(test_x, test_y):
                    score -= 15
                
                if (test_x, test_y) in self.scene.blocked_tiles:
                    score -= 25
        
        return max(0, score)

    def find_best_building_location(self, preferred_x, preferred_y, search_radius=10, building_size=1):
        """Find the best location for building near a preferred location"""
        best_score = -1
        best_location = None
        
        for radius in range(search_radius + 1):
            candidates = []
            
            if radius == 0:
                candidates = [(preferred_x, preferred_y)]
            else:
                # Check perimeter
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if abs(dx) == radius or abs(dy) == radius:
                            candidates.append((preferred_x + dx, preferred_y + dy))
            
            for x, y in candidates:
                score = self.calculate_buildability_score(x, y, building_size)
                if score > best_score:
                    best_score = score
                    best_location = (x, y)
            
            # If we found a good location at this radius, stop searching
            if best_score > 50:
                break
        
        return best_location if best_score > 0 else None

    def get_debug_info(self):
        """Get debug information about the planet state"""
        info = {
            "map_size": (self.scene.terrain_width, self.scene.terrain_height),
            "zoom_scale": self.scene.zoom_scale,
            "camera_position": self.scene.camera.position if self.scene.camera else (0, 0),
            "blocked_tiles_count": len(self.scene.blocked_tiles),
            "simulation_mode": getattr(self.scene, 'simulation_mode', 'unknown'),
            "mining_mode": getattr(self.scene, 'mining_mode', False)
        }
        
        return info

    def validate_world_state(self):
        """Validate that the world state is consistent"""
        issues = []
        
        # Check map data exists
        if not hasattr(self.scene, 'map_data') or not self.scene.map_data:
            issues.append("No map data found")
        
        # Check sprite lists exist
        if not hasattr(self.scene, 'sprite_lists') or not self.scene.sprite_lists:
            issues.append("Sprite lists not initialized")
        
        # Check essential collections exist
        for attr in ['blocked_tiles', 'tree_tiles', 'drops', 'inventory']:
            if not hasattr(self.scene, attr):
                issues.append(f"Missing {attr} collection")
        
        # Check camera exists
        if not self.scene.camera:
            issues.append("Camera not initialized")
        
        return issues

    def optimize_blocked_tiles(self):
        """Optimize blocked tiles calculation for better performance"""
        # Recalculate blocked tiles from scratch
        blocked = set()
        
        for y in range(len(self.scene.map_data)):
            for x in range(len(self.scene.map_data[0])):
                if self.scene.map_data[y][x] in (TILE_WATER, TILE_WATERSTACK, TILE_MOUNTAIN):
                    blocked.add((x, y))
        
        # Add tree and house tiles
        blocked.update(self.scene.tree_tiles)
        
        # Add house positions
        for house_sprite in self.scene.house_sprites:
            if hasattr(house_sprite, 'grid_x') and hasattr(house_sprite, 'grid_y'):
                blocked.add((house_sprite.grid_x, house_sprite.grid_y))
        
        self.scene.blocked_tiles = blocked
        print(f"[ArcadeUtilities] Optimized blocked tiles: {len(blocked)} total")

    def cleanup_dead_entities(self):
        """Clean up entities that are no longer alive"""
        initial_counts = {
            "animals": len(self.scene.animal_sprites),
            "bipeds": len(self.scene.biped_sprites),
            "drops": len(self.scene.drop_sprites)
        }
        
        # Clean up dead sprites from all lists
        for sprite_list in self.scene.sprite_lists:
            dead_sprites = [s for s in sprite_list if hasattr(s, 'alive') and not s.alive]
            for sprite in dead_sprites:
                sprite_list.remove(sprite)
        
        # Clean up drops list
        self.scene.drops = [d for d in self.scene.drops if getattr(d, 'alive', True)]
        
        # Log cleanup results
        final_counts = {
            "animals": len(self.scene.animal_sprites),
            "bipeds": len(self.scene.biped_sprites),
            "drops": len(self.scene.drop_sprites)
        }
        
        if any(initial_counts[k] != final_counts[k] for k in initial_counts):
            print(f"[ArcadeUtilities] Cleanup: Animals {initial_counts['animals']}→{final_counts['animals']}, "
                  f"Bipeds {initial_counts['bipeds']}→{final_counts['bipeds']}, "
                  f"Drops {initial_counts['drops']}→{final_counts['drops']}")

    def create_simple_texture(self, name, size, color):
        """Create a simple filled texture"""
        return arcade.Texture.create_filled(name, size, color)

    def create_diamond_texture(self, name, size, color):
        """Create a diamond-shaped texture for isometric tiles"""
        # For now, just create a filled texture
        # In a full implementation, this would create an actual diamond shape
        return arcade.Texture.create_filled(name, size, color)

    def get_sprite_at_position(self, screen_x, screen_y, sprite_list):
        """Get sprite at screen position from a sprite list"""
        for sprite in sprite_list:
            # Simple distance check
            distance = math.hypot(screen_x - sprite.center_x, screen_y - sprite.center_y)
            if distance < 20:  # 20 pixel radius for selection
                return sprite
        return None

    def convert_grid_to_iso(self, grid_x, grid_y):
        """Convert grid coordinates to isometric coordinates"""
        iso_x = (grid_x - grid_y) * (TILE_WIDTH // 2)
        iso_y = (grid_x + grid_y) * (TILE_HEIGHT // 2)
        return iso_x, iso_y

    def convert_iso_to_grid(self, iso_x, iso_y):
        """Convert isometric coordinates to grid coordinates"""
        grid_x = int((iso_x / (TILE_WIDTH // 2) + iso_y / (TILE_HEIGHT // 2)) / 2)
        grid_y = int((iso_y / (TILE_HEIGHT // 2) - iso_x / (TILE_WIDTH // 2)) / 2)
        return grid_x, grid_y

    def get_tile_center_iso(self, grid_x, grid_y):
        """Get the isometric center position of a grid tile"""
        return self.convert_grid_to_iso(grid_x, grid_y)

    def snap_to_grid(self, world_x, world_y):
        """Snap world coordinates to the nearest grid position"""
        grid_x, grid_y = self.convert_iso_to_grid(world_x, world_y)
        return self.convert_grid_to_iso(grid_x, grid_y)