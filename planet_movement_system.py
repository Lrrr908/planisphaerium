##########################################################
# planet_movement_system.py
# Handles pathfinding, movement simulation, and tracking
##########################################################

import math
import heapq
import time

class PlanetMovementSystem:
    """Handles all pathfinding and movement simulation"""
    
    def __init__(self, scene):
        self.scene = scene

    def find_path(self, sx, sy, gx, gy):
        """Enhanced pathfinding with height awareness"""
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            return self._a_star_path_layered(sx, sy, gx, gy)
        else:
            return self._a_star_path(sx, sy, gx, gy)

    def _a_star_path_layered(self, sx, sy, gx, gy):
        """A* pathfinding that considers terrain height"""
        if (gx, gy) in self.scene.blocked_tiles or (sx, sy) == (gx, gy):
            return [(gx, gy)]
            
        w, h = self.scene.terrain.width, self.scene.terrain.height
        if not (0 <= sx < w and 0 <= sy < h and 0 <= gx < w and 0 <= gy < h):
            return None

        def hcost(ax, ay, bx, by):
            # Include height difference in cost calculation
            try:
                height_diff = abs(self.scene.terrain.get_height_at(bx, by) - 
                                 self.scene.terrain.get_height_at(ax, ay))
                base_cost = math.hypot(bx - ax, by - ay)
                return base_cost + (height_diff * 0.5)  # Height changes cost extra
            except:
                return math.hypot(bx - ax, by - ay)

        def can_move_to(from_x, from_y, to_x, to_y):
            """Check if movement between tiles is possible"""
            if (to_x, to_y) in self.scene.blocked_tiles:
                return False
            try:
                return self.scene.map.can_walk_to(from_x, from_y, to_x, to_y)
            except:
                # Fallback: allow movement if height difference is reasonable
                try:
                    from_height = self.scene.terrain.get_height_at(from_x, from_y)
                    to_height = self.scene.terrain.get_height_at(to_x, to_y)
                    height_diff = abs(to_height - from_height)
                    return height_diff <= 2  # Max climbable height
                except:
                    return True  # If we can't determine height, allow movement

        open_set = []
        g = {(sx, sy): 0}
        f = {(sx, sy): hcost(sx, sy, gx, gy)}
        came = {}
        heapq.heappush(open_set, (f[(sx, sy)], (sx, sy)))
        moves = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]

        while open_set:
            _, (cx, cy) = heapq.heappop(open_set)
            if (cx, cy) == (gx, gy):
                return self._reconstruct(came, (gx, gy))
            for dx, dy in moves:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h and can_move_to(cx, cy, nx, ny):
                    ng = g[(cx, cy)] + hcost(cx, cy, nx, ny)
                    if ng < g.get((nx, ny), float("inf")):
                        came[(nx, ny)] = (cx, cy)
                        g[(nx, ny)] = ng
                        fval = ng + hcost(nx, ny, gx, gy)
                        f[(nx, ny)] = fval
                        heapq.heappush(open_set, (fval, (nx, ny)))
        return None

    def _a_star_path(self, sx, sy, gx, gy):
        """Standard A* pathfinding for flat terrain"""
        if (gx, gy) in self.scene.blocked_tiles or (sx, sy) == (gx, gy):
            return [(gx, gy)]
        w, h = self.scene.map.width, self.scene.map.height
        if not (0 <= sx < w and 0 <= sy < h and 0 <= gx < w and 0 <= gy < h):
            return None

        def hcost(ax, ay, bx, by):
            return math.hypot(bx - ax, by - ay)

        open_set = []
        g = {(sx, sy): 0}
        f = {(sx, sy): hcost(sx, sy, gx, gy)}
        came = {}
        heapq.heappush(open_set, (f[(sx, sy)], (sx, sy)))
        moves = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]

        while open_set:
            _, (cx, cy) = heapq.heappop(open_set)
            if (cx, cy) == (gx, gy):
                return self._reconstruct(came, (gx, gy))
            for dx, dy in moves:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in self.scene.blocked_tiles:
                    ng = g[(cx, cy)] + math.hypot(dx, dy)
                    if ng < g.get((nx, ny), float("inf")):
                        came[(nx, ny)] = (cx, cy)
                        g[(nx, ny)] = ng
                        fval = ng + hcost(nx, ny, gx, gy)
                        f[(nx, ny)] = fval
                        heapq.heappush(open_set, (fval, (nx, ny)))
        return None

    @staticmethod
    def _reconstruct(came, cur):
        """Reconstruct path from A* came dict"""
        path = [cur]
        while cur in came:
            cur = came[cur]
            path.append(cur)
        return path[::-1]

    def handle_right_click_movement(self, event):
        """Handle right-click movement commands with tracking"""
        try:
            if self.scene.unit_manager.units:
                # Get selected unit or first unit
                selected_unit = None
                for unit in self.scene.unit_manager.units:
                    if getattr(unit, 'selected', False):
                        selected_unit = unit
                        break
                
                if not selected_unit and self.scene.unit_manager.units:
                    selected_unit = self.scene.unit_manager.units[0]
                
                if selected_unit:
                    # Convert screen coordinates to tile coordinates
                    mx, my = event.pos
                    world_x = mx - self.scene.map.camera_offset_x
                    world_y = my - self.scene.map.camera_offset_y
                    
                    # Convert to grid coordinates (basic iso conversion)
                    tile_x = int((world_x / (self.scene.tile_width // 2) + world_y / (self.scene.tile_height // 2)) / 2)
                    tile_y = int((world_y / (self.scene.tile_height // 2) - world_x / (self.scene.tile_width // 2)) / 2)
                    
                    # Clamp to map bounds
                    tile_x = max(0, min(tile_x, len(self.scene.map_data[0]) - 1))
                    tile_y = max(0, min(tile_y, len(self.scene.map_data) - 1))
                    
                    # Find path and set destination
                    path = self.find_path(selected_unit.grid_x, selected_unit.grid_y, tile_x, tile_y)
                    if path:
                        selected_unit.path_tiles = path
                        selected_unit.path_index = 0
                        selected_unit.destination_x = tile_x
                        selected_unit.destination_y = tile_y
                        selected_unit.mission = "MOVE_TO"
                        selected_unit.moving = True
                        
                        # Set next tile info for better tracking
                        if len(path) > 1:
                            selected_unit.next_tile_x = path[1][0]
                            selected_unit.next_tile_y = path[1][1] 
                        else:
                            selected_unit.next_tile_x = tile_x
                            selected_unit.next_tile_y = tile_y
                        
                        # Track this command (with error handling)
                        unit_id = getattr(selected_unit, 'unit_id', 'unknown_unit')
                        print(f"[BiPed] Moving unit {unit_id} to ({tile_x}, {tile_y}) via {len(path)} tile path")
                        
                        # Immediately save the movement command
                        if hasattr(self.scene, 'entity_manager'):
                            self.scene.entity_manager.on_biped_command(selected_unit, "MOVE_TO")
                        
                        # Force immediate save to ensure command persistence
                        if hasattr(self.scene, 'entity_manager'):
                            self.scene.entity_manager.auto_save_trigger("movement_command_immediate")
                    else:
                        print(f"[BiPed] No valid path found to ({tile_x}, {tile_y})")
            
            # Also call the original handler for other right-click functionality
            self.scene.unit_manager.handle_right_click(event)
        except Exception as e:
            print(f"[PlanetScene] Error handling right-click movement: {e}")
            # Fall back to original handler only
            self.scene.unit_manager.handle_right_click(event)

    def simulate_time_away_movement(self):
        """Simulate movement progress for bipeds while player was away"""
        if self.scene.simulation_mode == "paused":
            print("[PlanetScene] Simulation mode is PAUSED - bipeds did not move while away")
            return
            
        print("[PlanetScene] Simulation mode is REALTIME - checking biped progress while away")
        
        current_time = time.time()
        moving_bipeds = []
        
        for biped in self.scene.unit_manager.units:
            if getattr(biped, 'moving', False) and hasattr(biped, 'last_command_time'):
                time_away = current_time - biped.last_command_time
                if time_away > 1.0:  # Only simulate if more than 1 second away
                    moving_bipeds.append((biped, time_away))
        
        if moving_bipeds:
            print(f"[PlanetScene] Simulating movement for {len(moving_bipeds)} bipeds")
            
            for biped, time_away in moving_bipeds:
                unit_id = getattr(biped, 'unit_id', 'unknown')
                print(f"[PlanetScene] Simulating {time_away:.1f}s of movement for {unit_id}")
                
                # Simulate the movement progress
                if hasattr(self.scene, 'entity_manager'):
                    result = self.scene.entity_manager.simulate_movement_progress(biped, time_away)
                    print(f"[PlanetScene] Simulation result for {unit_id}: {result}")
                    
                    # Check if the biped completed its path
                    if (biped.destination_x is not None and biped.destination_y is not None and
                        biped.grid_x == biped.destination_x and biped.grid_y == biped.destination_y):
                        print(f"[PlanetScene] {unit_id} completed its path while away!")
                        self.scene.entity_manager.handle_path_completion(biped)

    def resume_biped_movement(self, biped):
        """Resume movement for a biped that was moving when the planet was saved"""
        try:
            # Validate the path exists and is valid
            if not biped.path_tiles or biped.path_index >= len(biped.path_tiles):
                print(f"[PlanetScene] Cannot resume movement for {biped.unit_id}: invalid path")
                biped.moving = False
                biped.mission = "IDLE"
                return False
                
            # Check if the destination is still reachable
            dest_x, dest_y = biped.destination_x, biped.destination_y
            if dest_x is None or dest_y is None:
                print(f"[PlanetScene] Cannot resume movement for {biped.unit_id}: no destination")
                biped.moving = False
                biped.mission = "IDLE" 
                return False
                
            # Validate destination is not blocked
            if (dest_x, dest_y) in self.scene.blocked_tiles:
                print(f"[PlanetScene] Destination ({dest_x}, {dest_y}) is now blocked, recalculating path for {biped.unit_id}")
                # Recalculate path to destination
                new_path = self.find_path(biped.grid_x, biped.grid_y, dest_x, dest_y)
                if new_path:
                    biped.path_tiles = new_path
                    biped.path_index = 0
                    biped.moving = True
                    print(f"[PlanetScene] New path calculated with {len(new_path)} tiles")
                else:
                    print(f"[PlanetScene] No valid path to destination, stopping movement")
                    biped.moving = False
                    biped.mission = "IDLE"
                    return False
            
            # Ensure the biped is properly configured for movement
            biped.moving = True
            if biped.mission in ["IDLE", ""]:
                biped.mission = "MOVE_TO"
                
            print(f"[PlanetScene] Successfully resumed movement for {biped.unit_id}")
            print(f"              Current: ({biped.grid_x}, {biped.grid_y}) -> Target: ({dest_x}, {dest_y})")
            print(f"              Path progress: {biped.path_index}/{len(biped.path_tiles)} tiles")
            
            return True
            
        except Exception as e:
            print(f"[PlanetScene] Error resuming movement for {biped.unit_id}: {e}")
            biped.moving = False
            biped.mission = "IDLE"
            return False

    def validate_movement_state(self):
        """Validate and fix any movement state issues"""
        for biped in self.scene.unit_manager.units:
            try:
                # Check for corrupted movement state
                if getattr(biped, 'moving', False):
                    # Ensure path exists
                    if not getattr(biped, 'path_tiles', []):
                        print(f"[Movement] Fixing biped {getattr(biped, 'unit_id', 'unknown')} - no path but marked as moving")
                        biped.moving = False
                        biped.mission = "IDLE"
                        continue
                    
                    # Ensure path index is valid
                    path_index = getattr(biped, 'path_index', 0)
                    if path_index >= len(biped.path_tiles):
                        print(f"[Movement] Fixing biped {getattr(biped, 'unit_id', 'unknown')} - path index out of bounds")
                        biped.moving = False
                        biped.mission = "IDLE"
                        continue
                    
                    # Ensure destination exists
                    if (getattr(biped, 'destination_x', None) is None or 
                        getattr(biped, 'destination_y', None) is None):
                        print(f"[Movement] Fixing biped {getattr(biped, 'unit_id', 'unknown')} - no destination")
                        biped.moving = False
                        biped.mission = "IDLE"
                        continue
                        
            except Exception as e:
                print(f"[Movement] Error validating biped movement state: {e}")
                # Reset to safe state
                biped.moving = False
                biped.mission = "IDLE"
                biped.path_tiles = []
                biped.path_index = 0

    def get_movement_debug_info(self):
        """Get debug information about current movement state"""
        debug_info = {
            "total_bipeds": len(self.scene.unit_manager.units),
            "moving_bipeds": 0,
            "with_paths": 0,
            "moving_details": []
        }
        
        for unit in self.scene.unit_manager.units:
            if getattr(unit, 'moving', False):
                debug_info["moving_bipeds"] += 1
                
            if getattr(unit, 'path_tiles', []):
                debug_info["with_paths"] += 1
                
            if getattr(unit, 'moving', False):
                unit_id = getattr(unit, 'unit_id', 'unknown')[:12]
                dest_x = getattr(unit, 'destination_x', '?')
                dest_y = getattr(unit, 'destination_y', '?')
                path_progress = f"{getattr(unit, 'path_index', 0)}/{len(getattr(unit, 'path_tiles', []))}"
                
                detail = {
                    "unit_id": unit_id,
                    "current_pos": (unit.grid_x, unit.grid_y),
                    "destination": (dest_x, dest_y),
                    "path_progress": path_progress,
                    "mission": getattr(unit, 'mission', 'UNKNOWN')
                }
                
                # Add height info for layered terrain
                if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
                    detail["current_height"] = self.scene.terrain.get_height_at(unit.grid_x, unit.grid_y)
                    
                debug_info["moving_details"].append(detail)
        
        return debug_info

    def screen_to_grid_coordinates(self, screen_x, screen_y):
        """Convert screen coordinates to grid coordinates"""
        world_x = screen_x - self.scene.map.camera_offset_x
        world_y = screen_y - self.scene.map.camera_offset_y
        
        # Convert to grid coordinates (basic iso conversion)
        tile_x = int((world_x / (self.scene.tile_width // 2) + world_y / (self.scene.tile_height // 2)) / 2)
        tile_y = int((world_y / (self.scene.tile_height // 2) - world_x / (self.scene.tile_width // 2)) / 2)
        
        # Clamp to map bounds
        if hasattr(self.scene, 'map_data') and self.scene.map_data:
            tile_x = max(0, min(tile_x, len(self.scene.map_data[0]) - 1))
            tile_y = max(0, min(tile_y, len(self.scene.map_data) - 1))
        
        return tile_x, tile_y

    def grid_to_screen_coordinates(self, grid_x, grid_y):
        """Convert grid coordinates to screen coordinates"""
        # Standard isometric projection
        iso_x = (grid_x - grid_y) * (self.scene.tile_width // 2)
        iso_y = (grid_x + grid_y) * (self.scene.tile_height // 2)
        
        # Add camera offset
        screen_x = iso_x + self.scene.map.camera_offset_x
        screen_y = iso_y + self.scene.map.camera_offset_y
        
        # Add height offset for layered terrain
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            terrain_height = self.scene.terrain.get_height_at(grid_x, grid_y)
            height_offset = terrain_height * 16 * self.scene.zoom_scale
            screen_y -= height_offset
        
        return screen_x, screen_y

    def is_position_walkable(self, x, y):
        """Check if a position is walkable"""
        # Check bounds
        if (x < 0 or y < 0 or 
            y >= len(self.scene.map_data) or 
            x >= len(self.scene.map_data[0])):
            return False
            
        # Check if blocked
        if (x, y) in self.scene.blocked_tiles:
            return False
            
        # Check terrain type
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            if (x, y) not in self.scene.terrain.terrain_stacks:
                return False
            surface_tile = self.scene.terrain.get_surface_tile(x, y)
            height = self.scene.terrain.get_height_at(x, y)
            # Don't allow walking on water or extremely high terrain
            if surface_tile in (2, 5) or height > 6:  # TILE_WATER, TILE_WATERSTACK
                return False
        else:
            # Legacy terrain check
            if self.scene.map_data[y][x] in (2, 5, 4):  # Water or mountain
                return False
                
        return True

    def calculate_movement_cost(self, from_x, from_y, to_x, to_y):
        """Calculate movement cost between two positions"""
        base_cost = math.hypot(to_x - from_x, to_y - from_y)
        
        # Add height penalty for layered terrain
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            try:
                from_height = self.scene.terrain.get_height_at(from_x, from_y)
                to_height = self.scene.terrain.get_height_at(to_x, to_y)
                height_diff = abs(to_height - from_height)
                return base_cost + (height_diff * 0.5)
            except:
                pass
                
        return base_cost