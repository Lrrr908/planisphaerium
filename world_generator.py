"""
World Generation System
Handles terrain generation, biomes, and block stacking - Simple Arcade Style
"""

import random
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from ..core.constants import *

@dataclass
class Block:
    """Represents a single block in a stack"""
    grid_x: int
    grid_y: int
    layer: int  # Height level (0 = ground)
    block_type: str
    top_color: Tuple[int, int, int]
    left_color: Tuple[int, int, int]
    right_color: Tuple[int, int, int]
    biome: str

@dataclass
class Tile:
    """Represents a single tile with its block stack"""
    grid_x: int
    grid_y: int
    blocks: List[Block]
    biome: str
    height: int
    has_tree: bool = False
    has_resource: bool = False

class WorldGenerator:
    """Simple world generator for stacked block terrain"""
    
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        
        # Minecraft-style block colors
        self.block_colors = {
            'grass': (107, 142, 35),
            'dirt': (139, 69, 19),
            'stone': (128, 128, 128),
            'sand': (238, 203, 173),
            'water': (64, 164, 223),
            'snow': (255, 250, 250),
            'oak_log': (101, 67, 33),
            'birch_log': (196, 176, 128),
            'leaves': (34, 139, 34),
            'dark_leaves': (0, 100, 0),
            'coal_ore': (64, 64, 64),
            'iron_ore': (140, 140, 140),
            'gold_ore': (255, 215, 0),
            'diamond_ore': (185, 242, 255),
            'cobblestone': (119, 119, 119),
        }
        
    def generate_world(self, width: int = 50, height: int = 50) -> List[Block]:
        """Generate world as a flat list of blocks for easy rendering"""
        all_blocks = []
        
        # Generate terrain stacks
        for grid_y in range(height):
            for grid_x in range(width):
                blocks = self.generate_tile_blocks(grid_x, grid_y)
                all_blocks.extend(blocks)
                
        return all_blocks
        
    def generate_tile_blocks(self, grid_x: int, grid_y: int) -> List[Block]:
        """Generate blocks for a single tile position"""
        # Get biome and height
        biome = self.get_biome(grid_x, grid_y)
        height = self.get_height(grid_x, grid_y)
        
        blocks = []
        
        # Generate block stack from bottom to top
        for layer in range(height):
            block_type = self.get_block_type_for_layer(biome, layer, height)
            top_color = self.get_block_color(block_type, grid_x, grid_y, layer)
            
            block = Block(
                grid_x=grid_x,
                grid_y=grid_y,
                layer=layer,
                block_type=block_type,
                top_color=top_color,
                left_color=self.darken_color(top_color, 0.3),
                right_color=self.darken_color(top_color, 0.5),
                biome=biome
            )
            blocks.append(block)
            
        # Add tree blocks if needed
        if self.should_have_tree(grid_x, grid_y, biome):
            tree_blocks = self.generate_tree_blocks(grid_x, grid_y, height, biome)
            blocks.extend(tree_blocks)
            
        return blocks
        
    def get_biome(self, x: int, y: int) -> str:
        """Simple biome generation"""
        random.seed(self.seed + x * 73856093 + y * 19349663)
        biome_value = random.random()
        
        if biome_value < 0.15:
            return BIOME_WATER
        elif biome_value < 0.25:
            return BIOME_TUNDRA
        elif biome_value < 0.45:
            return BIOME_GRASSLAND
        elif biome_value < 0.65:
            return BIOME_FOREST
        elif biome_value < 0.80:
            return BIOME_DESERT
        else:
            return BIOME_MOUNTAIN
            
    def get_height(self, x: int, y: int) -> int:
        """Get terrain height (1-6 blocks)"""
        random.seed(self.seed + 1 + x * 73856093 + y * 19349663)
        base_height = random.randint(1, 3)
        
        # Add some variation
        random.seed(self.seed + 2 + (x // 2) * 73856093 + (y // 2) * 19349663)
        if random.random() < 0.1:  # 10% chance for tall features
            base_height += random.randint(1, 3)
            
        return min(6, base_height)
        
    def get_block_type_for_layer(self, biome: str, layer: int, total_height: int) -> str:
        """Get block type for a specific layer"""
        if layer == total_height - 1:  # Top layer
            if biome == BIOME_WATER:
                return 'water'
            elif biome == BIOME_DESERT:
                return 'sand'
            elif biome == BIOME_TUNDRA:
                return 'snow'
            elif biome == BIOME_MOUNTAIN:
                return 'stone'
            else:
                return 'grass'
                
        elif layer >= total_height - 3:  # Upper layers
            if biome == BIOME_DESERT:
                return 'sand'
            elif biome == BIOME_WATER:
                return 'sand'  # Sand under water
            else:
                return 'dirt'
                
        else:  # Deep layers
            if random.random() < 0.05:  # 5% chance for ore
                return random.choice(['coal_ore', 'iron_ore', 'gold_ore'])
            else:
                return 'stone'
                
    def generate_tree_blocks(self, grid_x: int, grid_y: int, ground_height: int, biome: str) -> List[Block]:
        """Generate tree blocks"""
        tree_blocks = []
        tree_height = random.randint(3, 5)
        
        # Tree trunk
        wood_type = 'birch_log' if biome == BIOME_TUNDRA else 'oak_log'
        for layer in range(ground_height, ground_height + tree_height):
            top_color = self.get_block_color(wood_type, grid_x, grid_y, layer)
            
            block = Block(
                grid_x=grid_x,
                grid_y=grid_y,
                layer=layer,
                block_type=wood_type,
                top_color=top_color,
                left_color=self.darken_color(top_color, 0.3),
                right_color=self.darken_color(top_color, 0.5),
                biome=biome
            )
            tree_blocks.append(block)
            
        # Tree leaves
        leaf_type = 'dark_leaves' if biome == BIOME_JUNGLE else 'leaves'
        for layer in range(ground_height + tree_height - 1, ground_height + tree_height + 2):
            top_color = self.get_block_color(leaf_type, grid_x, grid_y, layer)
            
            block = Block(
                grid_x=grid_x,
                grid_y=grid_y,
                layer=layer,
                block_type=leaf_type,
                top_color=top_color,
                left_color=self.darken_color(top_color, 0.3),
                right_color=self.darken_color(top_color, 0.5),
                biome=biome
            )
            tree_blocks.append(block)
            
        return tree_blocks
        
    def should_have_tree(self, x: int, y: int, biome: str) -> bool:
        """Check if position should have a tree"""
        if biome not in [BIOME_FOREST, BIOME_JUNGLE, BIOME_GRASSLAND]:
            return False
            
        random.seed(self.seed + 3 + x * 73856093 + y * 19349663)
        
        if biome == BIOME_FOREST:
            return random.random() > 0.6
        elif biome == BIOME_JUNGLE:
            return random.random() > 0.5
        else:  # Grassland
            return random.random() > 0.9
            
    def get_block_color(self, block_type: str, x: int, y: int, z: int) -> Tuple[int, int, int]:
        """Get block color with variation"""
        base_color = self.block_colors.get(block_type, (128, 128, 128))
        
        # Add some variation
        random.seed(self.seed + 5 + x * 73856093 + y * 19349663 + z * 83492791)
        variation = random.randint(-10, 10)
        
        color = tuple(max(0, min(255, c + variation)) for c in base_color)
        return color
        
    def darken_color(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Darken a color by factor"""
        return tuple(max(0, int(c * (1 - factor))) for c in color)
        
    def get_terrain_height_at(self, blocks: List[Block], grid_x: int, grid_y: int) -> int:
        """Get the height of terrain at a grid position"""
        max_height = 0
        for block in blocks:
            if block.grid_x == grid_x and block.grid_y == grid_y:
                if block.block_type != 'water':  # Don't count water as solid terrain
                    max_height = max(max_height, block.layer)
        return max_height