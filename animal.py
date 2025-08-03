"""
Animal Entity
Randomly generated animals with AI behaviors
"""

import random
import math
from typing import List, Tuple, Optional, Dict, Any
from .entity import Entity, EntityType, EntityState, EntityStats
from enum import Enum

class AnimalType(Enum):
    """Animal types"""
    HERBIVORE = "herbivore"
    CARNIVORE = "carnivore"
    OMNIVORE = "omnivore"

class AnimalShape(Enum):
    """Animal shapes for visual variety"""
    CIRCLE = "circle"
    SQUARE = "square"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"
    STAR = "star"

class Animal(Entity):
    """Animal entity - randomly generated creatures with AI"""
    
    def __init__(self, entity_id: str, x: float, y: float, animal_type: AnimalType = None):
        super().__init__(entity_id, EntityType.ANIMAL, x, y)
        
        # Randomly generate animal properties if not specified
        if animal_type is None:
            animal_type = random.choice(list(AnimalType))
            
        self.animal_type = animal_type
        self.shape = random.choice(list(AnimalShape))
        self.age = 0
        self.max_age = random.randint(50, 200)
        self.reproduction_timer = 0
        self.reproduction_cooldown = random.randint(30, 120)
        self.prey_target = None
        self.predator_target = None
        self.fleeing = False
        self.flee_timer = 0
        
        # Set stats based on animal type
        self.setup_animal_stats()
        
        # Generate random visual properties
        self.generate_visual_properties()
        
    def setup_animal_stats(self):
        """Set up stats based on animal type"""
        if self.animal_type == AnimalType.HERBIVORE:
            self.stats = EntityStats(
                health=random.randint(30, 60),
                max_health=60,
                hunger=random.randint(0, 30),
                max_hunger=100,
                speed=random.uniform(0.8, 1.5),
                attack=random.randint(2, 8),
                defense=random.randint(3, 10)
            )
        elif self.animal_type == AnimalType.CARNIVORE:
            self.stats = EntityStats(
                health=random.randint(50, 100),
                max_health=100,
                hunger=random.randint(0, 40),
                max_hunger=120,
                speed=random.uniform(1.2, 2.0),
                attack=random.randint(15, 30),
                defense=random.randint(8, 15)
            )
        else:  # OMNIVORE
            self.stats = EntityStats(
                health=random.randint(40, 80),
                max_health=80,
                hunger=random.randint(0, 35),
                max_hunger=110,
                speed=random.uniform(1.0, 1.8),
                attack=random.randint(8, 20),
                defense=random.randint(5, 12)
            )
            
    def generate_visual_properties(self):
        """Generate random visual properties"""
        # Generate random color based on animal type
        if self.animal_type == AnimalType.HERBIVORE:
            # Earth tones for herbivores
            base_colors = [
                (139, 69, 19),   # Saddle brown
                (160, 82, 45),   # Sienna
                (210, 180, 140), # Tan
                (244, 164, 96),  # Sandy brown
                (255, 228, 196), # Bisque
            ]
        elif self.animal_type == AnimalType.CARNIVORE:
            # Darker colors for carnivores
            base_colors = [
                (47, 79, 79),    # Dark slate gray
                (105, 105, 105), # Dim gray
                (128, 0, 0),     # Maroon
                (139, 0, 0),     # Dark red
                (25, 25, 112),   # Midnight blue
            ]
        else:  # OMNIVORE
            # Mixed colors for omnivores
            base_colors = [
                (85, 107, 47),   # Dark olive green
                (107, 142, 35),  # Olive drab
                (184, 134, 11),  # Dark goldenrod
                (205, 133, 63),  # Peru
                (160, 82, 45),   # Sienna
            ]
            
        # Pick base color and add variation
        base_color = random.choice(base_colors)
        variation = random.randint(-30, 30)
        self.color = tuple(max(0, min(255, c + variation)) for c in base_color)
        
        # Random size
        self.size = random.uniform(0.5, 1.5)
        
    def update(self, delta_time: float, world_data: Dict[Tuple[int, int], 'Tile'], entities: List['Entity']):
        """Update animal logic"""
        super().update(delta_time, world_data)
        
        # Update age
        self.age += delta_time
        if self.age > self.max_age:
            self.state = EntityState.DEAD
            return
            
        # Update hunger
        self.stats.hunger = min(self.stats.max_hunger, self.stats.hunger + delta_time * 1.5)
        
        # Update reproduction timer
        self.reproduction_timer += delta_time
        
        # Update fleeing timer
        if self.fleeing:
            self.flee_timer += delta_time
            if self.flee_timer > 10.0:  # Stop fleeing after 10 seconds
                self.fleeing = False
                self.flee_timer = 0
                
        # Handle current state
        if self.state == EntityState.DEAD:
            return
        elif self.fleeing:
            self.update_fleeing(delta_time, world_data)
        elif self.is_hungry():
            self.find_food(entities, world_data)
        elif self.animal_type == AnimalType.CARNIVORE:
            self.find_prey(entities)
        else:
            self.wander(delta_time, world_data)
            
    def update_fleeing(self, delta_time: float, world_data: Dict[Tuple[int, int], 'Tile']):
        """Update fleeing behavior"""
        if self.predator_target:
            # Move away from predator
            predator_x, predator_y = self.predator_target.get_position()
            dx = self.x - predator_x
            dy = self.y - predator_y
            
            # Normalize direction
            distance = math.sqrt(dx * dx + dy * dy)
            if distance > 0:
                # Move away from predator
                move_distance = self.stats.speed * delta_time * 1.5  # Faster when fleeing
                self.x += (dx / distance) * move_distance
                self.y += (dy / distance) * move_distance
                
    def find_food(self, entities: List['Entity'], world_data: Dict[Tuple[int, int], 'Tile']):
        """Find food based on animal type"""
        if self.animal_type == AnimalType.HERBIVORE:
            # Look for plants/grass
            food_pos = self.find_nearest_plant(world_data)
            if food_pos:
                self.set_target(food_pos[0], food_pos[1])
                self.state = EntityState.MOVING
        elif self.animal_type == AnimalType.CARNIVORE:
            # Look for prey
            prey = self.find_nearest_prey(entities)
            if prey:
                self.prey_target = prey
                self.set_target(prey.x, prey.y)
                self.state = EntityState.ATTACKING
        else:  # OMNIVORE
            # Try meat first, then plants
            prey = self.find_nearest_prey(entities)
            if prey:
                self.prey_target = prey
                self.set_target(prey.x, prey.y)
                self.state = EntityState.ATTACKING
            else:
                food_pos = self.find_nearest_plant(world_data)
                if food_pos:
                    self.set_target(food_pos[0], food_pos[1])
                    self.state = EntityState.MOVING
                    
    def find_prey(self, entities: List['Entity']):
        """Find prey to hunt"""
        prey = self.find_nearest_prey(entities)
        if prey:
            self.prey_target = prey
            self.set_target(prey.x, prey.y)
            self.state = EntityState.ATTACKING
            
    def find_nearest_plant(self, world_data: Dict[Tuple[int, int], 'Tile']) -> Optional[Tuple[int, int]]:
        """Find nearest plant food"""
        current_pos = self.get_grid_position()
        
        # Search in expanding circles
        for distance in range(1, 15):
            for dx in range(-distance, distance + 1):
                for dy in range(-distance, distance + 1):
                    if abs(dx) + abs(dy) == distance:
                        check_x, check_y = current_pos[0] + dx, current_pos[1] + dy
                        if (check_x, check_y) in world_data:
                            tile = world_data[(check_x, check_y)]
                            if tile.biome in ['grassland', 'forest', 'jungle']:
                                return (check_x, check_y)
        return None
        
    def find_nearest_prey(self, entities: List['Entity']) -> Optional['Entity']:
        """Find nearest prey animal"""
        nearest_prey = None
        nearest_distance = float('inf')
        
        for entity in entities:
            if (entity.entity_type == EntityType.ANIMAL and 
                entity != self and 
                entity.is_alive() and
                entity.animal_type == AnimalType.HERBIVORE):
                
                distance = self.distance_to(entity)
                if distance < nearest_distance and distance < 20:  # Within hunting range
                    nearest_prey = entity
                    nearest_distance = distance
                    
        return nearest_prey
        
    def wander(self, delta_time: float, world_data: Dict[Tuple[int, int], 'Tile']):
        """Wander around randomly"""
        if random.random() < 0.02:  # 2% chance to change direction
            current_pos = self.get_grid_position()
            
            # Find a random walkable position within 8 tiles
            for _ in range(10):
                dx = random.randint(-4, 4)
                dy = random.randint(-4, 4)
                target_x, target_y = current_pos[0] + dx, current_pos[1] + dy
                
                if (target_x, target_y) in world_data:
                    tile = world_data[(target_x, target_y)]
                    if tile.biome != 'water' and tile.height <= 2:
                        self.set_target(target_x, target_y)
                        self.state = EntityState.MOVING
                        return
                        
    def detect_predator(self, entities: List['Entity']):
        """Detect nearby predators and start fleeing"""
        for entity in entities:
            if (entity.entity_type == EntityType.ANIMAL and 
                entity != self and 
                entity.is_alive() and
                entity.animal_type == AnimalType.CARNIVORE):
                
                distance = self.distance_to(entity)
                if distance < 8:  # Detection range
                    self.predator_target = entity
                    self.fleeing = True
                    self.flee_timer = 0
                    return
                    
    def attack_prey(self, prey: 'Entity'):
        """Attack prey"""
        if prey and prey.is_alive() and self.distance_to(prey) < 1.0:
            damage = max(1, self.stats.attack - prey.stats.defense)
            prey.take_damage(damage)
            
            if not prey.is_alive():
                # Eat the prey
                self.stats.hunger = max(0, self.stats.hunger - 50)
                self.prey_target = None
                self.state = EntityState.IDLE
                
    def eat_plant(self):
        """Eat plant food"""
        self.stats.hunger = max(0, self.stats.hunger - 30)
        
    def can_reproduce(self) -> bool:
        """Check if animal can reproduce"""
        return (self.reproduction_timer > self.reproduction_cooldown and 
                self.stats.hunger < self.stats.max_hunger * 0.3 and
                self.age > 20 and self.age < self.max_age * 0.8)
                
    def reproduce(self) -> Optional['Animal']:
        """Reproduce and create a new animal"""
        if not self.can_reproduce():
            return None
            
        # Create offspring
        offspring = Animal(
            entity_id=f"animal_{random.randint(10000, 99999)}",
            x=self.x + random.uniform(-1, 1),
            y=self.y + random.uniform(-1, 1),
            animal_type=self.animal_type
        )
        
        # Reset reproduction timer
        self.reproduction_timer = 0
        
        return offspring
        
    def get_draw_data(self) -> Dict[str, Any]:
        """Get data for drawing the animal"""
        data = super().get_draw_data()
        data.update({
            'animal_type': self.animal_type.value,
            'shape': self.shape.value,
            'age_percent': self.age / self.max_age,
            'hunger_percent': self.stats.hunger / self.stats.max_hunger,
            'fleeing': self.fleeing,
        })
        return data 