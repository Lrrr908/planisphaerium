##########################################################
# planet_entity_manager.py
# Handles entity spawning, management, simulation, and time-away simulation
##########################################################

import random
import time
import math
import pygame
from unit_manager import create_biped_frames, BipedUnit
from animals import create_pixel_animal_frames, AnimalUnit

# Constants
TILE_WATER = 2
TILE_WATERSTACK = 5
TILE_DESERT = 11

def _rand_colour() -> tuple[int, int, int]:
    """Bright random colour helper."""
    return random.randint(64, 255), random.randint(64, 255), random.randint(64, 255)

class PlanetEntityManager:
    """Handles all entity spawning, management, and simulation"""
    
    def __init__(self, scene):
        self.scene = scene

    def spawn_initial_bipeds(self, valid_tiles):
        """Spawn bipeds using biome-aware placement like animals"""
        print(f"[_spawn_initial_bipeds] Spawning bipeds across diverse biomes")
        
        # Find diverse biome positions for bipeds
        planet_w, planet_h = self.scene.meta.tiles
        biped_positions = []
        
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            # For layered terrain, find positions across different biomes
            for attempt in range(50):
                x = random.randint(1, planet_w - 2)
                y = random.randint(1, planet_h - 2)
                
                if (x, y) in self.scene.terrain.terrain_stacks:
                    surface_tile = self.scene.terrain.get_surface_tile(x, y)
                    height = self.scene.terrain.get_height_at(x, y)
                    
                    # Accept grass, desert, or dirt at reasonable heights
                    if (surface_tile in [1, 11, 3] and height <= 4 and
                        (x, y) not in self.scene.blocked_tiles):
                        biped_positions.append((x, y))
                        
                if len(biped_positions) >= 8:
                    break
        else:
            # For flat terrain
            for y in range(planet_h):
                for x in range(planet_w):
                    if (self.scene.map_data[y][x] in [1, 11, 3] and
                        (x, y) not in self.scene.blocked_tiles):
                        biped_positions.append((x, y))
        
        if not biped_positions:
            print("[_spawn_initial_bipeds] No valid positions found, using fallback")
            biped_positions = valid_tiles[:8] if valid_tiles else []
        
        # Spawn bipeds at diverse positions
        colors = [(0, 255, 255), (102, 255, 102)]  # Cyan and green
        spawned_count = 0
        
        for idx, colour in enumerate(colors):
            if not biped_positions:
                break
                
            # Pick a random position from our diverse set
            bx, by = random.choice(biped_positions)
            biped_positions.remove((bx, by))  # Don't reuse the same spot
            
            current_time = time.time()
            biped = BipedUnit(
                self.scene, bx, by,
                frames=create_biped_frames(colour, 4, 32, 48),
                speed=2.5,
            )
            
            # Enhanced biped tracking data
            biped.unit_id = f"initial_biped_{idx}_{self.scene.meta.seed}_{int(current_time)}"
            biped.color = colour
            biped.creation_time = current_time
            biped.last_command_time = current_time
            biped.health = 100
            biped.max_health = 100
            biped.inventory = {}
            biped.mission = "IDLE"
            biped.mission_data = {}
            biped.path_tiles = []
            biped.path_index = 0
            biped.destination_x = None
            biped.destination_y = None
            biped.moving = False
            biped.move_progress = 0.0
            biped.selected = False
            biped.facing_direction = "down"
            
            biped.set_zoom_scale(self.scene.zoom_scale)
            self.scene.unit_manager.add_unit(biped)
            spawned_count += 1
            
            print(f"[_spawn_initial_bipeds] Biped {idx} spawned at ({bx}, {by}) in biome")
        
        print(f"[_spawn_initial_bipeds] Successfully spawned {spawned_count} bipeds across biomes")

    def spawn_animals(self, candidate_tiles):
        """Use the proper animal spawning system that spreads animals across biomes"""
        print(f"[_spawn_animals] Using biome-based animal spawning system")
        
        try:
            if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                # For layered terrain, find valid positions within planet boundary
                valid_positions = []
                for y in range(self.scene.terrain.height):
                    for x in range(self.scene.terrain.width):
                        if (x, y) in self.scene.terrain.terrain_stacks:
                            surface_tile = self.scene.terrain.get_surface_tile(x, y)
                            if surface_tile not in (TILE_WATER, TILE_WATERSTACK, -1):
                                # Check if it's forest land for animal spawning
                                if (hasattr(self.scene, 'forest_map') and 
                                    y < len(self.scene.forest_map) and 
                                    x < len(self.scene.forest_map[0]) and 
                                    self.scene.forest_map[y][x]):
                                    valid_positions.append((x, y))
                
                print(f"[_spawn_animals] Found {len(valid_positions)} valid forest positions")
                
                if valid_positions:
                    self.scene.animal_manager.spawn_random_animals(
                        override_count=min(8, len(valid_positions) // 20),
                        override_positions=valid_positions
                    )
                else:
                    print("[_spawn_animals] No forest positions found, using fallback")
                    self._spawn_animals_fallback(candidate_tiles)
            else:
                # For flat terrain, use the standard animal manager spawning
                self.scene.animal_manager.spawn_random_animals()
                
        except Exception as e:
            print(f"[_spawn_animals] Error with biome spawning: {e}, using fallback")
            self._spawn_animals_fallback(candidate_tiles)

    def _spawn_animals_fallback(self, candidate_tiles):
        """Fallback animal spawning if biome system fails"""
        print(f"[_spawn_animals_fallback] Using fallback spawning system")
        
        planet_w, planet_h = self.scene.meta.tiles
        spawn_positions = []
        
        # Sample positions for faster loading
        for _ in range(30):
            x = random.randint(planet_w//4, 3*planet_w//4)
            y = random.randint(planet_h//4, 3*planet_h//4)
            
            valid = False
            if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                if (x, y) in self.scene.terrain.terrain_stacks:
                    surface_tile = self.scene.terrain.get_surface_tile(x, y)
                    if surface_tile not in (TILE_WATER, TILE_WATERSTACK, -1):
                        valid = True
            else:
                if self.scene.map_data[y][x] not in (TILE_WATER, TILE_WATERSTACK, -1):
                    valid = True
                    
            if valid:
                spawn_positions.append((x, y))
        
        # Spawn animals at diverse positions
        sample = random.sample(spawn_positions, min(len(spawn_positions), 6))
        print(f"[_spawn_animals_fallback] Spawning animals at {len(sample)} diverse locations")

        for gx, gy in sample:
            try:
                frames = create_pixel_animal_frames(
                    body_color=_rand_colour(),
                    spike_count=random.randint(0, 4),
                    has_wings=random.choice([True, False]),
                    head_count=random.randint(1, 2),
                    has_horns=random.choice([True, False]),
                    has_snout=random.choice([True, False]),
                )
                sid = self.scene.animal_manager.next_species_id
                self.scene.animal_manager.next_species_id += 1

                animal = AnimalUnit(
                    scene=self.scene,
                    tile_x=gx,
                    tile_y=gy,
                    frames=frames,
                    species_id=sid,
                    founder_unit=None,
                    can_reproduce=True,
                )

                # Use proper layer-based draw order
                animal.draw_order = (gx + gy) * 10 + 2  # Layer 2: below trees

                # Set animal properties
                animal.diet = "herbivore"
                animal.aggression = random.uniform(0.0, 0.4)
                animal.growth_rate = 0.015
                animal.territory_radius = 3

                # Set zoom and calculate screen position immediately
                animal.set_zoom_scale(self.scene.zoom_scale)
                animal.calculate_screen_position(
                    self.scene.map.camera_offset_x,
                    self.scene.map.camera_offset_y,
                    self.scene.zoom_scale
                )

                print(f"[_spawn_animals_fallback] Animal {sid} at ({gx}, {gy}) draw_order: {animal.draw_order}")

                self.scene.animal_manager.species_founders[sid] = animal
                self.scene.animal_manager.add_animal(animal)
                
            except Exception as e:
                print(f"[_spawn_animals_fallback] Error spawning animal at ({gx}, {gy}): {e}")
                continue

    def generate_emergency_bipeds(self):
        """Generate bipeds if normal generation failed"""
        planet_w, planet_h = self.scene.meta.tiles
        
        for i in range(2):
            attempts = 0
            while attempts < 20:
                x = random.randint(planet_w//4, 3*planet_w//4)
                y = random.randint(planet_h//4, 3*planet_h//4)
                
                valid = False
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    if (x, y) in self.scene.terrain.terrain_stacks:
                        surface_tile = self.scene.terrain.get_surface_tile(x, y)
                        if surface_tile not in (TILE_WATER, TILE_WATERSTACK, -1):
                            valid = True
                else:
                    if self.scene.map_data[y][x] not in (TILE_WATER, TILE_WATERSTACK, -1):
                        valid = True
                        
                if valid:
                    color = (0, 255, 255) if i == 0 else (102, 255, 102)
                    biped = BipedUnit(self.scene, x, y, 
                                    frames=create_biped_frames(color, 4, 32, 48),
                                    speed=2.5)
                    biped.unit_id = f"emergency_biped_{i}"
                    biped.color = color
                    biped.set_zoom_scale(self.scene.zoom_scale)
                    self.scene.unit_manager.add_unit(biped)
                    print(f"[PlanetScene] Emergency biped {i} at ({x}, {y})")
                    break
                attempts += 1

    def generate_emergency_animals(self):
        """Generate animals if normal generation failed"""
        planet_w, planet_h = self.scene.meta.tiles
        
        for i in range(5):
            attempts = 0
            while attempts < 15:
                x = random.randint(1, planet_w - 2)
                y = random.randint(1, planet_h - 2)
                
                valid = False
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    if (x, y) in self.scene.terrain.terrain_stacks:
                        surface_tile = self.scene.terrain.get_surface_tile(x, y)
                        if surface_tile not in (TILE_WATER, TILE_WATERSTACK, -1):
                            valid = True
                else:
                    if self.scene.map_data[y][x] not in (TILE_WATER, TILE_WATERSTACK, -1):
                        valid = True
                        
                if valid:
                    frames = create_pixel_animal_frames(
                        body_color=_rand_colour(),
                        spike_count=random.randint(0, 2),
                        has_wings=random.choice([True, False]),
                    )
                    sid = self.scene.animal_manager.next_species_id
                    self.scene.animal_manager.next_species_id += 1
                    
                    animal = AnimalUnit(self.scene, x, y, frames, sid, None, True)
                    animal.draw_order = (x + y) * 10 + 2
                    
                    # Calculate position immediately
                    animal.set_zoom_scale(self.scene.zoom_scale)
                    animal.calculate_screen_position(
                        self.scene.map.camera_offset_x,
                        self.scene.map.camera_offset_y,
                        self.scene.zoom_scale
                    )
                    
                    self.scene.animal_manager.species_founders[sid] = animal
                    self.scene.animal_manager.add_animal(animal)
                    print(f"[PlanetScene] Emergency animal {i} at ({x}, {y}) draw_order: {animal.draw_order}")
                    break
                attempts += 1

    def simulate_movement_progress(self, biped, time_away_seconds):
        """Simulate how much progress a biped made while the player was away"""
        try:
            if not biped.path_tiles or biped.path_index >= len(biped.path_tiles):
                return "No valid path to simulate"
                
            # Calculate movement speed (tiles per second)
            biped_speed = getattr(biped, 'speed', 2.5)
            movement_rate = biped_speed / 60.0  # Convert to tiles per second
            
            # Calculate how many tiles the biped should have moved
            tiles_to_move = time_away_seconds * movement_rate
            original_index = biped.path_index
            original_pos = (biped.grid_x, biped.grid_y)
            
            print(f"[SIMULATION] Time away: {time_away_seconds:.1f}s, Speed: {biped_speed}, Can move {tiles_to_move:.2f} tiles")
            
            # Safety check: don't simulate excessive time (max 1 hour)
            if time_away_seconds > 3600:
                print(f"[SIMULATION] Warning: Very long time away ({time_away_seconds/3600:.1f} hours), capping simulation")
                time_away_seconds = 3600
                tiles_to_move = time_away_seconds * movement_rate
            
            # Move through the path
            tiles_moved = 0
            while tiles_to_move > 0 and biped.path_index < len(biped.path_tiles) - 1:
                # Move to next tile in path
                biped.path_index += 1
                tiles_moved += 1
                tiles_to_move -= 1.0
                
                # Update biped position
                next_tile = biped.path_tiles[biped.path_index]
                biped.grid_x, biped.grid_y = next_tile[0], next_tile[1]
                
                # Safety check: ensure position is valid
                if (biped.grid_x < 0 or biped.grid_y < 0 or 
                    biped.grid_y >= len(self.scene.map_data) or 
                    biped.grid_x >= len(self.scene.map_data[0])):
                    print(f"[SIMULATION] Error: Invalid position ({biped.grid_x}, {biped.grid_y}), reverting")
                    biped.grid_x, biped.grid_y = original_pos
                    biped.path_index = original_index
                    return "Simulation failed - invalid position"
                
                # Check if we've reached the destination
                if (biped.grid_x == biped.destination_x and 
                    biped.grid_y == biped.destination_y):
                    print(f"[SIMULATION] Biped reached destination while away!")
                    break
            
            # Update partial progress if stopped mid-tile
            if tiles_to_move > 0 and tiles_to_move < 1.0:
                biped.move_progress = tiles_to_move
            else:
                biped.move_progress = 0.0
                
            return f"Moved {tiles_moved} tiles (from index {original_index} to {biped.path_index})"
            
        except Exception as e:
            print(f"[SIMULATION] Error simulating movement: {e}")
            return f"Simulation error: {e}"

    def handle_path_completion(self, biped):
        """Handle when a biped completes its path"""
        try:
            # Move to final destination
            if biped.destination_x is not None and biped.destination_y is not None:
                biped.grid_x = biped.destination_x
                biped.grid_y = biped.destination_y
                
            # Clear movement state
            biped.moving = False
            biped.path_tiles = []
            biped.path_index = 0
            biped.move_progress = 0.0
            
            # Update mission based on what they were doing
            if biped.mission == "COLLECT_DROP" and biped.target_drop:
                # Try to collect the drop
                if biped.target_drop.alive:
                    print(f"[SIMULATION] Biped reached drop and collected it while away!")
                    self.scene.pick_up_drop(biped.target_drop)
                biped.target_drop = None
                biped.mission = "IDLE"
            elif biped.mission == "MOVE_TO":
                biped.mission = "IDLE"
                print(f"[SIMULATION] Biped completed movement and is now idle")
            
            # Update timestamp
            biped.last_command_time = time.time()
            
        except Exception as e:
            print(f"[SIMULATION] Error handling path completion: {e}")

    def check_entity_emergency_spawning(self):
        """Check if emergency spawning is needed and perform it"""
        # Emergency biped spawning
        if len(self.scene.unit_manager.units) == 0:
            print("[PlanetScene] Emergency biped generation")
            self.generate_emergency_bipeds()
            
        # Emergency animal spawning  
        if len(self.scene.animal_manager.animals) == 0:
            print("[PlanetScene] Emergency animal generation")
            self.generate_emergency_animals()

    def update_entity_tracking(self, dt):
        """Update entity tracking for auto-saving"""
        try:
            # Track biped movement for auto-saving
            pre_update_positions = {
                getattr(unit, 'unit_id', f'unit_{i}'): (unit.grid_x, unit.grid_y) 
                for i, unit in enumerate(self.scene.unit_manager.units) 
                if hasattr(unit, 'grid_x') and hasattr(unit, 'grid_y')
            }
            
            self.scene.unit_manager.update(dt)
            
            # Check if any bipeds moved and trigger auto-save
            for unit in self.scene.unit_manager.units:
                unit_id = getattr(unit, 'unit_id', f'unit_{hash(unit)}')
                if unit_id in pre_update_positions:
                    old_pos = pre_update_positions[unit_id]
                    new_pos = (getattr(unit, 'grid_x', 0), getattr(unit, 'grid_y', 0))
                    if old_pos != new_pos:
                        self.scene.on_biped_moved(unit)
                        break  # Only trigger once per frame
        except Exception as e:
            print(f"[PlanetScene] Error tracking biped movement: {e}")
            # Fall back to basic update
            self.scene.unit_manager.update(dt)

    def update_all_entities(self, dt):
        """Update all entities in the scene"""
        # Update entity tracking and movement
        self.update_entity_tracking(dt)
        
        # Calculate screen positions for all objects
        all_objects = self.scene.iso_objects + self.scene.unit_manager.units + self.scene.houses
        for obj in all_objects:
            try:
                obj.calculate_screen_position(
                    self.scene.map.camera_offset_x, self.scene.map.camera_offset_y, self.scene.zoom_scale
                )
            except Exception as e:
                print(f"[update] Error calculating screen position for {type(obj)}: {e}")
        
        # Update animals
        try:
            self.scene.animal_manager.update(dt)
            self.scene.animal_manager.calculate_screen_positions(
                self.scene.map.camera_offset_x, self.scene.map.camera_offset_y, self.scene.zoom_scale
            )
        except Exception as e:
            print(f"[update] Error updating animals: {e}")
            
        # Update drops
        for drop in list(self.scene.drops):
            try:
                drop.update(dt)
                drop.calculate_screen_position(
                    self.scene.map.camera_offset_x, self.scene.map.camera_offset_y, self.scene.zoom_scale
                )
                if not drop.alive:
                    self.scene.drops.remove(drop)
            except Exception as e:
                print(f"[update] Error updating drop: {e}")
                continue

    def auto_save_trigger(self, reason="unknown"):
        """Trigger auto-save when important state changes occur"""
        try:
            # Don't throttle critical movement commands
            immediate_save_reasons = ["movement_command_immediate", "biped_movement_restored"]
            
            if reason not in immediate_save_reasons and hasattr(self.scene, '_last_auto_save'):
                time_since_save = time.time() - self.scene._last_auto_save
                if time_since_save < 5.0:  # Don't save more than once every 5 seconds for non-critical saves
                    return
            
            self.scene._last_auto_save = time.time()
            if self.scene.planet_storage and hasattr(self.scene, 'meta'):
                self.scene.meta.state = self.scene.state_manager.serialize_state()
                if hasattr(self.scene, 'planet_id'):
                    self.scene.planet_storage.save_planet(self.scene.planet_id, self.scene.meta)
                    print(f"[PlanetScene] Auto-saved due to: {reason}")
                else:
                    print(f"[PlanetScene] Auto-save triggered ({reason}) but no planet_id set")
        except Exception as e:
            print(f"[PlanetScene] Auto-save failed ({reason}): {e}")
            # Don't crash the game if auto-save fails

    def on_biped_moved(self, biped):
        """Called whenever a biped moves to a new position"""
        try:
            biped.last_command_time = time.time()
            self.auto_save_trigger("biped_moved")
        except Exception as e:
            print(f"[PlanetScene] Error tracking biped movement: {e}")

    def on_biped_command(self, biped, command_type):
        """Called whenever a biped receives a new command"""
        try:
            biped.last_command_time = time.time()
            if not hasattr(biped, 'mission_data'):
                biped.mission_data = {}
            biped.mission_data['last_command'] = command_type
            self.auto_save_trigger(f"biped_command_{command_type}")
        except Exception as e:
            print(f"[PlanetScene] Error tracking biped command: {e}")

    def send_biped_to_collect(self, drop_obj):
        """Send a biped to collect a resource drop"""
        if not self.scene.unit_manager.units:
            return
        try:
            unit = self.scene.unit_manager.units[0]
            path = self.scene.find_path(unit.grid_x, unit.grid_y, drop_obj.grid_x, drop_obj.grid_y)
            if path:
                unit.path_tiles, unit.path_index = path, 0
                unit.mission, unit.target_drop = "COLLECT_DROP", drop_obj
                unit.destination_x, unit.destination_y = drop_obj.grid_x, drop_obj.grid_y
                
                # Trigger tracking update
                self.on_biped_command(unit, "COLLECT_DROP")
        except Exception as e:
            print(f"[PlanetScene] Error sending biped to collect: {e}")

    def pick_up_drop(self, drop_obj):
        """Pick up a resource drop"""
        self.scene.inventory.setdefault(drop_obj.resource_type, 0)
        self.scene.inventory[drop_obj.resource_type] += drop_obj.quantity
        drop_obj.alive = False
        print(f"Picked up {drop_obj.quantity} × {drop_obj.resource_type}: {self.scene.inventory}")

    def get_units_by_mission(self) -> dict:
        """Get count of units by mission type for monitoring"""
        try:
            mission_counts = {}
            units = getattr(self.scene, 'unit_manager', type('obj', (object,), {'units': []})).units
            for unit in units:
                mission = str(getattr(unit, 'mission', 'IDLE'))
                mission_counts[mission] = mission_counts.get(mission, 0) + 1
            return mission_counts
        except Exception as e:
            print(f"[PlanetScene] Error counting units by mission: {e}")
            return {"ERROR": 1}

    def find_valid_land_tile(self, tile_list, max_attempts: int = 500):
        """Pick a random (gx, gy) from tile_list that is on land, not blocked"""
        if not tile_list:
            print("[find_valid_land_tile] No tiles provided")
            return None
            
        attempts = 0
        while attempts < max_attempts:
            gx, gy = random.choice(tile_list)
            
            # Check terrain suitability - be more permissive
            valid = True
            if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                if (gx, gy) not in self.scene.terrain.terrain_stacks:
                    valid = False
                else:
                    surface_tile = self.scene.terrain.get_surface_tile(gx, gy)
                    height = self.scene.terrain.get_height_at(gx, gy)
                    # Allow placement on most terrain except water and extremely high
                    if surface_tile in (TILE_WATER, TILE_WATERSTACK) or height > 6:
                        valid = False
            else:
                # Legacy check
                if self.scene.is_water_tile(gx, gy):
                    valid = False
                    
            if (valid and 
                (gx, gy) not in {(h.grid_x, h.grid_y) for h in self.scene.houses}):
                print(f"[find_valid_land_tile] Found valid tile at ({gx}, {gy})")
                return gx, gy
                
            attempts += 1
            
        print(f"[find_valid_land_tile] Failed to find valid tile after {max_attempts} attempts")
        return None