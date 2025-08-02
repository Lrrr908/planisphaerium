# iso_map.py - Enhanced with 9-Section Internal Subdivision
import pygame
import random
import math
from typing import List, Dict, Any
from procedural_tiles import tile_generator, TileData, SubTile

TILE_WIDTH = 64
TILE_HEIGHT = 37
STACK_OFFSET = 10
BLOCK_HEIGHT = 16  # Reduced for better performance

############################################################
# IsoObject (basic positioning)
############################################################

class IsoObject:
    def __init__(self, grid_x, grid_y, draw_order=0):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.draw_order = draw_order
        self.screen_x = 0
        self.screen_y = 0

    def calculate_screen_position(self, cam_x, cam_y, zoom_scale=1.0):
        pass

    def draw(self, surface, tree_images=None, zoom_scale=1.0):
        pass

############################################################
# ProceduralIsoTile - SIMPLIFIED for proper stepped pyramids
############################################################

class ProceduralIsoTile(IsoObject):
    """SIMPLIFIED tile that works with actual stacked blocks for stepped pyramids"""
    
    def __init__(self, grid_x, grid_y, tile_type, tile_data=None, height=0, terrain_tile=None):
        # Draw order for proper depth sorting - LOWER values so units render above
        sum_xy = grid_x + grid_y
        draw_order = sum_xy * 10 + height * 1  # Much lower base values
        super().__init__(grid_x, grid_y, draw_order)
        
        self.tile_type = tile_type
        self.tile_data = tile_data or TileData(tile_type, [])
        self.height = height
        self.cached_surface = None
        self.current_zoom = 1.0
        
        # ENHANCED: Store reference to actual terrain tile for water animation
        self._terrain_tile = terrain_tile
        
        # NEW: 9-section internal grid (3x3) for interaction - NOT VISUAL
        self.sections = self._initialize_sections()
        
    def _initialize_sections(self) -> List[List[Dict]]:
        """Initialize 9 internal sections for interaction - SIMPLIFIED"""
        sections = []
        for row in range(3):
            section_row = []
            for col in range(3):
                section_data = {
                    'exists': True,           # Whether this section exists
                    'damage': 0.0,           # Damage to this section
                    'building_type': None,   # Building placed in this section
                    'building_id': None,     # ID of building in this section
                    'special': None,         # Special properties
                    'height_offset': 0.0     # REMOVED: No height offsets - use actual layers
                }
                
                # FIXED: Check if this section should exist based on terrain tile
                if self._terrain_tile and hasattr(self._terrain_tile, 'section_data'):
                    terrain_section = self._terrain_tile.section_data.get((col, row))
                    if terrain_section:
                        section_data['exists'] = terrain_section.get('exists', True)
                
                section_row.append(section_data)
            sections.append(section_row)
        return sections
        
    def set_zoom_scale(self, zoom_scale):
        if abs(zoom_scale - self.current_zoom) > 0.1:  # Only update if significant change
            self.current_zoom = zoom_scale
            self.cached_surface = None
            
    def calculate_screen_position(self, cam_x, cam_y, zoom_scale=1.0):
        # Standard isometric position
        iso_x = (self.grid_x - self.grid_y) * (TILE_WIDTH//2) * zoom_scale
        iso_y = (self.grid_x + self.grid_y) * (TILE_HEIGHT//2) * zoom_scale
        
        # Height offset for stacking - THIS IS THE KEY FOR STEPPED PYRAMIDS
        height_offset = self.height * BLOCK_HEIGHT * zoom_scale
        
        # ENHANCED: Additional visual height offset for water animation (ONLY type 2)
        visual_offset = 0
        animated = False
        
        # Try to get animation from terrain tile reference first
        if self._terrain_tile and self.tile_type == 2:  # ONLY regular water
            if hasattr(self._terrain_tile, 'visual_height_offset'):
                visual_offset = self._terrain_tile.visual_height_offset * zoom_scale
                animated = True
                
            # Add wave bobbing animation
            if (hasattr(self._terrain_tile, 'wave_phase') and 
                hasattr(self._terrain_tile, 'wave_amplitude')):
                import math
                wave_bob = (math.sin(self._terrain_tile.wave_phase) * 
                           self._terrain_tile.wave_amplitude * zoom_scale)
                visual_offset += wave_bob
        
        # ENHANCED: Fallback animation for water tiles without terrain reference
        if not animated and self.tile_type == 2:  # ONLY regular water
            import math
            import time
            current_time = time.time()
            
            # Simple wave animation as fallback - MORE DRAMATIC
            wave_noise = math.sin(self.grid_x * 0.3 + current_time * 2.0) * math.cos(self.grid_y * 0.2 + current_time * 1.5)
            distance_wave = math.sin(math.hypot(self.grid_x - 50, self.grid_y - 50) * 0.2 - current_time * 3.0)
            
            fallback_height = (wave_noise * 1.5 + distance_wave * 1.2) * 15 * zoom_scale  # Increased amplitude
            visual_offset = fallback_height
        
        self.screen_x = iso_x + cam_x
        self.screen_y = iso_y + cam_y - height_offset - visual_offset
        
    def draw(self, surface, tree_images=None, zoom_scale=1.0):
        # SIMPLIFIED: All tiles use standard procedural generation - no complex pyramid rendering
        # The stepped pyramid effect comes from having actual separate block layers
        
        # Generate tile surface if needed - SAME AS BEFORE, single block appearance
        if self.cached_surface is None or abs(zoom_scale - self.current_zoom) > 0.1:
            self.cached_surface = tile_generator.generate_tile(
                self.tile_type, self.tile_data, zoom_scale
            )
            self.current_zoom = zoom_scale
            
        if not self.cached_surface:
            return
            
        # Draw the block - EACH BLOCK IS A SIMPLE CLEAN BLOCK
        w, h = self.cached_surface.get_size()
        draw_x = self.screen_x - w // 2
        draw_y = self.screen_y - h
        surface.blit(self.cached_surface, (draw_x, draw_y))
        
        # ENHANCED: Add foam/splash effects for water tiles (ONLY type 2)
        if (self._terrain_tile and self.tile_type == 2 and  # ONLY regular water
            hasattr(self._terrain_tile, 'foam_intensity') and 
            self._terrain_tile.foam_intensity > 0.1):
            
            self._draw_water_foam(surface, zoom_scale)

    def _draw_water_foam(self, surface, zoom_scale):
        """Draw foam/splash effects on water tiles"""
        if not self._terrain_tile:
            return
            
        foam_intensity = getattr(self._terrain_tile, 'foam_intensity', 0.0)
        if foam_intensity <= 0.1:
            return
            
        # Create foam particles
        import random
        particle_count = int(foam_intensity * 8)
        
        for _ in range(particle_count):
            # Random position around tile center
            offset_x = random.randint(-int(20 * zoom_scale), int(20 * zoom_scale))
            offset_y = random.randint(-int(10 * zoom_scale), int(10 * zoom_scale))
            
            particle_x = self.screen_x + offset_x
            particle_y = self.screen_y + offset_y
            
            # Foam color with alpha based on intensity
            alpha = int(foam_intensity * 200)
            foam_color = (255, 255, 255, alpha)
            
            # Draw small foam bubble
            radius = max(1, int(2 * zoom_scale * foam_intensity))
            
            # Create foam surface with alpha
            foam_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(foam_surface, foam_color, (radius, radius), radius)
            
            surface.blit(foam_surface, (int(particle_x - radius), int(particle_y - radius)))
    
    def damage_section(self, section_col: int, section_row: int, damage: float) -> bool:
        """Damage a specific section in the 3x3 internal grid"""
        if not (0 <= section_col < 3 and 0 <= section_row < 3):
            return False
            
        section_data = self.sections[section_row][section_col]
        section_data['damage'] += damage
        
        # Remove section if damage exceeds threshold
        if section_data['damage'] >= 100.0:
            section_data['exists'] = False
            # Clear cached surface to force regeneration
            self.cached_surface = None
            
            # SIMPLIFIED: No special pyramid mining effects - let the terrain system handle it
            print(f"[Fixed Stepped Pyramid] Mined section ({section_col}, {section_row}) - block layer updated")
            
            return True
            
        return False
    
    def get_section_mining_difficulty(self, section_col: int, section_row: int) -> float:
        """Get mining difficulty for a specific section - SIMPLIFIED"""
        if self.tile_type == 4:  # Mountain
            # Difficulty based on height - higher blocks are harder
            base_difficulty = 1.5 + (self.height * 0.3)  # Higher layers are harder
            return min(base_difficulty, 4.0)  # Cap at 4.0
        else:
            return 1.0  # Standard difficulty for non-mountains
    
    def get_section_resources(self, section_col: int, section_row: int) -> Dict[str, int]:
        """Get resources from mining a specific section - SIMPLIFIED"""
        if self.tile_type == 4:  # Mountain
            # Resources based on height - higher blocks give better rewards
            if self.height >= 6:  # High mountain layers
                return {"stone": 3, "iron_ore": 2, "coal": 1}
            elif self.height >= 3:  # Mid mountain layers
                return {"stone": 2, "iron_ore": 1}
            else:  # Low mountain layers
                return {"stone": 1, "dirt": 1}
        else:
            return {"dirt": 1}  # Default resources
    
    def get_section_at_position(self, local_x: float, local_y: float) -> tuple:
        """Get section coordinates from local position within tile"""
        # Convert local position (0.0-1.0) to section grid coordinates (0-2)
        section_col = int(local_x * 3)
        section_row = int(local_y * 3)
        
        section_col = max(0, min(2, section_col))
        section_row = max(0, min(2, section_row))
        
        return section_col, section_row
    
    def get_section_from_mouse(self, mouse_x: int, mouse_y: int, zoom_scale: float) -> tuple:
        """Get section coordinates from mouse position"""
        # Calculate relative position within the tile
        tile_width = TILE_WIDTH * zoom_scale
        tile_height = TILE_HEIGHT * zoom_scale
        
        # Mouse position relative to tile center
        rel_x = mouse_x - self.screen_x
        rel_y = mouse_y - self.screen_y
        
        # Convert to tile-local coordinates (0.0-1.0)
        if abs(rel_x) < tile_width//2 and abs(rel_y) < tile_height//2:
            # Normalize to 0.0-1.0 range
            local_x = (rel_x + tile_width//2) / tile_width
            local_y = (rel_y + tile_height//2) / tile_height
            
            return self.get_section_at_position(local_x, local_y)
        
        return None, None
    
    def has_building_in_section(self, section_col: int, section_row: int) -> bool:
        """Check if section has a building"""
        if not (0 <= section_col < 3 and 0 <= section_row < 3):
            return False
        return self.sections[section_row][section_col]['building_type'] is not None
    
    def place_building_in_section(self, section_col: int, section_row: int, building_type: str, building_id: str) -> bool:
        """Place building in specific section"""
        if not (0 <= section_col < 3 and 0 <= section_row < 3):
            return False
            
        section = self.sections[section_row][section_col]
        if not section['exists'] or section['building_type'] is not None:
            return False
            
        section['building_type'] = building_type
        section['building_id'] = building_id
        return True
    
    def remove_building_from_section(self, section_col: int, section_row: int) -> bool:
        """Remove building from specific section"""
        if not (0 <= section_col < 3 and 0 <= section_row < 3):
            return False
            
        section = self.sections[section_row][section_col]
        if section['building_type'] is None:
            return False
            
        section['building_type'] = None
        section['building_id'] = None
        return True
    
    def get_intact_sections_count(self) -> int:
        """Get number of intact (undamaged) sections"""
        count = 0
        for row in self.sections:
            for section in row:
                if section['exists'] and section['damage'] < 100.0:
                    count += 1
        return count
        
    def invalidate_cache(self):
        """Force regeneration of tile graphics"""
        self.cached_surface = None

############################################################
# ProceduralIsoMap - Same as before but with FIXED 9-section support
############################################################

class ProceduralIsoMap:
    """Enhanced isometric map with FIXED 9-section internal subdivision support"""
    
    def __init__(self, map_data, subtile_manager, terrain=None):
        self.height = len(map_data)
        self.width = len(map_data[0]) if self.height > 0 else 0
        self.camera_offset_x = 1920 // 2
        self.camera_offset_y = 1080 // 2
        self.zoom_scale = 1.0
        self.subtile_manager = subtile_manager
        self.terrain = terrain
        self._map_data_ref = map_data
        
        self.tile_objects = []
        self.tile_dict = {}
        
        # Generate block tiles - NOW PROPERLY SUPPORTS STEPPED PYRAMIDS
        self._generate_block_tiles(map_data)
        
        # Debug info
        if self.terrain and hasattr(self.terrain, 'terrain_stacks'):
            stack_count = len(self.terrain.terrain_stacks)
            total_blocks = len(self.tile_objects)
            print(f"[FIXED 9-Section IsoMap] Generated {total_blocks} blocks with 9-section subdivision from {stack_count} positions")
            print(f"[FIXED Stepped Pyramids] Mountains now render as proper stacked blocks")
        else:
            print(f"[FIXED 9-Section IsoMap] Generated {len(self.tile_objects)} tiles with 9-section subdivision (flat terrain)")
        
    def _generate_block_tiles(self, map_data):
        """Generate block tiles with FIXED 9-section internal subdivision"""
        for y in range(self.height):
            for x in range(self.width):
                tile_type = map_data[y][x]
                if tile_type == -1:
                    continue
                    
                # Get tile data from subtile manager
                tile_data = self.subtile_manager.get_tile_data(x, y)
                
                # Create stacked blocks if terrain exists - THIS CREATES THE STEPPED PYRAMIDS
                if self.terrain and hasattr(self.terrain, 'terrain_stacks'):
                    stack = self.terrain.terrain_stacks.get((x, y), [])
                    if stack:
                        # FIXED: Create a separate tile object for each layer in the stack
                        # Each layer may have different sections existing based on pyramid pattern
                        for layer_index, terrain_tile in enumerate(stack):
                            tile_obj = ProceduralIsoTile(
                                x, y, 
                                terrain_tile.tile_type, 
                                tile_data, 
                                height=layer_index,  # THIS CREATES THE STACKING
                                terrain_tile=terrain_tile  # Pass terrain tile reference
                            )
                            self.tile_objects.append(tile_obj)
                            
                            # Store the top tile for easy access
                            if layer_index == len(stack) - 1:
                                self.tile_dict[(y, x)] = tile_obj
                    else:
                        # No stack data, create single block
                        tile_obj = ProceduralIsoTile(x, y, tile_type, tile_data, height=0)
                        self.tile_objects.append(tile_obj)
                        self.tile_dict[(y, x)] = tile_obj
                else:
                    # Flat terrain - single block
                    tile_obj = ProceduralIsoTile(x, y, tile_type, tile_data, height=0)
                    self.tile_objects.append(tile_obj)
                    self.tile_dict[(y, x)] = tile_obj
                
    def set_zoom_scale(self, zoom_scale):
        self.zoom_scale = zoom_scale
        for obj in self.tile_objects:
            obj.set_zoom_scale(zoom_scale)
            
    def update_camera(self, dx, dy):
        self.camera_offset_x += dx
        self.camera_offset_y += dy
        
    def get_all_objects(self):
        return self.tile_objects
        
    def invalidate_tile(self, grid_x: int, grid_y: int):
        """Force regeneration of blocks at position"""
        # Remove all existing blocks at this position
        self.tile_objects = [obj for obj in self.tile_objects 
                           if not (obj.grid_x == grid_x and obj.grid_y == grid_y)]
        
        # Remove from tile dict
        if (grid_y, grid_x) in self.tile_dict:
            del self.tile_dict[(grid_y, grid_x)]
        
        # Regenerate blocks for this position
        tile_type = -1
        if 0 <= grid_y < self.height and 0 <= grid_x < self.width:
            if self.terrain:
                tile_type = self.terrain.get_surface_tile(grid_x, grid_y)
                if hasattr(self, '_map_data_ref') and self._map_data_ref:
                    self._map_data_ref[grid_y][grid_x] = tile_type
            elif hasattr(self, '_map_data_ref'):
                tile_type = self._map_data_ref[grid_y][grid_x]
        
        if tile_type != -1:
            tile_data = self.subtile_manager.get_tile_data(grid_x, grid_y)
            
            # Regenerate block stack if terrain exists - MAINTAINS STEPPED PYRAMID
            if self.terrain and hasattr(self.terrain, 'terrain_stacks'):
                stack = self.terrain.terrain_stacks.get((grid_x, grid_y), [])
                if stack:
                    for layer_index, terrain_tile in enumerate(stack):
                        tile_obj = ProceduralIsoTile(
                            grid_x, grid_y, 
                            terrain_tile.tile_type, 
                            tile_data, 
                            height=layer_index,  # THIS MAINTAINS THE STACKING
                            terrain_tile=terrain_tile
                        )
                        tile_obj.set_zoom_scale(self.zoom_scale)
                        self.tile_objects.append(tile_obj)
                        if layer_index == len(stack) - 1:
                            self.tile_dict[(grid_y, grid_x)] = tile_obj
            else:
                # Single flat block
                tile_obj = ProceduralIsoTile(grid_x, grid_y, tile_type, tile_data, height=0)
                tile_obj.set_zoom_scale(self.zoom_scale)
                self.tile_objects.append(tile_obj)
                self.tile_dict[(grid_y, grid_x)] = tile_obj
    
    def damage_section_at_position(self, grid_x: int, grid_y: int, local_x: float, local_y: float, damage: float) -> bool:
        """Damage a specific section within a tile"""
        tile_obj = self.tile_dict.get((grid_y, grid_x))
        if not tile_obj:
            return False
            
        section_col, section_row = tile_obj.get_section_at_position(local_x, local_y)
        return tile_obj.damage_section(section_col, section_row, damage)
    
    def get_section_from_mouse(self, mouse_x: int, mouse_y: int, grid_x: int, grid_y: int) -> tuple:
        """Get section coordinates from mouse position"""
        tile_obj = self.tile_dict.get((grid_y, grid_x))
        if not tile_obj:
            return None, None
            
        return tile_obj.get_section_from_mouse(mouse_x, mouse_y, self.zoom_scale)
            
    def get_tile_at(self, grid_x: int, grid_y: int) -> ProceduralIsoTile:
        """Get top tile object at grid position"""
        return self.tile_dict.get((grid_y, grid_x))
        
    def can_walk_to(self, from_x: int, from_y: int, to_x: int, to_y: int) -> bool:
        """Check if unit can walk between positions with height awareness"""
        if not self.terrain:
            return True
            
        try:
            from_height = self.terrain.get_height_at(from_x, from_y)
            to_height = self.terrain.get_height_at(to_x, to_y)
            
            height_diff = abs(to_height - from_height)
            
            # Can climb up 1-2 blocks, can drop down any distance
            if to_height > from_height:
                return height_diff <= 2
            else:
                return True
        except:
            return True
            
    def get_height_at(self, x: int, y: int) -> int:
        """Get terrain height for compatibility"""
        if self.terrain and hasattr(self.terrain, 'get_height_at'):
            try:
                return self.terrain.get_height_at(x, y)
            except:
                return 0
        return 0

############################################################
# IsoTree - Clean rendering without shadows (unchanged)
############################################################

class IsoTree(IsoObject):
    def __init__(self, grid_x, grid_y, tree_type, off_x, off_y, original_image=None, height=0):
        sum_xy = grid_x + grid_y
        draw_order = sum_xy * 10 + height * 1 + 20  # Above terrain but below units
        super().__init__(grid_x, grid_y, draw_order)

        self.tree_type = tree_type
        self.off_x = off_x
        self.off_y = off_y
        self.height = height
        self.original_image = original_image
        self.scaled_image = original_image

    def set_zoom_scale(self, zoom_scale):
        if self.original_image:
            ow = self.original_image.get_width()
            oh = self.original_image.get_height()
            sw = max(1, int(ow * zoom_scale))
            sh = max(1, int(oh * zoom_scale))
            self.scaled_image = pygame.transform.smoothscale(
                self.original_image, (sw, sh)
            )
        else:
            self.scaled_image = None

    def calculate_screen_position(self, cam_x, cam_y, zoom_scale=1.0):
        # Standard isometric position
        iso_x = (self.grid_x - self.grid_y) * (TILE_WIDTH//2) * zoom_scale
        iso_y = (self.grid_x + self.grid_y) * (TILE_HEIGHT//2) * zoom_scale
        
        # Add offset
        sx = int(self.off_x * zoom_scale)
        sy = int(self.off_y * zoom_scale)
        
        # Height offset for stacked terrain
        height_offset = self.height * BLOCK_HEIGHT * zoom_scale
        
        self.screen_x = iso_x + cam_x + sx
        self.screen_y = iso_y + cam_y + sy - height_offset

    def draw(self, surface, tree_images=None, zoom_scale=1.0):
        if self.scaled_image:
            w = self.scaled_image.get_width()
            h = self.scaled_image.get_height()
            
            # Draw tree (no shadow)
            draw_x = self.screen_x - w // 2
            draw_y = self.screen_y - h
            surface.blit(self.scaled_image, (draw_x, draw_y))
        else:
            if tree_images:
                img = tree_images.get(self.tree_type, None)
                if img:
                    w = img.get_width()
                    h = img.get_height()
                    
                    # Draw tree (no shadow)
                    draw_x = self.screen_x - w // 2
                    draw_y = self.screen_y - h
                    surface.blit(img, (draw_x, draw_y))

############################################################
# Simplified Systems (unchanged but compatible with FIXED pyramids)
############################################################

class LayeredWaterSystem:
    """Enhanced water animation system with dynamic water integration"""
    
    def __init__(self, terrain):
        self.terrain = terrain
        self.wave_time = 0.0
        self.wave_speed = 2.0
        
    def update_water_animation(self, dt: float):
        """Enhanced water animation with dynamic water physics"""
        # If terrain has dynamic water system, update it
        if hasattr(self.terrain, 'water_system') and self.terrain.water_system:
            self.terrain.water_system.update_water_dynamics(dt)
        else:
            # Fallback to simple wave animation
            self._simple_water_animation(dt)
    
    def _simple_water_animation(self, dt: float):
        """Simple subterranean water animation for fallback"""
        import math
        self.wave_time += dt * 0.001 * self.wave_speed
        
        # Simple wave animation - much faster
        cx, cy = self.terrain.width // 2, self.terrain.height // 2
        
        # ENHANCED: Update ALL water tiles (ONLY type 2) with subterranean constraints
        water_tiles_updated = 0
        for (x, y), tile_stack in self.terrain.terrain_stacks.items():
            # Calculate land surface height for constraints
            land_height = 0
            for i in range(len(tile_stack) - 1, -1, -1):
                if tile_stack[i].tile_type != 2:  # Not water
                    land_height = i + 1
                    break
            
            for i, tile in enumerate(tile_stack):
                if tile.tile_type == 2:  # ONLY regular water
                    # ENHANCED: Apply constrained visual animation
                    dist = math.hypot(x - cx, y - cy)
                    
                    # Constrained wave motion for subterranean water
                    wave_height = math.sin(self.wave_time + dist * 0.5) * 2.0  # Reduced amplitude
                    secondary_wave = math.cos(x * 0.4 + self.wave_time * 2.0) * math.sin(y * 0.3 + self.wave_time * 1.5) * 1.5  # Reduced amplitude
                    
                    # CRITICAL: Constrain to stay below surface
                    max_offset = max(0, land_height - i - 1) * 5  # Stay below land
                    constrained_height = min(wave_height + secondary_wave, max_offset)
                    
                    tile.visual_height_offset = max(constrained_height, -15)  # Allow going deeper
                    tile.wave_phase = self.wave_time + dist * 0.2
                    tile.wave_amplitude = min(2.0, max_offset / 3)  # Constrained amplitude
                    tile.foam_intensity = 0.0  # No foam in simple mode
                    
                    # Keep tile as regular water
                    tile.tile_type = 2  # Always regular water
                    
                    water_tiles_updated += 1
                    break  # Only update first water tile in stack
        
        # Debug output occasionally
        if int(self.wave_time * 10) % 300 == 0:
            print(f"[SubterraneanWaterAnimation] Updated {water_tiles_updated} underground water tiles")
    
    def create_water_splash(self, x: int, y: int, intensity: float = 1.0):
        """Create splash effect in dynamic water"""
        if hasattr(self.terrain, 'water_system') and self.terrain.water_system:
            self.terrain.water_system.create_splash(x, y, intensity)
    
    def get_water_height(self, x: int, y: int) -> float:
        """Get current water height at position"""
        if hasattr(self.terrain, 'water_system') and self.terrain.water_system:
            return self.terrain.water_system.get_water_height_at(x, y)
        return 0.0

class LayeredResourceSystem:
    """Enhanced resource system for 9-section mining with FIXED pyramid mountains"""
    
    def __init__(self, terrain):
        self.terrain = terrain
        
    def can_biped_dig(self, biped_unit, target_x: int, target_y: int) -> bool:
        """Simple dig check"""
        if abs(target_x - biped_unit.grid_x) > 1 or abs(target_y - biped_unit.grid_y) > 1:
            return False
        return True
    
    def dig_section(self, biped_unit, target_x: int, target_y: int, section_col: int, section_row: int) -> bool:
        """Dig specific section of a tile (for FIXED pyramid mountains)"""
        # Get the tile object from the terrain's map
        if not hasattr(self.terrain, 'map'):
            # Try to find the scene through terrain
            scene = getattr(self.terrain, 'scene', None)
            if scene and hasattr(scene, 'map'):
                tile_obj = scene.map.get_tile_at(target_x, target_y)
            else:
                return False
        else:
            tile_obj = self.terrain.map.get_tile_at(target_x, target_y)
            
        if not tile_obj:
            return False
        
        # Check mining difficulty for this section
        difficulty = tile_obj.get_section_mining_difficulty(section_col, section_row)
        tool_power = self._get_biped_tool_power(biped_unit)
        
        if tool_power < difficulty:
            print(f"[FIXED Stepped Pyramid Mining] Tool too weak for block layer {tile_obj.height} section ({section_col}, {section_row}) - need {difficulty}, have {tool_power}")
            return False
        
        # Mine the section
        success = tile_obj.damage_section(section_col, section_row, 100.0)  # Full damage to remove
        
        if success:
            # Give section-specific resources
            resources = tile_obj.get_section_resources(section_col, section_row)
            
            if not hasattr(biped_unit, 'inventory'):
                biped_unit.inventory = {}
                
            for resource, amount in resources.items():
                biped_unit.inventory[resource] = biped_unit.inventory.get(resource, 0) + amount
            
            print(f"[FIXED Stepped Pyramid Mining] Mined layer {tile_obj.height} section ({section_col}, {section_row}) at ({target_x}, {target_y}), got: {resources}")
            return True
        
        return False
    
    def _get_biped_tool_power(self, biped_unit) -> float:
        """Get tool power for mining"""
        if not hasattr(biped_unit, 'inventory'):
            return 1.0
            
        tool = biped_unit.inventory.get("equipped_tool", "hands")
        if tool == "hands":
            return 1.0
        elif "pickaxe" in tool.lower():
            return 3.0
        elif "shovel" in tool.lower():
            return 2.0
        else:
            return 1.5
        
    def dig_tile(self, biped_unit, target_x: int, target_y: int) -> bool:
        """Enhanced digging for FIXED 9-section system - whole tile"""
        stack = self.terrain.terrain_stacks.get((target_x, target_y), [])
        if not stack or len(stack) <= 1:
            return False
            
        # Remove top block (all 9 sections)
        top_tile = stack.pop()
        
        # Give enhanced resources based on tile type and height
        base_resources = {"dirt": 1}
        if top_tile.tile_type == 4:  # Mountain - height-based rewards
            # Higher blocks give better rewards
            stone_amount = 3 + top_tile.height  # More stone from higher blocks
            base_resources = {"stone": stone_amount, "iron_ore": max(1, top_tile.height // 2), "dirt": 2}
        elif top_tile.tile_type == 1:  # Grass
            base_resources = {"dirt": 2, "grass": 1}
        elif top_tile.tile_type == 11:  # Desert
            base_resources = {"sand": 2, "dirt": 1}
            
        # 9 sections = 3x resources (balanced)
        multiplied_resources = {k: v * 3 for k, v in base_resources.items()}
        
        if not hasattr(biped_unit, 'inventory'):
            biped_unit.inventory = {}
            
        for resource, amount in multiplied_resources.items():
            biped_unit.inventory[resource] = biped_unit.inventory.get(resource, 0) + amount
            
        # Update terrain maps
        if stack:
            self.terrain.surface_map[target_y][target_x] = stack[-1].tile_type
            self.terrain.height_map[target_y][target_x] = len(stack)
        else:
            # Add bedrock
            from map_generation import TerrainTile
            bedrock_tile = TerrainTile(
                tile_type=3, height=0, x=target_x, y=target_y, sub_tiles={}
            )
            stack.append(bedrock_tile)
            self.terrain.surface_map[target_y][target_x] = 3
            self.terrain.height_map[target_y][target_x] = 1
        
        print(f"[FIXED 9-Section Mining] Dug whole block layer {top_tile.height} at ({target_x}, {target_y}), got: {multiplied_resources}")
        return True