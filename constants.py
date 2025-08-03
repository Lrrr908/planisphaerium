"""
Game Constants
Defines all the core constants used throughout the game
"""

# Isometric tile dimensions
TILE_WIDTH = 64
TILE_HEIGHT = 32  # Standard isometric ratio (2:1)
BLOCK_HEIGHT = 16

# Screen dimensions
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
HUD_WIDTH = 300  # Right side HUD width

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (192, 192, 192)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)

# Game states
GAME_STATE_PLANET = "planet"
GAME_STATE_SYSTEM = "system"
GAME_STATE_GALAXY = "galaxy"
GAME_STATE_UNIVERSE = "universe"

# Biome types
BIOME_GRASSLAND = "grassland"
BIOME_FOREST = "forest"
BIOME_DESERT = "desert"
BIOME_MOUNTAIN = "mountain"
BIOME_WATER = "water"
BIOME_TUNDRA = "tundra"
BIOME_JUNGLE = "jungle"

# Entity types
ENTITY_BIPED = "biped"
ENTITY_ANIMAL = "animal"
ENTITY_BUILDING = "building"
ENTITY_VEHICLE = "vehicle"
ENTITY_SHIP = "ship"

# Animal types
ANIMAL_HERBIVORE = "herbivore"
ANIMAL_CARNIVORE = "carnivore"
ANIMAL_OMNIVORE = "omnivore"

# Building types
BUILDING_HOUSE = "house"
BUILDING_FARM = "farm"
BUILDING_FACTORY = "factory"
BUILDING_LAB = "lab"
BUILDING_SPACEPORT = "spaceport"

# Resource types
RESOURCE_FOOD = "food"
RESOURCE_WOOD = "wood"
RESOURCE_STONE = "stone"
RESOURCE_METAL = "metal"
RESOURCE_ENERGY = "energy"
RESOURCE_SCIENCE = "science"

# Camera settings
CAMERA_MIN_ZOOM = 0.5
CAMERA_MAX_ZOOM = 3.0
CAMERA_ZOOM_SPEED = 0.1
CAMERA_PAN_SPEED = 5.0

# Pathfinding
PATHFINDING_GRID_SIZE = 32
PATHFINDING_MAX_DISTANCE = 1000

# World generation
WORLD_SIZE = 100  # 100x100 tiles
CHUNK_SIZE = 16   # 16x16 tiles per chunk
BIOME_SCALE = 0.02
HEIGHT_SCALE = 0.03
TREE_DENSITY = 0.1
ANIMAL_DENSITY = 0.05

# Game progression
UNLOCK_SYSTEM_VIEW = 1000  # Science points needed
UNLOCK_GALAXY_VIEW = 5000
UNLOCK_UNIVERSE_VIEW = 10000 