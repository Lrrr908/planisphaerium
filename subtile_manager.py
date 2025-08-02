# subtile_manager.py - Enhanced for FIXED 9-Section Stepped Pyramids
import pygame
import random
import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from procedural_tiles import SubTile, TileData, tile_generator

@dataclass
class BuildingBlueprint:
    """Template for buildings that can be placed on 9-section system"""
    name: str
    size: Tuple[int, int]  # Size in sections (width, height)
    required_sections: List[Tuple[int, int, str]]  # [(section_x, section_y, building_type), ...]
    cost: Dict[str, int] = field(default_factory=dict)  # Resource cost
    description: str = ""
    section_compatible: bool = True  # Whether this blueprint works with 9-section system
    
@dataclass
class SectionData:
    """Data for individual section in 9-section system"""
    exists: bool = True
    building_type: Optional[str] = None
    building_id: Optional[str] = None
    damage: float = 0.0
    variant: int = 0  # Visual variation
    
class SubTileManager:
    """Enhanced manager for FIXED 9-section internal subdivision with proper stepped pyramids"""
    
    def __init__(self, scene):
        self.scene = scene
        self.tile_data: Dict[Tuple[int, int], TileData] = {}  # (grid_x, grid_y) -> TileData
        self.buildings: Dict[str, Dict] = {}  # building_id -> building_info
        self.building_counter = 0
        
        # NEW: 9-section system data
        self.section_data: Dict[Tuple[int, int, int, int], SectionData] = {}  # (grid_x, grid_y, section_x, section_y) -> SectionData
        
        # Building blueprints - Enhanced for 9-section system
        self.blueprints = self._initialize_section_blueprints()
        
        # Selection state for building mode
        self.building_mode = False
        self.selected_blueprint = None
        self.preview_position = None
        self.section_building_mode = True  # NEW: Enable section-level building
        
        # OPTIMIZATION: Cache frequently accessed data
        self._tile_data_cache = {}
        self._section_data_cache = {}
        self._cache_size_limit = 200  # Increased for section data
        
    def _initialize_section_blueprints(self) -> Dict[str, BuildingBlueprint]:
        """Initialize building blueprints optimized for FIXED 9-section system"""
        blueprints = {}
        
        # SECTION-LEVEL BUILDINGS (work within single tiles with 9 sections)
        
        # Micro house (1 section)
        blueprints["micro_house"] = BuildingBlueprint(
            name="Micro House",
            size=(1, 1),
            required_sections=[(0, 0, "micro_foundation")],
            cost={"wood": 2, "stone": 1},
            description="Tiny 1-section living space",
            section_compatible=True
        )
        
        # Small building (2x2 sections within tile)
        blueprints["small_building"] = BuildingBlueprint(
            name="Small Building", 
            size=(2, 2),
            required_sections=[
                (0, 0, "foundation"), (1, 0, "foundation"),
                (0, 1, "wall"), (1, 1, "wall")
            ],
            cost={"wood": 6, "stone": 4},
            description="2x2 section building",
            section_compatible=True
        )
        
        # Bridge segment (3x1 sections)
        blueprints["bridge_segment"] = BuildingBlueprint(
            name="Bridge Segment",
            size=(3, 1),
            required_sections=[(0, 0, "floor"), (1, 0, "floor"), (2, 0, "floor")],
            cost={"wood": 6},
            description="3-section bridge segment",
            section_compatible=True
        )
        
        # Corner structure (2x2 sections)
        blueprints["corner_structure"] = BuildingBlueprint(
            name="Corner Structure",
            size=(2, 2),
            required_sections=[
                (0, 0, "base"), (1, 0, "base"),
                (0, 1, "wall"), (1, 1, "wall")
            ],
            cost={"wood": 4, "stone": 8},
            description="Defensive corner structure",
            section_compatible=True
        )
        
        # Platform (1x3 linear)
        blueprints["platform"] = BuildingBlueprint(
            name="Platform",
            size=(1, 3),
            required_sections=[(0, 0, "platform"), (0, 1, "platform"), (0, 2, "platform")],
            cost={"wood": 4, "stone": 2},
            description="Linear 3-section platform",
            section_compatible=True
        )
        
        # Single section types
        blueprints["single_wall"] = BuildingBlueprint(
            name="Wall Section",
            size=(1, 1),
            required_sections=[(0, 0, "wall")],
            cost={"wood": 1, "stone": 2},
            description="Single defensive wall section",
            section_compatible=True
        )
        
        blueprints["single_floor"] = BuildingBlueprint(
            name="Floor Section",
            size=(1, 1),
            required_sections=[(0, 0, "floor")],
            cost={"wood": 2},
            description="Single floor section",
            section_compatible=True
        )
        
        # Full tile buildings (use all 9 sections)
        blueprints["full_house"] = BuildingBlueprint(
            name="Full House",
            size=(3, 3),
            required_sections=[
                (0, 0, "foundation"), (1, 0, "foundation"), (2, 0, "foundation"),
                (0, 1, "wall"), (1, 1, "interior"), (2, 1, "wall"),
                (0, 2, "wall"), (1, 2, "wall"), (2, 2, "wall")
            ],
            cost={"wood": 15, "stone": 10},
            description="Full tile house using all 9 sections",
            section_compatible=True
        )
        
        return blueprints
        
    def get_section_data(self, grid_x: int, grid_y: int, section_x: int, section_y: int) -> SectionData:
        """Get or create section data for specific section position"""
        pos = (grid_x, grid_y, section_x, section_y)
        
        # Check cache first
        if pos in self._section_data_cache:
            return self._section_data_cache[pos]
            
        if pos not in self.section_data:
            # FIXED: Check if this section should exist based on terrain layers
            section_exists = self._check_section_exists_in_terrain(grid_x, grid_y, section_x, section_y)
            section_data = SectionData()
            section_data.exists = section_exists
            self.section_data[pos] = section_data
            
        # Cache the result
        result = self.section_data[pos]
        self._section_data_cache[pos] = result
        
        # Limit cache size
        if len(self._section_data_cache) > self._cache_size_limit:
            oldest_keys = list(self._section_data_cache.keys())[:50]
            for key in oldest_keys:
                del self._section_data_cache[key]
                
        return result
        
    def _check_section_exists_in_terrain(self, grid_x: int, grid_y: int, section_x: int, section_y: int) -> bool:
        """Check if section exists in the terrain based on FIXED stepped pyramid layers"""
        if not (hasattr(self.scene, 'use_layered_terrain') and 
                self.scene.use_layered_terrain and 
                hasattr(self.scene, 'terrain')):
            return True  # Default to exists for flat terrain
            
        try:
            # Get the terrain stack at this position
            stack = self.scene.terrain.terrain_stacks.get((grid_x, grid_y), [])
            if not stack:
                return False
                
            # Check if any layer in the stack has this section
            for terrain_tile in stack:
                if hasattr(terrain_tile, 'section_data'):
                    section_info = terrain_tile.section_data.get((section_x, section_y))
                    if section_info and section_info.get('exists', True):
                        return True
                        
            return True  # Default to exists if no specific section data
        except:
            return True  # Safe fallback
        
    def get_tile_data(self, grid_x: int, grid_y: int) -> TileData:
        """Get or create tile data with caching"""
        pos = (grid_x, grid_y)
        
        # Check cache first
        if pos in self._tile_data_cache:
            return self._tile_data_cache[pos]
            
        if pos not in self.tile_data:
            # Get base tile type from terrain
            if hasattr(self.scene, 'use_layered_terrain') and self.scene.use_layered_terrain:
                try:
                    tile_type = self.scene.terrain.get_surface_tile(grid_x, grid_y)
                except:
                    tile_type = 1  # Default to grass
            else:
                try:
                    tile_type = self.scene.map_data[grid_y][grid_x] if self._in_bounds(grid_x, grid_y) else 1
                except:
                    tile_type = 1  # Default to grass
                    
            self.tile_data[pos] = TileData(tile_type=tile_type, sub_tiles=[])
            
        # Cache the result
        result = self.tile_data[pos]
        self._tile_data_cache[pos] = result
        
        # Limit cache size
        if len(self._tile_data_cache) > self._cache_size_limit:
            oldest_keys = list(self._tile_data_cache.keys())[:20]
            for key in oldest_keys:
                del self._tile_data_cache[key]
                
        return result
        
    def _in_bounds(self, grid_x: int, grid_y: int) -> bool:
        """Check if grid position is within map bounds"""
        try:
            return (0 <= grid_x < len(self.scene.map_data[0]) and 
                    0 <= grid_y < len(self.scene.map_data))
        except:
            return False
    
    def _section_in_bounds(self, section_x: int, section_y: int) -> bool:
        """Check if section position is within 3x3 grid"""
        return 0 <= section_x < 3 and 0 <= section_y < 3
                
    def dig_section(self, grid_x: int, grid_y: int, section_x: int, section_y: int, tool_power: int = 1) -> bool:
        """Dig out a specific section in the FIXED 9-section system"""
        if not self._section_in_bounds(section_x, section_y):
            return False
            
        try:
            # FIXED: Check if we're using layered terrain with proper stepped pyramids
            if (hasattr(self.scene, 'use_layered_terrain') and 
                self.scene.use_layered_terrain and 
                hasattr(self.scene, 'terrain')):
                
                # Use the proper layered terrain digging
                return self._dig_section_layered_terrain(grid_x, grid_y, section_x, section_y, tool_power)
            else:
                # Fallback to legacy section digging
                return self._dig_section_legacy(grid_x, grid_y, section_x, section_y, tool_power)
                
        except Exception as e:
            print(f"[FIXED 9-Section Manager] Error digging section: {e}")
            return False
    
    def _dig_section_layered_terrain(self, grid_x: int, grid_y: int, section_x: int, section_y: int, tool_power: int) -> bool:
        """Dig section in layered terrain with FIXED stepped pyramids"""
        # Get the terrain stack
        stack = self.scene.terrain.terrain_stacks.get((grid_x, grid_y), [])
        if not stack:
            return False
            
        # Find the topmost layer that has this section
        target_layer_index = -1
        target_terrain_tile = None
        
        # Check from top to bottom
        for i in range(len(stack) - 1, -1, -1):
            terrain_tile = stack[i]
            if hasattr(terrain_tile, 'section_data'):
                section_info = terrain_tile.section_data.get((section_x, section_y))
                if section_info and section_info.get('exists', True):
                    target_layer_index = i
                    target_terrain_tile = terrain_tile
                    break
        
        if target_layer_index == -1 or not target_terrain_tile:
            return False  # No layer has this section
            
        # Check tool power vs layer difficulty
        layer_difficulty = 1.0 + (target_layer_index * 0.5)  # Higher layers are harder
        if target_terrain_tile.tile_type == 4:  # Mountain
            layer_difficulty += 1.0  # Mountains are harder
            
        if tool_power < layer_difficulty:
            print(f"[FIXED Stepped Pyramid] Tool too weak for layer {target_layer_index} - need {layer_difficulty}, have {tool_power}")
            return False
        
        # Remove the section from this layer
        if hasattr(target_terrain_tile, 'section_data'):
            section_info = target_terrain_tile.section_data.get((section_x, section_y), {})
            section_info['exists'] = False
            target_terrain_tile.section_data[(section_x, section_y)] = section_info
        
        # Give appropriate resources
        if target_terrain_tile.tile_type == 4:  # Mountain
            base_resources = {"stone": 2 + target_layer_index, "dirt": 1}
        else:
            base_resources = {"dirt": 1}
            
        # Single section = reduced resources
        section_resources = {k: max(1, v // 3) for k, v in base_resources.items()}
        self._give_resources_to_player(section_resources)
        
        # Invalidate caches
        self._invalidate_section_cache(grid_x, grid_y, section_x, section_y)
        
        # Check if we should remove the entire layer if no sections remain
        if hasattr(target_terrain_tile, 'section_data'):
            remaining_sections = sum(1 for sect_info in target_terrain_tile.section_data.values() 
                                   if sect_info.get('exists', True))
            
            if remaining_sections == 0:
                # Remove this entire layer
                stack.pop(target_layer_index)
                print(f"[FIXED Stepped Pyramid] Removed entire layer {target_layer_index} - no sections remain")
                
                # Update terrain maps
                if stack:
                    self.scene.terrain.surface_map[grid_y][grid_x] = stack[-1].tile_type
                    self.scene.terrain.height_map[grid_y][grid_x] = len(stack)
                else:
                    self.scene.terrain.surface_map[grid_y][grid_x] = 1  # Default to grass
                    self.scene.terrain.height_map[grid_y][grid_x] = 1
                
                # Invalidate the map tile for regeneration
                if hasattr(self.scene, 'map'):
                    self.scene.map.invalidate_tile(grid_x, grid_y)
        
        print(f"[FIXED Stepped Pyramid] Dug section at layer {target_layer_index} ({grid_x}, {grid_y}) section ({section_x}, {section_y})")
        return True
        
    def _dig_section_legacy(self, grid_x: int, grid_y: int, section_x: int, section_y: int, tool_power: int) -> bool:
        """Legacy section digging for flat terrain"""
        section_data = self.get_section_data(grid_x, grid_y, section_x, section_y)
        
        # Check if we can dig this section
        if not section_data.exists or section_data.building_type:
            return False
            
        # Get tile type for difficulty calculation
        tile_data = self.get_tile_data(grid_x, grid_y)
        required_power = self._get_dig_difficulty_fast(tile_data.tile_type)
        if tool_power < required_power:
            return False
            
        # Dig out the section
        section_data.exists = False
        
        # Give resources to player (reduced amount for single section)
        base_resources = self._get_dig_resources_fast(tile_data.tile_type)
        section_resources = {k: max(1, v // 5) for k, v in base_resources.items()}  # Reduce for single section
        self._give_resources_to_player(section_resources)
        
        # Invalidate caches
        self._invalidate_section_cache(grid_x, grid_y, section_x, section_y)
        
        # Check if we should update tile visual (if enough sections are gone)
        intact_sections = self._count_intact_sections(grid_x, grid_y)
        if intact_sections <= 6:  # More than 1/3 damaged
            # Notify the map system to update visual
            if hasattr(self.scene, 'map'):
                self.scene.map.invalidate_tile(grid_x, grid_y)
        
        print(f"[FIXED 9-Section Manager] Dug section at ({grid_x}, {grid_y}) section ({section_x}, {section_y})")
        return True
    
    def _count_intact_sections(self, grid_x: int, grid_y: int) -> int:
        """Count intact sections in a tile"""
        count = 0
        for section_x in range(3):
            for section_y in range(3):
                section_data = self.get_section_data(grid_x, grid_y, section_x, section_y)
                if section_data.exists and section_data.damage < 100.0:
                    count += 1
        return count
        
    def place_section_building(self, grid_x: int, grid_y: int, section_x: int, section_y: int, blueprint_name: str) -> bool:
        """Place a building on the FIXED 9-section system"""
        if blueprint_name not in self.blueprints:
            return False
            
        blueprint = self.blueprints[blueprint_name]
        
        if not blueprint.section_compatible:
            return False
        
        # Check if we can place the building
        if not self._can_place_section_building(grid_x, grid_y, section_x, section_y, blueprint):
            return False
            
        # Check resources
        if not self._has_resources_fast(blueprint.cost):
            return False
            
        # Consume resources
        self._consume_resources(blueprint.cost)
        
        # Create building
        building_id = f"section_building_{self.building_counter}"
        self.building_counter += 1
        
        try:
            affected_sections = set()
            for rel_x, rel_y, building_type in blueprint.required_sections:
                final_section_x = section_x + rel_x
                final_section_y = section_y + rel_y
                
                # Handle section positions that go outside the 3x3 grid
                final_grid_x = grid_x
                final_grid_y = grid_y
                
                while final_section_x >= 3:
                    final_grid_x += 1
                    final_section_x -= 3
                while final_section_x < 0:
                    final_grid_x -= 1
                    final_section_x += 3
                while final_section_y >= 3:
                    final_grid_y += 1
                    final_section_y -= 3
                while final_section_y < 0:
                    final_grid_y -= 1
                    final_section_y += 3
                
                if not self._in_bounds(final_grid_x, final_grid_y):
                    continue
                    
                section_data = self.get_section_data(final_grid_x, final_grid_y, final_section_x, final_section_y)
                section_data.building_id = building_id
                section_data.building_type = building_type
                
                affected_sections.add((final_grid_x, final_grid_y, final_section_x, final_section_y))
                
            # Store building info
            self.buildings[building_id] = {
                "blueprint": blueprint_name,
                "position": (grid_x, grid_y, section_x, section_y),
                "health": 100,
                "section_positions": list(affected_sections)
            }
            
            # Invalidate caches for affected areas
            for section_pos in affected_sections:
                self._invalidate_section_cache(*section_pos)
                
            print(f"[FIXED 9-Section Manager] Placed {blueprint_name} at ({grid_x}, {grid_y}) section ({section_x}, {section_y})")
            return True
        except Exception as e:
            print(f"[FIXED 9-Section Manager] Error placing building: {e}")
            return False
        
    def _can_place_section_building(self, grid_x: int, grid_y: int, section_x: int, section_y: int, blueprint: BuildingBlueprint) -> bool:
        """Check if building can be placed on FIXED 9-section system"""
        try:
            for rel_x, rel_y, building_type in blueprint.required_sections:
                check_section_x = section_x + rel_x
                check_section_y = section_y + rel_y
                
                # Calculate which main tile this section belongs to
                check_grid_x = grid_x
                check_grid_y = grid_y
                
                while check_section_x >= 3:
                    check_grid_x += 1
                    check_section_x -= 3
                while check_section_x < 0:
                    check_grid_x -= 1
                    check_section_x += 3
                while check_section_y >= 3:
                    check_grid_y += 1
                    check_section_y -= 3
                while check_section_y < 0:
                    check_grid_y -= 1
                    check_section_y += 3
                
                # Check bounds
                if not self._in_bounds(check_grid_x, check_grid_y):
                    return False
                    
                if not self._section_in_bounds(check_section_x, check_section_y):
                    return False
                    
                # Check tile type (no building on water unless it's a floor)
                tile_data = self.get_tile_data(check_grid_x, check_grid_y)
                if tile_data.tile_type in [2, 5] and building_type not in ["floor", "platform"]:
                    return False
                    
                # Check section availability
                section_data = self.get_section_data(check_grid_x, check_grid_y, check_section_x, check_section_y)
                if section_data.building_type is not None:
                    return False
                if not section_data.exists and building_type not in ["foundation", "micro_foundation", "platform", "base"]:
                    return False
                    
            return True
        except:
            return False
        
    def _has_resources_fast(self, cost: Dict[str, int]) -> bool:
        """Quick resource check"""
        try:
            inventory = getattr(self.scene, 'inventory', {})
            for resource, amount in cost.items():
                if inventory.get(resource, 0) < amount:
                    return False
            return True
        except:
            return False
        
    def _consume_resources(self, cost: Dict[str, int]):
        """Remove resources from player inventory"""
        try:
            inventory = getattr(self.scene, 'inventory', {})
            for resource, amount in cost.items():
                inventory[resource] = max(0, inventory.get(resource, 0) - amount)
        except:
            pass
            
    def _give_resources_to_player(self, resources: Dict[str, int]):
        """Add resources to player inventory"""
        try:
            inventory = getattr(self.scene, 'inventory', {})
            for resource, amount in resources.items():
                inventory[resource] = inventory.get(resource, 0) + amount
        except:
            pass
            
    def _get_dig_difficulty_fast(self, tile_type: int) -> int:
        """Get required tool power"""
        if tile_type in [1, 2, 5, 11]:  # Grass, water, desert
            return 1
        elif tile_type in [3]:  # Dirt
            return 2
        elif tile_type in [4]:  # Stone
            return 3
        else:
            return 2  # Default
        
    def _get_dig_resources_fast(self, tile_type: int) -> Dict[str, int]:
        """Get resources with mapping"""
        resource_map = {
            1: {"dirt": 1, "grass": 1},         # Grass
            2: {"water": 1},                    # Water
            3: {"dirt": 2},                     # Dirt  
            4: {"stone": 1, "dirt": 1},         # Stone
            5: {"water": 1},                    # Deep water
            11: {"sand": 2, "dirt": 1}          # Desert
        }
        return resource_map.get(tile_type, {"dirt": 1})
        
    def _invalidate_section_cache(self, grid_x: int, grid_y: int, section_x: int, section_y: int):
        """Invalidate caches for specific section"""
        # Clear from section cache
        pos = (grid_x, grid_y, section_x, section_y)
        if pos in self._section_data_cache:
            del self._section_data_cache[pos]
            
        # Also clear tile-level cache
        tile_pos = (grid_x, grid_y)
        if tile_pos in self._tile_data_cache:
            del self._tile_data_cache[tile_pos]
    
    def handle_section_click(self, mouse_pos: Tuple[int, int], grid_x: int, grid_y: int, section_x: int, section_y: int) -> bool:
        """Handle mouse clicks on specific sections"""
        try:
            if self.section_building_mode and self.building_mode and self.selected_blueprint:
                return self._handle_section_building_click(mouse_pos, grid_x, grid_y, section_x, section_y)
            else:
                return self._handle_section_digging_click(mouse_pos, grid_x, grid_y, section_x, section_y)
        except:
            return False
            
    def _handle_section_building_click(self, mouse_pos: Tuple[int, int], grid_x: int, grid_y: int, section_x: int, section_y: int) -> bool:
        """Handle click in section building mode"""
        try:
            success = self.place_section_building(grid_x, grid_y, section_x, section_y, self.selected_blueprint)
            if success:
                # Exit building mode after successful placement
                self.building_mode = False
                self.selected_blueprint = None
            return success
        except:
            return False
        
    def _handle_section_digging_click(self, mouse_pos: Tuple[int, int], grid_x: int, grid_y: int, section_x: int, section_y: int) -> bool:
        """Handle click in section digging mode"""
        try:
            # Default tool power
            tool_power = 2
            
            if hasattr(self.scene, 'unit_manager') and self.scene.unit_manager.units:
                try:
                    first_biped = self.scene.unit_manager.units[0]
                    tool_power = self._get_biped_tool_power_fast(first_biped)
                except:
                    tool_power = 2
                    
            return self.dig_section(grid_x, grid_y, section_x, section_y, tool_power)
        except:
            return False
        
    def _get_biped_tool_power_fast(self, biped) -> int:
        """Get tool power with simplified logic"""
        try:
            if not hasattr(biped, 'inventory'):
                return 2
                
            tool = biped.inventory.get("equipped_tool", "hands")
            if tool == "hands":
                return 1
            elif "shovel" in tool:
                return 2
            elif "pickaxe" in tool:
                return 3
            else:
                return 2
        except:
            return 2
        
    def start_section_building_mode(self, blueprint_name: str):
        """Start section-level building mode"""
        if blueprint_name in self.blueprints and self.blueprints[blueprint_name].section_compatible:
            self.building_mode = True
            self.section_building_mode = True
            self.selected_blueprint = blueprint_name
            print(f"[FIXED 9-Section Manager] Started section building mode: {blueprint_name}")
            return True
        return False
        
    def stop_building_mode(self):
        """Exit building mode"""
        self.building_mode = False
        self.section_building_mode = False
        self.selected_blueprint = None
        
    def get_section_building_preview(self, grid_x: int, grid_y: int, section_x: int, section_y: int) -> List[Tuple[int, int, int, int]]:
        """Get building preview for section system"""
        if not (self.selected_blueprint and self.selected_blueprint in self.blueprints):
            return []
            
        try:
            blueprint = self.blueprints[self.selected_blueprint]
            if not blueprint.section_compatible:
                return []
                
            preview_sections = []
            
            for rel_x, rel_y, building_type in blueprint.required_sections:
                final_section_x = section_x + rel_x
                final_section_y = section_y + rel_y
                
                # Calculate which main tile this section belongs to
                final_grid_x = grid_x
                final_grid_y = grid_y
                
                while final_section_x >= 3:
                    final_grid_x += 1
                    final_section_x -= 3
                while final_section_x < 0:
                    final_grid_x -= 1
                    final_section_x += 3
                while final_section_y >= 3:
                    final_grid_y += 1
                    final_section_y -= 3
                while final_section_y < 0:
                    final_grid_y -= 1
                    final_section_y += 3
                
                preview_sections.append((final_grid_x, final_grid_y, final_section_x, final_section_y))
                
            return preview_sections
        except:
            return []
        
    def damage_section_building(self, building_id: str, damage: float) -> bool:
        """Apply damage to a section building"""
        try:
            if building_id not in self.buildings:
                return False
                
            building = self.buildings[building_id]
            building["health"] -= damage
            
            if building["health"] <= 0:
                self._destroy_section_building(building_id)
                return True
                
            return False
        except:
            return False
        
    def _destroy_section_building(self, building_id: str):
        """Destroy a section building"""
        try:
            if building_id not in self.buildings:
                return
                
            building = self.buildings[building_id]
            blueprint_name = building["blueprint"]
            
            if blueprint_name in self.blueprints:
                blueprint = self.blueprints[blueprint_name]
                
                # Recover some resources
                recovered_resources = {}
                for resource, amount in blueprint.cost.items():
                    recovered = max(1, amount // 2)  # Recover half
                    recovered_resources[resource] = recovered
                    
                self._give_resources_to_player(recovered_resources)
            
            # Clear section data
            for section_pos in building.get("section_positions", []):
                if len(section_pos) == 4:
                    grid_x, grid_y, section_x, section_y = section_pos
                    section_data = self.get_section_data(grid_x, grid_y, section_x, section_y)
                    section_data.building_id = None
                    section_data.building_type = None
                    self._invalidate_section_cache(grid_x, grid_y, section_x, section_y)
                        
            # Remove building record
            if building_id in self.buildings:
                del self.buildings[building_id]
                
            print(f"[FIXED 9-Section Manager] Destroyed section building {building_id}")
        except Exception as e:
            print(f"[FIXED 9-Section Manager] Error destroying building: {e}")
    
    def get_section_info(self, grid_x: int, grid_y: int, section_x: int, section_y: int) -> Dict:
        """Get information about a specific section"""
        try:
            section_data = self.get_section_data(grid_x, grid_y, section_x, section_y)
            tile_data = self.get_tile_data(grid_x, grid_y)
            
            info = {
                "exists": section_data.exists,
                "building_type": section_data.building_type,
                "building_id": section_data.building_id,
                "damage": section_data.damage,
                "tile_type": tile_data.tile_type,
                "position": f"Tile ({grid_x}, {grid_y}) Section ({section_x}, {section_y})"
            }
            
            # FIXED: Add layer information if using layered terrain
            if (hasattr(self.scene, 'use_layered_terrain') and 
                self.scene.use_layered_terrain and 
                hasattr(self.scene, 'terrain')):
                
                stack = self.scene.terrain.terrain_stacks.get((grid_x, grid_y), [])
                info["layers"] = len(stack)
                info["pyramid_system"] = "FIXED stepped pyramid blocks"
            
            return info
        except:
            return {"error": "Could not get section info"}
    
    def regenerate_section_visuals(self, grid_x: int, grid_y: int):
        """Force regeneration of section visuals for a tile"""
        try:
            # Clear all section caches for this tile
            for section_x in range(3):
                for section_y in range(3):
                    self._invalidate_section_cache(grid_x, grid_y, section_x, section_y)
            
            # Notify map to regenerate
            if hasattr(self.scene, 'map'):
                self.scene.map.invalidate_tile(grid_x, grid_y)
                
            print(f"[FIXED 9-Section Manager] Regenerated visuals for tile ({grid_x}, {grid_y})")
        except Exception as e:
            print(f"[FIXED 9-Section Manager] Error regenerating visuals: {e}")
    
    def get_stats(self) -> Dict:
        """Get statistics about the FIXED 9-section system"""
        try:
            total_sections = len(self.section_data)
            existing_sections = sum(1 for section in self.section_data.values() if section.exists)
            building_sections = sum(1 for section in self.section_data.values() if section.building_type)
            damaged_sections = sum(1 for section in self.section_data.values() if section.damage > 0)
            
            stats = {
                "total_sections": total_sections,
                "existing_sections": existing_sections,
                "building_sections": building_sections,
                "damaged_sections": damaged_sections,
                "total_buildings": len(self.buildings),
                "section_building_mode": self.section_building_mode,
                "selected_blueprint": self.selected_blueprint,
                "pyramid_system": "FIXED stepped pyramid blocks"
            }
            
            # Add layered terrain stats
            if (hasattr(self.scene, 'use_layered_terrain') and 
                self.scene.use_layered_terrain and 
                hasattr(self.scene, 'terrain')):
                
                stack_count = len(self.scene.terrain.terrain_stacks)
                total_layers = sum(len(stack) for stack in self.scene.terrain.terrain_stacks.values())
                stats["terrain_stacks"] = stack_count
                stats["total_layers"] = total_layers
                stats["avg_layers_per_stack"] = round(total_layers / stack_count, 2) if stack_count > 0 else 0
                
            return stats
        except:
            return {"error": "Could not get stats"}

    # Legacy compatibility methods for older sub-tile system
    def dig_subtile(self, grid_x: int, grid_y: int, sub_x: int, sub_y: int, tool_power: int = 1) -> bool:
        """Legacy compatibility - convert sub-tile to section coordinates"""
        # Convert 4x4 sub-tile coordinates to 3x3 section coordinates
        section_x = min(2, (sub_x * 3) // 4)
        section_y = min(2, (sub_y * 3) // 4)
        return self.dig_section(grid_x, grid_y, section_x, section_y, tool_power)
        
    def place_building(self, grid_x: int, grid_y: int, sub_x: int, sub_y: int, blueprint_name: str) -> bool:
        """Legacy compatibility - convert sub-tile to section coordinates"""
        # Convert 4x4 sub-tile coordinates to 3x3 section coordinates
        section_x = min(2, (sub_x * 3) // 4)
        section_y = min(2, (sub_y * 3) // 4)
        return self.place_section_building(grid_x, grid_y, section_x, section_y, blueprint_name)
        
    def handle_click(self, mouse_pos: Tuple[int, int], grid_x: int, grid_y: int) -> bool:
        """Legacy compatibility - convert to section coordinates"""
        # Simple section detection from mouse position
        section_x, section_y = self._get_section_from_mouse(mouse_pos, grid_x, grid_y)
        if section_x is not None and section_y is not None:
            return self.handle_section_click(mouse_pos, grid_x, grid_y, section_x, section_y)
        return False
        
    def _get_section_from_mouse(self, mouse_pos: Tuple[int, int], grid_x: int, grid_y: int) -> Tuple[Optional[int], Optional[int]]:
        """Convert mouse position to section coordinates"""
        try:
            mx, my = mouse_pos
            
            # Calculate tile center in screen coordinates
            cam_x = getattr(self.scene.map, 'camera_offset_x', 0)
            cam_y = getattr(self.scene.map, 'camera_offset_y', 0)
            zoom = getattr(self.scene, 'zoom_scale', 1.0)
            
            iso_x = (grid_x - grid_y) * (32) * zoom
            iso_y = (grid_x + grid_y) * (18) * zoom
            tile_screen_x = iso_x + cam_x
            tile_screen_y = iso_y + cam_y
            
            # Calculate relative position within tile
            rel_x = mx - tile_screen_x
            rel_y = my - tile_screen_y
            
            # Convert to section coordinates
            tile_width = 64 * zoom
            tile_height = 37 * zoom
            
            if abs(rel_x) < tile_width//2 and abs(rel_y) < tile_height//2:
                # Normalize to 0.0-1.0 range
                local_x = (rel_x + tile_width//2) / tile_width
                local_y = (rel_y + tile_height//2) / tile_height
                
                # Convert to section coordinates (0-2)
                section_x = int(local_x * 3)
                section_y = int(local_y * 3)
                
                section_x = max(0, min(2, section_x))
                section_y = max(0, min(2, section_y))
                
                return section_x, section_y
                
            return None, None
        except:
            return None, None