"""
Game State Management
Handles the overall game state, progression, and resource management
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from ..core.constants import *

@dataclass
class Resource:
    """Resource data class"""
    name: str
    amount: int
    max_amount: int = 1000
    
    def add(self, amount: int) -> bool:
        """Add resources, return True if successful"""
        if self.amount + amount <= self.max_amount:
            self.amount += amount
            return True
        return False
    
    def remove(self, amount: int) -> bool:
        """Remove resources, return True if successful"""
        if self.amount >= amount:
            self.amount -= amount
            return True
        return False

@dataclass
class PlanetData:
    """Planet data for persistence"""
    name: str
    seed: int
    biome_data: Dict
    buildings: List[Dict]
    entities: List[Dict]
    resources: Dict[str, int]
    discovered: bool = False

class GameState:
    """Main game state manager"""
    
    def __init__(self):
        # Resources
        self.resources = {
            RESOURCE_FOOD: Resource(RESOURCE_FOOD, 100),
            RESOURCE_WOOD: Resource(RESOURCE_WOOD, 50),
            RESOURCE_STONE: Resource(RESOURCE_STONE, 25),
            RESOURCE_METAL: Resource(RESOURCE_METAL, 10),
            RESOURCE_ENERGY: Resource(RESOURCE_ENERGY, 100),
            RESOURCE_SCIENCE: Resource(RESOURCE_SCIENCE, 0)
        }
        
        # Progression
        self.science_points = 0
        self.biped_count = 2  # Start with 2 bipeds
        self.houses_built = 0
        
        # Unlocked features
        self.unlocked_views = {GAME_STATE_PLANET: True}
        self.unlocked_buildings = {BUILDING_HOUSE: True}
        self.unlocked_crafting = set()
        
        # Current location
        self.current_planet = "Earth"
        self.current_system = "Sol"
        self.current_galaxy = "Milky Way"
        
        # Discovered locations
        self.discovered_planets = {"Earth": PlanetData("Earth", 42, {}, [], [], {}, True)}
        self.discovered_systems = {"Sol": True}
        self.discovered_galaxies = {"Milky Way": True}
        
        # Game settings
        self.save_file = "game_save.json"
        
    def initialize(self):
        """Initialize the game state"""
        self.load_game()
        
    def add_science_points(self, points: int):
        """Add science points and check for unlocks"""
        self.science_points += points
        
        # Check for view unlocks
        if self.science_points >= UNLOCK_SYSTEM_VIEW and GAME_STATE_SYSTEM not in self.unlocked_views:
            self.unlocked_views[GAME_STATE_SYSTEM] = True
            
        if self.science_points >= UNLOCK_GALAXY_VIEW and GAME_STATE_GALAXY not in self.unlocked_views:
            self.unlocked_views[GAME_STATE_GALAXY] = True
            
        if self.science_points >= UNLOCK_UNIVERSE_VIEW and GAME_STATE_UNIVERSE not in self.unlocked_views:
            self.unlocked_views[GAME_STATE_UNIVERSE] = True
            
    def add_bipeds(self, count: int):
        """Add bipeds to the population"""
        self.biped_count += count
        
    def build_house(self):
        """Build a house and get 4 more bipeds"""
        if self.resources[RESOURCE_WOOD].amount >= 20 and self.resources[RESOURCE_STONE].amount >= 10:
            self.resources[RESOURCE_WOOD].remove(20)
            self.resources[RESOURCE_STONE].remove(10)
            self.houses_built += 1
            self.add_bipeds(4)
            return True
        return False
        
    def can_afford(self, costs: Dict[str, int]) -> bool:
        """Check if we can afford the given costs"""
        for resource, amount in costs.items():
            if resource in self.resources:
                if self.resources[resource].amount < amount:
                    return False
            else:
                return False
        return True
        
    def spend_resources(self, costs: Dict[str, int]) -> bool:
        """Spend resources, return True if successful"""
        if not self.can_afford(costs):
            return False
            
        for resource, amount in costs.items():
            self.resources[resource].remove(amount)
        return True
        
    def get_resource_amount(self, resource_name: str) -> int:
        """Get the amount of a specific resource"""
        if resource_name in self.resources:
            return self.resources[resource_name].amount
        return 0
        
    def is_view_unlocked(self, view_name: str) -> bool:
        """Check if a view is unlocked"""
        return self.unlocked_views.get(view_name, False)
        
    def save_game(self):
        """Save the game state to file"""
        save_data = {
            'resources': {name: res.amount for name, res in self.resources.items()},
            'science_points': self.science_points,
            'biped_count': self.biped_count,
            'houses_built': self.houses_built,
            'unlocked_views': self.unlocked_views,
            'unlocked_buildings': self.unlocked_buildings,
            'current_planet': self.current_planet,
            'current_system': self.current_system,
            'current_galaxy': self.current_galaxy,
            'discovered_planets': {name: asdict(data) for name, data in self.discovered_planets.items()},
            'discovered_systems': self.discovered_systems,
            'discovered_galaxies': self.discovered_galaxies
        }
        
        try:
            with open(self.save_file, 'w') as f:
                json.dump(save_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save game: {e}")
            
    def load_game(self):
        """Load the game state from file"""
        if not os.path.exists(self.save_file):
            return
            
        try:
            with open(self.save_file, 'r') as f:
                save_data = json.load(f)
                
            # Load resources
            for name, amount in save_data.get('resources', {}).items():
                if name in self.resources:
                    self.resources[name].amount = amount
                    
            # Load other data
            self.science_points = save_data.get('science_points', 0)
            self.biped_count = save_data.get('biped_count', 2)
            self.houses_built = save_data.get('houses_built', 0)
            self.unlocked_views = save_data.get('unlocked_views', {GAME_STATE_PLANET: True})
            self.unlocked_buildings = save_data.get('unlocked_buildings', {BUILDING_HOUSE: True})
            self.current_planet = save_data.get('current_planet', 'Earth')
            self.current_system = save_data.get('current_system', 'Sol')
            self.current_galaxy = save_data.get('current_galaxy', 'Milky Way')
            
            # Load discovered locations
            self.discovered_planets = {}
            for name, data in save_data.get('discovered_planets', {}).items():
                self.discovered_planets[name] = PlanetData(**data)
                
            self.discovered_systems = save_data.get('discovered_systems', {'Sol': True})
            self.discovered_galaxies = save_data.get('discovered_galaxies', {'Milky Way': True})
            
        except Exception as e:
            print(f"Failed to load game: {e}")
            
    def discover_planet(self, planet_name: str, seed: int, biome_data: Dict):
        """Discover a new planet"""
        if planet_name not in self.discovered_planets:
            self.discovered_planets[planet_name] = PlanetData(
                name=planet_name,
                seed=seed,
                biome_data=biome_data,
                buildings=[],
                entities=[],
                resources={},
                discovered=True
            )
            
    def discover_system(self, system_name: str):
        """Discover a new solar system"""
        self.discovered_systems[system_name] = True
        
    def discover_galaxy(self, galaxy_name: str):
        """Discover a new galaxy"""
        self.discovered_galaxies[galaxy_name] = True 