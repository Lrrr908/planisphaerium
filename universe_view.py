"""
Universe View
Shows multiple galaxies orbiting around a massive central black hole
"""

import arcade
from arcade import View
from typing import List, Dict, Tuple
import math

from ..core.constants import *

class UniverseView(View):
    """Universe view with multiple galaxies"""
    
    def __init__(self, game_window):
        super().__init__()
        self.game_window = game_window
        self.game_state = game_window.game_state
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        
        # Universe data
        self.galaxies = []
        self.time = 0
        
        # Initialize universe
        self.setup_universe()
        
    def setup_universe(self):
        """Set up the universe"""
        # Create galaxies
        galaxy_data = [
            {"name": "Milky Way", "distance": 200, "size": 25, "color": arcade.color.WHITE},
            {"name": "Andromeda", "distance": 400, "size": 30, "color": arcade.color.LIGHT_BLUE},
            {"name": "Triangulum", "distance": 350, "size": 20, "color": arcade.color.LIGHT_GREEN},
            {"name": "Large Magellanic Cloud", "distance": 300, "size": 15, "color": arcade.color.YELLOW},
            {"name": "Small Magellanic Cloud", "distance": 280, "size": 12, "color": arcade.color.ORANGE},
            {"name": "Centaurus A", "distance": 450, "size": 18, "color": arcade.color.RED},
        ]
        
        for i, data in enumerate(galaxy_data):
            galaxy = {
                "name": data["name"],
                "distance": data["distance"],
                "size": data["size"],
                "color": data["color"],
                "angle": i * 60,  # Start at different angles
                "speed": 0.1 + (i * 0.02),  # Different speeds
                "discovered": data["name"] == "Milky Way"  # Only Milky Way is discovered initially
            }
            self.galaxies.append(galaxy)
            
    def on_draw(self):
        """Draw the universe view"""
        arcade.start_render()
        
        # Clear background
        arcade.set_background_color(arcade.color.BLACK)
        
        # Draw stars in background
        for i in range(100):
            x = (i * 37) % self.width
            y = (i * 73) % self.height
            brightness = (i * 13) % 255
            arcade.draw_circle_filled(x, y, 1, (brightness, brightness, brightness))
        
        # Draw central supermassive black hole
        center_x = self.width // 2 + self.camera_x
        center_y = self.height // 2 + self.camera_y
        arcade.draw_circle_filled(center_x, center_y, 60, arcade.color.BLACK)
        arcade.draw_circle_outline(center_x, center_y, 60, arcade.color.PURPLE, 8)
        arcade.draw_circle_outline(center_x, center_y, 70, arcade.color.BLUE, 3)
        arcade.draw_circle_outline(center_x, center_y, 80, arcade.color.CYAN, 1)
        
        # Draw accretion disk
        for i in range(8):
            angle = i * 45
            angle_rad = math.radians(angle)
            x = center_x + math.cos(angle_rad) * 90
            y = center_y + math.sin(angle_rad) * 90
            arcade.draw_circle_filled(x, y, 3, arcade.color.YELLOW)
        
        # Draw orbits
        for galaxy in self.galaxies:
            if galaxy["discovered"]:
                arcade.draw_circle_outline(center_x, center_y, galaxy["distance"] * self.zoom, 
                                         arcade.color.DARK_GRAY, 1)
        
        # Draw galaxies
        for galaxy in self.galaxies:
            if galaxy["discovered"]:
                angle_rad = math.radians(galaxy["angle"])
                x = center_x + math.cos(angle_rad) * galaxy["distance"] * self.zoom
                y = center_y + math.sin(angle_rad) * galaxy["distance"] * self.zoom
                
                # Draw galaxy as spiral
                self.draw_galaxy_spiral(x, y, galaxy["size"] * self.zoom, galaxy["color"])
                
                # Draw galaxy name
                arcade.draw_text(galaxy["name"], x + galaxy["size"] * self.zoom + 5, y, 
                               arcade.color.WHITE, 12, anchor_y="center")
        
        # Draw UI
        self.draw_ui()
        
    def draw_galaxy_spiral(self, x: float, y: float, size: float, color: Tuple[int, int, int]):
        """Draw a spiral galaxy"""
        # Draw central bulge
        arcade.draw_circle_filled(x, y, size * 0.3, color)
        arcade.draw_circle_outline(x, y, size * 0.3, arcade.color.WHITE, 2)
        
        # Draw spiral arms
        for arm in range(4):
            angle_offset = arm * 90
            for r in range(int(size * 0.3), int(size), 5):
                angle_rad = math.radians(angle_offset + r * 2)
                star_x = x + math.cos(angle_rad) * r
                star_y = y + math.sin(angle_rad) * r
                arcade.draw_circle_filled(star_x, star_y, 1, color)
        
    def draw_ui(self):
        """Draw UI elements"""
        # Title
        arcade.draw_text("Universe View", 10, self.height - 30, arcade.color.WHITE, 20)
        
        # Instructions
        arcade.draw_text("Click on galaxies to visit them", 10, self.height - 60, arcade.color.WHITE, 14)
        arcade.draw_text("Press 1 to return to planet view", 10, self.height - 80, arcade.color.WHITE, 14)
        
        # Galaxy info
        y = 100
        arcade.draw_text("Discovered Galaxies:", 10, y, arcade.color.WHITE, 16)
        y -= 30
        
        for galaxy in self.galaxies:
            if galaxy["discovered"]:
                arcade.draw_text(f"• {galaxy['name']}", 20, y, arcade.color.WHITE, 12)
                y -= 20
                
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Handle mouse press"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Check if clicking on a galaxy
            center_x = self.width // 2 + self.camera_x
            center_y = self.height // 2 + self.camera_y
            
            for galaxy in self.galaxies:
                if galaxy["discovered"]:
                    angle_rad = math.radians(galaxy["angle"])
                    galaxy_x = center_x + math.cos(angle_rad) * galaxy["distance"] * self.zoom
                    galaxy_y = center_y + math.sin(angle_rad) * galaxy["distance"] * self.zoom
                    
                    distance = math.sqrt((x - galaxy_x) ** 2 + (y - galaxy_y) ** 2)
                    if distance < galaxy["size"] * self.zoom + 15:
                        self.visit_galaxy(galaxy)
                        break
                        
    def visit_galaxy(self, galaxy: Dict):
        """Visit a galaxy"""
        # Switch to galaxy view
        self.game_state.current_galaxy = galaxy["name"]
        self.game_window.show_galaxy_view()
        
    def on_mouse_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float):
        """Handle mouse scroll for zoom"""
        zoom_change = scroll_y * CAMERA_ZOOM_SPEED
        new_zoom = self.zoom + zoom_change
        self.zoom = max(CAMERA_MIN_ZOOM, min(CAMERA_MAX_ZOOM, new_zoom))
        
    def update(self, delta_time: float):
        """Update the universe view"""
        # Update galaxy positions
        for galaxy in self.galaxies:
            galaxy["angle"] += galaxy["speed"] * delta_time
            if galaxy["angle"] >= 360:
                galaxy["angle"] -= 360
                
        self.time += delta_time 