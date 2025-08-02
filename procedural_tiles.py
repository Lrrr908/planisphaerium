# procedural_tiles.py - Simplified Minecraft-style 3D Blocks
import pygame
import random
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Tile configuration - optimized for performance
TILE_WIDTH = 64
TILE_HEIGHT = 37
BLOCK_DEPTH = 16  # Reduced for better performance
SUB_TILE_WIDTH = TILE_WIDTH // 4
SUB_TILE_HEIGHT = TILE_HEIGHT // 4

@dataclass
class SubTile:
    """Individual 4x4 sub-tile within a main tile"""
    tile_type: int = 1
    exists: bool = True
    building_id: Optional[str] = None
    building_type: Optional[str] = None
    height_offset: float = 0.0
    damage: float = 0.0
    
@dataclass 
class TileData:
    """Enhanced tile data with sub-tile breakdown"""
    tile_type: int
    sub_tiles: List[List[SubTile]]
    base_height: int = 0
    damaged: bool = False
    
    def __post_init__(self):
        if not self.sub_tiles:
            self.sub_tiles = [[SubTile(self.tile_type) for _ in range(4)] for _ in range(4)]

class ProceduralTileGenerator:
    """Generates simple Minecraft-style 3D block tiles"""
    
    def __init__(self):
        self.tile_cache = {}
        
    def generate_tile(self, tile_type: int, tile_data: TileData = None, zoom_scale: float = 1.0) -> pygame.Surface:
        """Generate a Minecraft-style 3D block tile surface"""
        cache_key = f"{tile_type}_{zoom_scale:.1f}"  # Simplified cache key
        
        if cache_key in self.tile_cache:
            return self.tile_cache[cache_key]
            
        # Calculate dimensions for 3D block
        width = int(TILE_WIDTH * zoom_scale)
        height = int((TILE_HEIGHT + BLOCK_DEPTH) * zoom_scale)
        
        # Create surface with alpha
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw simple Minecraft-style block
        self._draw_simple_minecraft_block(surface, tile_type, zoom_scale)
            
        self.tile_cache[cache_key] = surface
        return surface
        
    def _draw_simple_minecraft_block(self, surface: pygame.Surface, tile_type: int, zoom_scale: float):
        """Draw a simple but proper Minecraft-style isometric block"""
        width, height = surface.get_size()
        
        # Get colors for this tile type
        top_color, left_color, right_color = self._get_minecraft_colors(tile_type)
        
        # Calculate dimensions
        tile_w = int(TILE_WIDTH * zoom_scale)
        tile_h = int(TILE_HEIGHT * zoom_scale)
        depth = int(BLOCK_DEPTH * zoom_scale)
        
        # Draw the three visible faces of the isometric cube
        
        # 1. TOP FACE (diamond/rhombus shape)
        top_points = [
            (tile_w // 2, 0),              # Top point
            (tile_w, tile_h // 2),         # Right point
            (tile_w // 2, tile_h),         # Bottom point
            (0, tile_h // 2)               # Left point
        ]
        pygame.draw.polygon(surface, top_color, top_points)
        
        # Add simple texture to top
        self._add_simple_texture(surface, top_color, top_points, tile_type)
        
        # 2. LEFT FACE (parallelogram)
        left_points = [
            (0, tile_h // 2),              # Top-left
            (tile_w // 2, tile_h),         # Top-right
            (tile_w // 2, tile_h + depth), # Bottom-right
            (0, tile_h // 2 + depth)       # Bottom-left
        ]
        pygame.draw.polygon(surface, left_color, left_points)
        
        # 3. RIGHT FACE (parallelogram)
        right_points = [
            (tile_w // 2, tile_h),          # Top-left
            (tile_w, tile_h // 2),          # Top-right
            (tile_w, tile_h // 2 + depth),  # Bottom-right
            (tile_w // 2, tile_h + depth)   # Bottom-left
        ]
        pygame.draw.polygon(surface, right_color, right_points)
        
        # Draw outlines for crisp block definition
        pygame.draw.polygon(surface, self._darken_color(top_color, 0.3), top_points, 1)
        pygame.draw.polygon(surface, self._darken_color(left_color, 0.2), left_points, 1)
        pygame.draw.polygon(surface, self._darken_color(right_color, 0.2), right_points, 1)
        
    def _add_simple_texture(self, surface: pygame.Surface, base_color: Tuple[int, int, int], 
                           points: List[Tuple[int, int]], tile_type: int):
        """Add simple texture patterns without heavy computation"""
        if tile_type == 1:  # Grass - just add a few green variations
            for _ in range(5):
                x = random.randint(points[3][0], points[1][0])
                y = random.randint(points[0][1], points[2][1])
                if self._point_in_diamond(x, y, points):
                    color = (
                        min(255, base_color[0] + random.randint(-10, 10)),
                        min(255, base_color[1] + random.randint(-5, 5)),
                        min(255, base_color[2] + random.randint(-8, 8))
                    )
                    pygame.draw.circle(surface, color, (x, y), 1)
                    
        elif tile_type == 4:  # Stone - add a few cracks
            for _ in range(2):
                x1 = random.randint(points[3][0], points[1][0])
                y1 = random.randint(points[0][1], points[2][1])
                x2 = x1 + random.randint(-8, 8)
                y2 = y1 + random.randint(-4, 4)
                if (self._point_in_diamond(x1, y1, points) and 
                    self._point_in_diamond(x2, y2, points)):
                    crack_color = self._darken_color(base_color, 0.4)
                    pygame.draw.line(surface, crack_color, (x1, y1), (x2, y2), 1)
                    
    def _point_in_diamond(self, x: int, y: int, points: List[Tuple[int, int]]) -> bool:
        """Simple check if point is in diamond - faster than full polygon check"""
        # Simple bounding box check first
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        return min_x <= x <= max_x and min_y <= y <= max_y
        
    def _get_minecraft_colors(self, tile_type: int) -> Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]:
        """Get Minecraft-style colors for top, left, and right faces"""
        color_map = {
            1: ((50, 160, 50), (101, 67, 33), (85, 55, 25)),      # Grass: green top, dirt sides  
            2: ((64, 164, 223), (45, 140, 190), (35, 120, 170)),  # Water: blue variations
            3: ((134, 96, 67), (110, 75, 50), (90, 60, 40)),      # Dirt: brown variations
            4: ((130, 130, 130), (105, 105, 105), (85, 85, 85)),  # Stone: gray variations
            5: ((32, 137, 203), (25, 110, 170), (20, 90, 140)),   # Deep water: darker blue
            11: ((247, 233, 163), (210, 195, 135), (180, 165, 115)), # Desert: sandy variations
        }
        return color_map.get(tile_type, ((50, 160, 50), (101, 67, 33), (85, 55, 25)))
        
    def _darken_color(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Darken a color by the given factor"""
        return (
            max(0, int(color[0] * (1 - factor))),
            max(0, int(color[1] * (1 - factor))),
            max(0, int(color[2] * (1 - factor)))
        )

# Global tile generator instance
tile_generator = ProceduralTileGenerator()