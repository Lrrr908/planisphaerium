"""
Biped Entity
Player-controlled humanoid characters - Zelda Style
"""

import random
import math
import arcade
from typing import List, Tuple, Optional, Dict, Any
from .entity import Entity, EntityType, EntityState, EntityStats
from enum import Enum

class BipedJob(Enum):
    """Biped job types"""
    WORKER = "worker"
    BUILDER = "builder"
    FARMER = "farmer"
    HUNTER = "hunter"
    SCIENTIST = "scientist"
    SOLDIER = "soldier"

class AnimationState(Enum):
    """Animation states for bipeds"""
    IDLE = "idle"
    WALKING = "walking"
    WORKING = "working"
    ATTACKING = "attacking"
    GATHERING = "gathering"

class Biped(Entity):
    """Biped entity - player-controlled humanoid characters with Zelda-style appearance"""
    
    def __init__(self, entity_id: str, x: float, y: float, job: BipedJob = BipedJob.WORKER):
        super().__init__(entity_id, EntityType.BIPED, x, y)
        
        # Biped-specific properties
        self.job = job
        self.inventory = {}
        self.current_task = None
        self.task_progress = 0.0
        self.task_target = None
        self.home_position = (x, y)
        self.work_position = None
        
        # Animation properties
        self.animation_state = AnimationState.IDLE
        self.animation_frame = 0.0
        self.animation_speed = 2.0
        self.facing_direction = 1  # 1 for right, -1 for left
        self.bob_offset = 0.0
        
        # Visual properties
        self.base_colors = self.get_job_colors()
        self.size = 12  # Increased size for better detail
        self.scale = 1.0
        
        # Set stats based on job
        self.setup_job_stats()
        
    def setup_job_stats(self):
        """Set up stats based on job"""
        if self.job == BipedJob.WORKER:
            self.stats = EntityStats(speed=1.2, attack=8, defense=5)
        elif self.job == BipedJob.BUILDER:
            self.stats = EntityStats(speed=1.0, attack=6, defense=4)
        elif self.job == BipedJob.FARMER:
            self.stats = EntityStats(speed=1.1, attack=5, defense=3)
        elif self.job == BipedJob.HUNTER:
            self.stats = EntityStats(speed=1.5, attack=15, defense=8)
        elif self.job == BipedJob.SCIENTIST:
            self.stats = EntityStats(speed=0.9, attack=3, defense=2)
        elif self.job == BipedJob.SOLDIER:
            self.stats = EntityStats(speed=1.3, attack=20, defense=15)
            
    def get_job_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Get color scheme based on job"""
        color_schemes = {
            BipedJob.WORKER: {
                'skin': (255, 220, 177),
                'hair': (139, 69, 19),
                'shirt': (100, 149, 237),
                'pants': (139, 131, 120),
                'tool': (169, 169, 169),
                'accent': (255, 255, 255)
            },
            BipedJob.BUILDER: {
                'skin': (255, 220, 177),
                'hair': (160, 82, 45),
                'shirt': (255, 140, 0),
                'pants': (101, 67, 33),
                'tool': (192, 192, 192),
                'accent': (255, 215, 0)
            },
            BipedJob.FARMER: {
                'skin': (255, 220, 177),
                'hair': (218, 165, 32),
                'shirt': (34, 139, 34),
                'pants': (160, 82, 45),
                'tool': (139, 69, 19),
                'accent': (255, 255, 0)
            },
            BipedJob.HUNTER: {
                'skin': (222, 184, 135),
                'hair': (139, 69, 19),
                'shirt': (139, 69, 19),
                'pants': (85, 107, 47),
                'tool': (160, 82, 45),
                'accent': (34, 139, 34)
            },
            BipedJob.SCIENTIST: {
                'skin': (255, 220, 177),
                'hair': (192, 192, 192),
                'shirt': (255, 255, 255),
                'pants': (25, 25, 112),
                'tool': (138, 43, 226),
                'accent': (0, 255, 255)
            },
            BipedJob.SOLDIER: {
                'skin': (255, 220, 177),
                'hair': (139, 69, 19),
                'shirt': (220, 20, 60),
                'pants': (47, 79, 79),
                'tool': (169, 169, 169),
                'accent': (255, 215, 0)
            }
        }
        return color_schemes.get(self.job, color_schemes[BipedJob.WORKER])
        
    def update(self, delta_time: float, world_data: Dict[Tuple[int, int], 'Tile']):
        """Update biped logic and animations"""
        super().update(delta_time, world_data)
        
        # Update animation
        self.update_animation(delta_time)
        
        # Update hunger
        self.stats.hunger = min(self.stats.max_hunger, self.stats.hunger + delta_time * 2)
        
        # Update energy
        if self.state == EntityState.WORKING:
            self.stats.energy = max(0, self.stats.energy - delta_time * 5)
        else:
            self.stats.energy = min(self.stats.max_energy, self.stats.energy + delta_time * 2)
            
        # Handle current task
        if self.current_task:
            self.update_task(delta_time, world_data)
        else:
            # Find new task if idle
            self.find_new_task(world_data)
            
    def update_animation(self, delta_time: float):
        """Update animation state and frame"""
        # Update animation frame
        self.animation_frame += delta_time * self.animation_speed
        
        # Update animation state based on entity state
        if self.state == EntityState.MOVING:
            self.animation_state = AnimationState.WALKING
            self.animation_speed = 4.0
        elif self.state == EntityState.WORKING:
            if self.current_task and self.current_task.get('type') == 'gather':
                self.animation_state = AnimationState.GATHERING
            else:
                self.animation_state = AnimationState.WORKING
            self.animation_speed = 3.0
        elif self.state == EntityState.ATTACKING:
            self.animation_state = AnimationState.ATTACKING
            self.animation_speed = 6.0
        else:
            self.animation_state = AnimationState.IDLE
            self.animation_speed = 1.0
            
        # Update facing direction based on movement
        if hasattr(self, 'velocity_x') and abs(self.velocity_x) > 0.1:
            self.facing_direction = 1 if self.velocity_x > 0 else -1
            
        # Update bobbing for walking
        if self.animation_state == AnimationState.WALKING:
            self.bob_offset = math.sin(self.animation_frame * 3) * 1.5
        else:
            self.bob_offset = 0
            
    def draw_character(self, x: float, y: float):
        """Draw the Zelda-style character"""
        # Apply bobbing offset
        draw_y = y + self.bob_offset
        
        # Get animation offsets
        arm_swing = math.sin(self.animation_frame) * 3 if self.animation_state == AnimationState.WALKING else 0
        work_offset = math.sin(self.animation_frame * 2) * 1.5 if self.animation_state == AnimationState.WORKING else 0
        
        # Scale and facing direction
        face_scale = self.facing_direction
        
        # Draw shadow
        shadow_color = (50, 50, 50, 100)
        arcade.draw_ellipse_filled(x, y - self.size * 0.8, 
                                 self.size * 1.2, self.size * 0.4, 
                                 shadow_color)
        
        # Body parts coordinates
        head_y = draw_y + self.size * 0.3
        body_y = draw_y - self.size * 0.1
        leg_y = draw_y - self.size * 0.6
        
        # Draw legs
        self.draw_legs(x, leg_y, face_scale)
        
        # Draw body
        self.draw_body(x, body_y, work_offset)
        
        # Draw arms
        self.draw_arms(x, body_y, face_scale, arm_swing, work_offset)
        
        # Draw head
        self.draw_head(x, head_y, face_scale)
        
        # Draw job-specific accessories
        self.draw_accessories(x, draw_y, face_scale)
        
        # Draw health bar if damaged
        if self.stats.health < self.stats.max_health:
            self.draw_health_bar(x, draw_y + self.size + 8)
            
    def draw_head(self, x: float, y: float, face_scale: float):
        """Draw character head"""
        colors = self.base_colors
        head_size = self.size * 0.35
        
        # Head (circle)
        arcade.draw_circle_filled(x, y, head_size, colors['skin'])
        arcade.draw_circle_outline(x, y, head_size, (0, 0, 0), 1)
        
        # Hair
        hair_points = [
            (x - head_size * 0.8, y + head_size * 0.3),
            (x - head_size * 0.6, y + head_size * 0.9),
            (x, y + head_size * 0.8),
            (x + head_size * 0.6, y + head_size * 0.9),
            (x + head_size * 0.8, y + head_size * 0.3),
        ]
        arcade.draw_polygon_filled(hair_points, colors['hair'])
        
        # Eyes
        eye_offset = head_size * 0.2 * face_scale
        arcade.draw_circle_filled(x - eye_offset, y + head_size * 0.1, 2, (0, 0, 0))
        arcade.draw_circle_filled(x + eye_offset, y + head_size * 0.1, 2, (0, 0, 0))
        
        # Mouth (small line)
        if self.animation_state == AnimationState.WORKING:
            # Concentrated expression
            arcade.draw_line(x - 3, y - head_size * 0.2, x + 3, y - head_size * 0.2, (0, 0, 0), 1)
        else:
            # Happy dot
            arcade.draw_circle_filled(x, y - head_size * 0.2, 1, (0, 0, 0))
            
    def draw_body(self, x: float, y: float, work_offset: float):
        """Draw character body"""
        colors = self.base_colors
        body_width = self.size * 0.4
        body_height = self.size * 0.5
        
        # Shirt (rectangle with rounded top)
        shirt_y = y + work_offset * 0.5
        arcade.draw_rectangle_filled(x, shirt_y, body_width, body_height, colors['shirt'])
        arcade.draw_rectangle_outline(x, shirt_y, body_width, body_height, (0, 0, 0), 1)
        
        # Shirt details (buttons or patterns)
        if self.job == BipedJob.SCIENTIST:
            # Lab coat buttons
            for i in range(3):
                button_y = shirt_y + body_height * 0.2 - i * body_height * 0.2
                arcade.draw_circle_filled(x, button_y, 1, colors['accent'])
        elif self.job == BipedJob.SOLDIER:
            # Military stripes
            for i in range(2):
                stripe_y = shirt_y + body_height * 0.1 - i * 3
                arcade.draw_rectangle_filled(x - body_width * 0.3, stripe_y, body_width * 0.6, 1, colors['accent'])
                
    def draw_arms(self, x: float, y: float, face_scale: float, arm_swing: float, work_offset: float):
        """Draw character arms"""
        colors = self.base_colors
        arm_length = self.size * 0.3
        arm_width = self.size * 0.15
        
        # Left arm
        left_arm_x = x - self.size * 0.25
        left_arm_angle = arm_swing if self.animation_state == AnimationState.WALKING else work_offset
        left_end_x = left_arm_x + math.cos(math.radians(left_arm_angle - 45)) * arm_length
        left_end_y = y - arm_length * 0.5 + math.sin(math.radians(left_arm_angle - 45)) * arm_length
        
        arcade.draw_line(left_arm_x, y, left_end_x, left_end_y, colors['skin'], int(arm_width))
        
        # Right arm
        right_arm_x = x + self.size * 0.25
        right_arm_angle = -arm_swing if self.animation_state == AnimationState.WALKING else -work_offset
        right_end_x = right_arm_x + math.cos(math.radians(right_arm_angle - 135)) * arm_length
        right_end_y = y - arm_length * 0.5 + math.sin(math.radians(right_arm_angle - 135)) * arm_length
        
        arcade.draw_line(right_arm_x, y, right_end_x, right_end_y, colors['skin'], int(arm_width))
        
        # Hands
        arcade.draw_circle_filled(left_end_x, left_end_y, arm_width * 0.6, colors['skin'])
        arcade.draw_circle_filled(right_end_x, right_end_y, arm_width * 0.6, colors['skin'])
        
    def draw_legs(self, x: float, y: float, face_scale: float):
        """Draw character legs"""
        colors = self.base_colors
        leg_width = self.size * 0.2
        leg_height = self.size * 0.4
        
        # Walking animation
        if self.animation_state == AnimationState.WALKING:
            left_offset = math.sin(self.animation_frame) * 3
            right_offset = -math.sin(self.animation_frame) * 3
        else:
            left_offset = 0
            right_offset = 0
            
        # Left leg (pants)
        left_leg_x = x - self.size * 0.15
        arcade.draw_rectangle_filled(left_leg_x + left_offset, y, leg_width, leg_height, colors['pants'])
        arcade.draw_rectangle_outline(left_leg_x + left_offset, y, leg_width, leg_height, (0, 0, 0), 1)
        
        # Right leg (pants)
        right_leg_x = x + self.size * 0.15
        arcade.draw_rectangle_filled(right_leg_x + right_offset, y, leg_width, leg_height, colors['pants'])
        arcade.draw_rectangle_outline(right_leg_x + right_offset, y, leg_width, leg_height, (0, 0, 0), 1)
        
        # Feet
        foot_y = y - leg_height * 0.6
        arcade.draw_ellipse_filled(left_leg_x + left_offset, foot_y, leg_width * 1.3, leg_width * 0.7, (139, 69, 19))
        arcade.draw_ellipse_filled(right_leg_x + right_offset, foot_y, leg_width * 1.3, leg_width * 0.7, (139, 69, 19))
        
    def draw_accessories(self, x: float, y: float, face_scale: float):
        """Draw job-specific accessories"""
        colors = self.base_colors
        
        if self.job == BipedJob.FARMER:
            # Straw hat
            hat_y = y + self.size * 0.6
            arcade.draw_ellipse_filled(x, hat_y, self.size * 0.8, self.size * 0.2, colors['tool'])
            arcade.draw_circle_filled(x, hat_y, self.size * 0.3, colors['tool'])
            
        elif self.job == BipedJob.HUNTER:
            # Quiver
            quiver_x = x + self.size * 0.4 * face_scale
            quiver_y = y + self.size * 0.1
            arcade.draw_rectangle_filled(quiver_x, quiver_y, 4, self.size * 0.6, colors['tool'])
            # Arrows
            for i in range(3):
                arrow_y = quiver_y + self.size * 0.2 - i * 3
                arcade.draw_circle_filled(quiver_x, arrow_y, 1, colors['accent'])
                
        elif self.job == BipedJob.SCIENTIST:
            # Goggles
            goggle_y = y + self.size * 0.35
            arcade.draw_circle_outline(x - 4, goggle_y, 3, colors['tool'], 2)
            arcade.draw_circle_outline(x + 4, goggle_y, 3, colors['tool'], 2)
            arcade.draw_line(x - 1, goggle_y, x + 1, goggle_y, colors['tool'], 1)
            
        elif self.job == BipedJob.SOLDIER:
            # Helmet
            helmet_y = y + self.size * 0.4
            arcade.draw_arc_filled(x, helmet_y, self.size * 0.8, self.size * 0.6, 
                                 colors['tool'], 0, 180)
                                 
        elif self.job == BipedJob.BUILDER:
            # Hard hat
            hat_y = y + self.size * 0.5
            arcade.draw_circle_filled(x, hat_y, self.size * 0.3, colors['accent'])
            arcade.draw_circle_outline(x, hat_y, self.size * 0.3, (0, 0, 0), 1)
            
    def draw_health_bar(self, x: float, y: float):
        """Draw health bar above character"""
        bar_width = self.size * 1.2
        bar_height = 4
        health_percent = self.stats.health / self.stats.max_health
        
        # Background
        arcade.draw_rectangle_filled(x, y, bar_width, bar_height, (100, 100, 100))
        
        # Health fill
        if health_percent > 0.6:
            color = (0, 255, 0)  # Green
        elif health_percent > 0.3:
            color = (255, 255, 0)  # Yellow
        else:
            color = (255, 0, 0)  # Red
            
        fill_width = bar_width * health_percent
        arcade.draw_rectangle_filled(x - bar_width/2 + fill_width/2, y, fill_width, bar_height, color)
        
        # Border
        arcade.draw_rectangle_outline(x, y, bar_width, bar_height, (0, 0, 0), 1)
        
    def update_task(self, delta_time: float, world_data: Dict[Tuple[int, int], 'Tile']):
        """Update current task progress"""
        if not self.current_task:
            return
            
        task_type = self.current_task.get('type')
        
        if task_type == 'move_to':
            # Task is complete when we reach the target
            if self.is_at_position(self.task_target[0], self.task_target[1]):
                self.complete_task()
                
        elif task_type == 'gather':
            # Gather resources
            self.task_progress += delta_time
            if self.task_progress >= 2.0:  # 2 seconds to gather
                self.gather_resource()
                self.complete_task()
                
        elif task_type == 'build':
            # Build something
            self.task_progress += delta_time
            if self.task_progress >= 5.0:  # 5 seconds to build
                self.build_structure()
                self.complete_task()
                
        elif task_type == 'hunt':
            # Hunt animals
            if self.task_target and isinstance(self.task_target, Entity):
                if self.distance_to(self.task_target) < 1.0:
                    self.attack_target(self.task_target)
                    if not self.task_target.is_alive():
                        self.complete_task()
                        
    def find_new_task(self, world_data: Dict[Tuple[int, int], 'Tile']):
        """Find a new task based on job and current state"""
        if self.is_hungry():
            # Find food
            food_target = self.find_nearest_food(world_data)
            if food_target:
                self.set_task('gather', food_target)
                return
                
        if self.stats.energy < 20:
            # Go home to rest
            self.set_task('move_to', self.home_position)
            return
            
        # Job-specific tasks
        if self.job == BipedJob.HUNTER:
            animal_target = self.find_nearest_animal(world_data)
            if animal_target:
                self.set_task('hunt', animal_target)
                return
                
        elif self.job == BipedJob.FARMER:
            # Find farm work
            pass
            
        elif self.job == BipedJob.BUILDER:
            # Find building work
            pass
            
        # Default: wander around
        if random.random() < 0.1:  # 10% chance to wander
            self.wander(world_data)
            
    def set_task(self, task_type: str, target):
        """Set a new task"""
        self.current_task = {
            'type': task_type,
            'target': target
        }
        self.task_progress = 0.0
        self.task_target = target
        
        if task_type == 'move_to':
            self.state = EntityState.MOVING
        elif task_type in ['gather', 'build']:
            self.state = EntityState.WORKING
        elif task_type == 'hunt':
            self.state = EntityState.ATTACKING
            
    def complete_task(self):
        """Complete current task"""
        self.current_task = None
        self.task_progress = 0.0
        self.task_target = None
        self.state = EntityState.IDLE
        
    def find_nearest_food(self, world_data: Dict[Tuple[int, int], 'Tile']) -> Optional[Tuple[int, int]]:
        """Find nearest food source"""
        current_pos = self.get_grid_position()
        
        # Search in expanding circles
        for distance in range(1, 20):
            for dx in range(-distance, distance + 1):
                for dy in range(-distance, distance + 1):
                    if abs(dx) + abs(dy) == distance:
                        check_x, check_y = current_pos[0] + dx, current_pos[1] + dy
                        if (check_x, check_y) in world_data:
                            tile = world_data[(check_x, check_y)]
                            if tile.has_resource or tile.biome in ['forest', 'grassland']:
                                return (check_x, check_y)
        return None
        
    def find_nearest_animal(self, world_data: Dict[Tuple[int, int], 'Tile']) -> Optional['Entity']:
        """Find nearest animal to hunt"""
        # This would need access to the entity manager
        # For now, return None
        return None
        
    def gather_resource(self):
        """Gather resources from current position"""
        # Add resources to inventory
        resource_type = random.choice(['food', 'wood', 'stone'])
        if resource_type not in self.inventory:
            self.inventory[resource_type] = 0
        self.inventory[resource_type] += random.randint(1, 3)
        
    def build_structure(self):
        """Build a structure"""
        # This would create a building entity
        pass
        
    def attack_target(self, target: 'Entity'):
        """Attack a target entity"""
        if target and target.is_alive():
            damage = max(1, self.stats.attack - target.stats.defense)
            target.take_damage(damage)
            
    def wander(self, world_data: Dict[Tuple[int, int], 'Tile']):
        """Wander to a random nearby location"""
        current_pos = self.get_grid_position()
        
        # Find a random walkable position within 10 tiles
        for _ in range(10):
            dx = random.randint(-5, 5)
            dy = random.randint(-5, 5)
            target_x, target_y = current_pos[0] + dx, current_pos[1] + dy
            
            if (target_x, target_y) in world_data:
                tile = world_data[(target_x, target_y)]
                if tile.biome != 'water' and tile.height <= 2:
                    self.set_task('move_to', (target_x, target_y))
                    return
                    
    def change_job(self, new_job: BipedJob):
        """Change biped's job"""
        self.job = new_job
        self.setup_job_stats()
        self.base_colors = self.get_job_colors()
        
    def get_draw_data(self) -> Dict[str, Any]:
        """Get data for drawing the biped"""
        data = super().get_draw_data()
        data.update({
            'job': self.job.value,
            'health_percent': self.stats.health / self.stats.max_health,
            'hunger_percent': self.stats.hunger / self.stats.max_hunger,
            'energy_percent': self.stats.energy / self.stats.max_energy,
            'animation_state': self.animation_state.value,
            'facing_direction': self.facing_direction,
        })
        return data