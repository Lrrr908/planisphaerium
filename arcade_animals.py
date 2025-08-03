##########################################################
# arcade_animals.py
# Manages animals and wildlife for Arcade
##########################################################

import arcade
import random
import math
import time

def _rand_colour():
    """Generate a random bright color"""
    return random.randint(64, 255), random.randint(64, 255), random.randint(64, 255)

class ArcadeAnimalManager:
    """Manages all animals and wildlife for Arcade"""
    
    def __init__(self, scene):
        self.scene = scene
        self.next_species_id = 1
        self.species_founders = {}  # species_id -> founder animal
        self.last_spawn_time = time.time()

    def add_animal(self, animal_sprite):
        """Add an animal to management"""
        if animal_sprite not in self.scene.animal_sprites:
            self.scene.animal_sprites.append(animal_sprite)
        print(f"[ArcadeAnimalManager] Added animal species {getattr(animal_sprite, 'species_id', 'unknown')}")

    def remove_animal(self, animal_sprite):
        """Remove an animal from management"""
        if animal_sprite in self.scene.animal_sprites:
            self.scene.animal_sprites.remove(animal_sprite)
        print(f"[ArcadeAnimalManager] Removed animal species {getattr(animal_sprite, 'species_id', 'unknown')}")

    def spawn_random_animals(self, count=None, area_center=None, area_radius=None):
        """Spawn random animals on the planet"""
        if count is None:
            count = random.randint(3, 8)
        
        spawned = 0
        max_attempts = 50
        
        for _ in range(count):
            attempts = 0
            while attempts < max_attempts:
                # Choose spawn location
                if area_center and area_radius:
                    # Spawn in specific area
                    center_x, center_y = area_center
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(0, area_radius)
                    spawn_x = int(center_x + math.cos(angle) * distance)
                    spawn_y = int(center_y + math.sin(angle) * distance)
                else:
                    # Spawn anywhere on planet
                    spawn_x = random.randint(1, self.scene.terrain_width - 2)
                    spawn_y = random.randint(1, self.scene.terrain_height - 2)
                
                # Check if location is valid
                if self._is_valid_spawn_location(spawn_x, spawn_y):
                    # Create animal
                    animal = self._create_random_animal(spawn_x, spawn_y)
                    if animal:
                        self.add_animal(animal)
                        spawned += 1
                        break
                
                attempts += 1
        
        print(f"[ArcadeAnimalManager] Spawned {spawned} random animals")
        return spawned

    def _is_valid_spawn_location(self, grid_x, grid_y):
        """Check if a location is valid for animal spawning"""
        # Check bounds
        if not (0 <= grid_x < self.scene.terrain_width and 0 <= grid_y < self.scene.terrain_height):
            return False
        
        # Check if blocked
        if (grid_x, grid_y) in self.scene.blocked_tiles:
            return False
        
        # Check terrain type
        if (0 <= grid_y < len(self.scene.map_data) and 
            0 <= grid_x < len(self.scene.map_data[0])):
            tile_type = self.scene.map_data[grid_y][grid_x]
            # Don't spawn in water or void
            if tile_type in (2, 5, -1):  # TILE_WATER, TILE_WATERSTACK, void
                return False
        
        return True

    def _create_random_animal(self, grid_x, grid_y):
        """Create a random animal at the specified location"""
        try:
            # Calculate isometric position
            iso_x = (grid_x - grid_y) * (64 // 2)  # TILE_WIDTH
            iso_y = (grid_x + grid_y) * (37 // 2)  # TILE_HEIGHT
            
            # Create animal sprite
            from arcade_planet_scene import ArcadeAnimalSprite
            animal = ArcadeAnimalSprite(iso_x, iso_y, _rand_colour())
            
            # Set animal properties
            animal.grid_x = grid_x
            animal.grid_y = grid_y
            animal.species_id = self.next_species_id
            animal.creation_time = time.time()
            animal.last_move_time = time.time()
            animal.move_cooldown = random.uniform(2.0, 5.0)  # Seconds between moves
            animal.territory_center_x = grid_x
            animal.territory_center_y = grid_y
            animal.territory_radius = random.randint(3, 8)
            animal.diet = random.choice(["herbivore", "omnivore", "carnivore"])
            animal.aggression = random.uniform(0.0, 0.5)
            animal.health = 100
            animal.max_health = 100
            animal.energy = 100
            animal.reproduction_cooldown = 0
            
            # Create species founder if this is a new species
            if self.next_species_id not in self.species_founders:
                self.species_founders[self.next_species_id] = animal
            
            self.next_species_id += 1
            return animal
            
        except Exception as e:
            print(f"[ArcadeAnimalManager] Error creating animal: {e}")
            return None

    def update(self, dt):
        """Update all animals"""
        current_time = time.time()
        
        for animal in self.scene.animal_sprites:
            self._update_animal_behavior(animal, dt, current_time)
        
        # Occasionally spawn new animals
        if current_time - self.last_spawn_time > 30.0:  # Every 30 seconds
            if len(self.scene.animal_sprites) < 20:  # Max population
                self.spawn_random_animals(1)
            self.last_spawn_time = current_time

    def _update_animal_behavior(self, animal, dt, current_time):
        """Update individual animal behavior"""
        try:
            # Movement behavior
            if (current_time - getattr(animal, 'last_move_time', 0) > 
                getattr(animal, 'move_cooldown', 3.0)):
                self._move_animal_randomly(animal)
                animal.last_move_time = current_time
                animal.move_cooldown = random.uniform(2.0, 5.0)
            
            # Energy and health management
            self._update_animal_vitals(animal, dt)
            
            # Territory behavior
            self._enforce_territory(animal)
            
        except Exception as e:
            print(f"[ArcadeAnimalManager] Error updating animal: {e}")

    def _move_animal_randomly(self, animal):
        """Move animal randomly within its territory"""
        try:
            # Get current grid position
            current_grid_x = getattr(animal, 'grid_x', 0)
            current_grid_y = getattr(animal, 'grid_y', 0)
            
            # Choose random direction
            directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            dx, dy = random.choice(directions)
            
            new_grid_x = current_grid_x + dx
            new_grid_y = current_grid_y + dy
            
            # Check if new position is valid and within territory
            if (self._is_valid_spawn_location(new_grid_x, new_grid_y) and
                self._is_within_territory(animal, new_grid_x, new_grid_y)):
                
                # Calculate new isometric position
                new_iso_x = (new_grid_x - new_grid_y) * (64 // 2)
                new_iso_y = (new_grid_x + new_grid_y) * (37 // 2)
                
                # Update position
                animal.center_x = new_iso_x
                animal.center_y = new_iso_y
                animal.grid_x = new_grid_x
                animal.grid_y = new_grid_y
                
        except Exception as e:
            print(f"[ArcadeAnimalManager] Error moving animal: {e}")

    def _is_within_territory(self, animal, grid_x, grid_y):
        """Check if position is within animal's territory"""
        territory_center_x = getattr(animal, 'territory_center_x', animal.grid_x)
        territory_center_y = getattr(animal, 'territory_center_y', animal.grid_y)
        territory_radius = getattr(animal, 'territory_radius', 5)
        
        distance = math.hypot(grid_x - territory_center_x, grid_y - territory_center_y)
        return distance <= territory_radius

    def _enforce_territory(self, animal):
        """Ensure animal stays within its territory"""
        current_x = getattr(animal, 'grid_x', 0)
        current_y = getattr(animal, 'grid_y', 0)
        
        if not self._is_within_territory(animal, current_x, current_y):
            # Move back towards territory center
            territory_center_x = getattr(animal, 'territory_center_x', current_x)
            territory_center_y = getattr(animal, 'territory_center_y', current_y)
            
            # Simple movement towards center
            dx = 1 if territory_center_x > current_x else -1 if territory_center_x < current_x else 0
            dy = 1 if territory_center_y > current_y else -1 if territory_center_y < current_y else 0
            
            new_x = current_x + dx
            new_y = current_y + dy
            
            if self._is_valid_spawn_location(new_x, new_y):
                new_iso_x = (new_x - new_y) * (64 // 2)
                new_iso_y = (new_x + new_y) * (37 // 2)
                
                animal.center_x = new_iso_x
                animal.center_y = new_iso_y
                animal.grid_x = new_x
                animal.grid_y = new_y

    def _update_animal_vitals(self, animal, dt):
        """Update animal health and energy"""
        # Energy decreases over time
        if hasattr(animal, 'energy'):
            animal.energy = max(0, animal.energy - dt * 0.1)
            
            # Health decreases if energy is too low
            if animal.energy < 20:
                if hasattr(animal, 'health'):
                    animal.health = max(0, animal.health - dt * 0.5)
                    
                    # Animal dies if health reaches 0
                    if animal.health <= 0:
                        animal.alive = False
        
        # Regenerate energy slowly
        if hasattr(animal, 'energy') and animal.energy < 100:
            animal.energy = min(100, animal.energy + dt * 0.05)

    def get_animal_count(self):
        """Get total number of animals"""
        return len(self.scene.animal_sprites)

    def get_species_count(self):
        """Get number of different species"""
        species_ids = set()
        for animal in self.scene.animal_sprites:
            species_ids.add(getattr(animal, 'species_id', 0))
        return len(species_ids)

    def get_animals_by_species(self):
        """Get animals grouped by species"""
        species = {}
        for animal in self.scene.animal_sprites:
            species_id = getattr(animal, 'species_id', 0)
            if species_id not in species:
                species[species_id] = []
            species[species_id].append(animal)
        return species

    def get_animals_in_area(self, center_x, center_y, radius):
        """Get all animals within a radius of a point"""
        animals_in_area = []
        
        for animal in self.scene.animal_sprites:
            animal_grid_x = getattr(animal, 'grid_x', 0)
            animal_grid_y = getattr(animal, 'grid_y', 0)
            distance = math.hypot(center_x - animal_grid_x, center_y - animal_grid_y)
            if distance <= radius:
                animals_in_area.append(animal)
        
        return animals_in_area

    def get_nearest_animal_to(self, grid_x, grid_y):
        """Get the nearest animal to a grid position"""
        if not self.scene.animal_sprites:
            return None
        
        nearest_animal = None
        nearest_distance = float('inf')
        
        for animal in self.scene.animal_sprites:
            animal_grid_x = getattr(animal, 'grid_x', 0)
            animal_grid_y = getattr(animal, 'grid_y', 0)
            distance = math.hypot(grid_x - animal_grid_x, grid_y - animal_grid_y)
            if distance < nearest_distance:
                nearest_animal = animal
                nearest_distance = distance
        
        return nearest_animal

    def calculate_screen_positions(self, camera_x, camera_y, zoom_scale):
        """Calculate screen positions for all animals (for compatibility)"""
        # In Arcade, this is typically handled automatically by the camera
        # This method exists for compatibility with the original pygame code
        pass

    def set_zoom_scale(self, zoom_scale):
        """Set zoom scale for all animals (for compatibility)"""
        # In Arcade, zoom is typically handled by the camera
        # This method exists for compatibility with the original pygame code
        pass

    def get_animal_stats(self):
        """Get statistics about all animals"""
        stats = {
            "total_animals": len(self.scene.animal_sprites),
            "species_count": self.get_species_count(),
            "alive_animals": len([a for a in self.scene.animal_sprites if getattr(a, 'alive', True)]),
            "diets": {},
            "average_health": 0,
            "average_energy": 0
        }
        
        if self.scene.animal_sprites:
            total_health = 0
            total_energy = 0
            
            for animal in self.scene.animal_sprites:
                # Count diets
                diet = getattr(animal, 'diet', 'unknown')
                stats["diets"][diet] = stats["diets"].get(diet, 0) + 1
                
                # Sum vitals
                total_health += getattr(animal, 'health', 100)
                total_energy += getattr(animal, 'energy', 100)
            
            stats["average_health"] = total_health / len(self.scene.animal_sprites)
            stats["average_energy"] = total_energy / len(self.scene.animal_sprites)
        
        return stats

    def heal_all_animals(self, amount=10):
        """Heal all animals"""
        for animal in self.scene.animal_sprites:
            if hasattr(animal, 'health'):
                max_health = getattr(animal, 'max_health', 100)
                animal.health = min(max_health, animal.health + amount)
        print(f"[ArcadeAnimalManager] Healed all animals for {amount} HP")

    def feed_all_animals(self, amount=20):
        """Feed all animals (restore energy)"""
        for animal in self.scene.animal_sprites:
            if hasattr(animal, 'energy'):
                animal.energy = min(100, animal.energy + amount)
        print(f"[ArcadeAnimalManager] Fed all animals (+{amount} energy)")

    def create_predator(self, grid_x, grid_y):
        """Create a predator animal at specific location"""
        if not self._is_valid_spawn_location(grid_x, grid_y):
            return None
        
        animal = self._create_random_animal(grid_x, grid_y)
        if animal:
            # Make it a predator
            animal.diet = "carnivore"
            animal.aggression = random.uniform(0.7, 1.0)
            animal.health = 150
            animal.max_health = 150
            animal.territory_radius = random.randint(8, 15)
            
            # Make it larger/different color
            animal.color = (200, 50, 50)  # Reddish
            animal.texture = arcade.Texture.create_filled("predator", (30, 30), animal.color)
            
            self.add_animal(animal)
            print(f"[ArcadeAnimalManager] Created predator at ({grid_x}, {grid_y})")
            return animal
        
        return None

    def cleanup_dead_animals(self):
        """Remove dead animals from management"""
        initial_count = len(self.scene.animal_sprites)
        
        # Remove dead animals
        alive_animals = [animal for animal in self.scene.animal_sprites if getattr(animal, 'alive', True)]
        
        # Update sprite list
        self.scene.animal_sprites.clear()
        for animal in alive_animals:
            self.scene.animal_sprites.append(animal)
        
        removed_count = initial_count - len(alive_animals)
        if removed_count > 0:
            print(f"[ArcadeAnimalManager] Removed {removed_count} dead animals")
        
        return removed_count

    def migrate_animals(self, from_area, to_area, count=None):
        """Migrate animals from one area to another"""
        from_center, from_radius = from_area
        to_center, to_radius = to_area
        
        # Get animals in source area
        source_animals = self.get_animals_in_area(from_center[0], from_center[1], from_radius)
        
        if not source_animals:
            return 0
        
        # Determine how many to migrate
        if count is None:
            count = min(len(source_animals), random.randint(1, 3))
        
        migrated = 0
        for _ in range(count):
            if not source_animals:
                break
            
            animal = random.choice(source_animals)
            source_animals.remove(animal)
            
            # Find new location in target area
            attempts = 0
            while attempts < 20:
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0, to_radius)
                new_x = int(to_center[0] + math.cos(angle) * distance)
                new_y = int(to_center[1] + math.sin(angle) * distance)
                
                if self._is_valid_spawn_location(new_x, new_y):
                    # Move animal
                    new_iso_x = (new_x - new_y) * (64 // 2)
                    new_iso_y = (new_x + new_y) * (37 // 2)
                    
                    animal.center_x = new_iso_x
                    animal.center_y = new_iso_y
                    animal.grid_x = new_x
                    animal.grid_y = new_y
                    animal.territory_center_x = new_x
                    animal.territory_center_y = new_y
                    
                    migrated += 1
                    break
                
                attempts += 1
        
        print(f"[ArcadeAnimalManager] Migrated {migrated} animals")
        return migrated

    def get_animal_info(self, animal):
        """Get detailed information about an animal"""
        return {
            "species_id": getattr(animal, 'species_id', 0),
            "position": (animal.center_x, animal.center_y),
            "grid_position": (getattr(animal, 'grid_x', 0), getattr(animal, 'grid_y', 0)),
            "health": getattr(animal, 'health', 100),
            "energy": getattr(animal, 'energy', 100),
            "diet": getattr(animal, 'diet', 'unknown'),
            "aggression": getattr(animal, 'aggression', 0.0),
            "territory_center": (getattr(animal, 'territory_center_x', 0), 
                               getattr(animal, 'territory_center_y', 0)),
            "territory_radius": getattr(animal, 'territory_radius', 5),
            "creation_time": getattr(animal, 'creation_time', 0),
            "alive": getattr(animal, 'alive', True)
        }