##########################################################
# arcade_state_manager.py
# Handles save/load state, serialization, and persistence for Arcade
##########################################################

import time
import arcade

class ArcadeStateManager:
    """Handles all state serialization, loading, and persistence for Arcade"""
    
    def __init__(self, scene):
        self.scene = scene

    def serialize_state(self) -> dict:
        """Turn the live world into a comprehensive save-dict"""
        return {
            # Core world data
            "world_data": {
                "terrain": self.scene.map_data if hasattr(self.scene, 'map_data') else [],
                "seed": self.scene.meta.seed,
                "size": self.scene.meta.tiles,
                "generation_version": 1
            },
            
            # Terrain system
            "terrain_system": {
                "use_layered": getattr(self.scene, 'use_layered_terrain', False),
                "terrain_width": self.scene.terrain_width,
                "terrain_height": self.scene.terrain_height,
                "terrain_data": self.scene.terrain_data
            },
            
            # Entities
            "entities": {
                "bipeds": [
                    {
                        "center_x": biped.center_x,
                        "center_y": biped.center_y,
                        "grid_x": getattr(biped, 'grid_x', 0),
                        "grid_y": getattr(biped, 'grid_y', 0),
                        "name": getattr(biped, 'name', 'Unknown'),
                        "color": getattr(biped, 'color', (0, 255, 0)),
                        "unit_id": getattr(biped, 'unit_id', f"biped_{hash(biped)}"),
                        "mission": getattr(biped, 'mission', 'IDLE'),
                        "moving": getattr(biped, 'moving', False),
                        "target_x": getattr(biped, 'target_x', None),
                        "target_y": getattr(biped, 'target_y', None),
                        "health": getattr(biped, 'health', 100),
                        "creation_time": getattr(biped, 'creation_time', time.time()),
                        "last_command_time": getattr(biped, 'last_command_time', time.time()),
                        "selected": getattr(biped, 'selected', False)
                    }
                    for biped in self.scene.biped_sprites
                ],
                "animals": [
                    {
                        "center_x": animal.center_x,
                        "center_y": animal.center_y,
                        "grid_x": getattr(animal, 'grid_x', 0),
                        "grid_y": getattr(animal, 'grid_y', 0),
                        "color": getattr(animal, 'color', (255, 165, 0)),
                        "species_id": getattr(animal, 'species_id', 0)
                    }
                    for animal in self.scene.animal_sprites
                ],
                "trees": [
                    {
                        "center_x": tree.center_x,
                        "center_y": tree.center_y,
                        "grid_x": getattr(tree, 'grid_x', 0),
                        "grid_y": getattr(tree, 'grid_y', 0)
                    }
                    for tree in self.scene.tree_sprites
                ],
                "houses": [
                    {
                        "center_x": house.center_x,
                        "center_y": house.center_y,
                        "grid_x": getattr(house, 'grid_x', 0),
                        "grid_y": getattr(house, 'grid_y', 0)
                    }
                    for house in self.scene.house_sprites
                ]
            },
            
            # Resources and inventory
            "resources": {
                "drops": [
                    {
                        "center_x": drop.center_x,
                        "center_y": drop.center_y,
                        "resource_type": getattr(drop, 'resource_type', 'unknown'),
                        "quantity": getattr(drop, 'quantity', 1)
                    }
                    for drop in self.scene.drop_sprites
                ],
                "inventory": self.scene.inventory
            },
            
            # Player progress and camera
            "player_data": {
                "camera_position": self.scene.camera.position if self.scene.camera else (0, 0),
                "zoom_scale": self.scene.zoom_scale,
                "house_built": getattr(self.scene, 'house_built', False),
                "simulation_mode": getattr(self.scene, 'simulation_mode', 'realtime'),
                "mining_mode": getattr(self.scene, 'mining_mode', False)
            },
            
            # Game state
            "game_state": {
                "blocked_tiles": list(self.scene.blocked_tiles),
                "tree_tiles": list(self.scene.tree_tiles),
                "wave_time": getattr(self.scene, 'wave_time', 0.0),
                "wave_speed": getattr(self.scene, 'wave_speed', 5.0)
            },
            
            # Save metadata
            "save_info": {
                "format_version": 1,
                "timestamp": time.time(),
                "engine": "arcade",
                "engine_version": arcade.VERSION
            }
        }

    def load_state(self, state: dict):
        """Rebuild from comprehensive saved dict"""
        print(f"[ArcadeStateManager] Loading planet state...")

        try:
            # Load world data
            self._load_world_data(state)
            
            # Load camera and settings
            self._load_camera_and_settings(state)
            
            # Load entities
            self._load_entities(state)
            
            # Load resources
            self._load_resources(state)
            
            # Load game state
            self._load_game_state(state)
            
            print(f"[ArcadeStateManager] Successfully loaded planet state")
            
        except Exception as e:
            print(f"[ArcadeStateManager] Error loading state: {e}")
            # Fall back to generating new world
            self.scene._generate_new_world()

    def _load_world_data(self, state):
        """Load world terrain data"""
        world_data = state.get("world_data", {})
        terrain_system = state.get("terrain_system", {})
        
        # Load basic terrain data
        self.scene.map_data = world_data.get("terrain", [])
        
        # Load terrain system data
        self.scene.use_layered_terrain = terrain_system.get("use_layered", False)
        self.scene.terrain_width = terrain_system.get("terrain_width", self.scene.meta.tiles[0])
        self.scene.terrain_height = terrain_system.get("terrain_height", self.scene.meta.tiles[1])
        self.scene.terrain_data = terrain_system.get("terrain_data", [])
        
        # Recreate terrain sprites
        if self.scene.map_data:
            self._recreate_terrain_sprites()

    def _recreate_terrain_sprites(self):
        """Recreate terrain sprites from map data"""
        self.scene.terrain_sprites.clear()
        
        for y in range(len(self.scene.map_data)):
            for x in range(len(self.scene.map_data[0])):
                tile_type = self.scene.map_data[y][x]
                
                if tile_type == -1:  # Skip void tiles
                    continue
                
                # Calculate isometric position
                iso_x = (x - y) * (64 // 2)  # TILE_WIDTH
                iso_y = (x + y) * (37 // 2)  # TILE_HEIGHT
                
                # Create terrain sprite
                from arcade_planet_scene import ArcadeTerrainSprite
                terrain_sprite = ArcadeTerrainSprite(tile_type, iso_x, iso_y, 1)
                self.scene.terrain_sprites.append(terrain_sprite)

    def _load_camera_and_settings(self, state):
        """Load camera position and settings"""
        player_data = state.get("player_data", {})
        
        # Load camera position
        camera_pos = player_data.get("camera_position", (0, 0))
        if self.scene.camera:
            self.scene.camera.move_to(camera_pos)
        
        # Load zoom
        self.scene.zoom_scale = player_data.get("zoom_scale", 1.0)
        
        # Load other settings
        self.scene.house_built = player_data.get("house_built", False)
        self.scene.simulation_mode = player_data.get("simulation_mode", "realtime")
        self.scene.mining_mode = player_data.get("mining_mode", False)

    def _load_entities(self, state):
        """Load all entities from save data"""
        entities = state.get("entities", {})
        
        # Load bipeds
        self._load_bipeds(entities.get("bipeds", []))
        
        # Load animals
        self._load_animals(entities.get("animals", []))
        
        # Load trees
        self._load_trees(entities.get("trees", []))
        
        # Load houses
        self._load_houses(entities.get("houses", []))

    def _load_bipeds(self, biped_data):
        """Load biped sprites from save data"""
        self.scene.biped_sprites.clear()
        
        for biped_info in biped_data:
            from arcade_planet_scene import ArcadeBipedSprite
            
            biped = ArcadeBipedSprite(
                biped_info["center_x"],
                biped_info["center_y"],
                biped_info.get("name", "Unknown"),
                biped_info.get("color", (0, 255, 0))
            )
            
            # Restore biped properties
            biped.grid_x = biped_info.get("grid_x", 0)
            biped.grid_y = biped_info.get("grid_y", 0)
            biped.unit_id = biped_info.get("unit_id", f"biped_{hash(biped)}")
            biped.mission = biped_info.get("mission", "IDLE")
            biped.moving = biped_info.get("moving", False)
            biped.target_x = biped_info.get("target_x")
            biped.target_y = biped_info.get("target_y")
            biped.health = biped_info.get("health", 100)
            biped.creation_time = biped_info.get("creation_time", time.time())
            biped.last_command_time = biped_info.get("last_command_time", time.time())
            biped.selected = biped_info.get("selected", False)
            
            self.scene.biped_sprites.append(biped)
        
        print(f"[ArcadeStateManager] Loaded {len(self.scene.biped_sprites)} bipeds")

    def _load_animals(self, animal_data):
        """Load animal sprites from save data"""
        self.scene.animal_sprites.clear()
        
        for animal_info in animal_data:
            from arcade_planet_scene import ArcadeAnimalSprite
            
            animal = ArcadeAnimalSprite(
                animal_info["center_x"],
                animal_info["center_y"],
                animal_info.get("color", (255, 165, 0))
            )
            
            # Restore animal properties
            animal.grid_x = animal_info.get("grid_x", 0)
            animal.grid_y = animal_info.get("grid_y", 0)
            animal.species_id = animal_info.get("species_id", 0)
            
            self.scene.animal_sprites.append(animal)
        
        print(f"[ArcadeStateManager] Loaded {len(self.scene.animal_sprites)} animals")

    def _load_trees(self, tree_data):
        """Load tree sprites from save data"""
        self.scene.tree_sprites.clear()
        self.scene.tree_tiles.clear()
        
        for tree_info in tree_data:
            from arcade_world_generator import ArcadeTreeSprite
            
            tree = ArcadeTreeSprite(
                tree_info["center_x"],
                tree_info["center_y"]
            )
            
            # Restore tree properties
            tree.grid_x = tree_info.get("grid_x", 0)
            tree.grid_y = tree_info.get("grid_y", 0)
            
            self.scene.tree_sprites.append(tree)
            self.scene.tree_tiles.add((tree.grid_x, tree.grid_y))
        
        print(f"[ArcadeStateManager] Loaded {len(self.scene.tree_sprites)} trees")

    def _load_houses(self, house_data):
        """Load house sprites from save data"""
        self.scene.house_sprites.clear()
        
        for house_info in house_data:
            from arcade_planet_scene import ArcadeHouseSprite
            
            house = ArcadeHouseSprite(
                house_info["center_x"],
                house_info["center_y"]
            )
            
            # Restore house properties
            house.grid_x = house_info.get("grid_x", 0)
            house.grid_y = house_info.get("grid_y", 0)
            
            self.scene.house_sprites.append(house)
        
        print(f"[ArcadeStateManager] Loaded {len(self.scene.house_sprites)} houses")

    def _load_resources(self, state):
        """Load resources and inventory"""
        resources = state.get("resources", {})
        
        # Load inventory
        self.scene.inventory = resources.get("inventory", {})
        
        # Load drops
        self.scene.drop_sprites.clear()
        self.scene.drops = []
        
        drop_data = resources.get("drops", [])
        for drop_info in drop_data:
            # Create a simple drop sprite
            drop = arcade.Sprite()
            drop.center_x = drop_info["center_x"]
            drop.center_y = drop_info["center_y"]
            drop.resource_type = drop_info.get("resource_type", "unknown")
            drop.quantity = drop_info.get("quantity", 1)
            drop.texture = arcade.Texture.create_filled("drop", (16, 16), arcade.color.GOLD)
            
            self.scene.drop_sprites.append(drop)
            self.scene.drops.append(drop)
        
        print(f"[ArcadeStateManager] Loaded {len(self.scene.drops)} drops")

    def _load_game_state(self, state):
        """Load general game state"""
        game_state = state.get("game_state", {})
        
        # Load blocked tiles
        blocked_tiles_list = game_state.get("blocked_tiles", [])
        self.scene.blocked_tiles = set(tuple(pos) for pos in blocked_tiles_list)
        
        # Load tree tiles
        tree_tiles_list = game_state.get("tree_tiles", [])
        self.scene.tree_tiles = set(tuple(pos) for pos in tree_tiles_list)
        
        # Load wave animation state
        self.scene.wave_time = game_state.get("wave_time", 0.0)
        self.scene.wave_speed = game_state.get("wave_speed", 5.0)

    def save_before_exit(self):
        """Save current state before switching scenes"""
        if self.scene.planet_storage and hasattr(self.scene, 'meta'):
            self.scene.meta.state = self.serialize_state()
            
            # Generate planet ID if not exists
            if not hasattr(self.scene, 'planet_id'):
                self.scene.planet_id = f"Planet_Seed_{self.scene.meta.seed}"
            
            self.scene.planet_storage.save_planet(self.scene.planet_id, self.scene.meta)
            print(f"[ArcadeStateManager] Saved planet state for {self.scene.planet_id}")

    def auto_save(self, reason="unknown"):
        """Trigger auto-save"""
        try:
            # Throttle auto-saves
            if hasattr(self.scene, '_last_auto_save'):
                time_since_save = time.time() - self.scene._last_auto_save
                if time_since_save < 5.0:  # Don't save more than once every 5 seconds
                    return
            
            self.scene._last_auto_save = time.time()
            
            if self.scene.planet_storage and hasattr(self.scene, 'meta'):
                self.scene.meta.state = self.serialize_state()
                
                if hasattr(self.scene, 'planet_id'):
                    self.scene.planet_storage.save_planet(self.scene.planet_id, self.scene.meta)
                    print(f"[ArcadeStateManager] Auto-saved: {reason}")
                else:
                    print(f"[ArcadeStateManager] Auto-save triggered ({reason}) but no planet_id set")
        except Exception as e:
            print(f"[ArcadeStateManager] Auto-save failed ({reason}): {e}")

    def get_save_info(self):
        """Get information about the current save state"""
        return {
            "has_save_data": hasattr(self.scene, 'meta') and self.scene.meta.state is not None,
            "planet_id": getattr(self.scene, 'planet_id', None),
            "last_save_time": getattr(self.scene, '_last_auto_save', None),
            "engine": "arcade",
            "format_version": 1
        }

    def export_state_to_file(self, filename):
        """Export state to a file"""
        import json
        
        try:
            state = self.serialize_state()
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"[ArcadeStateManager] Exported state to {filename}")
            return True
        except Exception as e:
            print(f"[ArcadeStateManager] Failed to export state: {e}")
            return False

    def import_state_from_file(self, filename):
        """Import state from a file"""
        import json
        
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            self.load_state(state)
            print(f"[ArcadeStateManager] Imported state from {filename}")
            return True
        except Exception as e:
            print(f"[ArcadeStateManager] Failed to import state: {e}")
            return False

    def validate_save_data(self, state):
        """Validate save data integrity"""
        required_keys = ["world_data", "entities", "save_info"]
        
        for key in required_keys:
            if key not in state:
                return False, f"Missing required key: {key}"
        
        # Check format version
        save_info = state.get("save_info", {})
        format_version = save_info.get("format_version", 0)
        
        if format_version > 1:
            return False, f"Unsupported format version: {format_version}"
        
        return True, "Valid save data"

    def create_backup(self):
        """Create a backup of the current state"""
        import json
        import datetime
        
        try:
            state = self.serialize_state()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"planet_backup_{self.scene.meta.seed}_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"[ArcadeStateManager] Created backup: {filename}")
            return filename
        except Exception as e:
            print(f"[ArcadeStateManager] Failed to create backup: {e}")
            return None