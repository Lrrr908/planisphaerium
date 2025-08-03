##########################################################
# arcade_movement_system.py
# Handles pathfinding, movement simulation, and tracking for Arcade
##########################################################

import math
import heapq
import time

TILE_WIDTH = 64
TILE_HEIGHT = 37

class ArcadeMovementSystem:
    """Handles all pathfinding and movement simulation for Arcade"""
    
    def __init__(self, scene):
        self.scene = scene

    def find_path(self, sx, sy, gx, gy):
        """Simple pathfinding using A*"""
        return self._a_star_path(sx, sy, gx, gy)

    def _a_star_path(self, sx, sy, gx, gy):
        """A* pathfinding for grid movement"""
        if (gx, gy) in self.scene.blocked_tiles or (sx, sy) == (gx, gy):
            return [(gx, gy)]
            
        w, h = len(self.scene.map_data[0]), len(self.scene.map_data)
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

    def handle_right_click_movement(self, screen_x, screen_y):
        """Handle right-click movement commands"""
        try:
            if self.scene.biped_sprites:
                # Get first biped (can be enhanced to handle selected biped)
                biped = self.scene.biped_sprites[0]
                
                # Convert screen coordinates to grid coordinates
                grid_x, grid_y = self._screen_to_grid(screen_x, screen_y)
                
                # Clamp to map bounds
                grid_x = max(0, min(grid_x, len(self.scene.map_data[0]) - 1))
                grid_y = max(0, min(grid_y, len(self.scene.map_data) - 1))
                
                # Check if target is valid
                if (grid_x, grid_y) in self.scene.blocked_tiles:
                    print(f"[ArcadeMovementSystem] Target ({grid_x}, {grid_y}) is blocked")
                    return
                
                # Convert target to isometric coordinates
                target_iso_x = (grid_x - grid_y) * (TILE_WIDTH // 2)
                target_iso_y = (grid_x + grid_y) * (TILE_HEIGHT // 2)
                
                # Set movement target
                biped.target_x = target_iso_x
                biped.target_y = target_iso_y
                biped.moving = True
                biped.mission = "MOVE_TO"
                
                print(f"[ArcadeMovementSystem] Moving biped to grid ({grid_x}, {grid_y}) iso ({target_iso_x}, {target_iso_y})")
                
                # Track the command
                if hasattr(self.scene, 'entity_manager'):
                    self.scene.entity_manager.on_biped_command(biped, "MOVE_TO")
        
        except Exception as e:
            print(f"[ArcadeMovementSystem] Error handling right-click movement: {e}")

    def _screen_to_grid(self, screen_x, screen_y):
        """Convert screen coordinates to grid coordinates"""
        # Get camera position
        camera_x, camera_y = self.scene.camera.position if self.scene.camera else (0, 0)
        
        # Convert to world coordinates
        world_x = screen_x + camera_x
        world_y = screen_y + camera_y
        
        # Convert to grid coordinates (isometric conversion)
        # This is a simplified conversion - may need adjustment based on exact isometric setup
        tile_x = int((world_x / (TILE_WIDTH // 2) + world_y / (TILE_HEIGHT // 2)) / 2)
        tile_y = int((world_y / (TILE_HEIGHT // 2) - world_x / (TILE_WIDTH // 2)) / 2)
        
        return tile_x, tile_y

    def _grid_to_screen(self, grid_x, grid_y):
        """Convert grid coordinates to screen coordinates"""
        # Get camera position
        camera_x, camera_y = self.scene.camera.position if self.scene.camera else (0, 0)
        
        # Standard isometric projection
        iso_x = (grid_x - grid_y) * (TILE_WIDTH // 2)
        iso_y = (grid_x + grid_y) * (TILE_HEIGHT // 2)
        
        # Convert to screen coordinates
        screen_x = iso_x - camera_x
        screen_y = iso_y - camera_y
        
        return screen_x, screen_y

    def simulate_time_away_movement(self):
        """Simulate movement progress for bipeds while player was away"""
        if self.scene.simulation_mode == "paused":
            print("[ArcadeMovementSystem] Simulation mode is PAUSED - bipeds did not move while away")
            return
            
        print("[ArcadeMovementSystem] Simulation mode is REALTIME - checking biped progress while away")
        
        current_time = time.time()
        moving_bipeds = []
        
        for biped in self.scene.biped_sprites:
            if (hasattr(biped, 'moving') and biped.moving and 
                hasattr(biped, 'last_command_time')):
                time_away = current_time - biped.last_command_time
                if time_away > 1.0:  # Only simulate if more than 1 second away
                    moving_bipeds.append((biped, time_away))
        
        if moving_bipeds:
            print(f"[ArcadeMovementSystem] Simulating movement for {len(moving_bipeds)} bipeds")
            
            for biped, time_away in moving_bipeds:
                unit_id = getattr(biped, 'unit_id', 'unknown')
                print(f"[ArcadeMovementSystem] Simulating {time_away:.1f}s of movement for {unit_id}")
                
                # Simulate the movement progress
                if hasattr(self.scene, 'entity_manager'):
                    result = self.scene.entity_manager.simulate_movement_progress(biped, time_away)
                    print(f"[ArcadeMovementSystem] Simulation result for {unit_id}: {result}")

    def validate_movement_state(self):
        """Validate and fix any movement state issues"""
        for biped in self.scene.biped_sprites:
            try:
                # Check for corrupted movement state
                if hasattr(biped, 'moving') and biped.moving:
                    # Ensure target exists
                    if not (hasattr(biped, 'target_x') and hasattr(biped, 'target_y')):
                        print(f"[ArcadeMovementSystem] Fixing biped {getattr(biped, 'unit_id', 'unknown')} - no target but marked as moving")
                        biped.moving = False
                        if hasattr(biped, 'mission'):
                            biped.mission = "IDLE"
                        continue
                        
            except Exception as e:
                print(f"[ArcadeMovementSystem] Error validating biped movement state: {e}")
                # Reset to safe state
                biped.moving = False
                if hasattr(biped, 'mission'):
                    biped.mission = "IDLE"

    def get_movement_debug_info(self):
        """Get debug information about current movement state"""
        debug_info = {
            "total_bipeds": len(self.scene.biped_sprites),
            "moving_bipeds": 0,
            "moving_details": []
        }
        
        for biped in self.scene.biped_sprites:
            if hasattr(biped, 'moving') and biped.moving:
                debug_info["moving_bipeds"] += 1
                
                unit_id = getattr(biped, 'unit_id', 'unknown')[:12]
                target_x = getattr(biped, 'target_x', '?')
                target_y = getattr(biped, 'target_y', '?')
                
                detail = {
                    "unit_id": unit_id,
                    "current_pos": (biped.center_x, biped.center_y),
                    "target": (target_x, target_y),
                    "mission": getattr(biped, 'mission', 'UNKNOWN')
                }
                
                debug_info["moving_details"].append(detail)
        
        return debug_info

    def screen_to_grid_coordinates(self, screen_x, screen_y):
        """Convert screen coordinates to grid coordinates (public method)"""
        return self._screen_to_grid(screen_x, screen_y)

    def grid_to_screen_coordinates(self, grid_x, grid_y):
        """Convert grid coordinates to screen coordinates (public method)"""
        return self._grid_to_screen(grid_x, grid_y)

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
        if self.scene.map_data[y][x] in (2, 5, 4, -1):  # Water, mountain, void
            return False
                
        return True

    def calculate_movement_cost(self, from_x, from_y, to_x, to_y):
        """Calculate movement cost between two positions"""
        return math.hypot(to_x - from_x, to_y - from_y)

    def find_nearest_walkable_position(self, target_x, target_y, max_radius=5):
        """Find the nearest walkable position to a target"""
        if self.is_position_walkable(target_x, target_y):
            return target_x, target_y
        
        # Search in expanding circles
        for radius in range(1, max_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) == radius or abs(dy) == radius:  # Only check perimeter
                        test_x, test_y = target_x + dx, target_y + dy
                        if self.is_position_walkable(test_x, test_y):
                            return test_x, test_y
        
        return None

    def get_path_length(self, path):
        """Calculate the total length of a path"""
        if not path or len(path) < 2:
            return 0.0
        
        total_length = 0.0
        for i in range(1, len(path)):
            dx = path[i][0] - path[i-1][0]
            dy = path[i][1] - path[i-1][1]
            total_length += math.hypot(dx, dy)
        
        return total_length

    def smooth_path(self, path):
        """Smooth a path by removing unnecessary waypoints"""
        if not path or len(path) < 3:
            return path
        
        smoothed = [path[0]]
        
        i = 0
        while i < len(path) - 1:
            # Try to find the furthest point we can reach directly
            furthest = i + 1
            for j in range(i + 2, len(path)):
                if self._has_line_of_sight(path[i], path[j]):
                    furthest = j
                else:
                    break
            
            smoothed.append(path[furthest])
            i = furthest
        
        return smoothed

    def _has_line_of_sight(self, start, end):
        """Check if there's a clear line of sight between two points"""
        x0, y0 = start
        x1, y1 = end
        
        # Use Bresenham's line algorithm to check each point
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        
        x, y = x0, y0
        
        x_inc = 1 if x1 > x0 else -1
        y_inc = 1 if y1 > y0 else -1
        
        error = dx - dy
        
        for _ in range(dx + dy):
            if not self.is_position_walkable(x, y):
                return False
            
            if x == x1 and y == y1:
                break
            
            error2 = error * 2
            
            if error2 > -dy:
                error -= dy
                x += x_inc
            
            if error2 < dx:
                error += dx
                y += y_inc
        
        return True