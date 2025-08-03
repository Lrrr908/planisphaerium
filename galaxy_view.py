"""
Galaxy View
Shows multiple solar systems orbiting around a central black hole
"""

import arcade
from arcade import View
from typing import List, Dict, Tuple
import math

from ..core.constants import *

class GalaxyView(View):
    """Galaxy view with multiple solar systems"""
    
    def __init__(self, game_window):
        super().__init__()
        self.game_window = game_window
        self.game_state = game_window.game_state
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        
        # Galaxy data
        self.systems = []
        self.time = 0
        
        # Initialize galaxy
        self.setup_galaxy()
        
    def setup_galaxy(self):
        """Set up the galaxy"""
        # Create solar systems
        system_data = [
            {"name": "Sol", "distance": 100, "size": 15, "color": arcade.color.YELLOW},
            {"name": "Alpha Centauri", "distance": 200, "size": 12, "color": arcade.color.ORANGE},
            {"name": "Proxima Centauri", "distance": 180, "size": 10, "color": arcade.color.RED},
            {"name": "Barnard's Star", "distance": 250, "size": 8, "color": arcade.color.RED},
            {"name": "Wolf 359", "distance": 300, "size": 6, "color": arcade.color.RED},
            {"name": "Lalande 21185", "distance": 220, "size": 9, "color": arcade.color.ORANGE},
        ]
        
        for i, data in enumerate(system_data):
            system = {
                "name": data["name"],
                "distance": data["distance"],
                "size": data["size"],
                "color": data["color"],
                "angle": i * 60,  # Start at different angles
                "speed": 0.2 + (i * 0.05),  # Different speeds
                "discovered": data["name"] == "Sol"  # Only Sol is discovered initially
            }
            self.systems.append(system)
            
    def on_draw(self):
        """Draw the galaxy view"""
        arcade.start_render()
        
        # Clear background
        arcade.set_background_color(arcade.color.BLACK)
        
        # Draw central black hole
        center_x = self.width // 2 + self.camera_x
        center_y = self.height // 2 + self.camera_y
        arcade.draw_circle_filled(center_x, center_y, 40, arcade.color.BLACK)
        arcade.draw_circle_outline(center_x, center_y, 40, arcade.color.PURPLE, 5)
        arcade.draw_circle_outline(center_x, center_y, 45, arcade.color.BLUE, 2)
        
        # Draw galaxy spiral arms (simplified)
        for i in range(4):
            angle = i * 90
            for r in range(50, 350, 20):
                angle_rad = math.radians(angle + r * 0.5)
                x = center_x + math.cos(angle_rad) * r * self.zoom
                y = center_y + math.sin(angle_rad) * r * self.zoom
                arcade.draw_circle_filled(x, y, 1, arcade.color.DARK_BLUE)
        
        # Draw orbits
        for system in self.systems:
            if system["discovered"]:
                arcade.draw_circle_outline(center_x, center_y, system["distance"] * self.zoom, 
                                         arcade.color.DARK_GRAY, 1)
        
        # Draw solar systems
        for system in self.systems:
            if system["discovered"]:
                angle_rad = math.radians(system["angle"])
                x = center_x + math.cos(angle_rad) * system["distance"] * self.zoom
                y = center_y + math.sin(angle_rad) * system["distance"] * self.zoom
                
                arcade.draw_circle_filled(x, y, system["size"] * self.zoom, system["color"])
                arcade.draw_circle_outline(x, y, system["size"] * self.zoom, arcade.color.WHITE, 2)
                
                # Draw system name
                arcade.draw_text(system["name"], x + system["size"] * self.zoom + 5, y, 
                               arcade.color.WHITE, 10, anchor_y="center")
        
        # Draw UI
        self.draw_ui()
        
    def draw_ui(self):
        """Draw UI elements"""
        # Title
        arcade.draw_text("Galaxy View", 10, self.height - 30, arcade.color.WHITE, 20)
        
        # Instructions
        arcade.draw_text("Click on systems to visit them", 10, self.height - 60, arcade.color.WHITE, 14)
        arcade.draw_text("Press 1 to return to planet view", 10, self.height - 80, arcade.color.WHITE, 14)
        
        # System info
        y = 100
        arcade.draw_text("Discovered Systems:", 10, y, arcade.color.WHITE, 16)
        y -= 30
        
        for system in self.systems:
            if system["discovered"]:
                arcade.draw_text(f"• {system['name']}", 20, y, arcade.color.WHITE, 12)
                y -= 20
                
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Handle mouse press"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Check if clicking on a system
            center_x = self.width // 2 + self.camera_x
            center_y = self.height // 2 + self.camera_y
            
            for system in self.systems:
                if system["discovered"]:
                    angle_rad = math.radians(system["angle"])
                    system_x = center_x + math.cos(angle_rad) * system["distance"] * self.zoom
                    system_y = center_y + math.sin(angle_rad) * system["distance"] * self.zoom
                    
                    distance = math.sqrt((x - system_x) ** 2 + (y - system_y) ** 2)
                    if distance < system["size"] * self.zoom + 10:
                        self.visit_system(system)
                        break
                        
    def visit_system(self, system: Dict):
        """Visit a solar system"""
        # Switch to system view
        self.game_state.current_system = system["name"]
        self.game_window.show_system_view()
        
    def on_mouse_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float):
        """Handle mouse scroll for zoom"""
        zoom_change = scroll_y * CAMERA_ZOOM_SPEED
        new_zoom = self.zoom + zoom_change
        self.zoom = max(CAMERA_MIN_ZOOM, min(CAMERA_MAX_ZOOM, new_zoom))
        
    def update(self, delta_time: float):
        """Update the galaxy view"""
        # Update system positions
        for system in self.systems:
            system["angle"] += system["speed"] * delta_time
            if system["angle"] >= 360:
                system["angle"] -= 360
                
        self.time += delta_time 