# map_generation.py - Enhanced for 9-Section Stepped Pyramids
import random
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any

@dataclass
class TerrainTile:
    """Single tile in a terrain stack with 9-section support"""
    tile_type: int          # 1=grass, 2=water, 3=stone, etc.
    height: int             # 0=ground level, 1=1 block up, etc.
    x: int                  # Grid position
    y: int
    sub_tiles: Dict         # 4x4 sub-tile building data (legacy)
    
    # Visual properties
    sprite_variant: int = 0
    damaged: float = 0.0    # For mining/digging
    
    # ENHANCED: Water animation properties
    visual_height_offset: float = 0.0  # Additional height offset for water animation
    wave_phase: float = 0.0            # Wave animation phase
    wave_amplitude: float = 0.0        # Wave strength
    foam_intensity: float = 0.0        # Foam/splash effects
    
    # NEW: 9-section data for Minecraft-style pyramids
    section_data: Dict[Tuple[int, int], Dict] = None  # (section_x, section_y) -> section_info
    
    def __post_init__(self):
        """Initialize 9-section data - FIXED for proper stepped pyramids"""
        if self.section_data is None:
            self.section_data = {}
            
        # Initialize 9 sections for this tile
        for section_y in range(3):
            for section_x in range(3):
                if (section_x, section_y) not in self.section_data:
                    self.section_data[(section_x, section_y)] = {
                        'exists': True,
                        'height_offset': 0.0,  # No complex height offsets - use actual layers
                        'damage': 0.0,
                        'building_type': None,
                        'building_id': None,
                        'variant': random.randint(0, 3)
                    }

class LayeredTerrain:
    """Manages stacked tiles with 9-section stepped pyramids"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        
        # Core storage: position -> list of stacked tiles
        # Key: (x, y) -> List[TerrainTile]
        self.terrain_stacks: Dict[Tuple[int, int], List[TerrainTile]] = {}
        
        # Quick lookup for existing code compatibility
        self.surface_map: List[List[int]] = [[1 for _ in range(width)] for _ in range(height)]
        self.height_map: List[List[int]] = [[0 for _ in range(width)] for _ in range(height)]
        
        # Dynamic water system
        self.water_system: 'DynamicWaterSystem' = None
        
    def get_surface_tile(self, x: int, y: int) -> int:
        """Get top tile type (for existing code compatibility)"""
        stack = self.terrain_stacks.get((x, y), [])
        if stack:
            return stack[-1].tile_type  # Top tile
        return 1  # Default grass
        
    def get_height_at(self, x: int, y: int) -> int:
        """Get terrain height at position"""
        stack = self.terrain_stacks.get((x, y), [])
        return len(stack) if stack else 1
        
    def add_tile_layer(self, x: int, y: int, tile_type: int, sub_tiles: Dict = None, pyramid_layer: int = 0, pyramid_sections: List[Tuple[int, int]] = None):
        """Add a tile layer at position with pyramid section control"""
        if (x, y) not in self.terrain_stacks:
            self.terrain_stacks[(x, y)] = []
            
        height = len(self.terrain_stacks[(x, y)])
        tile = TerrainTile(
            tile_type=tile_type,
            height=height,
            x=x,
            y=y,
            sub_tiles=sub_tiles or {},
            section_data=None  # Will be initialized in __post_init__
        )
        
        # FIXED: For pyramid layers, only certain sections exist
        if pyramid_sections is not None:
            # Initialize sections first
            tile.__post_init__()
            
            # Set all sections to not exist initially
            for section_y in range(3):
                for section_x in range(3):
                    tile.section_data[(section_x, section_y)]['exists'] = False
            
            # Only enable the specified sections for this pyramid layer
            for sect_x, sect_y in pyramid_sections:
                if 0 <= sect_x < 3 and 0 <= sect_y < 3:
                    tile.section_data[(sect_x, sect_y)]['exists'] = True
        
        self.terrain_stacks[(x, y)].append(tile)
        
        # Update compatibility maps
        self.surface_map[y][x] = tile_type
        self.height_map[y][x] = height + 1

############################################################
# ENHANCED TERRAIN GENERATION with FIXED Stepped Pyramids
############################################################

def generate_layered_terrain(width: int, height: int) -> LayeredTerrain:
    """Generate terrain with FIXED 9-section stepped pyramid mountains"""
    terrain = LayeredTerrain(width, height)
    
    print(f"[LayeredTerrain] Generating {width}x{height} terrain with FIXED Minecraft-style stepped pyramids...")
    
    # Start with existing flat generation as a base
    base_map = generate_procedural_map(width, height)
    
    # Convert flat terrain to layered terrain with FIXED stepped pyramids
    for y in range(height):
        for x in range(width):
            base_tile = base_map[y][x]
            
            if base_tile == -1:  # Void
                continue
            elif base_tile == 2:  # Water - create pure water columns
                water_depth = _calculate_water_depth_enhanced(x, y, width, height)
                _add_water_layers_enhanced(terrain, x, y, water_depth)
            elif base_tile == 4:  # Mountain - CREATE FIXED STEPPED PYRAMIDS
                mountain_height = _calculate_mountain_height_enhanced(x, y, width, height)
                _add_fixed_stepped_pyramid_mountain(terrain, x, y, mountain_height)
            elif base_tile in [6, 7]:  # Large mountains (256, 128) - BIGGER FIXED STEPPED PYRAMIDS
                if base_tile == 6:
                    mountain_height = _calculate_mountain_height_enhanced(x, y, width, height) + 4  # Taller
                else:
                    mountain_height = _calculate_mountain_height_enhanced(x, y, width, height) + 2
                _add_fixed_stepped_pyramid_mountain(terrain, x, y, mountain_height)
            else:  # Land tiles (grass, desert, dirt)
                land_height = _calculate_land_height_enhanced(x, y, width, height, base_tile)
                _add_land_layers_enhanced(terrain, x, y, land_height, base_tile)
    
    # ENHANCED: Add mountain ranges with FIXED stepped pyramids
    _add_fixed_stepped_mountain_ranges(terrain, width, height)
    
    # ENHANCED: Add plateau formations
    _add_plateaus(terrain, width, height)
    
    # DYNAMIC WATER: Initialize the subterranean water system
    terrain.water_system = DynamicWaterSystem(terrain)
    print(f"[LayeredTerrain] Initialized subterranean water system with {len(terrain.water_system.water_map)} underground pools")
    
    print(f"[LayeredTerrain] Generated terrain with {len(terrain.terrain_stacks)} stacked positions and FIXED stepped pyramid mountains")
    return terrain

def _add_fixed_stepped_pyramid_mountain(terrain: LayeredTerrain, x: int, y: int, height: int):
    """Add FIXED stepped pyramid mountain with proper layer-by-layer construction"""
    # Calculate how many pyramid layers we can fit
    max_pyramid_levels = min(4, height // 2)  # Up to 4 levels of pyramid
    base_layers = height - max_pyramid_levels
    
    # Add base mountain layers (full 9 sections each)
    for h in range(base_layers):
        terrain.add_tile_layer(x, y, 4)  # Stone foundation - all 9 sections exist
    
    # FIXED: Add stepped pyramid layers with specific section patterns
    pyramid_patterns = [
        # Level 0 (base): All 9 sections
        [(0,0), (1,0), (2,0), (0,1), (1,1), (2,1), (0,2), (1,2), (2,2)],
        # Level 1: Remove 4 corners (8 sections remain)
        [(1,0), (0,1), (1,1), (2,1), (1,2)],
        # Level 2: Center + 4 edges (5 sections)
        [(1,1)],
        # Level 3: Center only (1 section)
        [(1,1)]
    ]
    
    # Add pyramid layers with specific sections
    for level in range(max_pyramid_levels):
        if level < len(pyramid_patterns):
            sections_for_this_level = pyramid_patterns[level]
            terrain.add_tile_layer(x, y, 4, pyramid_sections=sections_for_this_level)
        else:
            # Fallback: just center section
            terrain.add_tile_layer(x, y, 4, pyramid_sections=[(1,1)])

def _add_fixed_stepped_mountain_ranges(terrain: LayeredTerrain, width: int, height: int):
    """Add dramatic mountain ranges using FIXED stepped pyramids"""
    print("[Enhanced Terrain] Adding FIXED stepped pyramid mountain ranges...")
    
    # Generate mountain ridge lines with FIXED stepped pyramids
    for y in range(height):
        for x in range(width):
            if (x, y) not in terrain.terrain_stacks:
                continue
                
            # Use ridge noise to create mountain ridges
            ridge_value = enhanced_noise.ridge_noise(x, y, octaves=3, scale=0.04)
            ridge_strength = enhanced_noise.multi_octave_noise(x * 2, y * 2, octaves=2, scale=0.08)
            
            # Create ridges where ridge noise is high
            if ridge_value > 0.7 and ridge_strength > 0.3:
                current_height = terrain.get_height_at(x, y)
                surface_tile = terrain.get_surface_tile(x, y)
                
                # Only enhance existing land (not water)
                if surface_tile not in [2, 5]:
                    # Add 2-6 more layers for ridge with FIXED stepped pyramid tops
                    additional_height = 2 + int(ridge_value * 6)
                    
                    # Add base mountain layers
                    for h in range(additional_height - 2):
                        terrain.add_tile_layer(x, y, 4)  # Stone
                    
                    # Add FIXED stepped pyramid top layers
                    _add_fixed_stepped_pyramid_mountain(terrain, x, y, additional_height)

def _calculate_mountain_height_enhanced(x: int, y: int, width: int, height: int) -> int:
    """Enhanced mountain height for FIXED stepped pyramids"""
    # Multi-layered noise for complex mountain shapes
    primary_noise = enhanced_noise.multi_octave_noise(x, y, octaves=5, persistence=0.6, scale=0.08)
    ridge_noise = enhanced_noise.ridge_noise(x, y, octaves=4, scale=0.06)
    domain_warp = enhanced_noise.domain_warped_noise(x, y, warp_strength=25.0)
    
    # Combine for dramatic mountain terrain
    mountain_noise = (primary_noise * 0.4 + ridge_noise * 0.4 + domain_warp * 0.2)
    
    # Distance from center - mountains near center are taller
    cx, cy = width // 2, height // 2
    dist_from_center = math.hypot(x - cx, y - cy)
    max_dist = math.hypot(cx, cy)
    center_factor = (1 - (dist_from_center / max_dist)) ** 1.5  # Exponential falloff
    
    # FIXED: Stepped pyramid mountains (reasonable heights for layered approach)
    base_height = 4 + int((mountain_noise + center_factor * 0.8) * 8)  # 4-12 high
    return max(4, min(base_height, 16))  # Cap at 16 blocks tall

def _calculate_water_depth_enhanced(x: int, y: int, width: int, height: int) -> int:
    """Enhanced water depth for proper water columns"""
    cx, cy = width // 2, height // 2
    dist_from_center = math.hypot(x - cx, y - cy)
    max_dist = math.hypot(cx, cy)
    
    depth_factor = 1 - (dist_from_center / max_dist)
    
    # Enhanced noise for natural water depth variation
    noise_variation = enhanced_noise.multi_octave_noise(x, y, octaves=3, persistence=0.6, scale=0.15)
    domain_warp = enhanced_noise.domain_warped_noise(x, y, warp_strength=15.0)
    
    combined_noise = (noise_variation + domain_warp) * 0.5
    
    # Water depth (height of water column)
    water_depth = max(1, int(depth_factor * 4 + combined_noise * 3))  # 1-7 blocks of water
    
    return max(1, min(water_depth, 8))  # Cap at 8 blocks deep

def _calculate_land_height_enhanced(x: int, y: int, width: int, height: int, base_tile: int) -> int:
    """Enhanced land height with sophisticated noise"""
    # Multi-octave noise for natural terrain
    primary_noise = enhanced_noise.multi_octave_noise(x, y, octaves=4, persistence=0.5, scale=0.12)
    detail_noise = enhanced_noise.multi_octave_noise(x, y, octaves=6, persistence=0.3, scale=0.25)
    domain_warp = enhanced_noise.domain_warped_noise(x, y, warp_strength=10.0)
    
    # Combine noises for complex terrain
    combined_noise = (primary_noise * 0.6 + detail_noise * 0.3 + domain_warp * 0.1)
    
    # Distance from center factor
    cx, cy = width // 2, height // 2
    dist_from_center = math.hypot(x - cx, y - cy)
    max_dist = math.hypot(cx, cy)
    center_factor = 1 - (dist_from_center / max_dist)
    
    if base_tile == 1:  # Grass - rolling hills and valleys
        base_height = 1 + int((combined_noise + center_factor * 0.4) * 6)  # 1-7 high
        return max(1, min(base_height, 8))
    elif base_tile == 11:  # Desert - varied dramatic terrain
        base_height = 1 + int((combined_noise + center_factor * 0.5) * 8)  # 1-9 high  
        return max(1, min(base_height, 12))
    elif base_tile == 3:  # Dirt - medium rolling terrain
        base_height = 1 + int((combined_noise + center_factor * 0.3) * 4)  # 1-5 high
        return max(1, min(base_height, 6))
    else:
        return max(1, int(combined_noise * 4) + 1)  # Default 1-5 high

def _add_land_layers_enhanced(terrain: LayeredTerrain, x: int, y: int, height: int, surface_type: int):
    """Enhanced land stacking with more geological realism"""
    for h in range(height):
        if h == 0:
            # Bedrock foundation
            tile_type = 4  # Stone bedrock
        elif h < height // 3:
            # Deep underground layers
            tile_type = 4  # Stone
        elif h < height * 2 // 3:
            # Mid layers - mix of stone and dirt
            if h % 2 == 0:
                tile_type = 3  # Dirt
            else:
                tile_type = 4  # Stone support
        elif h < height - 1:
            # Near surface layers
            tile_type = 3  # Dirt/soil
        else:
            # Top layer = surface type
            tile_type = surface_type
            
        terrain.add_tile_layer(x, y, tile_type)

def _add_water_layers_enhanced(terrain: LayeredTerrain, x: int, y: int, depth: int):
    """Create pure water columns - all tiles are water from bottom to top"""
    # Add stone bedrock at the very bottom for structural support
    terrain.add_tile_layer(x, y, 4)  # Stone bedrock foundation
    
    # Fill the rest with water tiles
    for h in range(depth):
        terrain.add_tile_layer(x, y, 2)  # Pure water column

def _add_plateaus(terrain: LayeredTerrain, width: int, height: int):
    """Add plateau formations for varied terrain"""
    print("[Enhanced Terrain] Adding plateau formations...")
    
    # Generate 2-3 plateau areas
    plateau_count = random.randint(2, 4)
    
    for _ in range(plateau_count):
        # Random plateau center
        center_x = random.randint(width // 4, 3 * width // 4)
        center_y = random.randint(height // 4, 3 * height // 4)
        plateau_radius = random.randint(8, 15)
        plateau_height = random.randint(3, 6)
        
        for y in range(max(0, center_y - plateau_radius), min(height, center_y + plateau_radius)):
            for x in range(max(0, center_x - plateau_radius), min(width, center_x + plateau_radius)):
                if (x, y) not in terrain.terrain_stacks:
                    continue
                    
                dist = math.hypot(x - center_x, y - center_y)
                if dist <= plateau_radius:
                    # Smooth plateau edges
                    edge_factor = 1.0 - (dist / plateau_radius)
                    actual_height = int(plateau_height * edge_factor)
                    
                    surface_tile = terrain.get_surface_tile(x, y)
                    if surface_tile not in [2, 5] and actual_height > 0:  # Not water
                        # Add plateau layers
                        for h in range(actual_height):
                            if h < actual_height - 1:
                                terrain.add_tile_layer(x, y, 4)  # Stone
                            else:
                                terrain.add_tile_layer(x, y, surface_tile)  # Keep surface type

############################################################
# ENHANCED NOISE SYSTEM (unchanged but needed)
############################################################

class EnhancedNoise:
    """Multi-octave noise generator for natural terrain"""
    
    def __init__(self, seed=None):
        if seed is not None:
            random.seed(seed)
        
        # Create permutation table for noise
        self.perm = list(range(256))
        random.shuffle(self.perm)
        self.perm = self.perm + self.perm  # Duplicate for easy wrapping
    
    def fade(self, t):
        """Smooth fade function"""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def lerp(self, t, a, b):
        """Linear interpolation"""
        return a + t * (b - a)
    
    def grad(self, hash_val, x, y):
        """Gradient function"""
        h = hash_val & 15
        u = x if h < 8 else y
        v = y if h < 4 else (x if h == 12 or h == 14 else 0)
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)
    
    def noise(self, x, y):
        """2D Perlin-style noise"""
        # Find grid cell
        X = int(x) & 255
        Y = int(y) & 255
        
        # Relative position in cell
        x -= int(x)
        y -= int(y)
        
        # Fade curves
        u = self.fade(x)
        v = self.fade(y)
        
        # Hash coordinates
        A = self.perm[X] + Y
        AA = self.perm[A]
        AB = self.perm[A + 1]
        B = self.perm[X + 1] + Y
        BA = self.perm[B]
        BB = self.perm[B + 1]
        
        # Interpolate gradients
        return self.lerp(v,
            self.lerp(u, self.grad(self.perm[AA], x, y),
                        self.grad(self.perm[BA], x - 1, y)),
            self.lerp(u, self.grad(self.perm[AB], x, y - 1),
                        self.grad(self.perm[BB], x - 1, y - 1)))
    
    def multi_octave_noise(self, x, y, octaves=4, persistence=0.5, scale=0.1):
        """Multi-octave noise for natural terrain variation"""
        value = 0.0
        amplitude = 1.0
        frequency = scale
        max_value = 0.0
        
        for i in range(octaves):
            value += self.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2.0
        
        return value / max_value
    
    def ridge_noise(self, x, y, octaves=3, scale=0.05):
        """Ridge noise for mountain ridges and valleys"""
        noise_val = self.multi_octave_noise(x, y, octaves, 0.6, scale)
        return 1.0 - abs(noise_val)
    
    def domain_warped_noise(self, x, y, warp_strength=20.0):
        """Domain warped noise for more interesting terrain"""
        warp_x = x + self.multi_octave_noise(x, y, 3, 0.4, 0.02) * warp_strength
        warp_y = y + self.multi_octave_noise(x + 100, y + 100, 3, 0.4, 0.02) * warp_strength
        return self.multi_octave_noise(warp_x, warp_y, 4, 0.5, 0.08)

# Global noise generator
enhanced_noise = EnhancedNoise()

############################################################
# EXISTING FUNCTIONS (mostly unchanged)
############################################################

def group_mountain_clusters(map_data):
    visited = set()
    clusters = []

    height = len(map_data)
    width = len(map_data[0]) if height > 0 else 0

    def dfs_iterative(sx, sy):
        stack = [(sx, sy)]
        cluster_pts = []
        while stack:
            x, y = stack.pop()
            if (x, y) not in visited:
                visited.add((x, y))
                cluster_pts.append((x, y))
                # check neighbors
                for nx, ny in [(x+1, y),(x-1, y),(x, y+1),(x, y-1)]:
                    if 0<=nx<width and 0<=ny<height:
                        if map_data[ny][nx] == 4 and (nx, ny) not in visited:
                            stack.append((nx, ny))
        return cluster_pts

    for y in range(height):
        for x in range(width):
            if map_data[y][x] == 4 and (x, y) not in visited:
                c = dfs_iterative(x, y)
                clusters.append(c)

    return clusters

def replace_mountain_clusters(map_data, clusters):
    for cluster in clusters:
        size = len(cluster)
        # foot tile => largest x+y
        base_x, base_y = max(cluster, key=lambda pos: pos[0]+pos[1])
        for (cx, cy) in cluster:
            map_data[cy][cx] = 0
        if size >= 16:
            map_data[base_y][base_x] = 6  # mountain-256
        elif size >= 4:
            map_data[base_y][base_x] = 7  # mountain-128

def generate_procedural_map(width, height):
    """Generate base procedural map (unchanged from original)"""
    map_data = [[0 for _ in range(width)] for _ in range(height)]

    biome_seeds = [
        ("water", 6),  # Water seeds for better pools
        ("desert", 4),
        ("mountain", 5),  # More mountain seeds for stepped pyramids
        ("grass", 4)
    ]
    seeds=[]
    for (b,count) in biome_seeds:
        for _ in range(count):
            sx = random.randint(0, width-1)
            sy = random.randint(0, height-1)
            seeds.append((sx, sy, b))

    def get_tile_for_biome(biome):
        if biome=="water":
            return 2  # ONLY use regular water
        elif biome=="desert":
            return 11
        elif biome=="mountain":
            return 4  # These will become stepped pyramids
        return 1

    def dist2(x1,y1,x2,y2):
        dx = x2 - x1
        dy = y2 - y1
        return dx*dx + dy*dy

    # Voronoi fill
    for y in range(height):
        for x in range(width):
            best_d2 = 999999999
            best_biome = "grass"
            for (sx, sy, b) in seeds:
                d2 = dist2(x,y, sx,sy)
                if d2 < best_d2:
                    best_d2 = d2
                    best_biome = b
            map_data[y][x] = get_tile_for_biome(best_biome)

    # cluster small mountains => bigger stepped pyramids
    clusters = group_mountain_clusters(map_data)
    replace_mountain_clusters(map_data, clusters)

    # leftover => grass
    for y in range(height):
        for x in range(width):
            if map_data[y][x] == 0:
                map_data[y][x] = 1

    # forced mountains on edges (these will become stepped pyramids)
    edge_mountain_prob = 1.0
    w = len(map_data[0])
    h = len(map_data)
    for x in range(w):
        if map_data[0][x] != 2 and random.random() < edge_mountain_prob:  # Don't convert water
            map_data[0][x] = 4
        if map_data[h-1][x] != 2 and random.random() < edge_mountain_prob:  # Don't convert water
            map_data[h-1][x] = 4
    for y in range(h):
        if map_data[y][0] != 2 and random.random() < edge_mountain_prob:  # Don't convert water
            map_data[y][0] = 4
        if map_data[y][w-1] != 2 and random.random() < edge_mountain_prob:  # Don't convert water
            map_data[y][w-1] = 4

    # re-run cluster
    clusters = group_mountain_clusters(map_data)
    replace_mountain_clusters(map_data, clusters)

    # random rings => mountain chance (these become stepped pyramids)
    RING_COUNT = 4
    ring_mountain_prob = 0.5
    for i in range(1, RING_COUNT+1):
        if i>h-1-i or i>w-1-i:
            break
        for x in range(i, w-i):
            if map_data[i][x] != 2:  # Don't convert water
                if random.random() < ring_mountain_prob:
                    map_data[i][x] = 4
            if map_data[h-1-i][x] != 2:  # Don't convert water
                if random.random() < ring_mountain_prob:
                    map_data[h-1-i][x] = 4

        for y in range(i, h-i):
            if map_data[y][i] != 2:  # Don't convert water
                if random.random() < ring_mountain_prob:
                    map_data[y][i] = 4
            if map_data[y][w-1-i] != 2:  # Don't convert water
                if random.random() < ring_mountain_prob:
                    map_data[y][w-1-i] = 4

    return map_data

# All other functions (apply_circular_mask, etc.) remain the same as original
def apply_circular_mask(map_data):
    height = len(map_data)
    width = len(map_data[0]) if height > 0 else 0

    cx, cy = width // 2, height // 2
    R = min(cx, cy) - 5
    for y in range(height):
        for x in range(width):
            dx = x - cx
            dy = y - cy
            dist_sq = dx*dx + dy*dy
            if dist_sq > R*R:
                map_data[y][x] = -1

def apply_circular_mask_layered(terrain: LayeredTerrain):
    """Apply circular mask to layered terrain"""
    width, height = terrain.width, terrain.height
    cx, cy = width // 2, height // 2
    R = min(cx, cy) - 5
    
    positions_to_remove = []
    
    for y in range(height):
        for x in range(width):
            dx = x - cx
            dy = y - cy
            dist_sq = dx*dx + dy*dy
            if dist_sq > R*R:
                positions_to_remove.append((x, y))
                terrain.surface_map[y][x] = -1
                terrain.height_map[y][x] = 0
    
    # Remove from terrain stacks
    for x, y in positions_to_remove:
        if (x, y) in terrain.terrain_stacks:
            del terrain.terrain_stacks[(x, y)]

def force_mountain_edge(map_data, margin=2):
    height = len(map_data)
    width = len(map_data[0]) if height > 0 else 0
    cx, cy = width // 2, height // 2
    R = min(cx, cy) - 5
    min_dist_sq = (R - margin)*(R - margin)
    max_dist_sq = R*R
    for y in range(height):
        for x in range(width):
            if map_data[y][x] == -1:
                continue
            dx = x - cx
            dy = y - cy
            dist_sq = dx*dx + dy*dy
            if min_dist_sq <= dist_sq <= max_dist_sq:
                if map_data[y][x] not in (2,5):
                    map_data[y][x] = 4  # These become stepped pyramids

def force_mountain_edge_layered(terrain: LayeredTerrain, margin=2):
    """Force mountain edge on layered terrain with FIXED stepped pyramids"""
    width, height = terrain.width, terrain.height
    cx, cy = width // 2, height // 2
    R = min(cx, cy) - 5
    min_dist_sq = (R - margin)*(R - margin)
    max_dist_sq = R*R
    
    for y in range(height):
        for x in range(width):
            if (x, y) not in terrain.terrain_stacks:
                continue
            dx = x - cx
            dy = y - cy
            dist_sq = dx*dx + dy*dy
            if min_dist_sq <= dist_sq <= max_dist_sq:
                surface_tile = terrain.get_surface_tile(x, y)
                if surface_tile != 2:  # Don't convert water pools
                    # Convert to FIXED stepped pyramid mountain
                    current_height = terrain.get_height_at(x, y)
                    mountain_height = max(current_height + 3, 8)  # Taller edge mountains
                    
                    # Clear existing stack and rebuild as FIXED stepped pyramid mountain
                    terrain.terrain_stacks[(x, y)] = []
                    _add_fixed_stepped_pyramid_mountain(terrain, x, y, mountain_height)

# Tree and vegetation functions remain the same but are aware of FIXED stepped pyramids
def make_forest_map(map_data):
    height = len(map_data)
    width = len(map_data[0])
    forest_map = [[False for _ in range(width)] for _ in range(height)]

    forest_seed_count = 8
    grass_positions = []
    for y in range(height):
        for x in range(width):
            if map_data[y][x] == 1:
                grass_positions.append((x,y))
    random.shuffle(grass_positions)
    seeds = grass_positions[:forest_seed_count]

    def dist2(x1,y1,x2,y2):
        dx=x2-x1
        dy=y2-y1
        return dx*dx + dy*dy

    for y in range(height):
        for x in range(width):
            if map_data[y][x] == 1:
                best_d2 = 999999999
                for (sx,sy) in seeds:
                    d2 = dist2(x,y,sx,sy)
                    if d2 < best_d2:
                        best_d2 = d2
                if best_d2 < 500:
                    forest_map[y][x] = True
    return forest_map

def make_forest_map_layered(terrain: LayeredTerrain):
    """Create forest map for layered terrain with FIXED stepped pyramids"""
    width, height = terrain.width, terrain.height
    forest_map = [[False for _ in range(width)] for _ in range(height)]

    print(f"[make_forest_map_layered] Creating forest map for {width}x{height} FIXED stepped pyramid terrain")

    # Find all grass positions - CHECK FOR CIRCULAR MASK
    grass_positions = []
    for y in range(height):
        for x in range(width):
            # CRITICAL: Only generate on valid terrain within the circular boundary
            if (x, y) in terrain.terrain_stacks and terrain.get_surface_tile(x, y) == 1:  # Grass
                grass_positions.append((x, y))
    
    print(f"[make_forest_map_layered] Found {len(grass_positions)} grass positions within planet boundary")
    
    if not grass_positions:
        print("[make_forest_map_layered] No grass positions found for forest placement")
        return forest_map
    
    # Create forest seeds - more of them for better coverage
    forest_seed_count = max(6, min(15, len(grass_positions) // 15))  # Reduced density
    random.shuffle(grass_positions)
    seeds = grass_positions[:min(forest_seed_count, len(grass_positions))]
    
    print(f"[make_forest_map_layered] Using {len(seeds)} forest seeds")

    def dist2(x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        return dx*dx + dy*dy

    forest_tiles_count = 0
    
    for y in range(height):
        for x in range(width):
            # CRITICAL: Only place trees on valid terrain within the boundary
            if (x, y) not in terrain.terrain_stacks:
                continue
            if terrain.get_surface_tile(x, y) != 1:  # Only on grass
                continue
                
            best_d2 = 999999999
            for (sx, sy) in seeds:
                d2 = dist2(x, y, sx, sy)
                if d2 < best_d2:
                    best_d2 = d2
                    
            # Reduced forest radius to prevent overflow
            if best_d2 < 400:  # Reduced from 800
                forest_map[y][x] = True
                forest_tiles_count += 1
    
    print(f"[make_forest_map_layered] Created forest map with {forest_tiles_count} forest tiles")
    return forest_map

def populate_trees_layered(terrain: LayeredTerrain, forest_map, base_density=0.04, water_density=0.12, cluster_size=(2,5)):
    """Populate trees on layered terrain with FIXED stepped pyramids"""
    width, height = terrain.width, terrain.height
    tree_data_list = []
    near_water_positions = find_grass_near_water_layered(terrain)
    used_starters = set()

    print(f"[populate_trees_layered] Generating trees on {width}x{height} FIXED stepped pyramid terrain")

    trees_generated = 0
    
    for y in range(height):
        for x in range(width):
            # CRITICAL: Only place trees on valid terrain within the circular boundary
            if (x, y) not in terrain.terrain_stacks:
                continue
                
            surface_tile = terrain.get_surface_tile(x, y)
            if surface_tile == -1:
                continue
            if not tile_is_grass(surface_tile):
                continue
            if (x, y) in used_starters:
                continue

            dens = water_density if (x, y) in near_water_positions else base_density
            if y < len(forest_map) and x < len(forest_map[0]) and forest_map[y][x]:
                dens *= 3  # Higher density in forests

            if random.random() < dens:
                count = random.randint(cluster_size[0], cluster_size[1])
                used_starters.add((x, y))
                possible = []
                radius = 2  # Reduced radius to keep trees closer
                for dy in range(-radius, radius + 1):
                    for dx2 in range(-radius, radius + 1):
                        nx = x + dx2
                        ny = y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            # CRITICAL: Only add positions that are within the planet boundary
                            if (nx, ny) in terrain.terrain_stacks:
                                surface = terrain.get_surface_tile(nx, ny)
                                if surface != -1 and tile_is_grass(surface):
                                    possible.append((nx, ny))
                random.shuffle(possible)
                chosen = possible[:count]

                for (sx, sy) in chosen:
                    # Get height for tree placement
                    tree_height = terrain.get_height_at(sx, sy)
                    
                    num_trees = random.randint(1, 2)  # Reduced tree count per tile
                    if sy < len(forest_map) and sx < len(forest_map[0]) and forest_map[sy][sx]:
                        num_trees = random.randint(1, 4)  # Reduced forest density
                    for _ in range(num_trees):
                        ttype = random.choice([1, 2, 3])
                        off_x = random.randint(-6, 6)  # Reduced spread
                        off_y = random.randint(-6, 0)
                        # Store tree data with height information
                        tree_data_list.append((sx, sy, ttype, off_x, off_y, tree_height))
                        trees_generated += 1

    print(f"[populate_trees_layered] Generated {len(tree_data_list)} tree positions ({trees_generated} total trees)")
    return tree_data_list

def find_grass_near_water_layered(terrain: LayeredTerrain):
    """Find grass tiles near water in layered terrain"""
    width, height = terrain.width, terrain.height
    near_water = set()
    
    for y in range(height):
        for x in range(width):
            # CRITICAL: Only check tiles that exist within the planet boundary
            if (x, y) not in terrain.terrain_stacks:
                continue
            if tile_is_grass(terrain.get_surface_tile(x, y)):
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        nx = x + dx
                        ny = y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            if (nx, ny) in terrain.terrain_stacks and tile_is_water(terrain.get_surface_tile(nx, ny)):
                                near_water.add((x, y))
                                break
    return near_water

def tile_is_grass(tv):
    return tv == 1

def tile_is_water(tv):
    return tv == 2  # ONLY regular water

def populate_trees(map_data, forest_map, base_density=0.02, water_density=0.10, cluster_size=(3,8)):
    """Original tree population for flat terrain"""
    # Same as original implementation
    height = len(map_data)
    width = len(map_data[0])
    tree_data_list = []
    near_water_positions = find_grass_near_water(map_data)
    used_starters=set()

    for y in range(height):
        for x in range(width):
            if map_data[y][x] == -1:
                continue
            if not tile_is_grass(map_data[y][x]):
                continue
            if (x,y) in used_starters:
                continue

            dens = water_density if (x,y) in near_water_positions else base_density
            if forest_map[y][x]:
                dens *= 3

            if random.random() < dens:
                count = random.randint(cluster_size[0], cluster_size[1])
                used_starters.add((x,y))
                possible=[]
                radius=4
                for dy in range(-radius, radius+1):
                    for dx2 in range(-radius, radius+1):
                        nx = x+dx2
                        ny = y+dy
                        if 0<=nx<width and 0<=ny<height:
                            if map_data[ny][nx] != -1 and tile_is_grass(map_data[ny][nx]):
                                possible.append((nx,ny))
                random.shuffle(possible)
                chosen=possible[:count]

                for (sx,sy) in chosen:
                    num_trees = random.randint(1,4)
                    if forest_map[sy][sx]:
                        num_trees = random.randint(2,8)
                    for _ in range(num_trees):
                        ttype = random.choice([1,2,3])
                        off_x = random.randint(-10,10)
                        off_y = random.randint(-10,0)
                        tree_data_list.append((sx, sy, ttype, off_x, off_y))

    return tree_data_list

def find_grass_near_water(map_data):
    height = len(map_data)
    width = len(map_data[0])
    near_water=set()
    for y in range(height):
        for x in range(width):
            if tile_is_grass(map_data[y][x]):
                for dy in [-1,0,1]:
                    for dx in [-1,0,1]:
                        nx = x+dx
                        ny = y+dy
                        if 0<=nx<width and 0<=ny<height:
                            if tile_is_water(map_data[ny][nx]):
                                near_water.add((x,y))
                                break
    return near_water

############################################################
# DYNAMIC WATER SYSTEM (unchanged but compatible)
############################################################

class DynamicWaterSystem:
    """Advanced water simulation with flow, waves, and tides (compatible with FIXED stepped pyramids)"""
    
    def __init__(self, terrain):
        self.terrain = terrain
        self.water_map = {}  # (x, y) -> WaterTile
        self.time = 0.0
        self.wave_speed = 3.0
        self.tide_period = 50.0
        self.flow_rate = 0.2
        
        # Water noise generator
        self.water_noise = EnhancedNoise(seed=42)
        
        # Initialize water tiles
        self._initialize_water_tiles()
        
        print(f"[DynamicWaterSystem] Initialized with {len(self.water_map)} water tiles")
        
    def _initialize_water_tiles(self):
        """Find all water positions and create water tiles"""
        water_count = 0
        
        for (x, y), stack in self.terrain.terrain_stacks.items():
            has_water = False
            water_layer_index = 0
            
            # Check ALL layers in the stack for water tiles (ONLY type 2)
            for i, tile in enumerate(stack):
                if tile.tile_type == 2:  # ONLY regular water
                    has_water = True
                    water_layer_index = i
                    break  # Use the first water layer found
            
            if has_water:
                self.water_map[(x, y)] = {
                    'base_level': float(water_layer_index),
                    'current_level': float(water_layer_index),
                    'velocity': 0.0,
                    'wave_phase': 0.0,
                    'flow_x': 0.0,
                    'flow_y': 0.0
                }
                water_count += 1
        
        print(f"[DynamicWaterSystem] Initialized {water_count} water tiles")
    
    def update_water_dynamics(self, dt: float):
        """Update water physics - flow, waves, and tides"""
        self.time += dt * 0.01
        
        # Update each water tile
        for (x, y), water_data in self.water_map.items():
            self._update_water_tile(x, y, water_data, dt)
        
        # Apply flow between adjacent water tiles
        self._apply_water_flow(dt)
        
        # Update terrain based on new water levels
        self._update_terrain_water_levels()
    
    def _update_water_tile(self, x: int, y: int, water_data: dict, dt: float):
        """Update individual water tile physics"""
        # Calculate surrounding land height to constrain water
        max_water_height = self._get_max_subterranean_height(x, y)
        
        # Wave motion for subterranean pools
        wave_noise = self.water_noise.multi_octave_noise(
            x + self.time * self.wave_speed, 
            y + self.time * self.wave_speed * 0.7, 
            octaves=4, persistence=0.7, scale=0.2
        )
        
        # Tidal motion but constrained to stay underground
        tide_factor = math.sin(self.time * 2 * math.pi / self.tide_period) * 1.5
        
        # Distance-based wave propagation
        cx, cy = self.terrain.width // 2, self.terrain.height // 2
        dist_from_center = math.hypot(x - cx, y - cy)
        wave_propagation = math.sin(dist_from_center * 0.3 - self.time * 4.0) * 1.0
        
        # Secondary wave patterns
        secondary_wave = math.cos(x * 0.5 + self.time * 2.5) * math.sin(y * 0.3 + self.time * 3.0) * 0.8
        
        # Combine all water effects with CONSTRAINED amplitudes
        base_level = water_data['base_level']
        wave_height = (wave_noise * 2.0 + tide_factor + wave_propagation + secondary_wave)
        
        # Constrained water movement - CANNOT exceed surface
        target_level = base_level + wave_height
        current_level = water_data['current_level']
        
        # Stronger momentum and less damping for dramatic underground movement
        level_diff = target_level - current_level
        water_data['velocity'] += level_diff * 0.3 - water_data['velocity'] * 0.02
        water_data['current_level'] += water_data['velocity'] * dt * 0.01
        
        # CRITICAL: Constrain water to stay BELOW surface level
        water_data['current_level'] = max(
            water_data['current_level'], 
            base_level - 3.0  # Allow water to go lower (deeper underground)
        )
        water_data['current_level'] = min(
            water_data['current_level'], 
            max_water_height - 1.0  # STAY BELOW SURFACE
        )
        
        # Calculate flow direction based on height differences
        self._calculate_water_flow(x, y, water_data)
    
    def _get_max_subterranean_height(self, x: int, y: int) -> float:
        """Get maximum height water can reach while staying subterranean"""
        # Check surrounding terrain to find minimum land height
        min_land_height = float('inf')
        
        # Check 3x3 area around water position
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if (nx, ny) in self.terrain.terrain_stacks:
                    stack = self.terrain.terrain_stacks[(nx, ny)]
                    # Find the height of non-water layers (land height)
                    land_height = 0
                    for i, tile in enumerate(stack):
                        if tile.tile_type != 2:  # Not water
                            land_height = i + 1
                    min_land_height = min(min_land_height, land_height)
        
        # Water cannot exceed the lowest surrounding land height
        return min_land_height if min_land_height != float('inf') else 3.0
    
    def _calculate_water_flow(self, x: int, y: int, water_data: dict):
        """Calculate flow direction based on surrounding water levels"""
        current_level = water_data['current_level']
        flow_x, flow_y = 0.0, 0.0
        
        # Check 4 adjacent directions
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (nx, ny) in self.water_map:
                neighbor_level = self.water_map[(nx, ny)]['current_level']
                height_diff = current_level - neighbor_level
                
                if height_diff > 0.1:  # Water flows downhill
                    flow_x += dx * height_diff * self.flow_rate
                    flow_y += dy * height_diff * self.flow_rate
        
        # Update flow with momentum
        water_data['flow_x'] = water_data['flow_x'] * 0.8 + flow_x * 0.2
        water_data['flow_y'] = water_data['flow_y'] * 0.8 + flow_y * 0.2
    
    def _apply_water_flow(self, dt: float):
        """Apply flow between water tiles"""
        flow_transfers = []
        
        for (x, y), water_data in self.water_map.items():
            flow_x = water_data['flow_x']
            flow_y = water_data['flow_y']
            
            if abs(flow_x) > 0.01 or abs(flow_y) > 0.01:
                # Determine target flow position
                target_x = x + (1 if flow_x > 0 else -1 if flow_x < 0 else 0)
                target_y = y + (1 if flow_y > 0 else -1 if flow_y < 0 else 0)
                
                if (target_x, target_y) in self.water_map:
                    flow_amount = min(abs(flow_x) + abs(flow_y), 0.1) * dt * 0.001
                    flow_transfers.append(((x, y), (target_x, target_y), flow_amount))
        
        # Apply transfers
        for (from_pos, to_pos, amount) in flow_transfers:
            if from_pos in self.water_map and to_pos in self.water_map:
                self.water_map[from_pos]['current_level'] -= amount
                self.water_map[to_pos]['current_level'] += amount
                
                # Don't let water level go too low
                self.water_map[from_pos]['current_level'] = max(
                    self.water_map[from_pos]['current_level'], 
                    self.water_map[from_pos]['base_level'] - 1.0
                )
    
    def _update_terrain_water_levels(self):
        """Update terrain based on new water levels"""
        for (x, y), stack in self.terrain.terrain_stacks.items():
            water_data = self.water_map.get((x, y))
            
            # Calculate land surface height for this position
            land_surface_height = self._get_land_surface_height(x, y)
            
            for i, tile in enumerate(stack):
                if tile.tile_type == 2:  # ONLY regular water
                    if water_data:
                        # Tile is in dynamic water system - use calculated values
                        current_level = water_data['current_level']
                        base_level = water_data['base_level']
                        height_difference = current_level - base_level
                        
                        # CRITICAL: Constrain visual height to stay below surface
                        max_visual_offset = max(0, land_surface_height - i - 1) * 8  # Stay below land
                        
                        # Visual height offset but constrained to subterranean
                        raw_offset = height_difference * 8
                        constrained_offset = min(raw_offset, max_visual_offset)
                        tile.visual_height_offset = max(constrained_offset, -20)  # Allow going deeper
                        
                        # Add wave animation properties
                        tile.wave_phase = self.time + i * 0.5
                        tile.wave_amplitude = min(abs(height_difference) * 2, max_visual_offset / 4)
                        
                        # ONLY use regular water type 2
                        tile.tile_type = 2
                        
                        # Add foam/splash effects for underground movement
                        if hasattr(water_data, 'velocity') and abs(water_data.get('velocity', 0)) > 0.3:
                            tile.foam_intensity = min(0.5, abs(water_data.get('velocity', 0)) * 1.5)
                        else:
                            tile.foam_intensity = 0.0
                    else:
                        # Fallback animation with subterranean constraints
                        self._apply_fallback_water_animation(tile, x, y, i, land_surface_height)
    
    def _get_land_surface_height(self, x: int, y: int) -> int:
        """Get the height of the land surface (non-water tiles)"""
        if (x, y) not in self.terrain.terrain_stacks:
            return 3
            
        stack = self.terrain.terrain_stacks[(x, y)]
        surface_height = 0
        
        # Find the topmost non-water tile
        for i in range(len(stack) - 1, -1, -1):
            if stack[i].tile_type != 2:  # Not water
                surface_height = i + 1
                break
                
        return surface_height
    
    def _apply_fallback_water_animation(self, tile, x, y, layer_index, land_surface_height):
        """Apply fallback animation to water tiles with subterranean constraints"""
        # Simple wave animation for tiles not in the dynamic system
        wave_noise = self.water_noise.multi_octave_noise(
            x + self.time * self.wave_speed * 0.5, 
            y + self.time * self.wave_speed * 0.3, 
            octaves=3, persistence=0.6, scale=0.25
        )
        
        # Distance-based wave
        cx, cy = self.terrain.width // 2, self.terrain.height // 2
        dist_from_center = math.hypot(x - cx, y - cy)
        wave_propagation = math.sin(dist_from_center * 0.3 - self.time * 3.0) * 0.6
        
        # Combine effects
        wave_height = (wave_noise * 1.5 + wave_propagation)
        
        # CRITICAL: Constrain to stay below surface
        max_visual_offset = max(0, land_surface_height - layer_index - 1) * 6
        
        # Apply to tile - constrained to subterranean
        raw_offset = wave_height * 8
        tile.visual_height_offset = min(raw_offset, max_visual_offset)
        tile.wave_phase = self.time + layer_index * 0.3
        tile.wave_amplitude = min(abs(wave_height) * 2, max_visual_offset / 4)
        tile.foam_intensity = 0.0
        tile.tile_type = 2  # Ensure it's regular water
    
    def get_water_height_at(self, x: int, y: int) -> float:
        """Get current water height at position"""
        if (x, y) in self.water_map:
            return self.water_map[(x, y)]['current_level']
        return 0.0
    
    def create_splash(self, x: int, y: int, intensity: float = 1.0):
        """Create a splash effect that propagates outward"""
        if (x, y) not in self.water_map:
            return
            
        # Add sudden upward velocity for splash
        self.water_map[(x, y)]['velocity'] += intensity
        
        # Propagate to nearby water tiles
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if (nx, ny) in self.water_map:
                    distance = math.hypot(dx, dy)
                    propagated_intensity = intensity * (0.5 / distance)
                    self.water_map[(nx, ny)]['velocity'] += propagated_intensity