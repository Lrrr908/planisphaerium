##########################################################
# planet_state_manager.py
# Handles save/load state, serialization, and persistence
##########################################################

import time
import os
import pygame
from iso_map import IsoTree, LayeredWaterSystem, LayeredResourceSystem, ProceduralIsoMap
from vegetation import generate_sprite
from drop import DropObject
from animals import create_pixel_animal_frames
from loading_screen import LoadingManager, PLANET_LOADING_STEPS

class PlanetStateManager:
    """Handles all state serialization, loading, and persistence"""
    
    def __init__(self, scene):
        self.scene = scene

    def serialize_state(self) -> dict:
        """Turn the live world into a comprehensive save-dict"""
        return {
            # Core world data
            "world_data": {
                "terrain": self.scene.map_data,
                "seed": self.scene.meta.seed,
                "size": self.scene.meta.tiles,
                "generation_version": 1
            },
            
            # Biome and vegetation 
            "biomes": {
                "forest_map": self.scene.forest_map,
                "tree_positions": [
                    {
                        "x": tree.grid_x,
                        "y": tree.grid_y, 
                        "type": tree.tree_type,
                        "offset_x": tree.off_x,
                        "offset_y": tree.off_y
                    }
                    for tree in self.scene.trees
                ]
            },
            
            # Buildings and structures
            "structures": {
                "houses": [
                    {"x": h.grid_x, "y": h.grid_y, "type": "basic_house"}
                    for h in self.scene.houses
                ],
                "subtile_buildings": getattr(self.scene.subtile_manager, 'buildings', {}) if hasattr(self.scene, 'subtile_manager') else {}
            },
            
            # Living entities
            "entities": {
                "animals": [
                    {
                        "species_id": animal.species_id,
                        "x": animal.grid_x,
                        "y": animal.grid_y,
                        "x_f": getattr(animal, 'x_f', 0.0),
                        "y_f": getattr(animal, 'y_f', 0.0),
                        "health": getattr(animal, 'health', 100),
                        "growth_scale": getattr(animal, 'growth_scale', 1.0),
                        "diet": getattr(animal, 'diet', 'herbivore'),
                        "aggression": getattr(animal, 'aggression', 0.0),
                        "territory_radius": getattr(animal, 'territory_radius', 3),
                        "sprite_data": self._serialize_animal_sprite(animal)
                    }
                    for animal in self.scene.animal_manager.animals if getattr(animal, 'alive', True)
                ],
                "species_data": {
                    str(sid): {
                        "founder_alive": getattr(founder, 'alive', True),
                        "sprite_frames": self._serialize_animal_sprite(founder)
                    }
                    for sid, founder in self.scene.animal_manager.species_founders.items()
                }
            },
            
            # Resources and items
            "resources": {
                "drops": [self._serialize_drop(drop) for drop in self.scene.drops],
                "inventory": self.scene.inventory
            },
            
            # Player progress - COMPREHENSIVE biped tracking
            "player_data": {
                "units": [
                    {
                        # Position data (exact coordinates)
                        "grid_x": unit.grid_x,
                        "grid_y": unit.grid_y,
                        "x_f": getattr(unit, 'x_f', 0.0),
                        "y_f": getattr(unit, 'y_f', 0.0),
                        "screen_x": getattr(unit, 'screen_x', 0),
                        "screen_y": getattr(unit, 'screen_y', 0),
                        
                        # Movement state (current path and destination)
                        "path_tiles": getattr(unit, 'path_tiles', []),
                        "path_index": getattr(unit, 'path_index', 0),
                        "destination_x": getattr(unit, 'destination_x', None),
                        "destination_y": getattr(unit, 'destination_y', None),
                        "moving": getattr(unit, 'moving', False),
                        "move_progress": getattr(unit, 'move_progress', 0.0),
                        
                        # Mission/task state
                        "mission": getattr(unit, 'mission', 'IDLE'),
                        "mission_data": getattr(unit, 'mission_data', {}),
                        "target_drop": None if not hasattr(unit, 'target_drop') or not unit.target_drop else {
                            "drop_id": getattr(unit.target_drop, 'id', None),
                            "drop_x": unit.target_drop.grid_x,
                            "drop_y": unit.target_drop.grid_y
                        },
                        
                        # Unit properties
                        "health": getattr(unit, 'health', 100),
                        "max_health": getattr(unit, 'max_health', 100),
                        "inventory": getattr(unit, 'inventory', {}),
                        "speed": getattr(unit, 'speed', 2.5),
                        "color": getattr(unit, 'color', (0, 255, 255)),
                        "selected": getattr(unit, 'selected', False),
                        
                        # Unique identifier for tracking
                        "unit_id": getattr(unit, 'unit_id', f"unit_{unit.grid_x}_{unit.grid_y}_{hash(unit)}"),
                        "creation_time": getattr(unit, 'creation_time', time.time()),
                        "last_command_time": getattr(unit, 'last_command_time', time.time()),
                        
                        # Animation state
                        "current_frame": getattr(unit, 'current_frame', 0),
                        "animation_time": getattr(unit, 'animation_time', 0.0),
                        "facing_direction": getattr(unit, 'facing_direction', 'down')
                    }
                    for unit in self.scene.unit_manager.units if getattr(unit, 'alive', True)
                ],
                "units_total": len(self.scene.unit_manager.units),
                "units_by_mission": self._get_units_by_mission(),
                "units_moving": len([u for u in self.scene.unit_manager.units if getattr(u, 'moving', False)]),
                "planet_seed": self.scene.meta.seed,
                "save_timestamp": time.time(),
                "camera": {
                    "x": self.scene.map.camera_offset_x,
                    "y": self.scene.map.camera_offset_y,
                    "zoom": self.scene.zoom_scale
                }
            },
            
            # Save metadata
            "save_info": {
                "format_version": 3,
                "timestamp": time.time(),
                "game_version": "1.0.0"
            },
            
            # Layered terrain data
            "terrain_system": {
                "use_layered": getattr(self.scene, 'use_layered_terrain', False),
                "terrain_stacks": {} if not hasattr(self.scene, 'terrain') else {
                    f"{x},{y}": [
                        {
                            "tile_type": tile.tile_type,
                            "height": tile.height,
                            "damaged": tile.damaged,
                            "sub_tiles": tile.sub_tiles
                        }
                        for tile in stack
                    ]
                    for (x, y), stack in self.scene.terrain.terrain_stacks.items()
                }
            }
        }

    def load_state(self, state: dict, surface=None, use_loading_screen=True):
        """Rebuild from comprehensive saved dict - FULLY PROCEDURAL"""
        planet_w, planet_h = self.scene.meta.tiles
        print(f"[PlanetScene] RESTORE planet {planet_w}×{planet_h}  seed={self.scene.meta.seed}")

        # Check save format version for compatibility
        save_version = state.get("save_info", {}).get("format_version", 1)
        if save_version < 3:
            print(f"[PlanetScene] Old save format {save_version}, using legacy loader")
            return self._load_legacy_state(state)

        if use_loading_screen and surface:
            # Use loading screen for loading
            loading_manager = LoadingManager(surface)
            
            # Define the actual loading steps with functions
            loading_steps = [
                ("Scanning planetary surface", self._initialize_procedural_system_step, None),
                ("Reconstructing terrain data", self._restore_terrain_system_step, (state,)),
                ("Reviving suspended organisms", self._restore_entities_step, (state,)),
                ("Synchronizing time streams", self._restore_camera_and_settings_step, (state,)),
                ("Restoring ecosystem state", self._restore_vegetation_and_structures_step, (state,)),
                ("Activating simulation engine", self._restore_resources_and_inventory_step, (state,)),
            ]
            
            success = loading_manager.load_with_progress(
                self._execute_loading,
                loading_steps,
                "Loading Planet"
            )
            
            if success:
                self._finalize_restoration()
            else:
                print("[PlanetScene] Loading screen failed, falling back to direct loading")
                self._load_state_direct(state)
        else:
            # Direct loading without loading screen
            self._load_state_direct(state)

    def _load_state_direct(self, state):
        """Direct state loading without loading screen"""
        self._initialize_procedural_system()
        self._restore_terrain_system(state)
        self._restore_camera_and_settings(state)
        self._restore_vegetation_and_structures(state)
        self._restore_entities(state)
        self._restore_resources_and_inventory(state)
        self._finalize_restoration()

    def _execute_loading(self, *args, progress_callback=None):
        """Execute loading with progress tracking - not used directly"""
        pass

    def _initialize_procedural_system_step(self, progress_callback=None):
        """Initialize procedural tile system with progress tracking"""
        if progress_callback:
            progress_callback(0, "Scanning planetary surface", 0.3, "Detecting quantum substrate")
        
        print("[PlanetScene] Initializing procedural tile system for loaded world...")
        from subtile_manager import SubTileManager
        self.scene.subtile_manager = SubTileManager(self.scene)
        
        if progress_callback:
            progress_callback(0, "Scanning planetary surface", 0.7, "Calibrating tile dimensions")
        
        self.scene.tile_width, self.scene.tile_height = 64, 37
        
        if progress_callback:
            progress_callback(0, "Scanning planetary surface", 1.0, "Surface scan complete")

    def _restore_terrain_system_step(self, state, progress_callback=None):
        """Restore terrain system from save data with progress tracking"""
        if progress_callback:
            progress_callback(1, "Reconstructing terrain data", 0.2, "Analyzing terrain format")
        
        terrain_system = state.get("terrain_system", {})
        self.scene.use_layered_terrain = terrain_system.get("use_layered", False)
        
        if self.scene.use_layered_terrain and terrain_system.get("terrain_stacks"):
            if progress_callback:
                progress_callback(1, "Reconstructing terrain data", 0.5, "Rebuilding layered terrain")
            self._restore_layered_terrain(terrain_system["terrain_stacks"])
            
            if progress_callback:
                progress_callback(1, "Reconstructing terrain data", 0.8, "Creating terrain renderer")
            self.scene.map = ProceduralIsoMap(self.scene.terrain.surface_map, self.scene.subtile_manager, self.scene.terrain)
            self.scene.water_system = LayeredWaterSystem(self.scene.terrain)
            self.scene.resource_system = LayeredResourceSystem(self.scene.terrain)
        else:
            if progress_callback:
                progress_callback(1, "Reconstructing terrain data", 0.6, "Restoring legacy terrain")
            self._restore_legacy_terrain(state)
            self.scene.map = ProceduralIsoMap(self.scene.map_data, self.scene.subtile_manager, None)
        
        if progress_callback:
            progress_callback(1, "Reconstructing terrain data", 1.0, "Terrain reconstruction complete")

    def _restore_camera_and_settings_step(self, state, progress_callback=None):
        """Restore camera position and settings with progress tracking"""
        if progress_callback:
            progress_callback(3, "Synchronizing time streams", 0.5, "Restoring camera position")
        
        player_data = state.get("player_data", {})
        camera_data = player_data.get("camera", {})
        self.scene.map.camera_offset_x = camera_data.get("x", 1920//2)
        self.scene.map.camera_offset_y = camera_data.get("y", 1080//2)
        self.scene.zoom_scale = camera_data.get("zoom", 1.0)
        
        if progress_callback:
            progress_callback(3, "Synchronizing time streams", 1.0, "Time synchronization complete")

    def _restore_vegetation_and_structures_step(self, state, progress_callback=None):
        """Restore trees and houses from enhanced save data with progress tracking"""
        if progress_callback:
            progress_callback(4, "Restoring ecosystem state", 0.1, "Loading sprite generators")
        
        # Trees
        self.scene.tree_images = {1:generate_sprite("pine"),2:generate_sprite("oak"),
                            3:generate_sprite("palm"),4:generate_sprite("cactus")}
        
        if progress_callback:
            progress_callback(4, "Restoring ecosystem state", 0.3, "Regenerating forest maps")
        
        biomes = state.get("biomes", {})
        self.scene.forest_map = biomes.get("forest_map", [])
        
        if progress_callback:
            progress_callback(4, "Restoring ecosystem state", 0.5, "Replanting vegetation")
        
        tree_positions = biomes.get("tree_positions", state.get("tree_tiles", []))
        self.scene.trees = []
        for tree_data in tree_positions:
            if isinstance(tree_data, dict):
                tree_height = 0
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    tree_height = self.scene.terrain.get_height_at(tree_data["x"], tree_data["y"])
                    
                tree = IsoTree(
                    tree_data["x"], tree_data["y"], tree_data.get("type", 1),
                    tree_data.get("offset_x", 0.0), tree_data.get("offset_y", 0.0),
                    original_image=self.scene.tree_images[tree_data.get("type", 1)],
                    height=tree_height
                )
                tree.draw_order = (tree_data["x"] + tree_data["y"]) * 10 + 5
                self.scene.trees.append(tree)
            else:
                # Legacy format: just coordinates
                x, y = tree_data
                tree_height = 0
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    tree_height = self.scene.terrain.get_height_at(x, y)
                tree = IsoTree(x, y, 1, 0, 0, original_image=self.scene.tree_images[1], height=tree_height)
                tree.draw_order = (x + y) * 10 + 5
                self.scene.trees.append(tree)
        
        self.scene.tree_tiles = {(t.grid_x, t.grid_y) for t in self.scene.trees}

        if progress_callback:
            progress_callback(4, "Restoring ecosystem state", 0.7, "Rebuilding settlements")

        # Houses
        import os
        import pygame
        hp = os.path.join(self.scene.assets_dir,"house.png")
        self.scene.house_image = pygame.image.load(hp).convert_alpha() \
            if os.path.exists(hp) else self._placeholder_house()
        
        structures = state.get("structures", {})
        house_data = structures.get("houses", state.get("house_tiles", []))
        
        self.scene.houses = []
        for house_info in house_data:
            if isinstance(house_info, dict):
                house_height = 0
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    house_height = self.scene.terrain.get_height_at(house_info["x"], house_info["y"])
                house = IsoTree(
                    house_info["x"], house_info["y"], 99, 0.5, 0,
                    original_image=self.scene.house_image, height=house_height
                )
                house.draw_order = (house_info["x"] + house_info["y"]) * 10 + 6
                self.scene.houses.append(house)
            else:
                # Legacy format: just coordinates
                x, y = house_info
                house_height = 0
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    house_height = self.scene.terrain.get_height_at(x, y)
                house = IsoTree(x, y, 99, 0.5, 0, original_image=self.scene.house_image, height=house_height)
                house.draw_order = (x + y) * 10 + 6
                self.scene.houses.append(house)
        
        self.scene.house_built = bool(self.scene.houses)
        
        if progress_callback:
            progress_callback(4, "Restoring ecosystem state", 1.0, "Ecosystem restoration complete")

    def _restore_entities_step(self, state, progress_callback=None):
        """Restore animals and units from save data with progress tracking"""
        if progress_callback:
            progress_callback(2, "Reviving suspended organisms", 0.2, "Initializing entity managers")
        
        from unit_manager import UnitManager
        from animals import AnimalManager

        # Initialize managers
        self.scene.unit_manager = UnitManager(self.scene)
        self.scene.animal_manager = AnimalManager(self.scene)
        
        if progress_callback:
            progress_callback(2, "Reviving suspended organisms", 0.5, "Awakening bipeds")
        
        # Restore bipeds/units from saved data
        self._restore_bipeds(state)
        
        if progress_callback:
            progress_callback(2, "Reviving suspended organisms", 0.8, "Regenerating animal genetics")
        
        self._restore_animals(state)
        
        if progress_callback:
            progress_callback(2, "Reviving suspended organisms", 1.0, "All organisms revived")

    def _restore_resources_and_inventory_step(self, state, progress_callback=None):
        """Restore drops and inventory with progress tracking"""
        if progress_callback:
            progress_callback(5, "Activating simulation engine", 0.3, "Materializing resource drops")
        
        resources = state.get("resources", {})
        drop_data = resources.get("drops", state.get("drops", []))
        self.scene.drops = []
        
        for drop_dict in drop_data:
            try:
                drop = self._create_drop_from_dict(drop_dict)
                if drop:
                    self.scene.drops.append(drop)
                
            except Exception as e:
                print(f"[PlanetScene] Warning: Could not restore drop {drop_dict}: {e}")
                continue
        
        if progress_callback:
            progress_callback(5, "Activating simulation engine", 0.7, "Restoring inventory systems")
            
        self.scene.inventory = resources.get("inventory", state.get("inventory", {}))
        
        if progress_callback:
            progress_callback(5, "Activating simulation engine", 1.0, "Simulation engine activated")

    def _initialize_procedural_system(self):
        """Initialize procedural tile system for loaded world"""
        print("[PlanetScene] Initializing procedural tile system for loaded world...")
        from subtile_manager import SubTileManager
        self.scene.subtile_manager = SubTileManager(self.scene)
        self.scene.tile_width, self.scene.tile_height = 64, 37

    def _restore_terrain_system(self, state):
        """Restore terrain system from save data"""
        terrain_system = state.get("terrain_system", {})
        self.scene.use_layered_terrain = terrain_system.get("use_layered", False)
        
        if self.scene.use_layered_terrain and terrain_system.get("terrain_stacks"):
            self._restore_layered_terrain(terrain_system["terrain_stacks"])
            self.scene.map = ProceduralIsoMap(self.scene.terrain.surface_map, self.scene.subtile_manager, self.scene.terrain)
            self.scene.water_system = LayeredWaterSystem(self.scene.terrain)
            self.scene.resource_system = LayeredResourceSystem(self.scene.terrain)
        else:
            self._restore_legacy_terrain(state)
            self.scene.map = ProceduralIsoMap(self.scene.map_data, self.scene.subtile_manager, None)

    def _restore_camera_and_settings(self, state):
        """Restore camera position and settings"""
        player_data = state.get("player_data", {})
        camera_data = player_data.get("camera", {})
        self.scene.map.camera_offset_x = camera_data.get("x", 1920//2)
        self.scene.map.camera_offset_y = camera_data.get("y", 1080//2)
        self.scene.zoom_scale = camera_data.get("zoom", 1.0)

    def _restore_vegetation_and_structures(self, state):
        """Restore trees and houses from enhanced save data"""
        # Trees
        self.scene.tree_images = {1:generate_sprite("pine"),2:generate_sprite("oak"),
                            3:generate_sprite("palm"),4:generate_sprite("cactus")}
        
        biomes = state.get("biomes", {})
        self.scene.forest_map = biomes.get("forest_map", [])
        
        tree_positions = biomes.get("tree_positions", state.get("tree_tiles", []))
        self.scene.trees = []
        for tree_data in tree_positions:
            if isinstance(tree_data, dict):
                tree_height = 0
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    tree_height = self.scene.terrain.get_height_at(tree_data["x"], tree_data["y"])
                    
                tree = IsoTree(
                    tree_data["x"], tree_data["y"], tree_data.get("type", 1),
                    tree_data.get("offset_x", 0.0), tree_data.get("offset_y", 0.0),
                    original_image=self.scene.tree_images[tree_data.get("type", 1)],
                    height=tree_height
                )
                tree.draw_order = (tree_data["x"] + tree_data["y"]) * 10 + 5
                self.scene.trees.append(tree)
            else:
                # Legacy format: just coordinates
                x, y = tree_data
                tree_height = 0
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    tree_height = self.scene.terrain.get_height_at(x, y)
                tree = IsoTree(x, y, 1, 0, 0, original_image=self.scene.tree_images[1], height=tree_height)
                tree.draw_order = (x + y) * 10 + 5
                self.scene.trees.append(tree)
        
        self.scene.tree_tiles = {(t.grid_x, t.grid_y) for t in self.scene.trees}

        # Houses
        import os
        import pygame
        hp = os.path.join(self.scene.assets_dir,"house.png")
        self.scene.house_image = pygame.image.load(hp).convert_alpha() \
            if os.path.exists(hp) else self._placeholder_house()
        
        structures = state.get("structures", {})
        house_data = structures.get("houses", state.get("house_tiles", []))
        
        self.scene.houses = []
        for house_info in house_data:
            if isinstance(house_info, dict):
                house_height = 0
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    house_height = self.scene.terrain.get_height_at(house_info["x"], house_info["y"])
                house = IsoTree(
                    house_info["x"], house_info["y"], 99, 0.5, 0,
                    original_image=self.scene.house_image, height=house_height
                )
                house.draw_order = (house_info["x"] + house_info["y"]) * 10 + 6
                self.scene.houses.append(house)
            else:
                # Legacy format: just coordinates
                x, y = house_info
                house_height = 0
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    house_height = self.scene.terrain.get_height_at(x, y)
                house = IsoTree(x, y, 99, 0.5, 0, original_image=self.scene.house_image, height=house_height)
                house.draw_order = (x + y) * 10 + 6
                self.scene.houses.append(house)
        
        self.scene.house_built = bool(self.scene.houses)

    def _restore_entities(self, state):
        """Restore animals and units from save data"""
        from unit_manager import UnitManager, create_biped_frames, BipedUnit
        from animals import AnimalManager, AnimalUnit

        # Initialize managers
        self.scene.unit_manager = UnitManager(self.scene)
        self.scene.animal_manager = AnimalManager(self.scene)
        
        # Restore bipeds/units from saved data
        self._restore_bipeds(state)
        self._restore_animals(state)

    def _restore_bipeds(self, state):
        """Restore comprehensive biped data"""
        from unit_manager import create_biped_frames, BipedUnit
        
        player_data = state.get("player_data", {})
        unit_data = player_data.get("units", [])
        
        print(f"[PlanetScene] Restoring {len(unit_data)} bipeds from save data")
        
        for unit_info in unit_data:
            unit_color = unit_info.get("color", (0, 255, 255))
            unit_speed = unit_info.get("speed", 2.5)
            unit_id = unit_info.get("unit_id", f"restored_{time.time()}")
            
            biped = BipedUnit(
                self.scene, 
                unit_info["grid_x"], 
                unit_info["grid_y"],
                frames=create_biped_frames(unit_color, 4, 32, 48),
                speed=unit_speed,
            )
            
            # Restore ALL unit state precisely
            self._restore_biped_state(biped, unit_info, unit_id, unit_color)
            
            biped.set_zoom_scale(self.scene.zoom_scale)
            self.scene.unit_manager.add_unit(biped)
            
            # Force position calculation
            biped.calculate_screen_position(
                self.scene.map.camera_offset_x,
                self.scene.map.camera_offset_y,
                self.scene.zoom_scale
            )
            
            # Resume movement if necessary
            if biped.moving and biped.path_tiles and len(biped.path_tiles) > biped.path_index:
                print(f"[PlanetScene] Resuming movement for biped {unit_id}")
                self._resume_biped_movement(biped)
        
        print(f"[PlanetScene] Successfully restored {len(self.scene.unit_manager.units)} bipeds")

    def _restore_biped_state(self, biped, unit_info, unit_id, unit_color):
        """Restore all biped state from save data"""
        biped.unit_id = unit_id
        biped.color = unit_color
        
        # Position state
        biped.grid_x = unit_info["grid_x"]
        biped.grid_y = unit_info["grid_y"] 
        biped.x_f = unit_info.get("x_f", 0.0)
        biped.y_f = unit_info.get("y_f", 0.0)
        biped.screen_x = unit_info.get("screen_x", 0)
        biped.screen_y = unit_info.get("screen_y", 0)
        
        # Movement state
        biped.path_tiles = unit_info.get("path_tiles", [])
        biped.path_index = unit_info.get("path_index", 0)
        biped.destination_x = unit_info.get("destination_x")
        biped.destination_y = unit_info.get("destination_y")
        biped.moving = unit_info.get("moving", False)
        biped.move_progress = unit_info.get("move_progress", 0.0)
        biped.next_tile_x = unit_info.get("next_tile_x")
        biped.next_tile_y = unit_info.get("next_tile_y")
        
        # Mission state
        biped.mission = unit_info.get("mission", "IDLE")
        biped.mission_data = unit_info.get("mission_data", {})
        
        # Handle target_drop restoration
        target_drop_info = unit_info.get("target_drop")
        if target_drop_info:
            for drop in self.scene.drops:
                if (getattr(drop, 'id', None) == target_drop_info.get("drop_id") or
                    (drop.grid_x == target_drop_info["drop_x"] and 
                     drop.grid_y == target_drop_info["drop_y"])):
                    biped.target_drop = drop
                    break
        
        # Unit properties
        biped.health = unit_info.get("health", 100)
        biped.max_health = unit_info.get("max_health", 100)
        biped.inventory = unit_info.get("inventory", {})
        biped.selected = unit_info.get("selected", False)
        
        # Timestamps
        biped.creation_time = unit_info.get("creation_time", time.time())
        biped.last_command_time = unit_info.get("last_command_time", time.time())
        
        # Animation state
        biped.current_frame = unit_info.get("current_frame", 0)
        biped.animation_time = unit_info.get("animation_time", 0.0)
        biped.facing_direction = unit_info.get("facing_direction", "down")

    def _restore_animals(self, state):
        """Restore animals with full state"""
        entities = state.get("entities", {})
        animal_data = entities.get("animals", [])
        species_data = entities.get("species_data", {})
        
        # Restore species founders first
        for species_id_str, founder_data in species_data.items():
            species_id = int(species_id_str)
            sprite_data = founder_data.get("sprite_frames", {})
            frames = create_pixel_animal_frames(**sprite_data)
            
            from animals import AnimalUnit
            founder = AnimalUnit(self.scene, 0, 0, frames, species_id, None, True)
            self.scene.animal_manager.species_founders[species_id] = founder
        
        # Restore actual animals
        for animal_info in animal_data:
            sprite_data = animal_info.get("sprite_data", {})
            frames = create_pixel_animal_frames(**sprite_data)
            
            from animals import AnimalUnit
            animal = AnimalUnit(
                scene=self.scene,
                tile_x=animal_info["x"],
                tile_y=animal_info["y"],
                frames=frames,
                species_id=animal_info["species_id"],
                founder_unit=self.scene.animal_manager.species_founders.get(animal_info["species_id"]),
                can_reproduce=True
            )
            
            # Restore animal state
            animal.x_f = animal_info.get("x_f", 0.0)
            animal.y_f = animal_info.get("y_f", 0.0)
            animal.health = animal_info.get("health", 100)
            animal.growth_scale = animal_info.get("growth_scale", 1.0)
            animal.diet = animal_info.get("diet", "herbivore")
            animal.aggression = animal_info.get("aggression", 0.0)
            animal.territory_radius = animal_info.get("territory_radius", 3)
            
            self.scene.animal_manager.add_animal(animal)
        
        # Update next species ID
        if species_data:
            self.scene.animal_manager.next_species_id = max(int(sid) for sid in species_data.keys()) + 1

    def _restore_resources_and_inventory(self, state):
        """Restore drops and inventory"""
        resources = state.get("resources", {})
        drop_data = resources.get("drops", state.get("drops", []))
        self.scene.drops = []
        
        for drop_dict in drop_data:
            try:
                drop = self._create_drop_from_dict(drop_dict)
                if drop:
                    self.scene.drops.append(drop)
                
            except Exception as e:
                print(f"[PlanetScene] Warning: Could not restore drop {drop_dict}: {e}")
                continue
            
        self.scene.inventory = resources.get("inventory", state.get("inventory", {}))

    def _finalize_restoration(self):
        """Finalize scene restoration"""
        self.scene.iso_objects = self.scene.map.get_all_objects() + self.scene.trees + self.scene.houses
        
        # Enhanced blocked tiles calculation
        if self.scene.use_layered_terrain:
            self.scene.blocked_tiles = self._calculate_blocked_tiles_layered()
        else:
            self.scene.blocked_tiles = {
                (c,r) for r,row in enumerate(self.scene.map_data)
                for c,t in enumerate(row)
                if t in (2, 5, 4)  # TILE_WATER, TILE_WATERSTACK, TILE_MOUNTAIN
            } | self.scene.tree_tiles
            
        self.scene.dragging = False
        self.scene.last_mouse_pos = (0, 0)
        self.scene.wave_time = 0.0
        self.scene.wave_speed = 5.0
        self.scene.wave_spacing = 3.0
        self.scene._propagate_zoom()

    def _restore_layered_terrain(self, terrain_stacks_data):
        """Restore layered terrain from save data"""
        from map_generation import LayeredTerrain, TerrainTile
        
        planet_w, planet_h = self.scene.meta.tiles
        self.scene.terrain = LayeredTerrain(planet_w, planet_h)
        
        for pos_key, stack_data in terrain_stacks_data.items():
            x, y = map(int, pos_key.split(','))
            
            for tile_data in stack_data:
                tile = TerrainTile(
                    tile_type=tile_data["tile_type"],
                    height=tile_data["height"],
                    x=x,
                    y=y,
                    sub_tiles=tile_data.get("sub_tiles", {}),
                    damaged=tile_data.get("damaged", 0.0)
                )
                
                if (x, y) not in self.scene.terrain.terrain_stacks:
                    self.scene.terrain.terrain_stacks[(x, y)] = []
                self.scene.terrain.terrain_stacks[(x, y)].append(tile)
        
        # Update compatibility maps
        for y in range(planet_h):
            for x in range(planet_w):
                self.scene.terrain.surface_map[y][x] = self.scene.terrain.get_surface_tile(x, y)
                self.scene.terrain.height_map[y][x] = self.scene.terrain.get_height_at(x, y)
        
        self.scene.map_data = self.scene.terrain.surface_map

    def _restore_legacy_terrain(self, state):
        """Restore legacy flat terrain from save data"""
        world_data = state.get("world_data", {})
        self.scene.map_data = world_data.get("terrain", state.get("map_data", []))
        self.scene.use_layered_terrain = False

    def _load_legacy_state(self, state: dict):
        """Load from old save format for backward compatibility"""
        planet_w, planet_h = self.scene.meta.tiles
        print(f"[PlanetScene] Loading legacy save format - PROCEDURAL MODE")

        self._initialize_procedural_system()
        
        # Legacy terrain and camera setup
        self.scene.map_data = state["map_data"]
        self.scene.map = ProceduralIsoMap(self.scene.map_data, self.scene.subtile_manager, None)
        
        # Legacy entities restoration
        self._restore_legacy_entities(state)
        
        # Legacy finalization
        self._finalize_restoration()

    def _restore_legacy_entities(self, state):
        """Restore entities from legacy save format"""
        from unit_manager import UnitManager
        from animals import AnimalManager
        
        # Trees and houses
        self.scene.tree_images = {1:generate_sprite("pine"),2:generate_sprite("oak"),
                            3:generate_sprite("palm"),4:generate_sprite("cactus")}
        self.scene.trees = []
        for x, y in state["tree_tiles"]:
            tree = IsoTree(x, y, 1, 0, 0, original_image=self.scene.tree_images[1])
            tree.draw_order = (x + y) * 10 + 5
            self.scene.trees.append(tree)
        self.scene.tree_tiles = set(state["tree_tiles"])

        import os
        import pygame
        hp = os.path.join(self.scene.assets_dir,"house.png")
        self.scene.house_image = pygame.image.load(hp).convert_alpha() \
            if os.path.exists(hp) else self._placeholder_house()
        self.scene.houses = []
        for x, y in state["house_tiles"]:
            house = IsoTree(x, y, 99, 0.5, 0, original_image=self.scene.house_image)
            house.draw_order = (x + y) * 10 + 6
            self.scene.houses.append(house)
        self.scene.house_built = bool(self.scene.houses)

        # Managers and drops
        self.scene.unit_manager = UnitManager(self.scene)
        self.scene.animal_manager = AnimalManager(self.scene)
        
        # Legacy drops
        legacy_drops = state.get("drops", [])
        self.scene.drops = []
        for drop_dict in legacy_drops:
            try:
                drop = self._create_drop_from_dict(drop_dict)
                if drop:
                    drop.id = f"legacy_drop_{drop.grid_x}_{drop.grid_y}_{hash(drop)}"
                    self.scene.drops.append(drop)
            except Exception as e:
                print(f"[PlanetScene] Warning: Could not restore legacy drop: {e}")
                continue
                
        self.scene.inventory = state.get("inventory", {})

    def save_before_exit(self):
        """Save current state before switching scenes"""
        if self.scene.planet_storage and hasattr(self.scene, 'meta'):
            self.scene.meta.state = self.serialize_state()
            if hasattr(self.scene, 'planet_id'):
                self.scene.planet_storage.save_planet(self.scene.planet_id, self.scene.meta)
                print(f"[PlanetScene] Saved planet state for {self.scene.planet_id}")
            else:
                planet_id = f"Planet_Seed_{self.scene.meta.seed}"
                self.scene.planet_storage.save_planet(planet_id, self.scene.meta)
                print(f"[PlanetScene] Saved planet state for seed {self.scene.meta.seed}")

    def _create_drop_from_dict(self, drop_dict):
        """Create a drop object from dictionary data"""
        try:
            # Try the standard method first
            if hasattr(DropObject, 'from_dict'):
                drop = DropObject.from_dict(drop_dict, self.scene)
            else:
                # Fallback manual creation
                drop = DropObject(
                    scene=self.scene,
                    grid_x=drop_dict.get("grid_x", 0),
                    grid_y=drop_dict.get("grid_y", 0),
                    resource_type=drop_dict.get("resource_type", "unknown"),
                    quantity=drop_dict.get("quantity", 1)
                )
            
            # Set additional properties
            drop.alive = drop_dict.get("alive", True)
            drop.hovered = drop_dict.get("hovered", False)
            
            # Set ID
            if "drop_id" in drop_dict:
                drop.id = drop_dict["drop_id"]
            else:
                drop.id = f"drop_{drop.grid_x}_{drop.grid_y}_{hash(drop)}"
            
            return drop
            
        except Exception as e:
            print(f"[PlanetStateManager] Error creating drop from dict: {e}")
            return None

    def _serialize_drop(self, drop) -> dict:
        """Serialize a drop object safely"""
        try:
            # Try the standard method first
            if hasattr(drop, 'as_dict'):
                return drop.as_dict()
            else:
                # Fallback manual serialization
                return {
                    "grid_x": getattr(drop, 'grid_x', 0),
                    "grid_y": getattr(drop, 'grid_y', 0),
                    "resource_type": getattr(drop, 'resource_type', 'unknown'),
                    "quantity": getattr(drop, 'quantity', 1),
                    "alive": getattr(drop, 'alive', True),
                    "hovered": getattr(drop, 'hovered', False),
                    "drop_id": getattr(drop, 'id', f"drop_{getattr(drop, 'grid_x', 0)}_{getattr(drop, 'grid_y', 0)}_{hash(drop)}")
                }
        except Exception as e:
            print(f"[PlanetStateManager] Error serializing drop: {e}")
            # Return a minimal valid drop
            return {
                "grid_x": 0,
                "grid_y": 0,
                "resource_type": "unknown",
                "quantity": 1,
                "alive": True,
                "hovered": False,
                "drop_id": f"error_drop_{hash(drop)}"
            }

    def _serialize_animal_sprite(self, animal) -> dict:
        """Save animal appearance data for restoration"""
        try:
            return {
                "body_color": getattr(animal, 'body_color', (200, 100, 100)),
                "body_width": getattr(animal, 'body_width', 14),
                "body_height": getattr(animal, 'body_height', 8),
                "has_wings": getattr(animal, 'has_wings', False),
                "spike_count": getattr(animal, 'spike_count', 0),
                "head_count": getattr(animal, 'head_count', 1),
                "has_horns": getattr(animal, 'has_horns', False),
                "has_snout": getattr(animal, 'has_snout', False)
            }
        except Exception as e:
            print(f"[PlanetScene] Error serializing animal sprite: {e}")
            return {
                "body_color": (200, 100, 100),
                "body_width": 14,
                "body_height": 8,
                "has_wings": False,
                "spike_count": 0,
                "head_count": 1,
                "has_horns": False,
                "has_snout": False
            }

    def _get_units_by_mission(self) -> dict:
        """Get count of units by mission type for monitoring"""
        try:
            mission_counts = {}
            for unit in self.scene.unit_manager.units:
                mission = str(getattr(unit, 'mission', 'IDLE'))
                mission_counts[mission] = mission_counts.get(mission, 0) + 1
            return mission_counts
        except Exception as e:
            print(f"[PlanetScene] Error counting units by mission: {e}")
            return {"ERROR": 1}

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
                if surface_tile in (2, 5) or height > 6:  # TILE_WATER, TILE_WATERSTACK
                    blocked.add((x, y))
        return blocked

    def _resume_biped_movement(self, biped):
        """Resume movement for a biped that was moving when saved"""
        try:
            if not biped.path_tiles or biped.path_index >= len(biped.path_tiles):
                print(f"[PlanetScene] Cannot resume movement for {biped.unit_id}: invalid path")
                biped.moving = False
                biped.mission = "IDLE"
                return False
                
            dest_x, dest_y = biped.destination_x, biped.destination_y
            if dest_x is None or dest_y is None:
                print(f"[PlanetScene] Cannot resume movement for {biped.unit_id}: no destination")
                biped.moving = False
                biped.mission = "IDLE" 
                return False
                
            if (dest_x, dest_y) in self.scene.blocked_tiles:
                print(f"[PlanetScene] Destination blocked, recalculating path for {biped.unit_id}")
                new_path = self.scene.find_path(biped.grid_x, biped.grid_y, dest_x, dest_y)
                if new_path:
                    biped.path_tiles = new_path
                    biped.path_index = 0
                    biped.moving = True
                else:
                    biped.moving = False
                    biped.mission = "IDLE"
                    return False
            
            biped.moving = True
            if biped.mission in ["IDLE", ""]:
                biped.mission = "MOVE_TO"
                
            print(f"[PlanetScene] Successfully resumed movement for {biped.unit_id}")
            return True
            
        except Exception as e:
            print(f"[PlanetScene] Error resuming movement for {biped.unit_id}: {e}")
            biped.moving = False
            biped.mission = "IDLE"
            return False

    def _placeholder_house(self):
        """Create placeholder house sprite"""
        import pygame
        img = pygame.Surface((96,96), pygame.SRCALPHA)
        pygame.draw.rect(img,(150,75,0),(0,24,96,72))
        pygame.draw.polygon(img,(200,0,0),[(0,24),(48,0),(96,24)])
        return img