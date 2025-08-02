# planet_storage.py - Centralized planet data management
import json
import os
import time
from typing import Dict, Optional, List, Any
from planet_meta import PlanetMeta

class PlanetStorage:
    """Manages persistent storage of all planet data"""
    
    def __init__(self, save_directory: str = "saves"):
        self.save_directory = save_directory
        self.planets_file = os.path.join(save_directory, "planets.json")
        self.ensure_save_directory()
        
    def ensure_save_directory(self):
        """Create save directory if it doesn't exist"""
        os.makedirs(self.save_directory, exist_ok=True)
        
    def save_planet(self, planet_id: str, planet_meta: PlanetMeta):
        """Save single planet to storage"""
        all_planets = self.load_all_planets()
        
        # Update last visited time
        planet_meta.last_visited = time.time()
        
        # Update quick stats for UI
        if planet_meta.state:
            planet_meta.quick_stats = self._extract_quick_stats(planet_meta.state)
            
        all_planets[planet_id] = planet_meta
        self._save_all_planets(all_planets)
        
    def load_planet(self, planet_id: str) -> Optional[PlanetMeta]:
        """Load single planet from storage"""
        all_planets = self.load_all_planets()
        return all_planets.get(planet_id)
        
    def load_all_planets(self) -> Dict[str, PlanetMeta]:
        """Load all planets from storage"""
        if not os.path.exists(self.planets_file):
            return {}
            
        try:
            with open(self.planets_file, 'r') as f:
                data = json.load(f)
                
            planets = {}
            for planet_id, planet_data in data.items():
                planets[planet_id] = PlanetMeta.from_save_dict(planet_data)
                
            return planets
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading planets: {e}")
            return {}
            
    def _save_all_planets(self, planets: Dict[str, PlanetMeta]):
        """Save all planets to storage"""
        data = {}
        for planet_id, planet_meta in planets.items():
            data[planet_id] = planet_meta.to_save_dict()
            
        with open(self.planets_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _extract_quick_stats(self, state: dict) -> dict:
        """Extract summary stats for UI display"""
        entities = state.get("entities", {})
        structures = state.get("structures", {})
        
        return {
            "animal_count": len(entities.get("animals", [])),
            "building_count": len(structures.get("subtile_buildings", {}).get("buildings", {})),
            "house_count": len(structures.get("houses", [])),
            "species_count": len(entities.get("species_data", {})),
            "has_been_visited": True
        }
        
    def get_planet_list(self) -> List[Dict[str, Any]]:
        """Get list of all planets with summary info"""
        planets = self.load_all_planets()
        
        planet_list = []
        for planet_id, meta in planets.items():
            planet_list.append({
                "id": planet_id,
                "seed": meta.seed,
                "size": meta.tiles,
                "type": meta.planet_type,
                "last_visited": meta.last_visited,
                "playtime": meta.total_playtime,
                "stats": meta.quick_stats or {}
            })
            
        return planet_list