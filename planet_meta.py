# planet_meta.py
from dataclasses import dataclass, field
from typing import Tuple, Any, Dict
import time

@dataclass
class PlanetMeta:
    """
    Seed + size + persistent game-state bundle for a single planet or moon.
    state == None  → first visit (needs procedural generation)
    state == dict  → subsequent visits (restore from save)
    """
    seed: int                               # RNG seed chosen in SystemScene
    tiles: Tuple[int, int]                  # (width, height) in map tiles
    state: Dict[str, Any] | None = None
    
    # NEW: Metadata about the planet
    planet_type: str = "terrestrial"        # terrestrial, desert, arctic, etc.
    generation_version: int = 1             # Track world generation changes
    last_visited: float = 0.0               # Timestamp of last visit
    total_playtime: float = 0.0             # Time spent on this planet
    
    # NEW: Quick access stats (for UI, don't need to parse full state)
    quick_stats: Dict[str, Any] = field(default_factory=dict)  # Population, buildings, resources
    
    def to_save_dict(self) -> Dict[str, Any]:
        """Convert to saveable format"""
        return {
            "seed": self.seed,
            "tiles": self.tiles,
            "planet_type": self.planet_type,
            "generation_version": self.generation_version,
            "last_visited": self.last_visited,
            "total_playtime": self.total_playtime,
            "quick_stats": self.quick_stats,
            "state": self.state
        }
    
    @classmethod
    def from_save_dict(cls, data: Dict[str, Any]) -> 'PlanetMeta':
        """Load from save data"""
        return cls(
            seed=data["seed"],
            tiles=tuple(data["tiles"]),
            state=data.get("state"),
            planet_type=data.get("planet_type", "terrestrial"),
            generation_version=data.get("generation_version", 1),
            last_visited=data.get("last_visited", 0.0),
            total_playtime=data.get("total_playtime", 0.0),
            quick_stats=data.get("quick_stats", {})
        )