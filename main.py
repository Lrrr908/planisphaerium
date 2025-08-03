#!/usr/bin/env python3
"""
Isometric Civilization Game
A 3D block-based civilization builder with space exploration
"""

import arcade
import sys
import os

# Add the game modules to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game.core.game_window import IsometricGameWindow

def main():
    """Main function to start the game"""
    # Set up the game window
    window = IsometricGameWindow(
        width=1600,
        height=900,
        title="Isometric Civilization Game",
        resizable=True
    )
    
    # Set up the game
    window.setup()
    
    # Run the game
    arcade.run()

if __name__ == "__main__":
    main() 