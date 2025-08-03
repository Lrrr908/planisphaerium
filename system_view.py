"""
System View
Shows the solar system with planets orbiting around a star
"""

import arcade
from arcade import View
from typing import List, Dict, Tuple
import math

from ..core.constants import *

class SystemView(View):
    """Solar system view with orbiting planets"""
    
    def __init__(self, game_window):
        super().__init__()
        self.game_window = game_window
        self.game_state = game_window.game_state
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        
        # System data
        self.planets = []
        self.ships = []
        self.time = 0
        
        # Initialize system
        self.setup_system()
        
    def setup_system(self):
        """Set up the solar system"""
        # Create planets
        planet_data = [
            {"name": "Mercury", "distance": 50, "size": 8, "color": arcade.color.GRAY},
            {"name": "Venus", "distance": 80, "size": 12, "color": arcade.color.YELLOW},
            {"name": "Earth", "distance": 120, "size": 14, "color": arcade.color.BLUE},
            {"name": "Mars", "distance": 160, "size": 10, "color": arcade.color.RED},
            {"name": "Jupiter", "distance": 220, "size": 20, "color": arcade.color.ORANGE},
            {"name": "Saturn", "distance": 280, "size": 18, "color": arcade.color.YELLOW},
        ]
        
        for i, data in enumerate(planet_data):
            planet = {
                "name": data["name"],
                "distance": data["distance"],
                "size": data["size"],
                "color": data["color"],
                "angle": i * 60,  # Start at different angles
                "speed": 0.5 + (i * 0.1),  # Different speeds
                "discovered": data["name"] == "Earth"  # Only Earth is discovered initially
            }
            self.planets.append(planet)
            
    def on_draw(self):
        """Draw the system view"""
        arcade.start_render()
        
        # Clear background
        arcade.set_background_color(arcade.color.BLACK)
        
        # Draw star (sun)
        center_x = self.width // 2 + self.camera_x
        center_y = self.height // 2 + self.camera_y
        arcade.draw_circle_filled(center_x, center_y, 30, arcade.color.YELLOW)
        arcade.draw_circle_outline(center_x, center_y, 30, arcade.color.ORANGE, 3)
        
        # Draw orbits
        for planet in self.planets:
            if planet["discovered"]:
                arcade.draw_circle_outline(center_x, center_y, planet["distance"] * self.zoom, 
                                         arcade.color.DARK_GRAY, 1)
        
        # Draw planets
        for planet in self.planets:
            if planet["discovered"]:
                angle_rad = math.radians(planet["angle"])
                x = center_x + math.cos(angle_rad) * planet["distance"] * self.zoom
                y = center_y + math.sin(angle_rad) * planet["distance"] * self.zoom
                
                arcade.draw_circle_filled(x, y, planet["size"] * self.zoom, planet["color"])
                arcade.draw_circle_outline(x, y, planet["size"] * self.zoom, arcade.color.WHITE, 2)
                
                # Draw planet name
                arcade.draw_text(planet["name"], x + planet["size"] * self.zoom + 5, y, 
                               arcade.color.WHITE, 12, anchor_y="center")
        
        # Draw ships
        for ship in self.ships:
            arcade.draw_circle_filled(ship["x"], ship["y"], 5, arcade.color.CYAN)
            arcade.draw_circle_outline(ship["x"], ship["y"], 5, arcade.color.WHITE, 1)
            
        # Draw UI
        self.draw_ui()
        
    def draw_ui(self):
        """Draw UI elements"""
        # Title
        arcade.draw_text("Solar System View", 10, self.height - 30, arcade.color.WHITE, 20)
        
        # Instructions
        arcade.draw_text("Click on planets to visit them", 10, self.height - 60, arcade.color.WHITE, 14)
        arcade.draw_text("Press 1 to return to planet view", 10, self.height - 80, arcade.color.WHITE, 14)
        
        # Planet info
        y = 100
        arcade.draw_text("Discovered Planets:", 10, y, arcade.color.WHITE, 16)
        y -= 30
        
        for planet in self.planets:
            if planet["discovered"]:
                arcade.draw_text(f"• {planet['name']}", 20, y, arcade.color.WHITE, 12)
                y -= 20
                
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Handle mouse press"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Check if clicking on a planet
            center_x = self.width // 2 + self.camera_x
            center_y = self.height // 2 + self.camera_y
            
            for planet in self.planets:
                if planet["discovered"]:
                    angle_rad = math.radians(planet["angle"])
                    planet_x = center_x + math.cos(angle_rad) * planet["distance"] * self.zoom
                    planet_y = center_y + math.sin(angle_rad) * planet["distance"] * self.zoom
                    
                    distance = math.sqrt((x - planet_x) ** 2 + (y - planet_y) ** 2)
                    if distance < planet["size"] * self.zoom + 10:
                        self.visit_planet(planet)
                        break
                        
    def visit_planet(self, planet: Dict):
        """Visit a planet"""
        # Switch to planet view
        self.game_state.current_planet = planet["name"]
        self.game_window.show_planet_view()
        
    def on_mouse_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float):
        """Handle mouse scroll for zoom"""
        zoom_change = scroll_y * CAMERA_ZOOM_SPEED
        new_zoom = self.zoom + zoom_change
        self.zoom = max(CAMERA_MIN_ZOOM, min(CAMERA_MAX_ZOOM, new_zoom))
        
    def update(self, delta_time: float):
        """Update the system view"""
        # Update planet positions
        for planet in self.planets:
            planet["angle"] += planet["speed"] * delta_time
            if planet["angle"] >= 360:
                planet["angle"] -= 360
                
        self.time += delta_time 