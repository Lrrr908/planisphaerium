##########################################################
# planet_event_handler.py
# Handles input processing, events, and UI interactions
##########################################################

import pygame
import math
import time

class PlanetEventHandler:
    """Handles all input processing and event management"""
    
    def __init__(self, scene):
        self.scene = scene

    def handle_events(self, events):
        """Main event handling dispatch"""
        for event in events:
            if event.type == pygame.QUIT:
                self.scene.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event)

            elif event.type == pygame.MOUSEBUTTONUP:
                self._handle_mouse_up(event)

            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(event)

            elif event.type == pygame.MOUSEWHEEL:
                self._handle_zoom(event)

            elif event.type == pygame.KEYDOWN:
                self._handle_key_down(event)

        # Forward events to unit manager
        self.scene.unit_manager.handle_events(events)

    def _handle_mouse_down(self, event):
        """Handle mouse button down events"""
        if event.button == 1:  # Left click
            self._handle_left_click(event)
        elif event.button == 3:  # Right click
            self._handle_right_click(event)

    def _handle_left_click(self, event):
        """Handle left mouse button clicks"""
        # Check for sub-tile building/mining first
        if hasattr(self.scene, 'subtile_manager'):
            mx, my = event.pos
            tile_x, tile_y = self._screen_to_grid(mx, my)
            
            # Clamp to map bounds
            if (0 <= tile_x < len(self.scene.map_data[0]) and 0 <= tile_y < len(self.scene.map_data)):
                if self.scene.subtile_manager.handle_click(event.pos, tile_x, tile_y):
                    # Update tile graphics
                    self.scene.map.invalidate_tile(tile_x, tile_y)
                    return  # Click consumed
        
        # Check for mining mode first
        if getattr(self.scene, 'mining_mode', False) and self.scene.use_layered_terrain:
            if self._handle_mining_click(event.pos):
                return  # Mining click consumed
        
        # Try to select a unit first
        if self.scene.unit_manager.select_unit_at(event.pos):
            return  # click consumed – no camera drag

        # Otherwise start dragging the map
        self.scene.dragging = True
        self.scene.last_mouse_pos = pygame.mouse.get_pos()

        # Check if we clicked a resource drop
        self._check_drop_collection(event.pos)

    def _handle_right_click(self, event):
        """Handle right mouse button clicks"""
        # Handle right-click movement commands with tracking
        if hasattr(self.scene, 'movement_system'):
            self.scene.movement_system.handle_right_click_movement(event)
        else:
            # Fallback to unit manager
            self.scene.unit_manager.handle_right_click(event)

    def _handle_mouse_up(self, event):
        """Handle mouse button up events"""
        if event.button == 1:  # Left click release
            self.scene.dragging = False

    def _handle_mouse_motion(self, event):
        """Handle mouse motion events"""
        mx, my = event.pos
        
        # Update drop hover states
        for drop in self.scene.drops:
            drop.hovered = drop.get_rect().collidepoint(mx, my)
        
        # Handle camera dragging
        if self.scene.dragging:
            self.scene.map.update_camera(mx - self.scene.last_mouse_pos[0], my - self.scene.last_mouse_pos[1])
            self.scene.last_mouse_pos = (mx, my)

    def _handle_key_down(self, event):
        """Handle keyboard input"""
        if event.key == pygame.K_ESCAPE:
            self.scene.running = False
            
        elif event.key == pygame.K_h:
            self._attempt_build_first_house()
            
        elif event.key == pygame.K_t:
            self._toggle_simulation_mode()
            
        elif event.key == pygame.K_l:
            self._toggle_terrain_system()
            
        elif event.key == pygame.K_m:
            self._toggle_mining_mode()
            
        elif event.key == pygame.K_r:
            if event.mod & pygame.KMOD_CTRL:
                self._regenerate_world()

    def _handle_zoom(self, event):
        """Handle mouse wheel zoom events"""
        mx, my = pygame.mouse.get_pos()
        old_zoom = self.scene.zoom_scale

        # Change zoom
        if event.y > 0:
            self.scene.zoom_scale *= 1.1
        else:
            self.scene.zoom_scale /= 1.1
        self.scene.zoom_scale = max(0.1, min(self.scene.zoom_scale, 5.0))

        # Keep cursor anchored
        ratio = self.scene.zoom_scale / old_zoom
        wx, wy = mx - self.scene.map.camera_offset_x, my - self.scene.map.camera_offset_y
        self.scene.map.camera_offset_x = mx - wx * ratio
        self.scene.map.camera_offset_y = my - wy * ratio

        # Propagate to everything that depends on scale
        self.scene._propagate_zoom()

    def _handle_mining_click(self, mouse_pos):
        """Handle mining/digging when in mining mode"""
        if not self.scene.use_layered_terrain or not hasattr(self.scene, 'resource_system'):
            return False
            
        mx, my = mouse_pos
        tile_x, tile_y = self._screen_to_grid(mx, my)
        
        # Clamp to map bounds
        tile_x = max(0, min(tile_x, self.scene.terrain.width - 1))
        tile_y = max(0, min(tile_y, self.scene.terrain.height - 1))
        
        # Find nearest biped to do the digging
        if not self.scene.unit_manager.units:
            print("[Mining] No bipeds available for digging")
            return True
            
        # Get closest biped
        closest_biped = min(self.scene.unit_manager.units, 
                           key=lambda u: math.hypot(u.grid_x - tile_x, u.grid_y - tile_y))
        
        # Check if biped can dig here
        if self.scene.resource_system.can_biped_dig(closest_biped, tile_x, tile_y):
            success = self.scene.resource_system.dig_tile(closest_biped, tile_x, tile_y)
            if success:
                print(f"[Mining] Biped dug tile at ({tile_x}, {tile_y})")
                # Update map rendering with procedural tiles
                from iso_map import ProceduralIsoMap
                self.scene.map = ProceduralIsoMap(self.scene.terrain.surface_map, self.scene.subtile_manager, self.scene.terrain)
                self.scene.iso_objects = self.scene.map.get_all_objects() + self.scene.trees + self.scene.houses
                # Recalculate blocked tiles
                if hasattr(self.scene, 'world_generator'):
                    self.scene.blocked_tiles = self.scene.world_generator._calculate_blocked_tiles_layered()
            else:
                print(f"[Mining] Failed to dig tile at ({tile_x}, {tile_y})")
        else:
            dist = math.hypot(closest_biped.grid_x - tile_x, closest_biped.grid_y - tile_y)
            print(f"[Mining] Cannot dig at ({tile_x}, {tile_y}) - distance: {dist:.1f}, tool insufficient, or tile too hard")
        
        return True

    def _check_drop_collection(self, mouse_pos):
        """Check if clicked on a resource drop and send biped to collect"""
        mx, my = mouse_pos
        for drop in self.scene.drops:
            if drop.get_rect().collidepoint(mx, my):
                if hasattr(self.scene, 'entity_manager'):
                    self.scene.entity_manager.send_biped_to_collect(drop)
                else:
                    # Fallback
                    self.scene.send_biped_to_collect(drop)
                break

    def _attempt_build_first_house(self):
        """Attempt to build the first house"""
        if getattr(self.scene, 'house_built', False) or not self.scene.unit_manager.units:
            return

        b0 = self.scene.unit_manager.units[0]
        gx, gy = b0.grid_x, b0.grid_y
        if (gx, gy) in self.scene.blocked_tiles:
            print("Tile blocked – can't build.")
            return

        # Get house height for layered terrain
        house_height = 0
        if self.scene.use_layered_terrain and hasattr(self.scene, 'terrain'):
            house_height = self.scene.terrain.get_height_at(gx, gy)

        # Place house object
        from iso_map import IsoTree
        house = IsoTree(gx, gy, 99, 0.5, 0, original_image=self.scene.house_image, height=house_height)
        house.draw_order = (gx + gy) * 10 + 6  # Layer 6: above trees
        house.set_zoom_scale(self.scene.zoom_scale)
        self.scene.houses.append(house)
        self.scene.iso_objects.append(house)
        self.scene.blocked_tiles.add((gx, gy))
        self.scene.house_built = True
        print(f"House built at {gx}, {gy}")

        # Spawn two extra bipeds
        self._spawn_house_bipeds(gx, gy)

    def _spawn_house_bipeds(self, house_x, house_y):
        """Spawn additional bipeds near the new house"""
        import time
        from unit_manager import create_biped_frames, BipedUnit
        
        def _rand_colour():
            import random
            return random.randint(64, 255), random.randint(64, 255), random.randint(64, 255)
        
        current_time = time.time()
        for idx, colour in enumerate([_rand_colour(), _rand_colour()]):
            if hasattr(self.scene, 'entity_manager'):
                tile = self.scene.entity_manager.find_valid_land_tile(
                    [(house_x + dx, house_y + dy)
                     for dx in range(-4, 5)
                     for dy in range(-4, 5)]
                )
            else:
                # Fallback
                tile = self.scene.find_valid_land_tile(
                    [(house_x + dx, house_y + dy)
                     for dx in range(-4, 5)
                     for dy in range(-4, 5)]
                )
            if not tile:
                continue

            bx, by = tile
            u = BipedUnit(
                self.scene, bx, by,
                frames=create_biped_frames(colour, 4, 32, 48),
                speed=2.4,
            )
            
            # Enhanced tracking for house-spawned bipeds
            u.unit_id = f"house_biped_{idx}_{house_x}_{house_y}_{int(current_time)}"
            u.color = colour
            u.creation_time = current_time
            u.last_command_time = current_time
            u.health = 100
            u.max_health = 100
            u.inventory = {}
            u.mission = "IDLE"
            u.mission_data = {}
            u.path_tiles = []
            u.path_index = 0
            u.destination_x = None
            u.destination_y = None
            u.moving = False
            u.move_progress = 0.0
            u.selected = False
            u.facing_direction = "down"
            
            u.set_zoom_scale(self.scene.zoom_scale)
            self.scene.unit_manager.add_unit(u)
            u.calculate_screen_position(
                self.scene.map.camera_offset_x,
                self.scene.map.camera_offset_y,
                self.scene.zoom_scale,
            )

    def _toggle_simulation_mode(self):
        """Toggle between paused and realtime simulation"""
        if self.scene.simulation_mode == "paused":
            self.scene.simulation_mode = "realtime"
            print("[PlanetScene] Switched to REALTIME simulation - bipeds work while you're away!")
        else:
            self.scene.simulation_mode = "paused"
            print("[PlanetScene] Switched to PAUSED simulation - bipeds freeze when you leave")

    def _toggle_terrain_system(self):
        """Toggle terrain system information display"""
        if hasattr(self.scene, 'use_layered_terrain'):
            print(f"[PlanetScene] Layered terrain: {'ON' if self.scene.use_layered_terrain else 'OFF'}")
            print("[PlanetScene] Press Ctrl+R to regenerate world with different terrain system")

    def _toggle_mining_mode(self):
        """Toggle mining mode for digging terrain"""
        if self.scene.use_layered_terrain:
            self.scene.mining_mode = not getattr(self.scene, 'mining_mode', False)
            mode_text = "ON" if self.scene.mining_mode else "OFF"
            print(f"[PlanetScene] Mining mode: {mode_text}")
            if self.scene.mining_mode:
                print("[PlanetScene] Left-click on terrain to dig/mine. Bipeds will automatically do the work.")

    def _regenerate_world(self):
        """Regenerate the world (for testing)"""
        print("[PlanetScene] Regenerating world...")
        self.scene.meta.state = None  # Clear saved state
        if hasattr(self.scene, 'world_generator'):
            self.scene.world_generator._generate_new_world()
        else:
            self.scene._generate_new_world()
        if hasattr(self.scene, 'state_manager'):
            self.scene.meta.state = self.scene.state_manager.serialize_state()
        else:
            self.scene.meta.state = self.scene._serialize_state()

    def _screen_to_grid(self, screen_x, screen_y):
        """Convert screen coordinates to grid coordinates"""
        world_x = screen_x - self.scene.map.camera_offset_x
        world_y = screen_y - self.scene.map.camera_offset_y
        
        # Convert to grid coordinates (basic iso conversion)
        tile_x = int((world_x / (self.scene.tile_width // 2) + world_y / (self.scene.tile_height // 2)) / 2)
        tile_y = int((world_y / (self.scene.tile_height // 2) - world_x / (self.scene.tile_width // 2)) / 2)
        
        return tile_x, tile_y

    def get_mouse_grid_position(self):
        """Get current mouse position in grid coordinates"""
        mx, my = pygame.mouse.get_pos()
        return self._screen_to_grid(mx, my)

    def is_mouse_over_ui(self):
        """Check if mouse is over UI elements"""
        mx, my = pygame.mouse.get_pos()
        
        # Check if mouse is over right panel (assuming UI panel is on the right)
        if mx > 1920 - 300:  # Assuming 300px wide UI panel
            return True
            
        # Add other UI element checks here
        return False

    def handle_drag_selection(self, start_pos, end_pos):
        """Handle drag selection of multiple units"""
        # Calculate selection rectangle
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        left = min(x1, x2)
        right = max(x1, x2)
        top = min(y1, y2)
        bottom = max(y1, y2)
        
        # Select units within rectangle
        selected_units = []
        for unit in self.scene.unit_manager.units:
            unit_screen_x = getattr(unit, 'screen_x', 0)
            unit_screen_y = getattr(unit, 'screen_y', 0)
            
            if (left <= unit_screen_x <= right and 
                top <= unit_screen_y <= bottom):
                unit.selected = True
                selected_units.append(unit)
            else:
                unit.selected = False
                
        return selected_units

    def handle_group_movement_command(self, target_x, target_y):
        """Handle movement command for multiple selected units"""
        selected_units = [u for u in self.scene.unit_manager.units if getattr(u, 'selected', False)]
        
        if not selected_units:
            return False
            
        # Move each selected unit to the target area with some spacing
        for i, unit in enumerate(selected_units):
            # Calculate offset position for formation
            offset_x = (i % 3) - 1  # -1, 0, 1 pattern
            offset_y = (i // 3) - 1
            
            final_x = target_x + offset_x
            final_y = target_y + offset_y
            
            # Clamp to map bounds
            final_x = max(0, min(final_x, len(self.scene.map_data[0]) - 1))
            final_y = max(0, min(final_y, len(self.scene.map_data) - 1))
            
            # Find path for this unit
            if hasattr(self.scene, 'movement_system'):
                path = self.scene.movement_system.find_path(unit.grid_x, unit.grid_y, final_x, final_y)
            else:
                path = self.scene.find_path(unit.grid_x, unit.grid_y, final_x, final_y)
                
            if path:
                unit.path_tiles = path
                unit.path_index = 0
                unit.destination_x = final_x
                unit.destination_y = final_y
                unit.mission = "MOVE_TO"
                unit.moving = True
                
                # Track the command
                if hasattr(self.scene, 'entity_manager'):
                    self.scene.entity_manager.on_biped_command(unit, "MOVE_TO")
                    
        return True

    def get_input_state(self):
        """Get current input state for debugging"""
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        
        return {
            "keys_pressed": [i for i, pressed in enumerate(keys) if pressed],
            "mouse_buttons": mouse_buttons,
            "mouse_pos": mouse_pos,
            "dragging": getattr(self.scene, 'dragging', False),
            "mining_mode": getattr(self.scene, 'mining_mode', False)
        }