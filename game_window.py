"""
Main Game Window
Handles the different game views and manages the overall game state
"""

import arcade
from arcade import View
from typing import Optional

from .constants import *
from ..world.planet_view import PlanetView
from ..world.system_view import SystemView
from ..world.galaxy_view import GalaxyView
from ..world.universe_view import UniverseView
from ..systems.game_state import GameState

class IsometricGameWindow(arcade.Window):
    """Main game window that manages different views"""
    
    def __init__(self, width: int, height: int, title: str, resizable: bool = True):
        super().__init__(width, height, title, resizable=resizable)
        
        # Game state
        self.game_state = GameState()
        
        # Views
        self.planet_view: Optional[PlanetView] = None
        self.system_view: Optional[SystemView] = None
        self.galaxy_view: Optional[GalaxyView] = None
        self.universe_view: Optional[UniverseView] = None
        
        # Current view
        self._current_view: Optional[View] = None
        
        # Set up the window
        arcade.set_background_color(arcade.color.BLACK)
        
    def setup(self):
        """Set up the game"""
        # Initialize game state
        self.game_state.initialize()
        
        # Create views
        self.planet_view = PlanetView(self)
        self.system_view = SystemView(self)
        self.galaxy_view = GalaxyView(self)
        self.universe_view = UniverseView(self)
        
        # Start with planet view
        self.show_planet_view()
        
    def show_planet_view(self):
        """Switch to planet view"""
        if self.planet_view:
            self.show_view(self.planet_view)
            self._current_view = self.planet_view
            
    def show_system_view(self):
        """Switch to system view"""
        if self.game_state.science_points >= UNLOCK_SYSTEM_VIEW and self.system_view:
            self.show_view(self.system_view)
            self._current_view = self.system_view
            
    def show_galaxy_view(self):
        """Switch to galaxy view"""
        if self.game_state.science_points >= UNLOCK_GALAXY_VIEW and self.galaxy_view:
            self.show_view(self.galaxy_view)
            self._current_view = self.galaxy_view
            
    def show_universe_view(self):
        """Switch to universe view"""
        if self.game_state.science_points >= UNLOCK_UNIVERSE_VIEW and self.universe_view:
            self.show_view(self.universe_view)
            self._current_view = self.universe_view
            
    def on_key_press(self, key, modifiers):
        """Handle key presses"""
        # View switching
        if key == arcade.key.NUM_1:
            self.show_planet_view()
        elif key == arcade.key.NUM_2:
            self.show_system_view()
        elif key == arcade.key.NUM_3:
            self.show_galaxy_view()
        elif key == arcade.key.NUM_4:
            self.show_universe_view()
        elif key == arcade.key.ESCAPE:
            arcade.close_window()
            
        # Pass to current view
        if self._current_view:
            self._current_view.on_key_press(key, modifiers)
            
    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse presses"""
        if self._current_view:
            self._current_view.on_mouse_press(x, y, button, modifiers)
            
    def on_mouse_release(self, x, y, button, modifiers):
        """Handle mouse releases"""
        if self._current_view:
            self._current_view.on_mouse_release(x, y, button, modifiers)
            
    def on_mouse_motion(self, x, y, dx, dy):
        """Handle mouse motion"""
        if self._current_view:
            self._current_view.on_mouse_motion(x, y, dx, dy)
            
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Handle mouse scroll"""
        if self._current_view:
            self._current_view.on_mouse_scroll(x, y, scroll_x, scroll_y)
            
    def on_draw(self):
        """Draw the current view"""
        if self._current_view:
            self._current_view.on_draw()
        else:
            # Fallback drawing
            arcade.start_render()
            arcade.draw_text("Loading...", self.width // 2, self.height // 2, 
                           arcade.color.WHITE, 24, anchor_x="center", anchor_y="center")
            
    def update(self, delta_time):
        """Update the current view"""
        if self._current_view:
            self._current_view.update(delta_time) 