##########################################################
# planet_world_generator.py
# Handles world generation, terrain creation, vegetation, and initial spawning
##########################################################

import os
import random
import math
import pygame
from map_generation import (
    generate_procedural_map,
    generate_layered_terrain,
    apply_circular_mask,
    apply_circular_mask_layered,
    force_mountain_edge,
    force_mountain_edge_layered,
    make_forest_map,
    make_forest_map_layered,
    populate_trees,
    populate_trees_layered,
)
from iso_map import IsoTree, LayeredWaterSystem, LayeredResourceSystem, ProceduralIsoMap
from vegetation import generate_sprite
from subtile_manager import SubTileManager
from loading_screen import LoadingManager, PLANET_GENERATION_STEPS

# Constants
TILE_WATER = 2
TILE_WATERSTACK = 5
TILE_MOUNTAIN = 4
TILE_DESERT = 11

def _rand_colour() -> tuple[int, int, int]:
    """Bright random colour helper."""
    return random.randint(64, 255), random.randint(64, 255), random.randint(64, 255)

class PlanetWorldGenerator:
    """Handles all world generation, terrain creation, and initial population"""
    
    def __init__(self, scene):
        self.scene = scene
        
    def _generate_new_world(self, surface=None, use_loading_screen=True):
        """Generate the planet on first visit with optional loading screen"""
        planet_w, planet_h = self.scene.meta.tiles
        print(f"[PlanetScene] NEW planet {planet_w}×{planet_h}  seed={self.scene.meta.seed}")

        if use_loading_screen and surface:
            # Use loading screen for generation
            loading_manager = LoadingManager(surface)
            
            # Define the actual generation steps with functions
            generation_steps = [
                ("Initializing quantum substrate", self._initialize_systems, None),
                ("Engineering genetic algorithms", self._generate_terrain_step, (planet_w, planet_h)), 
                ("Cultivating diverse biomes", self._setup_camera_and_spawn_areas, (planet_w, planet_h)),
                ("Spawning primordial organisms", self._generate_vegetation_step, None),
                ("Establishing ecosystem balance", self._initialize_entities_step, None),
                ("Calibrating atmospheric conditions", self._finalize_generation_step, None),
                ("Activating geological processes", self._emergency_fallbacks_step, None),
                ("Finalizing planetary systems", self._complete_generation, None),
            ]
            
            success = loading_manager.load_with_progress(
                self._execute_generation,
                generation_steps,
                "Generating New Planet"
            )
            
            if not success:
                print("[PlanetScene] Loading screen generation failed, falling back to direct generation")
                self._generate_new_world_direct(planet_w, planet_h)
        else:
            # Direct generation without loading screen
            self._generate_new_world_direct(planet_w, planet_h)

    def _generate_new_world_direct(self, planet_w, planet_h):
        """Direct world generation without loading screen"""
        # ── Initialize procedural tile system ──────────────────
        print("[PlanetScene] Initializing procedural tile system...")
        self.scene.subtile_manager = SubTileManager(self.scene)
        
        # No more PNG loading - tiles are generated procedurally!
        self.scene.tile_width, self.scene.tile_height = 64, 37

        # ── Tree & house sprites ───────────────────────────────────
        self.scene.tree_images = {
            1: generate_sprite("pine"), 2: generate_sprite("oak"),
            3: generate_sprite("palm"), 4: generate_sprite("cactus"),
        }
        hp = os.path.join(self.scene.assets_dir, "house.png")
        self.scene.house_image = pygame.image.load(hp).convert_alpha() \
            if os.path.exists(hp) else self._placeholder_house()

        # ── Terrain & masks ─────────────────────────────────────────
        self._generate_terrain(planet_w, planet_h)
        self._setup_camera_and_spawn_areas(planet_w, planet_h)
        self._generate_vegetation()
        self._initialize_entities()
        
        # Final setup
        self.scene.iso_objects = self.scene.map.get_all_objects() + self.scene.trees + self.scene.houses
        self.scene.drops = []
        self.scene.inventory = {}
        self.scene.dragging = False
        self.scene.last_mouse_pos = (0, 0)
        self.scene.wave_time = 0.0
        self.scene.wave_speed = 5.0
        self.scene.wave_spacing = 3.0
        
        self.scene._propagate_zoom()
        self._emergency_fallbacks()
        self._log_generation_results()

    def _execute_generation(self, *args, progress_callback=None):
        """Execute generation with progress tracking - not used directly"""
        pass

    def _initialize_systems(self, progress_callback=None):
        """Initialize procedural tile system"""
        if progress_callback:
            progress_callback(0, "Initializing quantum substrate", 0.2, "Setting up tile system")
        
        print("[PlanetScene] Initializing procedural tile system...")
        self.scene.subtile_manager = SubTileManager(self.scene)
        self.scene.tile_width, self.scene.tile_height = 64, 37
        
        if progress_callback:
            progress_callback(0, "Initializing quantum substrate", 0.6, "Loading sprite generators")
        
        # Tree & house sprites
        self.scene.tree_images = {
            1: generate_sprite("pine"), 2: generate_sprite("oak"),
            3: generate_sprite("palm"), 4: generate_sprite("cactus"),
        }
        
        if progress_callback:
            progress_callback(0, "Initializing quantum substrate", 1.0, "Systems ready")
        
        hp = os.path.join(self.scene.assets_dir, "house.png")
        self.scene.house_image = pygame.image.load(hp).convert_alpha() \
            if os.path.exists(hp) else self._placeholder_house()

    def _generate_terrain_step(self, planet_w, planet_h, progress_callback=None):
        """Generate terrain with progress tracking"""
        if progress_callback:
            progress_callback(1, "Engineering genetic algorithms", 0.1, "Calculating quantum fields")
        
        if self.scene.use_layered_terrain:
            if progress_callback:
                progress_callback(1, "Engineering genetic algorithms", 0.3, "Generating layered substrate")
            print("[PlanetScene] Generating LAYERED terrain with stackable mountains/hills")
            self.scene.terrain = generate_layered_terrain(planet_w, planet_h)
            
            if progress_callback:
                progress_callback(1, "Engineering genetic algorithms", 0.6, "Applying planetary curvature")
            apply_circular_mask_layered(self.scene.terrain)
            force_mountain_edge_layered(self.scene.terrain, margin=2)
            
            if progress_callback:
                progress_callback(1, "Engineering genetic algorithms", 0.8, "Creating surface maps")
            # Compatibility: Create flat map reference for existing code
            self.scene.map_data = self.scene.terrain.surface_map
            
            # Create layered map renderer with procedural tiles
            self.scene.map = ProceduralIsoMap(self.scene.map_data, self.scene.subtile_manager, self.scene.terrain)
            
            if progress_callback:
                progress_callback(1, "Engineering genetic algorithms", 1.0, "Initializing water/resource systems")
            # Enhanced systems
            self.scene.water_system = LayeredWaterSystem(self.scene.terrain)
            self.scene.resource_system = LayeredResourceSystem(self.scene.terrain)
        else:
            if progress_callback:
                progress_callback(1, "Engineering genetic algorithms", 0.4, "Generating flat terrain")
            print("[PlanetScene] Generating FLAT terrain (legacy mode)")
            self.scene.map_data = generate_procedural_map(planet_w, planet_h)
            
            if progress_callback:
                progress_callback(1, "Engineering genetic algorithms", 0.7, "Shaping planetary boundaries")
            apply_circular_mask(self.scene.map_data)
            force_mountain_edge(self.scene.map_data, margin=2)
            
            if progress_callback:
                progress_callback(1, "Engineering genetic algorithms", 1.0, "Creating terrain renderer")
            # Create procedural map renderer
            self.scene.map = ProceduralIsoMap(self.scene.map_data, self.scene.subtile_manager, None)

    def _generate_vegetation_step(self, progress_callback=None):
        """Generate vegetation with progress tracking"""
        if progress_callback:
            progress_callback(3, "Spawning primordial organisms", 0.1, "Analyzing biome conditions")
        
        if self.scene.use_layered_terrain:
            print("[PlanetScene] Generating vegetation on layered terrain")
            try:
                if progress_callback:
                    progress_callback(3, "Spawning primordial organisms", 0.3, "Creating forest ecosystems")
                self.scene.forest_map = make_forest_map_layered(self.scene.terrain)
                
                if progress_callback:
                    progress_callback(3, "Spawning primordial organisms", 0.6, "Seeding plant genetics")
                tree_data = populate_trees_layered(self.scene.terrain, self.scene.forest_map, 0.04, 0.12)
                
                if progress_callback:
                    progress_callback(3, "Spawning primordial organisms", 0.9, "Growing vegetation")
                self.scene.trees = self._spawn_trees_layered(tree_data)
                print(f"[PlanetScene] Tree data: {len(tree_data)} positions, spawned: {len(self.scene.trees)} trees")
            except Exception as e:
                print(f"[PlanetScene] Error generating layered trees: {e}")
                if progress_callback:
                    progress_callback(3, "Spawning primordial organisms", 0.7, "Using fallback vegetation")
                self.scene.trees = self._generate_simple_trees()
        else:
            print("[PlanetScene] Generating vegetation on flat terrain")
            if progress_callback:
                progress_callback(3, "Spawning primordial organisms", 0.4, "Mapping forest regions")
            self.scene.forest_map = make_forest_map(self.scene.map_data)
            
            if progress_callback:
                progress_callback(3, "Spawning primordial organisms", 0.7, "Planting diverse species")
            tree_data = populate_trees(self.scene.map_data, self.scene.forest_map, 0.05, 0.15)
            self.scene.trees = self._spawn_trees(tree_data)
            
        if progress_callback:
            progress_callback(3, "Spawning primordial organisms", 1.0, "Vegetation established")
        
        # Update tree tiles and blocked tiles
        self.scene.tree_tiles = {(t.grid_x, t.grid_y) for t in self.scene.trees}
        self.scene.blocked_tiles.update(self.scene.tree_tiles)

    def _initialize_entities_step(self, progress_callback=None):
        """Initialize houses and entities with progress tracking"""
        if progress_callback:
            progress_callback(4, "Establishing ecosystem balance", 0.5, "Preparing settlement zones")
        
        self.scene.houses = []
        self.scene.house_built = False
        
        if progress_callback:
            progress_callback(4, "Establishing ecosystem balance", 1.0, "Ecosystem ready")

    def _finalize_generation_step(self, progress_callback=None):
        """Finalize generation with progress tracking"""
        if progress_callback:
            progress_callback(5, "Calibrating atmospheric conditions", 0.2, "Assembling world objects")
        
        # Final setup
        self.scene.iso_objects = self.scene.map.get_all_objects() + self.scene.trees + self.scene.houses
        
        if progress_callback:
            progress_callback(5, "Calibrating atmospheric conditions", 0.5, "Initializing resource systems")
        self.scene.drops = []
        self.scene.inventory = {}
        
        if progress_callback:
            progress_callback(5, "Calibrating atmospheric conditions", 0.8, "Setting environmental parameters")
        self.scene.dragging = False
        self.scene.last_mouse_pos = (0, 0)
        self.scene.wave_time = 0.0
        self.scene.wave_speed = 5.0
        self.scene.wave_spacing = 3.0
        
        if progress_callback:
            progress_callback(5, "Calibrating atmospheric conditions", 1.0, "Propagating zoom settings")
        self.scene._propagate_zoom()

    def _emergency_fallbacks_step(self, progress_callback=None):
        """Emergency fallbacks with progress tracking"""
        if progress_callback:
            progress_callback(6, "Activating geological processes", 0.5, "Checking ecosystem integrity")
        
        self._emergency_fallbacks()
        
        if progress_callback:
            progress_callback(6, "Activating geological processes", 1.0, "Geological systems active")

    def _complete_generation(self, progress_callback=None):
        """Complete generation with progress tracking"""
        if progress_callback:
            progress_callback(7, "Finalizing planetary systems", 0.5, "Running final diagnostics")
        
        self._log_generation_results()
        
        if progress_callback:
            progress_callback(7, "Finalizing planetary systems", 1.0, "Planet generation complete")

    def _generate_terrain(self, planet_w, planet_h):
        """Generate terrain system (layered or flat)"""
        if self.scene.use_layered_terrain:
            print("[PlanetScene] Generating LAYERED terrain with stackable mountains/hills")
            self.scene.terrain = generate_layered_terrain(planet_w, planet_h)
            apply_circular_mask_layered(self.scene.terrain)
            force_mountain_edge_layered(self.scene.terrain, margin=2)
            
            # Compatibility: Create flat map reference for existing code
            self.scene.map_data = self.scene.terrain.surface_map
            
            # Create layered map renderer with procedural tiles
            self.scene.map = ProceduralIsoMap(self.scene.map_data, self.scene.subtile_manager, self.scene.terrain)
            
            # Enhanced systems
            self.scene.water_system = LayeredWaterSystem(self.scene.terrain)
            self.scene.resource_system = LayeredResourceSystem(self.scene.terrain)
        else:
            print("[PlanetScene] Generating FLAT terrain (legacy mode)")
            self.scene.map_data = generate_procedural_map(planet_w, planet_h)
            apply_circular_mask(self.scene.map_data)
            force_mountain_edge(self.scene.map_data, margin=2)
            
            # Create procedural map renderer
            self.scene.map = ProceduralIsoMap(self.scene.map_data, self.scene.subtile_manager, None)

    def _setup_camera_and_spawn_areas(self, planet_w, planet_h, progress_callback=None):
        """Setup camera positioning and find valid spawn areas"""
        if progress_callback:
            progress_callback(2, "Cultivating diverse biomes", 0.2, "Surveying planetary surface")
        
        # Find valid tiles for spawning
        valid = [(x,y) for y in range(planet_h) for x in range(planet_w)
                 if self.scene.map_data[y][x] != -1]
        if not valid:
            print("[PlanetScene] ERROR: No valid tiles found!")
            return
        
        if progress_callback:
            progress_callback(2, "Cultivating diverse biomes", 0.4, "Locating planetary center")
            
        # Find the actual center of the planet (closest valid tile to geometric center)
        cx,cy = min(valid, key=lambda t: math.hypot(t[0]-planet_w/2,t[1]-planet_h/2))
        inner = int((planet_w//2)*0.8)
        self.scene.near_centre = [t for t in valid if math.hypot(t[0]-cx,t[1]-cy)<inner] or valid

        if progress_callback:
            progress_callback(2, "Cultivating diverse biomes", 0.6, "Positioning orbital cameras")
        
        # Camera positioning - CENTER THE PLANET ON SCREEN
        # Convert planet center to isometric screen coordinates
        iso_x = (cx - cy) * (self.scene.tile_width // 2)
        iso_y = (cx + cy) * (self.scene.tile_height // 2)
        
        # Position camera so planet center appears at screen center
        screen_center_x = 1920 // 2
        screen_center_y = 1080 // 2
        
        self.scene.map.camera_offset_x = screen_center_x - iso_x
        self.scene.map.camera_offset_y = screen_center_y - iso_y
        
        print(f"[PlanetScene] Planet center: ({cx}, {cy})")
        print(f"[PlanetScene] Isometric position: ({iso_x}, {iso_y})")
        print(f"[PlanetScene] Camera offset: ({self.scene.map.camera_offset_x}, {self.scene.map.camera_offset_y})")

        if progress_callback:
            progress_callback(2, "Cultivating diverse biomes", 0.8, "Mapping terrain obstacles")
        
        # Calculate blocked tiles
        if self.scene.use_layered_terrain:
            self.scene.blocked_tiles = self._calculate_blocked_tiles_layered()
        else:
            self.scene.blocked_tiles = {
                (c,r) for r in range(self.scene.map.height) for c in range(self.scene.map.width)
                if self.scene.map_data[r][c] in (TILE_WATER, TILE_WATERSTACK, TILE_MOUNTAIN)
            }
        
        if progress_callback:
            progress_callback(2, "Cultivating diverse biomes", 1.0, "Biome cultivation complete")

    def _generate_vegetation(self):
        """Generate trees and vegetation"""
        if self.scene.use_layered_terrain:
            print("[PlanetScene] Generating vegetation on layered terrain")
            try:
                self.scene.forest_map = make_forest_map_layered(self.scene.terrain)
                tree_data = populate_trees_layered(self.scene.terrain, self.scene.forest_map, 0.04, 0.12)
                self.scene.trees = self._spawn_trees_layered(tree_data)
                print(f"[PlanetScene] Tree data: {len(tree_data)} positions, spawned: {len(self.scene.trees)} trees")
            except Exception as e:
                print(f"[PlanetScene] Error generating layered trees: {e}")
                self.scene.trees = self._generate_simple_trees()
        else:
            print("[PlanetScene] Generating vegetation on flat terrain")
            self.scene.forest_map = make_forest_map(self.scene.map_data)
            tree_data = populate_trees(self.scene.map_data, self.scene.forest_map, 0.05, 0.15)
            self.scene.trees = self._spawn_trees(tree_data)
            
        # Update tree tiles and blocked tiles
        self.scene.tree_tiles = {(t.grid_x, t.grid_y) for t in self.scene.trees}
        self.scene.blocked_tiles.update(self.scene.tree_tiles)

    def _initialize_entities(self):
        """Initialize houses, bipeds, and animals"""
        self.scene.houses = []
        self.scene.house_built = False

    def _spawn_trees_layered(self, tree_data_list):
        """Spawn trees on layered terrain with height information"""
        trees = []
        used = set()
        
        print(f"[PlanetScene] Spawning {len(tree_data_list)} tree clusters on layered terrain")
        
        for tree_data in tree_data_list:
            if len(tree_data) == 6:  # New format with height
                gx, gy, tree_type, ox, oy, height = tree_data
            else:  # Old format without height
                gx, gy, tree_type, ox, oy = tree_data
                height = self.scene.terrain.get_height_at(gx, gy) if hasattr(self.scene, 'terrain') else 0
                
            if (gx, gy) in used:
                continue
                
            # Check if position is valid for tree placement
            if hasattr(self.scene, 'terrain'):
                if (gx, gy) not in self.scene.terrain.terrain_stacks:
                    continue
                surface_tile = self.scene.terrain.get_surface_tile(gx, gy)
                if surface_tile == -1:  # Void tile
                    continue
                    
            used.add((gx, gy))
            tree = IsoTree(gx, gy, tree_type, ox, oy, 
                          original_image=self.scene.tree_images.get(tree_type, self.scene.tree_images[1]),
                          height=height)
            tree.draw_order = (gx + gy) * 10 + 5  # Layer 5: above animals
            trees.append(tree)
            
        print(f"[PlanetScene] Successfully spawned {len(trees)} trees")
        return trees

    def _spawn_trees(self, tree_data_list):
        """Populate the world with IsoTree objects based on terrain."""
        h, w = len(self.scene.map_data), len(self.scene.map_data[0])
        used = set()
        trees = []

        # Dense forest – pines + oaks
        forest_tiles = [
            (gx, gy, ox, oy)
            for gx, gy, _, ox, oy in tree_data_list
            if self.scene.forest_map[gy][gx] and self.scene.map_data[gy][gx] != TILE_DESERT
        ]
        
        # Randomly choose cluster centres
        for cx, cy, *_ in random.sample(forest_tiles, max(1, len(forest_tiles)//400)):
            for _ in range(random.randint(3, 8)):
                nx, ny = cx + random.randint(-2, 2), cy + random.randint(-2, 2)
                if (
                    0 <= nx < w and 0 <= ny < h
                    and self.scene.forest_map[ny][nx] and (nx, ny) not in used
                ):
                    used.add((nx, ny))
                    tree = IsoTree(nx, ny, 1, random.random(), random.random(),
                                   original_image=self.scene.tree_images[1])
                    tree.draw_order = (nx + ny) * 10 + 5
                    trees.append(tree)

        # Remaining forest tiles → oaks
        for gx, gy, ox, oy in forest_tiles:
            if (gx, gy) in used:
                continue
            used.add((gx, gy))
            tree = IsoTree(gx, gy, 2, ox, oy, original_image=self.scene.tree_images[2])
            tree.draw_order = (gx + gy) * 10 + 5
            trees.append(tree)

        # Desert shoreline palms
        shoreline = []
        for gy in range(h):
            for gx in range(w):
                if self.scene.map_data[gy][gx] != TILE_DESERT:
                    continue
                if any(
                    0 <= gx+dx < w and 0 <= gy+dy < h
                    and self.scene.map_data[gy+dy][gx+dx] in (TILE_WATER, TILE_WATERSTACK)
                    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))
                ):
                    shoreline.append((gx, gy))

        for sx, sy in shoreline:
            for _ in range(random.randint(1, 3)):
                ox, oy = sx + random.randint(-2, 2), sy + random.randint(-2, 2)
                if (
                    0 <= ox < w and 0 <= oy < h
                    and self.scene.map_data[oy][ox] == TILE_DESERT
                    and (ox, oy) not in used
                ):
                    used.add((ox, oy))
                    tree = IsoTree(ox, oy, 3, random.random(), random.random(),
                                   original_image=self.scene.tree_images[3])
                    tree.draw_order = (ox + oy) * 10 + 5
                    trees.append(tree)

        # Sparse desert cacti
        for gy in range(h):
            for gx in range(w):
                if self.scene.map_data[gy][gx] == TILE_DESERT and (gx, gy) not in used:
                    if random.random() <= 0.03:
                        used.add((gx, gy))
                        tree = IsoTree(gx, gy, 4, random.random(), random.random(),
                                       original_image=self.scene.tree_images[4])
                        tree.draw_order = (gx + gy) * 10 + 5
                        trees.append(tree)
        return trees

    def _generate_simple_trees(self):
        """Fallback tree generation for when layered fails"""
        trees = []
        planet_w, planet_h = self.scene.meta.tiles
        tree_count = (planet_w * planet_h) // 200
        
        for _ in range(tree_count):
            attempts = 0
            while attempts < 25:
                x = random.randint(0, planet_w - 1)
                y = random.randint(0, planet_h - 1)
                
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    if (x, y) in self.scene.terrain.terrain_stacks:
                        surface_tile = self.scene.terrain.get_surface_tile(x, y)
                        height = self.scene.terrain.get_height_at(x, y)
                        if surface_tile == 1 and height <= 3:
                            tree = IsoTree(x, y, random.choice([1, 2, 3]), 
                                         random.randint(-5, 5), random.randint(-5, 0),
                                         original_image=self.scene.tree_images[random.choice([1, 2, 3])],
                                         height=height)
                            tree.draw_order = (x + y) * 10 + 5
                            trees.append(tree)
                            break
                else:
                    if self.scene.map_data[y][x] == 1:
                        tree = IsoTree(x, y, random.choice([1, 2, 3]), 
                                     random.randint(-5, 5), random.randint(-5, 0),
                                     original_image=self.scene.tree_images[random.choice([1, 2, 3])])
                        tree.draw_order = (x + y) * 10 + 5
                        trees.append(tree)
                        break
                attempts += 1
        
        print(f"[PlanetScene] Fallback generated {len(trees)} simple trees")
        return trees

    def _generate_emergency_trees(self, count):
        """Generate trees if normal generation failed"""
        trees = []
        planet_w, planet_h = self.scene.meta.tiles
        
        for _ in range(count):
            attempts = 0
            while attempts < 10:
                x = random.randint(1, planet_w - 2)
                y = random.randint(1, planet_h - 2)
                
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    if (x, y) in self.scene.terrain.terrain_stacks:
                        surface_tile = self.scene.terrain.get_surface_tile(x, y)
                        height = self.scene.terrain.get_height_at(x, y)
                        if surface_tile == 1 and height <= 4:
                            tree = IsoTree(x, y, random.choice([1, 2]), 0, 0,
                                         original_image=self.scene.tree_images[random.choice([1, 2])],
                                         height=height)
                            tree.draw_order = (x + y) * 10 + 5
                            trees.append(tree)
                            break
                else:
                    if self.scene.map_data[y][x] == 1:
                        tree = IsoTree(x, y, random.choice([1, 2]), 0, 0,
                                     original_image=self.scene.tree_images[random.choice([1, 2])])
                        tree.draw_order = (x + y) * 10 + 5
                        trees.append(tree)
                        break
                attempts += 1
        
        return trees

    def _calculate_blocked_tiles_layered(self):
        """Calculate blocked tiles for layered terrain"""
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
                    
        print(f"[PlanetScene] Blocked {len(blocked)} tiles out of {self.scene.terrain.width * self.scene.terrain.height}")
        return blocked

    def _emergency_fallbacks(self):
        """Emergency generation if normal systems failed"""
        if len(self.scene.trees) < 5:
            print("[PlanetScene] Emergency tree generation")
            emergency_trees = self._generate_emergency_trees(10)
            self.scene.trees.extend(emergency_trees)
            self.scene.tree_tiles.update((t.grid_x, t.grid_y) for t in emergency_trees)
            self.scene.iso_objects.extend(emergency_trees)

    def _log_generation_results(self):
        """Log final generation results"""
        print(f"[PlanetScene] Final entity counts:")
        print(f"  - Terrain objects: {len(self.scene.map.get_all_objects())}")
        print(f"  - Trees: {len(self.scene.trees)}")
        print(f"  - Total drawable objects: {len(self.scene.iso_objects)}")

    def _placeholder_house(self):
        """Create placeholder house sprite"""
        img = pygame.Surface((96,96), pygame.SRCALPHA)
        pygame.draw.rect(img,(150,75,0),(0,24,96,72))
        pygame.draw.polygon(img,(200,0,0),[(0,24),(48,0),(96,24)])
        return img