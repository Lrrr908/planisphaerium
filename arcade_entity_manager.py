##########################################################
# arcade_entity_manager.py
# Handles entity spawning, management, simulation, and time-away simulation for Arcade
##########################################################

import random
import time
import math
import arcade

# Constants
TILE_WATER = 2
TILE_WATERSTACK = 5
TILE_DESERT = 11
TILE_WIDTH = 64
TILE_HEIGHT = 37

def _rand_colour():
    """Bright random colour helper."""
    return random.randint(64, 255), random.randint(64, 255), random.randint(64, 255)

class ArcadeEntityManager:
    """Handles all entity spawning, management, and simulation for Arcade"""
    
    def __init__(self, scene):
        self.scene = scene

    def spawn_initial_bipeds(self, valid_tiles):
        """Spawn initial bipeds"""
        print(f"[ArcadeEntityManager] Spawning initial bipeds")
        
        if not valid_tiles:
            print("[ArcadeEntityManager] No valid tiles for biped spawning")
            return
        
        # Spawn 2 initial bipeds
        colors = [(0, 255, 255), (102, 255, 102)]  # Cyan and green
        spawned_count = 0
        
        for idx, color in enumerate(colors):
            if not valid_tiles:
                break
                
            # Pick a random position
            bx, by = random.choice(valid_tiles)
            valid_tiles.remove((bx, by))  # Don't reuse the same spot
            
            # Calculate isometric position
            iso_x = (bx - by) * (TILE_WIDTH // 2)
            iso_y = (bx + by) * (TILE_HEIGHT // 2)
            
            # Create biped sprite
            from arcade_planet_scene import ArcadeBipedSprite
            biped = ArcadeBipedSprite(iso_x, iso_y, f"Biped{idx}", color)
            
            # Set biped properties
            biped.grid_x = bx
            biped.grid_y = by
            biped.unit_id = f"initial_biped_{idx}_{self.scene.meta.seed}"
            biped.creation_time = time.time()
            biped.last_command_time = time.time()
            biped.health = 100
            biped.mission = "IDLE"
            biped.moving = False
            
            self.scene.biped_sprites.append(biped)
            spawned_count += 1
            
            print(f"[ArcadeEntityManager] Biped {idx} spawned at ({bx}, {by})")
        
        print(f"[ArcadeEntityManager] Successfully spawned {spawned_count} bipeds")

    def spawn_animals(self, valid_tiles):
        """Spawn initial animals"""
        print(f"[ArcadeEntityManager] Spawning animals")
        
        if not valid_tiles:
            print("[ArcadeEntityManager] No valid tiles for animal spawning")
            return
        
        # Spawn 5 animals
        animal_count = min(5, len(valid_tiles) // 4)
        
        for i in range(animal_count):
            if not valid_tiles:
                break
                
            # Pick a random position
            ax, ay = random.choice(valid_tiles)
            
            # Calculate isometric position
            iso_x = (ax - ay) * (TILE_WIDTH // 2)
            iso_y = (ax + ay) * (TILE_HEIGHT // 2)
            
            # Create animal sprite
            from arcade_planet_scene import ArcadeAnimalSprite
            animal = ArcadeAnimalSprite(iso_x, iso_y, _rand_colour())
            
            # Set animal properties
            animal.grid_x = ax
            animal.grid_y = ay
            animal.species_id = i
            
            self.scene.animal_sprites.append(animal)
        
        print(f"[ArcadeEntityManager] Spawned {len(self.scene.animal_sprites)} animals")

    def update_all_entities(self, dt):
        """Update all entities in the scene"""
        # Update all sprite lists
        for sprite_list in self.scene.sprite_lists:
            sprite_list.update()
        
        # Update any custom entity logic here
        self._update_biped_movement(dt)
        self._update_animal_behavior(dt)

    def _update_biped_movement(self, dt):
        """Update biped movement"""
        for biped in self.scene.biped_sprites:
            if hasattr(biped, 'moving') and biped.moving:
                # Simple movement logic - can be expanded
                if hasattr(biped, 'target_x') and hasattr(biped, 'target_y'):
                    # Move towards target
                    dx = biped.target_x - biped.center_x
                    dy = biped.target_y - biped.center_y
                    distance = math.hypot(dx, dy)
                    
                    if distance > 2:  # Still moving
                        speed = 50 * dt  # pixels per second
                        biped.center_x += (dx / distance) * speed
                        biped.center_y += (dy / distance) * speed
                    else:
                        # Reached target
                        biped.center_x = biped.target_x
                        biped.center_y = biped.target_y
                        biped.moving = False
                        delattr(biped, 'target_x')
                        delattr(biped, 'target_y')

    def _update_animal_behavior(self, dt):
        """Update animal behavior"""
        for animal in self.scene.animal_sprites:
            # Simple random movement
            if random.random() < 0.005:  # 0.5% chance per frame
                animal.center_x += random.randint(-20, 20)
                animal.center_y += random.randint(-20, 20)

    def send_biped_to_collect(self, drop_obj):
        """Send a biped to collect a resource drop"""
        if not self.scene.biped_sprites:
            return
            
        # Get first biped
        biped = self.scene.biped_sprites[0]
        
        # Set movement target
        biped.target_x = drop_obj.center_x
        biped.target_y = drop_obj.center_y
        biped.moving = True
        biped.mission = "COLLECT_DROP"
        
        print(f"[ArcadeEntityManager] Sent biped to collect drop at ({drop_obj.center_x}, {drop_obj.center_y})")

    def pick_up_drop(self, drop_obj):
        """Pick up a resource drop"""
        resource_type = getattr(drop_obj, 'resource_type', 'unknown')
        quantity = getattr(drop_obj, 'quantity', 1)
        
        self.scene.inventory.setdefault(resource_type, 0)
        self.scene.inventory[resource_type] += quantity
        
        # Remove drop
        drop_obj.alive = False
        if drop_obj in self.scene.drop_sprites:
            self.scene.drop_sprites.remove(drop_obj)
        
        print(f"Picked up {quantity} × {resource_type}: {self.scene.inventory}")

    def find_valid_land_tile(self, tile_list, max_attempts=500):
        """Find a valid land tile from the list"""
        if not tile_list:
            return None
            
        attempts = 0
        while attempts < max_attempts:
            gx, gy = random.choice(tile_list)
            
            # Check if valid
            if (0 <= gx < self.scene.terrain_width and 
                0 <= gy < self.scene.terrain_height and
                (gx, gy) not in self.scene.blocked_tiles):
                return gx, gy
                
            attempts += 1
        
        return None

    def check_entity_emergency_spawning(self):
        """Check if emergency spawning is needed"""
        # Emergency biped spawning
        if len(self.scene.biped_sprites) == 0:
            print("[ArcadeEntityManager] Emergency biped generation")
            self._generate_emergency_bipeds()
            
        # Emergency animal spawning  
        if len(self.scene.animal_sprites) == 0:
            print("[ArcadeEntityManager] Emergency animal generation")
            self._generate_emergency_animals()

    def _generate_emergency_bipeds(self):
        """Generate emergency bipeds"""
        for i in range(2):
            # Find a safe spot
            attempts = 0
            while attempts < 20:
                x = random.randint(self.scene.terrain_width//4, 3*self.scene.terrain_width//4)
                y = random.randint(self.scene.terrain_height//4, 3*self.scene.terrain_height//4)
                
                if ((x, y) not in self.scene.blocked_tiles and 
                    0 <= y < len(self.scene.map_data) and 
                    0 <= x < len(self.scene.map_data[0]) and
                    self.scene.map_data[y][x] not in (TILE_WATER, TILE_WATERSTACK, -1)):
                    
                    # Calculate isometric position
                    iso_x = (x - y) * (TILE_WIDTH // 2)
                    iso_y = (x + y) * (TILE_HEIGHT // 2)
                    
                    color = (0, 255, 255) if i == 0 else (102, 255, 102)
                    from arcade_planet_scene import ArcadeBipedSprite
                    biped = ArcadeBipedSprite(iso_x, iso_y, f"Emergency{i}", color)
                    biped.grid_x = x
                    biped.grid_y = y
                    biped.unit_id = f"emergency_biped_{i}"
                    
                    self.scene.biped_sprites.append(biped)
                    print(f"[ArcadeEntityManager] Emergency biped {i} at ({x}, {y})")
                    break
                attempts += 1

    def _generate_emergency_animals(self):
        """Generate emergency animals"""
        for i in range(3):
            # Find a safe spot
            attempts = 0
            while attempts < 15:
                x = random.randint(1, self.scene.terrain_width - 2)
                y = random.randint(1, self.scene.terrain_height - 2)
                
                if ((x, y) not in self.scene.blocked_tiles and 
                    0 <= y < len(self.scene.map_data) and 
                    0 <= x < len(self.scene.map_data[0]) and
                    self.scene.map_data[y][x] not in (TILE_WATER, TILE_WATERSTACK, -1)):
                    
                    # Calculate isometric position
                    iso_x = (x - y) * (TILE_WIDTH // 2)
                    iso_y = (x + y) * (TILE_HEIGHT // 2)
                    
                    from arcade_planet_scene import ArcadeAnimalSprite
                    animal = ArcadeAnimalSprite(iso_x, iso_y, _rand_colour())
                    animal.grid_x = x
                    animal.grid_y = y
                    animal.species_id = i
                    
                    self.scene.animal_sprites.append(animal)
                    print(f"[ArcadeEntityManager] Emergency animal {i} at ({x}, {y})")
                    break
                attempts += 1

    def auto_save_trigger(self, reason="unknown"):
        """Trigger auto-save when important state changes occur"""
        try:
            if hasattr(self.scene, '_last_auto_save'):
                time_since_save = time.time() - self.scene._last_auto_save
                if time_since_save < 5.0:  # Don't save more than once every 5 seconds
                    return
            
            self.scene._last_auto_save = time.time()
            print(f"[ArcadeEntityManager] Auto-save triggered: {reason}")
            # TODO: Implement actual saving
        except Exception as e:
            print(f"[ArcadeEntityManager] Auto-save failed ({reason}): {e}")

    def on_biped_moved(self, biped):
        """Called whenever a biped moves to a new position"""
        try:
            biped.last_command_time = time.time()
            self.auto_save_trigger("biped_moved")
        except Exception as e:
            print(f"[ArcadeEntityManager] Error tracking biped movement: {e}")

    def on_biped_command(self, biped, command_type):
        """Called whenever a biped receives a new command"""
        try:
            biped.last_command_time = time.time()
            if not hasattr(biped, 'mission_data'):
                biped.mission_data = {}
            biped.mission_data['last_command'] = command_type
            self.auto_save_trigger(f"biped_command_{command_type}")
        except Exception as e:
            print(f"[ArcadeEntityManager] Error tracking biped command: {e}")

    def get_units_by_mission(self):
        """Get count of units by mission type for monitoring"""
        try:
            mission_counts = {}
            for biped in self.scene.biped_sprites:
                mission = str(getattr(biped, 'mission', 'IDLE'))
                mission_counts[mission] = mission_counts.get(mission, 0) + 1
            return mission_counts
        except Exception as e:
            print(f"[ArcadeEntityManager] Error counting units by mission: {e}")
            return {"ERROR": 1}

    def simulate_movement_progress(self, biped, time_away_seconds):
        """Simulate how much progress a biped made while the player was away"""
        try:
            # Simple simulation - just complete the movement if enough time passed
            if hasattr(biped, 'moving') and biped.moving:
                if hasattr(biped, 'target_x') and hasattr(biped, 'target_y'):
                    # Calculate if biped would have reached target
                    dx = biped.target_x - biped.center_x
                    dy = biped.target_y - biped.center_y
                    distance = math.hypot(dx, dy)
                    
                    # Assume movement speed of 50 pixels per second
                    time_needed = distance / 50
                    
                    if time_away_seconds >= time_needed:
                        # Complete the movement
                        biped.center_x = biped.target_x
                        biped.center_y = biped.target_y
                        biped.moving = False
                        return f"Completed movement after {time_needed:.1f}s"
                    else:
                        # Partial movement
                        progress = time_away_seconds / time_needed
                        biped.center_x += dx * progress
                        biped.center_y += dy * progress
                        return f"Moved {progress*100:.1f}% of the way"
            
            return "No movement to simulate"
            
        except Exception as e:
            print(f"[ArcadeEntityManager] Error simulating movement: {e}")
            return f"Simulation error: {e}"