"""
Entity System
Base classes for all game entities (bipeds, animals, buildings, etc.)
"""

import math
import random
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
from ..core.constants import *

class EntityType(Enum):
    """Entity types"""
    BIPED = "biped"
    ANIMAL = "animal"
    BUILDING = "building"
    VEHICLE = "vehicle"
    SHIP = "ship"

class EntityState(Enum):
    """Entity states"""
    IDLE = "idle"
    MOVING = "moving"
    WORKING = "working"
    ATTACKING = "attacking"
    EATING = "eating"
    SLEEPING = "sleeping"
    DEAD = "dead"

@dataclass
class EntityStats:
    """Entity statistics"""
    health: int = 100
    max_health: int = 100
    hunger: int = 0
    max_hunger: int = 100
    energy: int = 100
    max_energy: int = 100
    speed: float = 1.0
    attack: int = 10
    defense: int = 5

class Entity:
    """Base class for all game entities"""
    
    def __init__(self, entity_id: str, entity_type: EntityType, x: float, y: float):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.state = EntityState.IDLE
        self.stats = EntityStats()
        self.path = []
        self.path_index = 0
        self.animation_frame = 0
        self.animation_timer = 0
        self.color = (255, 255, 255)
        self.size = 1.0
        self.selected = False
        
    def update(self, delta_time: float, world_data: Dict[Tuple[int, int], 'Tile']):
        """Update entity logic"""
        self.animation_timer += delta_time
        
        # Update animation
        if self.animation_timer > 0.1:  # 10 FPS animation
            self.animation_frame = (self.animation_frame + 1) % 4
            self.animation_timer = 0
            
        # Update movement
        if self.state == EntityState.MOVING and self.path:
            self.update_movement(delta_time)
            
    def update_movement(self, delta_time: float):
        """Update entity movement along path"""
        if not self.path or self.path_index >= len(self.path):
            self.state = EntityState.IDLE
            return
            
        # Get current target
        target_x, target_y = self.path[self.path_index]
        
        # Calculate direction
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance < 0.1:  # Close enough to target
            self.path_index += 1
            if self.path_index >= len(self.path):
                self.state = EntityState.IDLE
                return
            target_x, target_y = self.path[self.path_index]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.sqrt(dx * dx + dy * dy)
            
        # Move towards target
        if distance > 0:
            speed = self.stats.speed * delta_time
            move_distance = min(speed, distance)
            
            self.x += (dx / distance) * move_distance
            self.y += (dy / distance) * move_distance
            
    def set_path(self, path: List[Tuple[int, int]]):
        """Set movement path"""
        self.path = path
        self.path_index = 0
        if path:
            self.state = EntityState.MOVING
        else:
            self.state = EntityState.IDLE
            
    def set_target(self, x: float, y: float):
        """Set target position"""
        self.target_x = x
        self.target_y = y
        
    def get_position(self) -> Tuple[float, float]:
        """Get current position"""
        return (self.x, self.y)
        
    def get_grid_position(self) -> Tuple[int, int]:
        """Get current grid position"""
        return (int(self.x), int(self.y))
        
    def distance_to(self, other: 'Entity') -> float:
        """Calculate distance to another entity"""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)
        
    def is_at_position(self, x: float, y: float, tolerance: float = 0.5) -> bool:
        """Check if entity is at a specific position"""
        dx = self.x - x
        dy = self.y - y
        return math.sqrt(dx * dx + dy * dy) < tolerance
        
    def take_damage(self, damage: int):
        """Take damage"""
        self.stats.health = max(0, self.stats.health - damage)
        if self.stats.health <= 0:
            self.state = EntityState.DEAD
            
    def heal(self, amount: int):
        """Heal entity"""
        self.stats.health = min(self.stats.max_health, self.stats.health + amount)
        
    def add_hunger(self, amount: int):
        """Add hunger"""
        self.stats.hunger = min(self.stats.max_hunger, self.stats.hunger + amount)
        
    def eat(self, amount: int):
        """Eat to reduce hunger"""
        self.stats.hunger = max(0, self.stats.hunger - amount)
        
    def is_alive(self) -> bool:
        """Check if entity is alive"""
        return self.state != EntityState.DEAD and self.stats.health > 0
        
    def is_hungry(self) -> bool:
        """Check if entity is hungry"""
        return self.stats.hunger > self.stats.max_hunger * 0.7
        
    def select(self):
        """Select this entity"""
        self.selected = True
        
    def deselect(self):
        """Deselect this entity"""
        self.selected = False
        
    def get_draw_data(self) -> Dict[str, Any]:
        """Get data for drawing the entity"""
        return {
            'x': self.x,
            'y': self.y,
            'color': self.color,
            'size': self.size,
            'selected': self.selected,
            'animation_frame': self.animation_frame,
            'state': self.state.value
        } 