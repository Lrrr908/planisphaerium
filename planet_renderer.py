##########################################################
# planet_renderer.py - Enhanced for FIXED 9-Section Internal Subdivision
# Handles all rendering, drawing, visual effects, and display
##########################################################

import pygame
import math
from iso_map import IsoTree

# Constants
TILE_WATER = 2
# Removed TILE_WATERSTACK (5) - only using single water type now

class PlanetRenderer:
    """Handles all rendering and visual effects with FIXED 9-section internal subdivision"""
    
    def __init__(self, scene):
        self.scene = scene
        self.show_section_grid = False  # Debug option to show 3x3 section boundaries
        self.section_highlight = None   # (grid_x, grid_y, section_col, section_row) for highlighting

    def render(self, surface):
        """Main render function - FIXED stepped pyramids render as clean stacked blocks"""
        surface.fill((255, 255, 255))
        
        # Collect all drawable objects WITHOUT DUPLICATES
        drawables = self._collect_drawable_objects()
        
        # Sort by draw order for proper depth - CRITICAL for stepped pyramids
        drawables_sorted = self._sort_drawables(drawables)
        
        # Draw everything - FIXED stepped pyramids now render properly
        self._draw_objects(surface, drawables_sorted)
        
        # Draw 9-section specific overlays (debug only)
        if self.show_section_grid:
            self._draw_section_grid_overlay(surface)
            
        # Draw section highlight if active
        if self.section_highlight:
            self._draw_section_highlight(surface)
        
        # Draw UI overlays
        self._draw_tooltips(surface)
        self._draw_debug_info(surface)

    def _collect_drawable_objects(self):
        """Collect all objects that need to be drawn"""
        drawables = []
        
        # Add terrain/map objects (already includes trees + houses from iso_objects)
        # FIXED: These now include properly stacked pyramid blocks
        drawables.extend(self.scene.iso_objects)
        
        # Add units/bipeds
        drawables.extend(self.scene.unit_manager.units)
        
        # Add animals
        drawables.extend(self.scene.animal_manager.animals)
        
        # Add drops
        drawables.extend(self.scene.drops)
        
        # Note: houses and trees are already in iso_objects, so we don't add them separately
        return drawables

    def _sort_drawables(self, drawables):
        """Sort drawables by draw order for proper depth rendering - CRITICAL for stepped pyramids"""
        try:
            # FIXED: Proper sorting ensures stepped pyramid blocks render in correct order
            return sorted(drawables, key=lambda o: getattr(o, 'draw_order', 0))
        except Exception as e:
            print(f"[FIXED render] Error sorting drawables: {e}")
            return drawables  # Use unsorted if sorting fails

    def _draw_objects(self, surface, drawables_sorted):
        """Draw all sorted objects - FIXED stepped pyramids now render as clean blocks"""
        for obj in drawables_sorted:
            try:
                # Calculate screen position first
                if hasattr(obj, 'calculate_screen_position'):
                    obj.calculate_screen_position(
                        self.scene.map.camera_offset_x,
                        self.scene.map.camera_offset_y,
                        self.scene.zoom_scale
                    )
                
                # Draw the object - FIXED: Each block renders as a simple clean block
                if isinstance(obj, IsoTree):
                    obj.draw(surface, self.scene.tree_images, self.scene.zoom_scale)
                else:
                    obj.draw(surface, None, self.scene.zoom_scale)
                    
            except Exception as e:
                print(f"[FIXED render] Error drawing object {type(obj)}: {e}")
                continue

    def _draw_section_grid_overlay(self, surface):
        """Draw overlay showing 3x3 internal section grids for debugging"""
        if not hasattr(self.scene, 'map_data'):
            return
            
        overlay_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        for y in range(len(self.scene.map_data)):
            for x in range(len(self.scene.map_data[0])):
                if self.scene.map_data[y][x] == -1:
                    continue
                    
                # Calculate tile screen position
                iso_x = (x - y) * (32) * self.scene.zoom_scale
                iso_y = (x + y) * (18) * self.scene.zoom_scale
                screen_x = iso_x + self.scene.map.camera_offset_x
                screen_y = iso_y + self.scene.map.camera_offset_y
                
                # Draw 3x3 section grid lines INSIDE the tile
                tile_width = 64 * self.scene.zoom_scale
                tile_height = 37 * self.scene.zoom_scale
                
                # Draw section dividers (subtle lines)
                for i in range(1, 3):  # 2 divider lines for 3x3 grid
                    # Vertical dividers
                    div_x = screen_x + (i - 1.5) * (tile_width / 3)
                    start_y = screen_y - tile_height // 2
                    end_y = screen_y + tile_height // 2
                    pygame.draw.line(overlay_surface, (255, 255, 0, 80), 
                                   (div_x, start_y), (div_x, end_y), 1)
                    
                    # Horizontal dividers
                    div_y = screen_y + (i - 1.5) * (tile_height / 3)
                    start_x = screen_x - tile_width // 2
                    end_x = screen_x + tile_width // 2
                    pygame.draw.line(overlay_surface, (255, 255, 0, 80), 
                                   (start_x, div_y), (end_x, div_y), 1)
        
        surface.blit(overlay_surface, (0, 0))

    def _draw_section_highlight(self, surface):
        """Draw highlight around specific section within a tile"""
        if not self.section_highlight:
            return
            
        grid_x, grid_y, section_col, section_row = self.section_highlight
        
        # Calculate tile screen position
        iso_x = (grid_x - grid_y) * (32) * self.scene.zoom_scale
        iso_y = (grid_x + grid_y) * (18) * self.scene.zoom_scale
        screen_x = iso_x + self.scene.map.camera_offset_x
        screen_y = iso_y + self.scene.map.camera_offset_y
        
        # Calculate section position within tile
        tile_width = 64 * self.scene.zoom_scale
        tile_height = 37 * self.scene.zoom_scale
        section_width = tile_width / 3
        section_height = tile_height / 3
        
        # Position of specific section
        section_offset_x = (section_col - 1) * section_width
        section_offset_y = (section_row - 1) * section_height
        
        highlight_x = screen_x + section_offset_x
        highlight_y = screen_y + section_offset_y
        
        # Get tile object for additional info
        tile_obj = self.scene.map.get_tile_at(grid_x, grid_y)
        
        # Draw highlight rectangle around the section
        highlight_rect = pygame.Rect(
            highlight_x - section_width//2, 
            highlight_y - section_height//2,
            section_width, 
            section_height
        )
        
        # Color based on tile type
        if tile_obj and tile_obj.tile_type == 4:  # Mountain
            pygame.draw.rect(surface, (255, 165, 0), highlight_rect, 2)  # Orange for mountain
            
            # FIXED: Draw simplified layer info for stepped pyramids
            if hasattr(tile_obj, 'height'):
                layer_level = tile_obj.height
                difficulty = tile_obj.get_section_mining_difficulty(section_col, section_row)
                
                # Draw layer level and difficulty info
                font = pygame.font.SysFont("Arial", 12)
                info_text = f"Layer:{layer_level} D:{difficulty:.1f}"
                info_surf = font.render(info_text, True, (255, 255, 255))
                
                # Background for text
                text_rect = info_surf.get_rect()
                text_bg = pygame.Surface((text_rect.width + 4, text_rect.height + 2), pygame.SRCALPHA)
                text_bg.fill((0, 0, 0, 180))
                
                surface.blit(text_bg, (highlight_x - text_rect.width//2 - 2, highlight_y - text_rect.height - 10))
                surface.blit(info_surf, (highlight_x - text_rect.width//2, highlight_y - text_rect.height - 9))
        else:
            pygame.draw.rect(surface, (255, 0, 0), highlight_rect, 2)  # Red for regular tiles

    def _draw_tooltips(self, surface):
        """Draw tooltips for hovered objects"""
        # Draw tooltips for drops
        for drop in self.scene.drops:
            if getattr(drop, 'hovered', False):
                try:
                    font = pygame.font.SysFont("Arial", 16)
                    mx, my = pygame.mouse.get_pos()
                    tip = font.render(f"{drop.resource_type} × {drop.quantity}", True, (0, 0, 0))
                    surface.blit(tip, (mx + 12, my + 12))
                except Exception as e:
                    print(f"[FIXED render] Error drawing tooltip: {e}")

    def _draw_debug_info(self, surface):
        """Draw debug information on screen with FIXED 9-section system info"""
        try:
            font = pygame.font.SysFont("Arial", 14)
            y_offset = 10
            
            # Draw simulation mode
            mode_color = (0, 150, 0) if self.scene.simulation_mode == "realtime" else (150, 0, 0)
            mode_text = f"SIM: {self.scene.simulation_mode.upper()} (Press T to toggle)"
            mode_surf = font.render(mode_text, True, mode_color)
            surface.blit(mode_surf, (10, y_offset))
            y_offset += 20
            
            # Draw terrain system status
            terrain_type = "LAYERED FIXED-PYRAMIDS" if getattr(self.scene, 'use_layered_terrain', False) else "FLAT FIXED-PYRAMIDS"
            terrain_color = (0, 150, 0) if "LAYERED" in terrain_type else (100, 100, 100)
            terrain_text = f"TERRAIN: {terrain_type} (Ctrl+R to regenerate)"
            terrain_surf = font.render(terrain_text, True, terrain_color)
            surface.blit(terrain_surf, (10, y_offset))
            y_offset += 20
            
            # Draw FIXED 9-section system status
            section_text = "9-SECTION SYSTEM: FIXED STEPPED PYRAMID BLOCKS (G to toggle grid)"
            section_color = (0, 200, 100)
            section_surf = font.render(section_text, True, section_color)
            surface.blit(section_surf, (10, y_offset))
            y_offset += 20
            
            # Draw water system status
            water_system_active = (getattr(self.scene, 'use_layered_terrain', False) and 
                                 hasattr(self.scene, 'terrain') and 
                                 hasattr(self.scene.terrain, 'water_system') and 
                                 self.scene.terrain.water_system)
            
            if water_system_active:
                water_count = len(self.scene.terrain.water_system.water_map)
                water_text = f"WATER: SUBTERRANEAN POOLS ({water_count} underground) - FIXED blocks"
                water_color = (0, 100, 200)
            else:
                water_text = "WATER: STATIC UNDERGROUND - FIXED blocks"
                water_color = (100, 100, 100)
            
            water_surf = font.render(water_text, True, water_color)
            surface.blit(water_surf, (10, y_offset))
            y_offset += 20
            
            # Draw rendering system status  
            render_text = "RENDER: FIXED STEPPED PYRAMID BLOCKS (Clean stacked blocks)"
            render_surf = font.render(render_text, True, (0, 150, 0))
            surface.blit(render_surf, (10, y_offset))
            y_offset += 20
            
            # Draw camera position
            camera_text = f"Camera: ({self.scene.map.camera_offset_x:.0f}, {self.scene.map.camera_offset_y:.0f}) Zoom: {self.scene.zoom_scale:.2f}"
            camera_surf = font.render(camera_text, True, (0, 0, 0))
            surface.blit(camera_surf, (10, y_offset))
            y_offset += 20
            
            # Draw entity counts with FIXED section info
            total_blocks = len(self.scene.iso_objects)
            total_sections = total_blocks * 9  # Each block has 9 sections
            entity_text = f"Entities: {len(self.scene.unit_manager.units)} bipeds, {len(self.scene.animal_manager.animals)} animals, {len(self.scene.trees)} trees"
            entity_surf = font.render(entity_text, True, (0, 0, 0))
            surface.blit(entity_surf, (10, y_offset))
            y_offset += 20
            
            section_count_text = f"FIXED Blocks: {total_blocks} blocks × 9 = {total_sections} internal sections"
            section_count_surf = font.render(section_count_text, True, (0, 100, 0))
            surface.blit(section_count_surf, (10, y_offset))
            y_offset += 20
            
            # Draw layer information for stepped pyramids
            if getattr(self.scene, 'use_layered_terrain', False) and hasattr(self.scene, 'terrain'):
                stack_count = len(self.scene.terrain.terrain_stacks)
                total_layers = sum(len(stack) for stack in self.scene.terrain.terrain_stacks.values())
                avg_layers = total_layers / stack_count if stack_count > 0 else 0
                
                layer_text = f"FIXED Pyramid Layers: {total_layers} total blocks, avg {avg_layers:.1f} layers per position"
                layer_surf = font.render(layer_text, True, (200, 100, 0))
                surface.blit(layer_surf, (10, y_offset))
                y_offset += 20
            
            # Draw mining mode (if applicable)
            if getattr(self.scene, 'use_layered_terrain', False):
                mining_active = getattr(self.scene, 'mining_mode', False)
                mining_color = (200, 100, 0) if mining_active else (100, 100, 100)
                mining_text = f"FIXED PYRAMID MINING: {'ON' if mining_active else 'OFF'} (Press M to toggle)"
                mining_surf = font.render(mining_text, True, mining_color)
                surface.blit(mining_surf, (10, y_offset))
                y_offset += 20
            
            # Draw water dynamics info if available
            if water_system_active:
                water_system = self.scene.terrain.water_system
                tide_phase = math.sin(water_system.time * 2 * math.pi / water_system.tide_period)
                tide_text = f"TIDE: {tide_phase:.2f} | WAVE SPEED: {water_system.wave_speed:.1f} (per-block animation)"
                tide_surf = font.render(tide_text, True, (0, 100, 200))
                surface.blit(tide_surf, (10, y_offset))
                y_offset += 20
            
            # Draw biped movement information
            self._draw_biped_debug_info(surface, font, y_offset)
            
        except Exception as e:
            print(f"[FIXED render] Error drawing debug info: {e}")

    def _draw_biped_debug_info(self, surface, font, start_y):
        """Draw detailed biped movement debug information"""
        try:
            # Get movement debug info
            if hasattr(self.scene, 'movement_system'):
                debug_info = self.scene.movement_system.get_movement_debug_info()
            else:
                # Fallback calculation
                debug_info = {
                    "total_bipeds": len(self.scene.unit_manager.units),
                    "moving_bipeds": len([u for u in self.scene.unit_manager.units if getattr(u, 'moving', False)]),
                    "with_paths": len([u for u in self.scene.unit_manager.units if getattr(u, 'path_tiles', [])]),
                    "moving_details": []
                }
            
            # Draw summary
            debug_text = f"Bipeds: {debug_info['total_bipeds']} | Moving: {debug_info['moving_bipeds']} | With Paths: {debug_info['with_paths']}"
            text_surf = font.render(debug_text, True, (0, 0, 0))
            surface.blit(text_surf, (10, start_y))
            y_offset = start_y + 20
            
            # Draw details for moving bipeds
            if debug_info['moving_bipeds'] > 0:
                for i, detail in enumerate(debug_info.get('moving_details', [])):
                    if i >= 3:  # Only show first 3 to avoid clutter
                        remaining = debug_info['moving_bipeds'] - 3
                        if remaining > 0:
                            more_text = f"... and {remaining} more moving bipeds"
                            more_surf = font.render(more_text, True, (0, 0, 100))
                            surface.blit(more_surf, (10, y_offset))
                        break
                    
                    # Format detail text with FIXED layer info
                    unit_id = detail.get('unit_id', 'unknown')
                    current_pos = detail.get('current_pos', (0, 0))
                    destination = detail.get('destination', ('?', '?'))
                    path_progress = detail.get('path_progress', '0/0')
                    
                    if self.scene.use_layered_terrain and 'current_height' in detail:
                        detail_text = f"{unit_id}: ({current_pos[0]},{current_pos[1]})@L{detail['current_height']} -> ({destination[0]},{destination[1]}) [{path_progress}]"
                    else:
                        detail_text = f"{unit_id}: ({current_pos[0]},{current_pos[1]}) -> ({destination[0]},{destination[1]}) [{path_progress}]"
                        
                    detail_surf = font.render(detail_text, True, (0, 0, 100))
                    surface.blit(detail_surf, (10, y_offset))
                    y_offset += 20
                    
        except Exception as e:
            print(f"[FIXED render] Error drawing biped debug info: {e}")

    def update_water_animation(self, dt):
        """Update water animation effects for FIXED 9-section system"""
        if self.scene.use_layered_terrain and hasattr(self.scene, 'water_system'):
            self.scene.water_system.update_water_animation(dt)
        else:
            self._update_legacy_water_animation()

    def _update_legacy_water_animation(self):
        """Legacy water animation for flat terrain - single water type"""
        cx, cy = self.scene.map.width // 2, self.scene.map.height // 2
        for y in range(self.scene.map.height):
            for x in range(self.scene.map.width):
                t = self.scene.map_data[y][x]
                if t != TILE_WATER:  # Only animate regular water
                    continue
                dist = math.hypot(x - cx, y - cy)
                wave = (dist - self.scene.wave_speed * self.scene.wave_time) % (self.scene.wave_spacing * 2)
                
                # Keep as regular water but vary the visual height
                # Note: This is for flat terrain so visual height changes would need to be added separately

    def handle_section_interaction(self, mouse_pos, grid_x, grid_y):
        """Handle interactions with individual sections in the FIXED 9-section system"""
        if not (getattr(self.scene, 'use_layered_terrain', False) and 
                hasattr(self.scene, 'terrain')):
            return False
        
        # Get the tile object (this will be the TOP layer of the stepped pyramid)
        tile_obj = self.scene.map.get_tile_at(grid_x, grid_y)
        if not tile_obj:
            return False
        
        # Calculate which section was clicked
        mx, my = mouse_pos
        section_col, section_row = self.scene.map.get_section_from_mouse(mx, my, grid_x, grid_y)
        
        if section_col is not None and section_row is not None:
            # Set highlight
            self.section_highlight = (grid_x, grid_y, section_col, section_row)
            
            # Handle section-specific interaction
            if hasattr(self.scene, 'resource_system'):
                # FIXED: Use proper layered pyramid mining
                if tile_obj.tile_type == 4:  # Mountain
                    # Use FIXED stepped pyramid mining
                    success = self.scene.resource_system.dig_section(
                        self.scene.unit_manager.units[0] if self.scene.unit_manager.units else None,
                        grid_x, grid_y, section_col, section_row
                    )
                    if success:
                        print(f"[FIXED Stepped Pyramid Renderer] Mined layer {tile_obj.height} section at ({grid_x}, {grid_y}) section ({section_col}, {section_row})")
                        return True
                else:
                    # Regular section mining
                    local_x = section_col / 3.0
                    local_y = section_row / 3.0
                    success = self.scene.map.damage_section_at_position(
                        grid_x, grid_y, local_x, local_y, 25.0
                    )
                    if success:
                        print(f"[FIXED 9-Section] Damaged section at ({grid_x}, {grid_y}) section ({section_col}, {section_row})")
                        return True
        
        return False

    def handle_water_interaction(self, mouse_pos, grid_x, grid_y):
        """Handle interactions with water tiles in FIXED 9-section system"""
        if not (getattr(self.scene, 'use_layered_terrain', False) and 
                hasattr(self.scene, 'terrain') and 
                hasattr(self.scene.terrain, 'water_system')):
            return False
        
        # Check if clicked position is water
        if (grid_x, grid_y) in self.scene.terrain.terrain_stacks:
            surface_tile = self.scene.terrain.get_surface_tile(grid_x, grid_y)
            if surface_tile == 2:  # ONLY regular water
                # Create splash effect (affects whole tile with 9 sections)
                if hasattr(self.scene, 'water_system'):
                    self.scene.water_system.create_splash(grid_x, grid_y, 2.0)
                elif hasattr(self.scene.terrain, 'water_system'):
                    self.scene.terrain.water_system.create_splash(grid_x, grid_y, 2.0)
                
                print(f"[FIXED 9-Section Renderer] Created water splash on FIXED block with 9 sections at ({grid_x}, {grid_y})")
                return True
        
        return False

    def toggle_section_grid_display(self):
        """Toggle display of 3x3 section grid overlay"""
        self.show_section_grid = not self.show_section_grid
        print(f"[FIXED 9-Section Renderer] Section grid display: {'ON' if self.show_section_grid else 'OFF'}")

    def clear_section_highlight(self):
        """Clear any section highlight"""
        self.section_highlight = None

    def draw_selection_rectangle(self, surface, start_pos, end_pos):
        """Draw selection rectangle for unit selection"""
        if not start_pos or not end_pos:
            return
            
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)
        
        # Draw selection rectangle
        rect = pygame.Rect(left, top, right - left, bottom - top)
        pygame.draw.rect(surface, (0, 255, 0), rect, 2)
        
        # Draw semi-transparent fill
        selection_surface = pygame.Surface((right - left, bottom - top), pygame.SRCALPHA)
        selection_surface.fill((0, 255, 0, 50))
        surface.blit(selection_surface, (left, top))

    def draw_movement_indicators(self, surface):
        """Draw movement path indicators for selected units"""
        for unit in self.scene.unit_manager.units:
            if not getattr(unit, 'selected', False) or not getattr(unit, 'path_tiles', []):
                continue
                
            # Draw path
            path_points = []
            for tile_x, tile_y in unit.path_tiles:
                if hasattr(self.scene, 'movement_system'):
                    screen_x, screen_y = self.scene.movement_system.grid_to_screen_coordinates(tile_x, tile_y)
                else:
                    # Fallback calculation
                    iso_x = (tile_x - tile_y) * (self.scene.tile_width // 2)
                    iso_y = (tile_x + tile_y) * (self.scene.tile_height // 2)
                    screen_x = iso_x + self.scene.map.camera_offset_x
                    screen_y = iso_y + self.scene.map.camera_offset_y
                
                path_points.append((int(screen_x), int(screen_y)))
            
            # Draw path line
            if len(path_points) > 1:
                pygame.draw.lines(surface, (255, 255, 0), False, path_points, 3)
            
            # Draw destination marker
            if path_points:
                dest_x, dest_y = path_points[-1]
                pygame.draw.circle(surface, (255, 0, 0), (int(dest_x), int(dest_y)), 8)
                pygame.draw.circle(surface, (255, 255, 255), (int(dest_x), int(dest_y)), 6)

    def get_render_stats(self):
        """Get rendering statistics for debugging with FIXED 9-section info"""
        stats = {
            "total_objects": len(self.scene.iso_objects),
            "total_sections": len(self.scene.iso_objects) * 9,
            "units": len(self.scene.unit_manager.units),
            "animals": len(self.scene.animal_manager.animals),
            "drops": len(self.scene.drops),
            "trees": len(self.scene.trees),
            "houses": len(self.scene.houses),
            "zoom_scale": self.scene.zoom_scale,
            "camera_pos": (self.scene.map.camera_offset_x, self.scene.map.camera_offset_y),
            "section_system": "FIXED 9-section internal subdivision",
            "pyramid_system": "FIXED stepped pyramid blocks",
            "section_grid_display": self.show_section_grid,
            "shadows": "disabled"
        }
        
        # Add FIXED terrain-specific stats
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            stats["terrain_stacks"] = len(self.scene.terrain.terrain_stacks)
            stats["total_blocks"] = sum(len(stack) for stack in self.scene.terrain.terrain_stacks.values())
            stats["max_height"] = max(
                self.scene.terrain.get_height_at(x, y) 
                for x, y in self.scene.terrain.terrain_stacks
            ) if self.scene.terrain.terrain_stacks else 0
            
            # Calculate average pyramid height
            if self.scene.terrain.terrain_stacks:
                avg_height = sum(
                    self.scene.terrain.get_height_at(x, y) 
                    for x, y in self.scene.terrain.terrain_stacks
                ) / len(self.scene.terrain.terrain_stacks)
                stats["avg_pyramid_height"] = round(avg_height, 2)
            
            # Add water system stats
            if hasattr(self.scene.terrain, 'water_system') and self.scene.terrain.water_system:
                water_system = self.scene.terrain.water_system
                stats["water_tiles"] = len(water_system.water_map)
                stats["water_sections"] = len(water_system.water_map) * 9
                stats["water_flow"] = "dynamic per-block"
                stats["tide_cycle"] = water_system.tide_period
                
                # Calculate average water level
                if water_system.water_map:
                    avg_level = sum(
                        data['current_level'] for data in water_system.water_map.values()
                    ) / len(water_system.water_map)
                    stats["avg_water_level"] = round(avg_level, 2)
            else:
                stats["water_flow"] = "static per-block"
        
        return stats

    def capture_screenshot(self, surface, filename=None):
        """Capture screenshot of current FIXED 9-section view"""
        if filename is None:
            import time
            filename = f"planet_fixed_pyramids_screenshot_{int(time.time())}.png"
        
        try:
            pygame.image.save(surface, filename)
            print(f"[FIXED 9-Section Renderer] Screenshot saved to {filename}")
            return True
        except Exception as e:
            print(f"[FIXED 9-Section Renderer] Error saving screenshot: {e}")
            return False

    # Additional methods for FIXED stepped pyramids
    def draw_grid_overlay(self, surface, alpha=50):
        """Draw grid overlay for debugging"""
        if not hasattr(self.scene, 'map_data'):
            return
            
        grid_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        for y in range(len(self.scene.map_data)):
            for x in range(len(self.scene.map_data[0])):
                # Calculate screen position
                iso_x = (x - y) * (self.scene.tile_width // 2) * self.scene.zoom_scale
                iso_y = (x + y) * (self.scene.tile_height // 2) * self.scene.zoom_scale
                screen_x = iso_x + self.scene.map.camera_offset_x
                screen_y = iso_y + self.scene.map.camera_offset_y
                
                # Draw tile outline
                tile_points = [
                    (screen_x, screen_y - self.scene.tile_height // 2 * self.scene.zoom_scale),
                    (screen_x + self.scene.tile_width // 2 * self.scene.zoom_scale, screen_y),
                    (screen_x, screen_y + self.scene.tile_height // 2 * self.scene.zoom_scale),
                    (screen_x - self.scene.tile_width // 2 * self.scene.zoom_scale, screen_y)
                ]
                
                pygame.draw.lines(grid_surface, (255, 255, 255, alpha), True, tile_points, 1)
        
        surface.blit(grid_surface, (0, 0))

    def draw_height_map_overlay(self, surface):
        """Draw height map overlay for FIXED layered terrain"""
        if not (self.scene.use_layered_terrain and hasattr(self.scene, 'terrain')):
            return
            
        height_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        for y in range(self.scene.terrain.height):
            for x in range(self.scene.terrain.width):
                if (x, y) not in self.scene.terrain.terrain_stacks:
                    continue
                    
                height = self.scene.terrain.get_height_at(x, y)
                if height <= 0:
                    continue
                
                # Calculate screen position for the TOP of the pyramid
                iso_x = (x - y) * (self.scene.tile_width // 2) * self.scene.zoom_scale
                iso_y = (x + y) * (self.scene.tile_height // 2) * self.scene.zoom_scale
                screen_x = iso_x + self.scene.map.camera_offset_x
                screen_y = iso_y + self.scene.map.camera_offset_y - height * 16 * self.scene.zoom_scale
                
                # Color based on height - FIXED pyramids
                intensity = min(255, height * 30)
                color = (intensity, 0, 255 - intensity, 100)
                
                # Draw height indicator
                pygame.draw.circle(height_surface, color, (int(screen_x), int(screen_y)), 
                                 int(5 * self.scene.zoom_scale))
                
                # Draw height text
                font = pygame.font.SysFont("Arial", 10)
                height_text = font.render(str(height), True, (255, 255, 255))
                surface.blit(height_text, (int(screen_x - 5), int(screen_y - 15)))
        
        surface.blit(height_surface, (0, 0))

    def draw_blocked_tiles_overlay(self, surface):
        """Draw overlay showing blocked tiles"""
        blocked_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        for x, y in self.scene.blocked_tiles:
            # Calculate screen position
            iso_x = (x - y) * (self.scene.tile_width // 2) * self.scene.zoom_scale
            iso_y = (x + y) * (self.scene.tile_height // 2) * self.scene.zoom_scale
            screen_x = iso_x + self.scene.map.camera_offset_x
            screen_y = iso_y + self.scene.map.camera_offset_y
            
            # Draw blocked indicator
            pygame.draw.circle(blocked_surface, (255, 0, 0, 100), 
                             (int(screen_x), int(screen_y)), 
                             int(10 * self.scene.zoom_scale))
        
        surface.blit(blocked_surface, (0, 0))

    def set_visual_effects(self, enable_effects=True):
        """Enable or disable visual effects for performance"""
        self.visual_effects_enabled = enable_effects
        
        if not enable_effects:
            print("[FIXED 9-Section Renderer] Visual effects disabled for better performance")
        else:
            print("[FIXED 9-Section Renderer] Visual effects enabled")

    def draw_minimap(self, surface, minimap_rect):
        """Draw a minimap view of the FIXED 9-section world"""
        if not hasattr(self.scene, 'map_data'):
            return
            
        minimap_surface = pygame.Surface((minimap_rect.width, minimap_rect.height))
        minimap_surface.fill((0, 0, 0))
        
        map_width = len(self.scene.map_data[0])
        map_height = len(self.scene.map_data)
        
        # Scale factors
        x_scale = minimap_rect.width / map_width
        y_scale = minimap_rect.height / map_height
        
        # Draw terrain (each pixel represents a FIXED stepped pyramid with 9 internal sections)
        for y in range(map_height):
            for x in range(map_width):
                tile_type = self.scene.map_data[y][x]
                
                # Choose color based on tile type - FIXED pyramids get special colors
                if tile_type == 1:  # Grass
                    color = (0, 128, 0)
                elif tile_type == 2:  # Water (only one type now)
                    color = (0, 0, 255)
                elif tile_type == 3:  # Dirt
                    color = (139, 69, 19)
                elif tile_type == 4:  # Stone/Mountain - FIXED stepped pyramids
                    # Check height for pyramid visualization
                    if (self.scene.use_layered_terrain and hasattr(self.scene, 'terrain') and 
                        (x, y) in self.scene.terrain.terrain_stacks):
                        height = self.scene.terrain.get_height_at(x, y)
                        # Color intensity based on pyramid height
                        intensity = min(255, 100 + height * 15)
                        color = (intensity, intensity, intensity)
                    else:
                        color = (128, 128, 128)
                elif tile_type == 11:  # Desert
                    color = (255, 215, 0)
                else:
                    color = (64, 64, 64)
                
                minimap_x = int(x * x_scale)
                minimap_y = int(y * y_scale)
                pygame.draw.rect(minimap_surface, color, 
                               (minimap_x, minimap_y, max(1, int(x_scale)), max(1, int(y_scale))))
        
        # Draw units as white dots
        for unit in self.scene.unit_manager.units:
            unit_x = int(unit.grid_x * x_scale)
            unit_y = int(unit.grid_y * y_scale)
            pygame.draw.circle(minimap_surface, (255, 255, 255), (unit_x, unit_y), 2)
        
        # Draw animals as yellow dots
        for animal in self.scene.animal_manager.animals:
            animal_x = int(animal.grid_x * x_scale)
            animal_y = int(animal.grid_y * y_scale)
            pygame.draw.circle(minimap_surface, (255, 255, 0), (animal_x, animal_y), 1)
        
        surface.blit(minimap_surface, minimap_rect)

    def draw_pyramid_analysis_overlay(self, surface):
        """Draw analysis overlay showing FIXED stepped pyramid structure"""
        if not (self.scene.use_layered_terrain and hasattr(self.scene, 'terrain')):
            return
            
        overlay_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        # Count pyramid types
        mountain_positions = []
        for (x, y), stack in self.scene.terrain.terrain_stacks.items():
            if any(tile.tile_type == 4 for tile in stack):  # Has mountain blocks
                height = len(stack)
                mountain_positions.append((x, y, height))
        
        # Draw pyramid height indicators
        for x, y, height in mountain_positions:
            # Calculate screen position
            iso_x = (x - y) * (32) * self.scene.zoom_scale
            iso_y = (x + y) * (18) * self.scene.zoom_scale
            screen_x = iso_x + self.scene.map.camera_offset_x
            screen_y = iso_y + self.scene.map.camera_offset_y - height * 16 * self.scene.zoom_scale
            
            # Color based on pyramid height
            if height >= 8:
                color = (255, 0, 0, 150)  # Red for tall pyramids
            elif height >= 5:
                color = (255, 165, 0, 150)  # Orange for medium pyramids
            else:
                color = (255, 255, 0, 150)  # Yellow for small pyramids
            
            # Draw pyramid indicator
            radius = int(8 * self.scene.zoom_scale * (height / 10.0))
            pygame.draw.circle(overlay_surface, color, (int(screen_x), int(screen_y)), radius)
            
            # Draw height text
            font = pygame.font.SysFont("Arial", 12)
            height_text = font.render(f"L{height}", True, (255, 255, 255))
            text_rect = height_text.get_rect(center=(int(screen_x), int(screen_y)))
            overlay_surface.blit(height_text, text_rect)
        
        surface.blit(overlay_surface, (0, 0))
        
        # Draw legend
        legend_y = 100
        font = pygame.font.SysFont("Arial", 14)
        legend_texts = [
            ("FIXED Stepped Pyramid Analysis:", (255, 255, 255)),
            ("Red: Tall pyramids (8+ layers)", (255, 0, 0)),
            ("Orange: Medium pyramids (5-7 layers)", (255, 165, 0)),
            ("Yellow: Small pyramids (2-4 layers)", (255, 255, 0))
        ]
        
        for i, (text, color) in enumerate(legend_texts):
            text_surf = font.render(text, True, color)
            surface.blit(text_surf, (10, legend_y + i * 20))