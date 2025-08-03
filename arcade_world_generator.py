##########################################################
# arcade_world_generator.py
# Handles world generation, terrain creation, vegetation, and initial spawning for Arcade
##########################################################

import random
import math
import arcade

# Constants
TILE_WATER = 2
TILE_WATERSTACK = 5
TILE_MOUNTAIN = 4
TILE_DESERT = 11
TILE_WIDTH = 64
TILE_HEIGHT = 37

class ArcadeWorldGenerator:
    """Handles all world generation, terrain creation, and initial population for Arcade"""
    
    def __init__(self, scene):
        self.scene = scene

    def generate_new_world(self):
        """Generate the planet on first visit"""
        planet_w, planet_h = self.scene.meta.tiles
        print(f"[ArcadeWorldGenerator] NEW planet {planet_w}×{planet_h} seed={self.scene.meta.seed}")

        # Generate terrain
        self._generate_terrain(planet_w, planet_h)
        
        # Setup camera and spawn areas
        self._setup_camera_and_spawn_areas(planet_w, planet_h)
        
        # Generate vegetation
        self._generate_vegetation()
        
        # Initialize entities
        self._initialize_entities()
        
        print(f"[ArcadeWorldGenerator] Generated terrain with {len(self.scene.terrain_sprites)} tiles")

    def _generate_terrain(self, planet_w, planet_h):
        """Generate terrain system"""
        print("[ArcadeWorldGenerator] Generating terrain...")
        
        # Generate procedural map data
        self.scene.map_data = self._generate_procedural_map(planet_w, planet_h)
        
        # Apply circular mask
        self._apply_circular_mask(self.scene.map_data)
        
        # Force mountain edges
        self._force_mountain_edge(self.scene.map_data, margin=2)
        
        # Create terrain sprites from map data
        self._create_terrain_sprites()

    def _generate_procedural_map(self, width, height):
        """Generate base procedural map"""
        map_data = [[0 for _ in range(width)] for _ in range(height)]

        # Create biome seeds
        biome_seeds = [
            ("water", 6),
            ("desert", 4),
            ("mountain", 5),
            ("grass", 4)
        ]
        
        seeds = []
        for (biome, count) in biome_seeds:
            for _ in range(count):
                sx = random.randint(0, width-1)
                sy = random.randint(0, height-1)
                seeds.append((sx, sy, biome))

        def get_tile_for_biome(biome):
            if biome == "water":
                return TILE_WATER
            elif biome == "desert":
                return TILE_DESERT
            elif biome == "mountain":
                return TILE_MOUNTAIN
            return 1  # Grass

        def dist2(x1, y1, x2, y2):
            dx = x2 - x1
            dy = y2 - y1
            return dx*dx + dy*dy

        # Voronoi fill
        for y in range(height):
            for x in range(width):
                best_d2 = 999999999
                best_biome = "grass"
                for (sx, sy, biome) in seeds:
                    d2 = dist2(x, y, sx, sy)
                    if d2 < best_d2:
                        best_d2 = d2
                        best_biome = biome
                map_data[y][x] = get_tile_for_biome(best_biome)

        return map_data

    def _apply_circular_mask(self, map_data):
        """Apply circular mask to create planet boundary"""
        height = len(map_data)
        width = len(map_data[0]) if height > 0 else 0

        cx, cy = width // 2, height // 2
        R = min(cx, cy) - 5
        
        for y in range(height):
            for x in range(width):
                dx = x - cx
                dy = y - cy
                dist_sq = dx*dx + dy*dy
                if dist_sq > R*R:
                    map_data[y][x] = -1  # Void

    def _force_mountain_edge(self, map_data, margin=2):
        """Force mountain edge around planet boundary"""
        height = len(map_data)
        width = len(map_data[0]) if height > 0 else 0
        cx, cy = width // 2, height // 2
        R = min(cx, cy) - 5
        min_dist_sq = (R - margin)*(R - margin)
        max_dist_sq = R*R
        
        for y in range(height):
            for x in range(width):
                if map_data[y][x] == -1:
                    continue
                dx = x - cx
                dy = y - cy
                dist_sq = dx*dx + dy*dy
                if min_dist_sq <= dist_sq <= max_dist_sq:
                    if map_data[y][x] not in (TILE_WATER, TILE_WATERSTACK):
                        map_data[y][x] = TILE_MOUNTAIN

    def _create_terrain_sprites(self):
        """Create Arcade sprites for terrain"""
        self.scene.terrain_sprites.clear()
        
        for y in range(len(self.scene.map_data)):
            for x in range(len(self.scene.map_data[0])):
                tile_type = self.scene.map_data[y][x]
                
                if tile_type == -1:  # Skip void tiles
                    continue
                
                # Calculate isometric position
                iso_x = (x - y) * (TILE_WIDTH // 2)
                iso_y = (x + y) * (TILE_HEIGHT // 2)
                
                # Create terrain sprite
                from arcade_planet_scene import ArcadeTerrainSprite
                terrain_sprite = ArcadeTerrainSprite(tile_type, iso_x, iso_y, 1)
                self.scene.terrain_sprites.append(terrain_sprite)

    def _setup_camera_and_spawn_areas(self, planet_w, planet_h):
        """Setup camera positioning and find valid spawn areas"""
        # Find valid tiles for spawning
        valid = [(x, y) for y in range(planet_h) for x in range(planet_w)
                 if self.scene.map_data[y][x] != -1]
        
        if not valid:
            print("[ArcadeWorldGenerator] ERROR: No valid tiles found!")
            return
        
        # Find the actual center of the planet
        cx, cy = min(valid, key=lambda t: math.hypot(t[0]-planet_w/2, t[1]-planet_h/2))
        inner = int((planet_w//2)*0.8)
        self.scene.valid_spawn_tiles = [t for t in valid if math.hypot(t[0]-cx, t[1]-cy) < inner] or valid

        # Calculate blocked tiles
        self.scene.blocked_tiles = {
            (x, y) for y in range(planet_h) for x in range(planet_w)
            if self.scene.map_data[y][x] in (TILE_WATER, TILE_WATERSTACK, TILE_MOUNTAIN)
        }
        
        print(f"[ArcadeWorldGenerator] Found {len(valid)} valid tiles, {len(self.scene.valid_spawn_tiles)} spawn tiles")

    def _generate_vegetation(self):
        """Generate trees and vegetation"""
        print("[ArcadeWorldGenerator] Generating vegetation...")
        
        # Simple tree generation
        tree_count = (self.scene.terrain_width * self.scene.terrain_height) // 100
        
        for _ in range(tree_count):
            attempts = 0
            while attempts < 20:
                x = random.randint(0, self.scene.terrain_width - 1)
                y = random.randint(0, self.scene.terrain_height - 1)
                
                if (x, y) not in self.scene.blocked_tiles and self.scene.map_data[y][x] == 1:  # Grass
                    # Calculate isometric position
                    iso_x = (x - y) * (TILE_WIDTH // 2)
                    iso_y = (x + y) * (TILE_HEIGHT // 2)
                    
                    # Create tree sprite
                    tree = ArcadeTreeSprite(iso_x, iso_y)
                    self.scene.tree_sprites.append(tree)
                    self.scene.tree_tiles.add((x, y))
                    self.scene.blocked_tiles.add((x, y))
                    break
                attempts += 1
        
        print(f"[ArcadeWorldGenerator] Generated {len(self.scene.tree_sprites)} trees")

    def _initialize_entities(self):
        """Initialize houses and other entities"""
        self.scene.houses = []
        self.scene.house_built = False
        print("[ArcadeWorldGenerator] Entities initialized")


class ArcadeTreeSprite(arcade.Sprite):
    """Tree sprite for Arcade"""
    
    def __init__(self, x: float, y: float):
        super().__init__()
        self.center_x = x
        self.center_y = y
        
        # Create a simple tree texture (green circle on brown rectangle)
        self.texture = arcade.Texture.create_filled("tree", (32, 48), (34, 139, 34))  # Green