##########################################################
# planet_utilities.py
# Utility functions and helper methods for planet scene
##########################################################

import pygame
import math

# Constants
TILE_WATER = 2
TILE_WATERSTACK = 5
TILE_MOUNTAIN = 4
TILE_DESERT = 11

class PlanetUtilities:
    """Collection of utility functions for planet scene operations"""
    
    def __init__(self, scene):
        self.scene = scene

    def is_water_tile(self, gx: int, gy: int) -> bool:
        """Convenience check for the two water tile IDs."""
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            # Check if position exists before getting tile type
            if (gx, gy) not in self.scene.terrain.terrain_stacks:
                return True  # Treat void as water (not walkable)
            surface_tile = self.scene.terrain.get_surface_tile(gx, gy)
            return surface_tile in (TILE_WATER, TILE_WATERSTACK)
        else:
            return self.scene.map_data[gy][gx] in (TILE_WATER, TILE_WATERSTACK)

    def is_valid_position(self, x, y):
        """Check if a position is within map bounds and valid"""
        if not hasattr(self.scene, 'map_data'):
            return False
            
        if x < 0 or y < 0:
            return False
            
        if y >= len(self.scene.map_data) or x >= len(self.scene.map_data[0]):
            return False
            
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            return (x, y) in self.scene.terrain.terrain_stacks
        else:
            return self.scene.map_data[y][x] != -1

    def get_tile_type_at(self, x, y):
        """Get tile type at given coordinates"""
        if not self.is_valid_position(x, y):
            return -1
            
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            return self.scene.terrain.get_surface_tile(x, y)
        else:
            return self.scene.map_data[y][x]

    def get_height_at(self, x, y):
        """Get terrain height at given coordinates"""
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            if (x, y) in self.scene.terrain.terrain_stacks:
                return self.scene.terrain.get_height_at(x, y)
        return 0

    def propagate_zoom(self):
        """Propagate zoom scale to all objects that need it"""
        self.scene.map.set_zoom_scale(self.scene.zoom_scale)

        for obj in self.scene.trees + self.scene.houses + self.scene.unit_manager.units:
            obj.set_zoom_scale(self.scene.zoom_scale)

        self.scene.animal_manager.set_zoom_scale(self.scene.zoom_scale)
        self.scene.animal_manager.calculate_screen_positions(
            self.scene.map.camera_offset_x, self.scene.map.camera_offset_y, self.scene.zoom_scale
        )

        for drop in self.scene.drops:
            drop.set_zoom_scale(self.scene.zoom_scale)
            drop.calculate_screen_position(
                self.scene.map.camera_offset_x, self.scene.map.camera_offset_y, self.scene.zoom_scale
            )

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

    def find_flat_area(self, center_x, center_y, min_size=3):
        """Find a flat area suitable for building"""
        if not (self.scene.use_layered_terrain and hasattr(self.scene, 'terrain')):
            # For flat terrain, just check if area is not blocked
            for y in range(center_y - min_size//2, center_y + min_size//2 + 1):
                for x in range(center_x - min_size//2, center_x + min_size//2 + 1):
                    if (x, y) in self.scene.blocked_tiles or not self.is_valid_position(x, y):
                        return False
            return True
        
        # For layered terrain, check height consistency
        base_height = self.get_height_at(center_x, center_y)
        
        for y in range(center_y - min_size//2, center_y + min_size//2 + 1):
            for x in range(center_x - min_size//2, center_x + min_size//2 + 1):
                if not self.is_valid_position(x, y):
                    return False
                    
                height = self.get_height_at(x, y)
                if abs(height - base_height) > 1:  # Allow 1 height difference
                    return False
                    
                if (x, y) in self.scene.blocked_tiles:
                    return False
        
        return True

    def get_spawn_areas_by_biome(self):
        """Get valid spawn areas organized by biome type"""
        spawn_areas = {
            "grassland": [],
            "desert": [],
            "dirt": [],
            "mountain": [],
            "shoreline": []
        }
        
        planet_w, planet_h = self.scene.meta.tiles
        
        for y in range(planet_h):
            for x in range(planet_w):
                if not self.is_valid_position(x, y) or (x, y) in self.scene.blocked_tiles:
                    continue
                
                biome = self.get_biome_at(x, y)
                
                if biome in spawn_areas:
                    spawn_areas[biome].append((x, y))
                
                # Check for shoreline
                if self.is_shoreline(x, y):
                    spawn_areas["shoreline"].append((x, y))
        
        return spawn_areas

    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        # Standard isometric projection
        iso_x = (world_x - world_y) * (self.scene.tile_width // 2) * self.scene.zoom_scale
        iso_y = (world_x + world_y) * (self.scene.tile_height // 2) * self.scene.zoom_scale
        
        # Add camera offset
        screen_x = iso_x + self.scene.map.camera_offset_x
        screen_y = iso_y + self.scene.map.camera_offset_y
        
        # Add height offset for layered terrain
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            height = self.get_height_at(world_x, world_y)
            height_offset = height * 16 * self.scene.zoom_scale
            screen_y -= height_offset
        
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        # Remove camera offset
        world_x = screen_x - self.scene.map.camera_offset_x
        world_y = screen_y - self.scene.map.camera_offset_y
        
        # Convert from isometric to grid coordinates
        grid_x = int((world_x / (self.scene.tile_width // 2) + world_y / (self.scene.tile_height // 2)) / 2 / self.scene.zoom_scale)
        grid_y = int((world_y / (self.scene.tile_height // 2) - world_x / (self.scene.tile_width // 2)) / 2 / self.scene.zoom_scale)
        
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
            (1920, 0),
            (1920, 1080),
            (0, 1080)
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

    def get_resource_value_at(self, x, y):
        """Get resource value at given coordinates"""
        if not self.is_valid_position(x, y):
            return 0
            
        # Base value depends on tile type
        tile_type = self.get_tile_type_at(x, y)
        base_values = {
            1: 1,   # Grassland - low
            3: 2,   # Dirt - medium
            4: 5,   # Mountain - high
            11: 1,  # Desert - low
        }
        
        base_value = base_values.get(tile_type, 0)
        
        # Height bonus for layered terrain
        if self.scene.use_layered_terrain:
            height = self.get_height_at(x, y)
            base_value += height * 0.5
        
        return base_value

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
        
        # Height consistency bonus for layered terrain
        if self.scene.use_layered_terrain:
            base_height = self.get_height_at(x, y)
            height_consistency = 0
            count = 0
            
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    test_x, test_y = x + dx, y + dy
                    if self.is_valid_position(test_x, test_y):
                        height = self.get_height_at(test_x, test_y)
                        height_consistency += abs(height - base_height)
                        count += 1
            
            if count > 0:
                avg_height_diff = height_consistency / count
                score -= avg_height_diff * 10  # Penalty for uneven terrain
        
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
            "map_size": self.scene.meta.tiles,
            "use_layered_terrain": getattr(self.scene, 'use_layered_terrain', False),
            "zoom_scale": self.scene.zoom_scale,
            "camera_position": (self.scene.map.camera_offset_x, self.scene.map.camera_offset_y),
            "blocked_tiles_count": len(self.scene.blocked_tiles),
            "simulation_mode": getattr(self.scene, 'simulation_mode', 'unknown'),
            "mining_mode": getattr(self.scene, 'mining_mode', False)
        }
        
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            info["terrain_stacks_count"] = len(self.scene.terrain.terrain_stacks)
            heights = [self.scene.terrain.get_height_at(x, y) for x, y in self.scene.terrain.terrain_stacks]
            if heights:
                info["min_height"] = min(heights)
                info["max_height"] = max(heights)
                info["avg_height"] = sum(heights) / len(heights)
        
        return info

    def validate_world_state(self):
        """Validate that the world state is consistent"""
        issues = []
        
        # Check map data exists
        if not hasattr(self.scene, 'map_data') or not self.scene.map_data:
            issues.append("No map data found")
        
        # Check entity managers exist
        if not hasattr(self.scene, 'unit_manager'):
            issues.append("Unit manager missing")
        if not hasattr(self.scene, 'animal_manager'):
            issues.append("Animal manager missing")
        
        # Check essential collections exist
        for attr in ['trees', 'houses', 'drops', 'blocked_tiles']:
            if not hasattr(self.scene, attr):
                issues.append(f"Missing {attr} collection")
        
        # Check layered terrain consistency
        if self.scene.use_layered_terrain:
            if not hasattr(self.scene, 'terrain'):
                issues.append("Layered terrain enabled but terrain object missing")
            elif hasattr(self.scene, 'terrain'):
                # Check surface map consistency
                for y in range(len(self.scene.map_data)):
                    for x in range(len(self.scene.map_data[0])):
                        if (x, y) in self.scene.terrain.terrain_stacks:
                            surface_tile = self.scene.terrain.get_surface_tile(x, y)
                            if surface_tile != self.scene.map_data[y][x]:
                                issues.append(f"Surface map inconsistency at ({x}, {y})")
                                break
                    if issues:
                        break
        
        return issues

    def optimize_blocked_tiles(self):
        """Optimize blocked tiles calculation for better performance"""
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            # Recalculate from scratch for layered terrain
            blocked = set()
            for y in range(self.scene.terrain.height):
                for x in range(self.scene.terrain.width):
                    if (x, y) not in self.scene.terrain.terrain_stacks:
                        blocked.add((x, y))
                        continue
                    surface_tile = self.scene.terrain.get_surface_tile(x, y)
                    height = self.scene.terrain.get_height_at(x, y)
                    if surface_tile in (TILE_WATER, TILE_WATERSTACK) or height > 6:
                        blocked.add((x, y))
            
            # Add tree and house tiles
            blocked.update(self.scene.tree_tiles)
            blocked.update((h.grid_x, h.grid_y) for h in self.scene.houses)
            
            self.scene.blocked_tiles = blocked
        else:
            # For flat terrain
            blocked = set()
            for y in range(len(self.scene.map_data)):
                for x in range(len(self.scene.map_data[0])):
                    if self.scene.map_data[y][x] in (TILE_WATER, TILE_WATERSTACK, TILE_MOUNTAIN):
                        blocked.add((x, y))
            
            # Add tree and house tiles
            blocked.update(self.scene.tree_tiles)
            blocked.update((h.grid_x, h.grid_y) for h in self.scene.houses)
            
            self.scene.blocked_tiles = blocked

    def cleanup_dead_entities(self):
        """Clean up entities that are no longer alive"""
        # Clean up dead animals
        initial_animal_count = len(self.scene.animal_manager.animals)
        self.scene.animal_manager.animals = [a for a in self.scene.animal_manager.animals if getattr(a, 'alive', True)]
        
        # Clean up dead drops
        initial_drop_count = len(self.scene.drops)
        self.scene.drops = [d for d in self.scene.drops if getattr(d, 'alive', True)]
        
        # Clean up dead units
        initial_unit_count = len(self.scene.unit_manager.units)
        self.scene.unit_manager.units = [u for u in self.scene.unit_manager.units if getattr(u, 'alive', True)]
        
        # Log cleanup results
        if (len(self.scene.animal_manager.animals) != initial_animal_count or
            len(self.scene.drops) != initial_drop_count or
            len(self.scene.unit_manager.units) != initial_unit_count):
            print(f"[Cleanup] Removed {initial_animal_count - len(self.scene.animal_manager.animals)} dead animals, "
                  f"{initial_drop_count - len(self.scene.drops)} dead drops, "
                  f"{initial_unit_count - len(self.scene.unit_manager.units)} dead units")