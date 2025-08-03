"""
Isometric Utilities
Functions for converting between screen coordinates and isometric grid coordinates
"""

import math
from typing import Tuple, List
from .constants import TILE_WIDTH, TILE_HEIGHT, BLOCK_HEIGHT

def screen_to_isometric(screen_x: float, screen_y: float, camera_x: float = 0, camera_y: float = 0, zoom: float = 1.0) -> Tuple[int, int]:
    """
    Convert screen coordinates to isometric grid coordinates
    
    Args:
        screen_x: Screen X coordinate
        screen_y: Screen Y coordinate
        camera_x: Camera X offset
        camera_y: Camera Y offset
        zoom: Camera zoom level
        
    Returns:
        Tuple of (grid_x, grid_y) coordinates
    """
    # Adjust for camera
    world_x = (screen_x - camera_x) / zoom
    world_y = (screen_y - camera_y) / zoom
    
    # Convert to isometric coordinates
    iso_x = (world_x / TILE_WIDTH + world_y / TILE_HEIGHT) / 2
    iso_y = (world_y / TILE_HEIGHT - world_x / TILE_WIDTH) / 2
    
    return int(iso_x), int(iso_y)

def isometric_to_screen(grid_x: int, grid_y: int, camera_x: float = 0, camera_y: float = 0, zoom: float = 1.0) -> Tuple[float, float]:
    """
    Convert isometric grid coordinates to screen coordinates
    
    Args:
        grid_x: Grid X coordinate
        grid_y: Grid Y coordinate
        camera_x: Camera X offset
        camera_y: Camera Y offset
        zoom: Camera zoom level
        
    Returns:
        Tuple of (screen_x, screen_y) coordinates
    """
    # Convert to world coordinates
    world_x = (grid_x - grid_y) * TILE_WIDTH / 2
    world_y = (grid_x + grid_y) * TILE_HEIGHT / 2
    
    # Apply camera and zoom
    screen_x = world_x * zoom + camera_x
    screen_y = world_y * zoom + camera_y
    
    return screen_x, screen_y

def get_tile_corners(grid_x: int, grid_y: int, height: int = 0, camera_x: float = 0, camera_y: float = 0, zoom: float = 1.0) -> List[Tuple[float, float]]:
    """
    Get the screen coordinates of a tile's corners for drawing
    
    Args:
        grid_x: Grid X coordinate
        grid_y: Grid Y coordinate
        height: Height of the tile (for 3D effect)
        camera_x: Camera X offset
        camera_y: Camera Y offset
        zoom: Camera zoom level
        
    Returns:
        List of 4 corner coordinates (top-left, top-right, bottom-right, bottom-left)
    """
    # Base tile position
    center_x, center_y = isometric_to_screen(grid_x, grid_y, camera_x, camera_y, zoom)
    
    # Calculate corner offsets
    half_width = TILE_WIDTH / 2 * zoom
    half_height = TILE_HEIGHT / 2 * zoom
    height_offset = height * BLOCK_HEIGHT * zoom
    
    # Top corners (raised by height)
    top_left = (center_x - half_width, center_y - half_height + height_offset)
    top_right = (center_x + half_width, center_y - half_height + height_offset)
    
    # Bottom corners (ground level)
    bottom_right = (center_x + half_width, center_y + half_height)
    bottom_left = (center_x - half_width, center_y + half_height)
    
    return [top_left, top_right, bottom_right, bottom_left]

def get_tile_center(grid_x: int, grid_y: int, height: int = 0, camera_x: float = 0, camera_y: float = 0, zoom: float = 1.0) -> Tuple[float, float]:
    """
    Get the center screen coordinates of a tile
    
    Args:
        grid_x: Grid X coordinate
        grid_y: Grid Y coordinate
        height: Height of the tile
        camera_x: Camera X offset
        camera_y: Camera Y offset
        zoom: Camera zoom level
        
    Returns:
        Tuple of (center_x, center_y) coordinates
    """
    center_x, center_y = isometric_to_screen(grid_x, grid_y, camera_x, camera_y, zoom)
    height_offset = height * BLOCK_HEIGHT * zoom
    
    return center_x, center_y + height_offset

def get_tile_bounds(grid_x: int, grid_y: int, camera_x: float = 0, camera_y: float = 0, zoom: float = 1.0) -> Tuple[float, float, float, float]:
    """
    Get the bounding box of a tile in screen coordinates
    
    Args:
        grid_x: Grid X coordinate
        grid_y: Grid Y coordinate
        camera_x: Camera X offset
        camera_y: Camera Y offset
        zoom: Camera zoom level
        
    Returns:
        Tuple of (left, top, right, bottom) bounds
    """
    corners = get_tile_corners(grid_x, grid_y, 0, camera_x, camera_y, zoom)
    
    x_coords = [corner[0] for corner in corners]
    y_coords = [corner[1] for corner in corners]
    
    return min(x_coords), min(y_coords), max(x_coords), max(y_coords)

def distance_between_tiles(grid_x1: int, grid_y1: int, grid_x2: int, grid_y2: int) -> float:
    """
    Calculate the distance between two tiles in grid coordinates
    
    Args:
        grid_x1, grid_y1: First tile coordinates
        grid_x2, grid_y2: Second tile coordinates
        
    Returns:
        Distance between the tiles
    """
    dx = grid_x2 - grid_x1
    dy = grid_y2 - grid_y1
    return math.sqrt(dx * dx + dy * dy)

def get_visible_tiles(camera_x: float, camera_y: float, screen_width: int, screen_height: int, zoom: float = 1.0) -> List[Tuple[int, int]]:
    """
    Get all tiles visible in the current view
    
    Args:
        camera_x: Camera X offset
        camera_y: Camera Y offset
        screen_width: Screen width
        screen_height: Screen height
        zoom: Camera zoom level
        
    Returns:
        List of visible tile coordinates
    """
    visible_tiles = []
    
    # Convert screen corners to grid coordinates
    top_left = screen_to_isometric(0, 0, camera_x, camera_y, zoom)
    top_right = screen_to_isometric(screen_width, 0, camera_x, camera_y, zoom)
    bottom_left = screen_to_isometric(0, screen_height, camera_x, camera_y, zoom)
    bottom_right = screen_to_isometric(screen_width, screen_height, camera_x, camera_y, zoom)
    
    # Calculate grid bounds
    min_x = min(top_left[0], top_right[0], bottom_left[0], bottom_right[0]) - 2
    max_x = max(top_left[0], top_right[0], bottom_left[0], bottom_right[0]) + 2
    min_y = min(top_left[1], top_right[1], bottom_left[1], bottom_right[1]) - 2
    max_y = max(top_left[1], top_right[1], bottom_left[1], bottom_right[1]) + 2
    
    # Generate visible tiles
    for grid_x in range(min_x, max_x + 1):
        for grid_y in range(min_y, max_y + 1):
            visible_tiles.append((grid_x, grid_y))
    
    return visible_tiles

def get_tile_neighbors(grid_x: int, grid_y: int) -> List[Tuple[int, int]]:
    """
    Get the 6 neighboring tiles in isometric grid
    
    Args:
        grid_x: Grid X coordinate
        grid_y: Grid Y coordinate
        
    Returns:
        List of neighboring tile coordinates
    """
    # Isometric grid has 6 neighbors
    neighbors = [
        (grid_x + 1, grid_y),     # Right
        (grid_x - 1, grid_y),     # Left
        (grid_x, grid_y + 1),     # Top
        (grid_x, grid_y - 1),     # Bottom
        (grid_x + 1, grid_y - 1), # Top-right
        (grid_x - 1, grid_y + 1), # Bottom-left
    ]
    
    return neighbors 