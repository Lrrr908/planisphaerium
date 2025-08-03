# arcade_scene_manager.py - Arcade 3.3.2 Scene Management
import arcade
from typing import Dict, Optional, Any

class ArcadeSceneManager:
    """Manages scene transitions and state for Arcade 3.3.2"""
    
    def __init__(self, game_window):
        self.game_window = game_window
        self.scenes: Dict[str, arcade.View] = {}
        self.current_scene: Optional[arcade.View] = None
        self.scene_history: list = []
        
    def add_scene(self, name: str, scene: arcade.View):
        """Add a scene to the manager"""
        self.scenes[name] = scene
        print(f"[ArcadeSceneManager] Added scene: {name}")
        
    def switch_to_scene(self, scene_name: str):
        """Switch to a specific scene"""
        if scene_name not in self.scenes:
            print(f"[ArcadeSceneManager] Error: Scene '{scene_name}' not found")
            return False
            
        # Store current scene in history
        if self.current_scene:
            self.scene_history.append(self.current_scene)
            
        # Switch to new scene
        self.current_scene = self.scenes[scene_name]
        self.game_window.show_view(self.current_scene)
        
        print(f"[ArcadeSceneManager] Switched to scene: {scene_name}")
        return True
        
    def go_back(self):
        """Go back to the previous scene"""
        if self.scene_history:
            previous_scene = self.scene_history.pop()
            self.current_scene = previous_scene
            self.game_window.show_view(self.current_scene)
            print(f"[ArcadeSceneManager] Went back to previous scene")
            return True
        return False
        
    def get_current_scene(self) -> Optional[arcade.View]:
        """Get the current scene"""
        return self.current_scene
        
    def get_scene(self, name: str) -> Optional[arcade.View]:
        """Get a specific scene by name"""
        return self.scenes.get(name)
        
    def has_scene(self, name: str) -> bool:
        """Check if a scene exists"""
        return name in self.scenes
        
    def get_scene_names(self) -> list:
        """Get list of all scene names"""
        return list(self.scenes.keys())
        
    def clear_history(self):
        """Clear scene history"""
        self.scene_history.clear()
        
    def get_history_count(self) -> int:
        """Get number of scenes in history"""
        return len(self.scene_history) 