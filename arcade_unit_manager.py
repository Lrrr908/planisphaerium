##########################################################
# arcade_unit_manager.py
# Manages bipeds/units for Arcade
##########################################################

import arcade
import math
import time

class ArcadeUnitManager:
    """Manages all biped units for Arcade"""
    
    def __init__(self, scene):
        self.scene = scene
        self.selected_unit = None

    def add_unit(self, unit_sprite):
        """Add a unit to management"""
        if unit_sprite not in self.scene.biped_sprites:
            self.scene.biped_sprites.append(unit_sprite)
        print(f"[ArcadeUnitManager] Added unit: {getattr(unit_sprite, 'name', 'Unknown')}")

    def remove_unit(self, unit_sprite):
        """Remove a unit from management"""
        if unit_sprite in self.scene.biped_sprites:
            self.scene.biped_sprites.remove(unit_sprite)
        if self.selected_unit == unit_sprite:
            self.selected_unit = None
        print(f"[ArcadeUnitManager] Removed unit: {getattr(unit_sprite, 'name', 'Unknown')}")

    def select_unit_at(self, screen_x, screen_y):
        """Select a unit at screen coordinates"""
        # Convert screen to world coordinates
        world_x, world_y = self._screen_to_world(screen_x, screen_y)
        
        # Find closest unit
        closest_unit = None
        closest_distance = float('inf')
        
        for unit in self.scene.biped_sprites:
            distance = math.hypot(world_x - unit.center_x, world_y - unit.center_y)
            if distance < 30 and distance < closest_distance:  # 30 pixel selection radius
                closest_unit = unit
                closest_distance = distance
        
        if closest_unit:
            # Deselect all units
            for unit in self.scene.biped_sprites:
                if hasattr(unit, 'selected'):
                    unit.selected = False
            
            # Select the clicked unit
            closest_unit.selected = True
            self.selected_unit = closest_unit
            
            print(f"[ArcadeUnitManager] Selected unit: {getattr(closest_unit, 'name', 'Unknown')}")
            return True
        
        return False

    def deselect_all(self):
        """Deselect all units"""
        for unit in self.scene.biped_sprites:
            if hasattr(unit, 'selected'):
                unit.selected = False
        self.selected_unit = None

    def get_selected_unit(self):
        """Get the currently selected unit"""
        return self.selected_unit

    def get_selected_units(self):
        """Get all selected units"""
        return [unit for unit in self.scene.biped_sprites if getattr(unit, 'selected', False)]

    def handle_right_click(self, screen_x, screen_y):
        """Handle right-click for unit movement"""
        if hasattr(self.scene, 'movement_system'):
            self.scene.movement_system.handle_right_click_movement(screen_x, screen_y)
        else:
            # Fallback movement handling
            self._simple_movement_command(screen_x, screen_y)

    def _simple_movement_command(self, screen_x, screen_y):
        """Simple movement command fallback"""
        if self.scene.biped_sprites:
            # Get first biped (or selected biped)
            unit = self.selected_unit if self.selected_unit else self.scene.biped_sprites[0]
            
            # Convert screen to world coordinates
            world_x, world_y = self._screen_to_world(screen_x, screen_y)
            
            # Set movement target
            unit.target_x = world_x
            unit.target_y = world_y
            unit.moving = True
            if hasattr(unit, 'mission'):
                unit.mission = "MOVE_TO"
            
            print(f"[ArcadeUnitManager] Moving unit to ({world_x:.1f}, {world_y:.1f})")

    def _screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        # Get camera position
        camera_x, camera_y = self.scene.camera.position if self.scene.camera else (0, 0)
        
        # Convert to world coordinates
        world_x = screen_x + camera_x
        world_y = screen_y + camera_y
        
        return world_x, world_y

    def update(self, dt):
        """Update all units"""
        for unit in self.scene.biped_sprites:
            self._update_unit(unit, dt)

    def _update_unit(self, unit, dt):
        """Update individual unit"""
        # Handle movement
        if hasattr(unit, 'moving') and unit.moving:
            if hasattr(unit, 'target_x') and hasattr(unit, 'target_y'):
                # Calculate movement
                dx = unit.target_x - unit.center_x
                dy = unit.target_y - unit.center_y
                distance = math.hypot(dx, dy)
                
                if distance > 2:  # Still moving
                    speed = 50 * dt  # pixels per second
                    unit.center_x += (dx / distance) * speed
                    unit.center_y += (dy / distance) * speed
                else:
                    # Reached target
                    unit.center_x = unit.target_x
                    unit.center_y = unit.target_y
                    unit.moving = False
                    if hasattr(unit, 'mission'):
                        unit.mission = "IDLE"
                    
                    # Clean up movement properties
                    if hasattr(unit, 'target_x'):
                        delattr(unit, 'target_x')
                    if hasattr(unit, 'target_y'):
                        delattr(unit, 'target_y')

    def get_unit_count(self):
        """Get total number of units"""
        return len(self.scene.biped_sprites)

    def get_units_by_mission(self):
        """Get units grouped by mission"""
        missions = {}
        for unit in self.scene.biped_sprites:
            mission = getattr(unit, 'mission', 'IDLE')
            if mission not in missions:
                missions[mission] = []
            missions[mission].append(unit)
        return missions

    def get_idle_units(self):
        """Get all idle units"""
        return [unit for unit in self.scene.biped_sprites 
                if getattr(unit, 'mission', 'IDLE') == 'IDLE']

    def get_moving_units(self):
        """Get all moving units"""
        return [unit for unit in self.scene.biped_sprites 
                if getattr(unit, 'moving', False)]

    def assign_mission(self, unit, mission_type, mission_data=None):
        """Assign a mission to a unit"""
        if hasattr(unit, 'mission'):
            unit.mission = mission_type
        if hasattr(unit, 'mission_data'):
            unit.mission_data = mission_data or {}
        else:
            unit.mission_data = mission_data or {}
        
        unit.last_command_time = time.time()
        
        print(f"[ArcadeUnitManager] Assigned mission '{mission_type}' to unit {getattr(unit, 'name', 'Unknown')}")

    def cancel_unit_mission(self, unit):
        """Cancel a unit's current mission"""
        if hasattr(unit, 'mission'):
            unit.mission = "IDLE"
        if hasattr(unit, 'moving'):
            unit.moving = False
        if hasattr(unit, 'target_x'):
            delattr(unit, 'target_x')
        if hasattr(unit, 'target_y'):
            delattr(unit, 'target_y')
        
        print(f"[ArcadeUnitManager] Cancelled mission for unit {getattr(unit, 'name', 'Unknown')}")

    def get_nearest_unit_to(self, world_x, world_y):
        """Get the nearest unit to a world position"""
        if not self.scene.biped_sprites:
            return None
        
        nearest_unit = None
        nearest_distance = float('inf')
        
        for unit in self.scene.biped_sprites:
            distance = math.hypot(world_x - unit.center_x, world_y - unit.center_y)
            if distance < nearest_distance:
                nearest_unit = unit
                nearest_distance = distance
        
        return nearest_unit

    def get_units_in_area(self, center_x, center_y, radius):
        """Get all units within a radius of a point"""
        units_in_area = []
        
        for unit in self.scene.biped_sprites:
            distance = math.hypot(center_x - unit.center_x, center_y - unit.center_y)
            if distance <= radius:
                units_in_area.append(unit)
        
        return units_in_area

    def select_units_in_area(self, center_x, center_y, radius):
        """Select all units in an area"""
        units_in_area = self.get_units_in_area(center_x, center_y, radius)
        
        # Deselect all first
        self.deselect_all()
        
        # Select units in area
        for unit in units_in_area:
            unit.selected = True
        
        if units_in_area:
            self.selected_unit = units_in_area[0]  # Set first as primary selection
        
        print(f"[ArcadeUnitManager] Selected {len(units_in_area)} units in area")
        return units_in_area

    def group_move_selected_units(self, target_x, target_y):
        """Move all selected units to target area in formation"""
        selected_units = self.get_selected_units()
        
        if not selected_units:
            return
        
        # Simple formation - arrange in a grid
        formation_spacing = 30
        formation_size = int(math.ceil(math.sqrt(len(selected_units))))
        
        for i, unit in enumerate(selected_units):
            # Calculate formation offset
            row = i // formation_size
            col = i % formation_size
            
            offset_x = (col - formation_size // 2) * formation_spacing
            offset_y = (row - formation_size // 2) * formation_spacing
            
            # Set individual target
            unit.target_x = target_x + offset_x
            unit.target_y = target_y + offset_y
            unit.moving = True
            if hasattr(unit, 'mission'):
                unit.mission = "MOVE_TO"
        
        print(f"[ArcadeUnitManager] Group moving {len(selected_units)} units")

    def get_unit_stats(self):
        """Get statistics about all units"""
        stats = {
            "total_units": len(self.scene.biped_sprites),
            "selected_units": len(self.get_selected_units()),
            "idle_units": len(self.get_idle_units()),
            "moving_units": len(self.get_moving_units()),
            "missions": {}
        }
        
        # Count missions
        for unit in self.scene.biped_sprites:
            mission = getattr(unit, 'mission', 'IDLE')
            stats["missions"][mission] = stats["missions"].get(mission, 0) + 1
        
        return stats

    def heal_unit(self, unit, amount=10):
        """Heal a unit"""
        if hasattr(unit, 'health'):
            max_health = getattr(unit, 'max_health', 100)
            unit.health = min(max_health, unit.health + amount)
            print(f"[ArcadeUnitManager] Healed unit {getattr(unit, 'name', 'Unknown')} for {amount} HP")

    def damage_unit(self, unit, amount=10):
        """Damage a unit"""
        if hasattr(unit, 'health'):
            unit.health = max(0, unit.health - amount)
            if unit.health <= 0:
                unit.alive = False
                print(f"[ArcadeUnitManager] Unit {getattr(unit, 'name', 'Unknown')} has died")
            else:
                print(f"[ArcadeUnitManager] Unit {getattr(unit, 'name', 'Unknown')} took {amount} damage")

    def set_unit_speed(self, unit, speed):
        """Set unit movement speed"""
        if hasattr(unit, 'speed'):
            unit.speed = speed
        else:
            unit.speed = speed
        print(f"[ArcadeUnitManager] Set unit speed to {speed}")

    def get_unit_info(self, unit):
        """Get detailed information about a unit"""
        return {
            "name": getattr(unit, 'name', 'Unknown'),
            "position": (unit.center_x, unit.center_y),
            "grid_position": (getattr(unit, 'grid_x', 0), getattr(unit, 'grid_y', 0)),
            "health": getattr(unit, 'health', 100),
            "max_health": getattr(unit, 'max_health', 100),
            "mission": getattr(unit, 'mission', 'IDLE'),
            "moving": getattr(unit, 'moving', False),
            "selected": getattr(unit, 'selected', False),
            "creation_time": getattr(unit, 'creation_time', 0),
            "last_command_time": getattr(unit, 'last_command_time', 0),
            "unit_id": getattr(unit, 'unit_id', 'unknown')
        }

    def find_unit_by_id(self, unit_id):
        """Find a unit by its ID"""
        for unit in self.scene.biped_sprites:
            if getattr(unit, 'unit_id', None) == unit_id:
                return unit
        return None

    def validate_units(self):
        """Validate and fix unit state issues"""
        issues_fixed = 0
        
        for unit in self.scene.biped_sprites:
            # Fix missing essential properties
            if not hasattr(unit, 'health'):
                unit.health = 100
                issues_fixed += 1
            
            if not hasattr(unit, 'mission'):
                unit.mission = "IDLE"
                issues_fixed += 1
            
            if not hasattr(unit, 'moving'):
                unit.moving = False
                issues_fixed += 1
            
            if not hasattr(unit, 'selected'):
                unit.selected = False
                issues_fixed += 1
            
            # Fix corrupted movement state
            if unit.moving and not (hasattr(unit, 'target_x') and hasattr(unit, 'target_y')):
                unit.moving = False
                unit.mission = "IDLE"
                issues_fixed += 1
        
        if issues_fixed > 0:
            print(f"[ArcadeUnitManager] Fixed {issues_fixed} unit state issues")
        
        return issues_fixed

    def cleanup_dead_units(self):
        """Remove dead units from management"""
        initial_count = len(self.scene.biped_sprites)
        
        # Remove dead units
        alive_units = [unit for unit in self.scene.biped_sprites if getattr(unit, 'alive', True)]
        
        # Update sprite list
        self.scene.biped_sprites.clear()
        for unit in alive_units:
            self.scene.biped_sprites.append(unit)
        
        # Clear selected unit if it's dead
        if self.selected_unit and not getattr(self.selected_unit, 'alive', True):
            self.selected_unit = None
        
        removed_count = initial_count - len(alive_units)
        if removed_count > 0:
            print(f"[ArcadeUnitManager] Removed {removed_count} dead units")
        
        return removed_count