##########################################################
# arcade_event_handler.py
# Handles input processing, events, and UI interactions for Arcade
##########################################################

import arcade
import math
import time

TILE_WIDTH = 64
TILE_HEIGHT = 37

class ArcadeEventHandler:
    """Handles all input processing and event management for Arcade"""
    
    def __init__(self, scene):
        self.scene = scene

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse button down events"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._handle_left_click(x, y, modifiers)
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self._handle_right_click(x, y, modifiers)

    def _handle_left_click(self, x: int, y: int, modifiers: int):
        """Handle left mouse button clicks"""
        # Check for mining mode first
        if getattr(self.scene, 'mining_mode', False) and self.scene.use_layered_terrain:
            if self._handle_mining_click(x, y):
                return  # Mining click consumed
        
        # Try to select a unit first
        if self.scene.unit_manager.select_unit_at(x, y):
            return  # click consumed – no camera drag

        # Otherwise start dragging the map
        self.scene.mouse_dragging = True
        self.scene.last_mouse_x = x
        self.scene.last_mouse_y = y

        # Check if we clicked a resource drop
        self._check_drop_collection(x, y)

    def _handle_right_click(self, x: int, y: int, modifiers: int):
        """Handle right mouse button clicks"""
        # Handle right-click movement commands with tracking
        if hasattr(self.scene, 'movement_system'):
            self.scene.movement_system.handle_right_click_movement(x, y)
        else:
            # Fallback to unit manager
            self.scene.unit_manager.handle_right_click(x, y)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse button up events"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.scene.mouse_dragging = False

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        """Handle mouse motion events"""
        # Update drop hover states
        for drop in self.scene.drops:
            # Convert drop position to screen coordinates for collision detection
            drop_screen_x, drop_screen_y = self._world_to_screen(drop.center_x, drop.center_y)
            distance = math.hypot(x - drop_screen_x, y - drop_screen_y)
            if hasattr(drop, 'hovered'):
                drop.hovered = distance < 20  # 20 pixel radius for hover
        
        # Handle camera dragging
        if self.scene.mouse_dragging:
            self.scene.move_camera(-dx, -dy)  # Negative because we want opposite movement
            self.scene.last_mouse_x = x
            self.scene.last_mouse_y = y

    def on_key_press(self, key: int, modifiers: int):
        """Handle keyboard input"""
        if key == arcade.key.ESCAPE:
            # Exit or return to menu
            import sys
            sys.exit()
            
        elif key == arcade.key.H:
            self._attempt_build_first_house()
            
        elif key == arcade.key.T:
            self._toggle_simulation_mode()
            
        elif key == arcade.key.L:
            self._toggle_terrain_system()
            
        elif key == arcade.key.M:
            self._toggle_mining_mode()
            
        elif key == arcade.key.R:
            if modifiers & arcade.key.MOD_CTRL:
                self._regenerate_world()
                
        elif key == arcade.key.SPACE:
            self._toggle_pause()
            
        elif key == arcade.key.I:
            self._show_debug_info()
            
        elif key == arcade.key.C:
            self._center_camera()

    def on_key_release(self, key: int, modifiers: int):
        """Handle key release events"""
        pass

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """Handle mouse wheel zoom events"""
        zoom_factor = 1.1 if scroll_y > 0 else 1/1.1
        self.scene.zoom_camera(zoom_factor, x, y)

    def _handle_mining_click(self, x: int, y: int):
        """Handle mining/digging when in mining mode"""
        print(f"[ArcadeEventHandler] Mining mode click at ({x}, {y})")
        
        # Convert screen to grid coordinates
        grid_x, grid_y = self._screen_to_grid(x, y)
        
        # Clamp to map bounds
        grid_x = max(0, min(grid_x, self.scene.terrain_width - 1))
        grid_y = max(0, min(grid_y, self.scene.terrain_height - 1))
        
        print(f"[ArcadeEventHandler] Mining at grid ({grid_x}, {grid_y})")
        
        # For now, just print the action - can be enhanced with actual mining logic
        if hasattr(self.scene, 'resource_system'):
            # Implement actual mining logic here
            pass
        
        return True

    def _check_drop_collection(self, x: int, y: int):
        """Check if clicked on a resource drop and send biped to collect"""
        for drop in self.scene.drops:
            drop_screen_x, drop_screen_y = self._world_to_screen(drop.center_x, drop.center_y)
            distance = math.hypot(x - drop_screen_x, y - drop_screen_y)
            if distance < 20:  # 20 pixel radius for click detection
                if hasattr(self.scene, 'entity_manager'):
                    self.scene.entity_manager.send_biped_to_collect(drop)
                else:
                    # Fallback
                    self.scene.send_biped_to_collect(drop)
                break

    def _attempt_build_first_house(self):
        """Attempt to build the first house"""
        if getattr(self.scene, 'house_built', False) or not self.scene.biped_sprites:
            print("[ArcadeEventHandler] Cannot build house - already built or no bipeds")
            return

        # Get first biped
        biped = self.scene.biped_sprites[0]
        gx, gy = getattr(biped, 'grid_x', 0), getattr(biped, 'grid_y', 0)
        
        if (gx, gy) in self.scene.blocked_tiles:
            print("[ArcadeEventHandler] Tile blocked – can't build house")
            return

        # Create house sprite
        from arcade_planet_scene import ArcadeHouseSprite
        house_sprite = ArcadeHouseSprite(biped.center_x, biped.center_y)
        house_sprite.grid_x = gx
        house_sprite.grid_y = gy
        
        self.scene.house_sprites.append(house_sprite)
        self.scene.blocked_tiles.add((gx, gy))
        self.scene.house_built = True
        print(f"[ArcadeEventHandler] House built at grid ({gx}, {gy})")

        # Spawn two extra bipeds
        self._spawn_house_bipeds(gx, gy)

    def _spawn_house_bipeds(self, house_x, house_y):
        """Spawn additional bipeds near the new house"""
        def _rand_colour():
            import random
            return random.randint(64, 255), random.randint(64, 255), random.randint(64, 255)
        
        for idx in range(2):
            # Find valid tile near house
            tile = self._find_nearby_valid_tile(house_x, house_y)
            if not tile:
                continue

            bx, by = tile
            
            # Calculate isometric position
            iso_x = (bx - by) * (TILE_WIDTH // 2)
            iso_y = (bx + by) * (TILE_HEIGHT // 2)
            
            # Create biped sprite
            from arcade_planet_scene import ArcadeBipedSprite
            biped_sprite = ArcadeBipedSprite(iso_x, iso_y, f"HouseBiped{idx}", _rand_colour())
            biped_sprite.grid_x = bx
            biped_sprite.grid_y = by
            biped_sprite.unit_id = f"house_biped_{idx}_{house_x}_{house_y}"
            biped_sprite.creation_time = time.time()
            biped_sprite.health = 100
            biped_sprite.mission = "IDLE"
            
            # Add to scene
            self.scene.biped_sprites.append(biped_sprite)
            
            print(f"[ArcadeEventHandler] Spawned house biped {idx} at ({bx}, {by})")

    def _find_nearby_valid_tile(self, center_x, center_y, radius=4):
        """Find a valid tile near the center point"""
        for r in range(1, radius + 1):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if abs(dx) == r or abs(dy) == r:  # Only check perimeter
                        test_x, test_y = center_x + dx, center_y + dy
                        if (0 <= test_x < self.scene.terrain_width and 
                            0 <= test_y < self.scene.terrain_height and
                            (test_x, test_y) not in self.scene.blocked_tiles):
                            return test_x, test_y
        return None

    def _toggle_simulation_mode(self):
        """Toggle between paused and realtime simulation"""
        if self.scene.simulation_mode == "paused":
            self.scene.simulation_mode = "realtime"
            print("[ArcadeEventHandler] Switched to REALTIME simulation")
        else:
            self.scene.simulation_mode = "paused"
            print("[ArcadeEventHandler] Switched to PAUSED simulation")

    def _toggle_terrain_system(self):
        """Toggle terrain system information display"""
        print(f"[ArcadeEventHandler] Layered terrain: {'ON' if self.scene.use_layered_terrain else 'OFF'}")
        print("[ArcadeEventHandler] Press Ctrl+R to regenerate world with different settings")

    def _toggle_mining_mode(self):
        """Toggle mining mode for digging terrain"""
        if self.scene.use_layered_terrain:
            self.scene.mining_mode = not getattr(self.scene, 'mining_mode', False)
            mode_text = "ON" if self.scene.mining_mode else "OFF"
            print(f"[ArcadeEventHandler] Mining mode: {mode_text}")
            if self.scene.mining_mode:
                print("[ArcadeEventHandler] Left-click on terrain to dig/mine")
        else:
            print("[ArcadeEventHandler] Mining mode requires layered terrain")

    def _regenerate_world(self):
        """Regenerate the world (for testing)"""
        print("[ArcadeEventHandler] Regenerating world...")
        self.scene.regenerate_world()

    def _toggle_pause(self):
        """Toggle pause (placeholder)"""
        print("[ArcadeEventHandler] Pause toggled")
        # Could implement actual pause logic here

    def _show_debug_info(self):
        """Show debug information"""
        debug_info = self.scene.get_debug_info()
        print("[ArcadeEventHandler] Debug Info:")
        for category, data in debug_info.items():
            print(f"  {category}: {data}")

    def _center_camera(self):
        """Center camera on the terrain"""
        self.scene._center_camera()
        print("[ArcadeEventHandler] Camera centered")

    def _screen_to_grid(self, screen_x, screen_y):
        """Convert screen coordinates to grid coordinates"""
        # Get camera position
        camera_x, camera_y = self.scene.camera.position if self.scene.camera else (0, 0)
        
        # Convert to world coordinates
        world_x = screen_x + camera_x
        world_y = screen_y + camera_y
        
        # Convert to grid coordinates (isometric conversion)
        tile_x = int((world_x / (TILE_WIDTH // 2) + world_y / (TILE_HEIGHT // 2)) / 2)
        tile_y = int((world_y / (TILE_HEIGHT // 2) - world_x / (TILE_WIDTH // 2)) / 2)
        
        return tile_x, tile_y

    def _world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        # Get camera position
        camera_x, camera_y = self.scene.camera.position if self.scene.camera else (0, 0)
        
        # Convert to screen coordinates
        screen_x = world_x - camera_x
        screen_y = world_y - camera_y
        
        return screen_x, screen_y

    def get_mouse_grid_position(self):
        """Get current mouse position in grid coordinates (for external use)"""
        # This would need access to current mouse position
        # For now, return None - implement when needed with mouse tracking
        return None

    def is_mouse_over_ui(self, x, y):
        """Check if mouse is over UI elements"""
        # Check if mouse is over right panel (assuming UI panel is on the right)
        if x > self.scene.window.width - 300:  # Assuming 300px wide UI panel
            return True
            
        # Add other UI element checks here
        return False

    def handle_drag_selection(self, start_x, start_y, end_x, end_y):
        """Handle drag selection of multiple units"""
        # Calculate selection rectangle
        left = min(start_x, end_x)
        right = max(start_x, end_x)
        top = min(start_y, end_y)
        bottom = max(start_y, end_y)
        
        # Select units within rectangle
        selected_units = []
        for biped_sprite in self.scene.biped_sprites:
            # Convert world position to screen position
            screen_x, screen_y = self._world_to_screen(biped_sprite.center_x, biped_sprite.center_y)
            
            if (left <= screen_x <= right and 
                top <= screen_y <= bottom):
                if hasattr(biped_sprite, 'selected'):
                    biped_sprite.selected = True
                selected_units.append(biped_sprite)
            else:
                if hasattr(biped_sprite, 'selected'):
                    biped_sprite.selected = False
                
        return selected_units

    def handle_group_movement_command(self, target_x, target_y):
        """Handle movement command for multiple selected units"""
        selected_units = [u for u in self.scene.biped_sprites if getattr(u, 'selected', False)]
        
        if not selected_units:
            return False
        
        # Convert screen to grid coordinates
        grid_x, grid_y = self._screen_to_grid(target_x, target_y)
        
        # Move each selected unit to the target area with some spacing
        for i, unit in enumerate(selected_units):
            # Calculate offset position for formation
            offset_x = (i % 3) - 1  # -1, 0, 1 pattern
            offset_y = (i // 3) - 1
            
            final_x = grid_x + offset_x
            final_y = grid_y + offset_y
            
            # Clamp to map bounds
            final_x = max(0, min(final_x, self.scene.terrain_width - 1))
            final_y = max(0, min(final_y, self.scene.terrain_height - 1))
            
            # Convert back to isometric coordinates
            target_iso_x = (final_x - final_y) * (TILE_WIDTH // 2)
            target_iso_y = (final_x + final_y) * (TILE_HEIGHT // 2)
            
            # Set movement target
            unit.target_x = target_iso_x
            unit.target_y = target_iso_y
            unit.moving = True
            if hasattr(unit, 'mission'):
                unit.mission = "MOVE_TO"
                
        print(f"[ArcadeEventHandler] Group moving {len(selected_units)} units to ({grid_x}, {grid_y})")
        return True

    def get_input_state(self):
        """Get current input state for debugging"""
        return {
            "dragging": getattr(self.scene, 'mouse_dragging', False),
            "mining_mode": getattr(self.scene, 'mining_mode', False),
            "camera_position": self.scene.camera.position if self.scene.camera else (0, 0),
            "zoom_scale": self.scene.zoom_scale,
            "simulation_mode": self.scene.simulation_mode,
            "house_built": self.scene.house_built
        }

    def handle_window_resize(self, width, height):
        """Handle window resize events"""
        print(f"[ArcadeEventHandler] Window resized to {width}x{height}")
        # Update camera if needed
        if self.scene.camera:
            self.scene.camera.resize(width, height)
        if self.scene.ui_camera:
            self.scene.ui_camera.resize(width, height)

    def handle_file_drop(self, file_path):
        """Handle file drop events (for loading saves, etc.)"""
        print(f"[ArcadeEventHandler] File dropped: {file_path}")
        # Could implement save file loading here
        if file_path.endswith('.json'):
            try:
                if hasattr(self.scene, 'state_manager'):
                    success = self.scene.state_manager.import_state_from_file(file_path)
                    if success:
                        print("[ArcadeEventHandler] Successfully loaded save file")
                    else:
                        print("[ArcadeEventHandler] Failed to load save file")
            except Exception as e:
                print(f"[ArcadeEventHandler] Error loading file: {e}")

    def create_context_menu(self, x, y):
        """Create context menu at position (placeholder for future enhancement)"""
        print(f"[ArcadeEventHandler] Context menu requested at ({x}, {y})")
        # Could implement actual context menu here
        return None

    def handle_hotkey(self, key_combination):
        """Handle hotkey combinations"""
        print(f"[ArcadeEventHandler] Hotkey pressed: {key_combination}")
        # Could implement hotkey system here
        pass