##########################################################
# planet_scene.py
# Main planet scene class that orchestrates all the modular components
##########################################################

import random
import time
from scene_manager import Scene
from planet_meta import PlanetMeta

# Import all the modular components
from planet_world_generator import PlanetWorldGenerator
from planet_state_manager import PlanetStateManager
from planet_entity_manager import PlanetEntityManager
from planet_movement_system import PlanetMovementSystem
from planet_event_handler import PlanetEventHandler
from planet_renderer import PlanetRenderer
from planet_utilities import PlanetUtilities

# Import managers that are used by the modules
from unit_manager import UnitManager
from animals import AnimalManager

##########################################################
# Constants & Configuration
##########################################################

SIZES = [(60, 60), (100, 100), (200, 200), (300, 300)]
SIZE_WEIGHTS = [0.08, 0.20, 0.15, 0.01]

##########################################################
# Main PlanetScene Class
##########################################################

class PlanetScene(Scene):
    """
    Main planet scene class that orchestrates all modular components.
    This class acts as the central coordinator for all planet systems.
    """
    
    def __init__(self, assets_dir: str, meta: PlanetMeta, surface=None):
        super().__init__()
        
        # Core scene properties
        self.assets_dir = assets_dir
        self.meta = meta
        self.planet_storage = None  # Will be set by main.py or system_scene
        self.surface = surface      # For loading screen display
        
        # Initialize random seed for deterministic generation
        random.seed(self.meta.seed)
        
        # Scene configuration
        self.zoom_scale = 1.0
        self.simulation_mode = "realtime"  # "paused" or "realtime"
        self.use_layered_terrain = True    # Enable layered terrain by default
        self.mining_mode = False           # Mining mode for digging
        
        # Initialize all modular components
        self._initialize_modules()
        
        # Initialize managers that modules will use
        self._initialize_managers()
        
        # Generate or load world state with loading screen
        self._initialize_world_state()
        
        # Set up auto-save tracking
        self._last_auto_save = time.time()

    def _initialize_modules(self):
        """Initialize all modular components"""
        self.world_generator = PlanetWorldGenerator(self)
        self.state_manager = PlanetStateManager(self)
        self.entity_manager = PlanetEntityManager(self)
        self.movement_system = PlanetMovementSystem(self)
        self.event_handler = PlanetEventHandler(self)
        self.renderer = PlanetRenderer(self)
        self.utilities = PlanetUtilities(self)

    def _initialize_managers(self):
        """Initialize entity managers"""
        self.unit_manager = UnitManager(self)
        self.animal_manager = AnimalManager(self)

    def _initialize_world_state(self):
        """Initialize world state - either generate new or load existing with loading screen"""
        if self.meta.state is None:
            print(f"[PlanetScene] Generating new world for seed {self.meta.seed}")
            self._generate_new_world()
            self.meta.state = self.state_manager.serialize_state()
        else:
            print(f"[PlanetScene] Loading existing world for seed {self.meta.seed}")
            
            # Use loading screen for loading existing worlds
            use_loading_screen = self.surface is not None
            self.state_manager.load_state(self.meta.state, self.surface, use_loading_screen)
            
            # Simulate time away if in realtime mode
            if self.simulation_mode == "realtime":
                self.movement_system.simulate_time_away_movement()

    def _generate_new_world(self):
        """Generate a new world using the world generator module with loading screen"""
        # Use loading screen for new world generation
        use_loading_screen = self.surface is not None
        self.world_generator._generate_new_world(self.surface, use_loading_screen)
        
        # Spawn initial entities using entity manager
        if hasattr(self, 'near_centre'):
            self.entity_manager.spawn_initial_bipeds(self.near_centre)
            self.entity_manager.spawn_animals(self.near_centre)
        
        # Check for emergency spawning if needed
        self.entity_manager.check_entity_emergency_spawning()

    ##########################################################
    # Core Scene Interface Methods
    ##########################################################

    def handle_events(self, events):
        """Handle input events using the event handler module"""
        self.event_handler.handle_events(events)

    def update(self, dt):
        """Update all game systems"""
        # Handle camera dragging
        if getattr(self, 'dragging', False):
            import pygame
            mx, my = pygame.mouse.get_pos()
            if hasattr(self, 'last_mouse_pos'):
                self.map.update_camera(mx - self.last_mouse_pos[0], my - self.last_mouse_pos[1])
                self.last_mouse_pos = (mx, my)

        # Update wave animation time
        self.wave_time = getattr(self, 'wave_time', 0.0) + dt * 0.001
        
        # Update water animation
        self.renderer.update_water_animation(dt)
        
        # Update all entities using entity manager
        self.entity_manager.update_all_entities(dt)
        
        # Validate movement states periodically
        if hasattr(self, '_last_validation'):
            if time.time() - self._last_validation > 10.0:  # Every 10 seconds
                self.movement_system.validate_movement_state()
                self._last_validation = time.time()
        else:
            self._last_validation = time.time()
        
        # Cleanup dead entities periodically
        if hasattr(self, '_last_cleanup'):
            if time.time() - self._last_cleanup > 30.0:  # Every 30 seconds
                self.utilities.cleanup_dead_entities()
                self._last_cleanup = time.time()
        else:
            self._last_cleanup = time.time()

    def render(self, surface):
        """Render the scene using the renderer module"""
        self.renderer.render(surface)

    ##########################################################
    # Utility Methods (delegated to modules)
    ##########################################################

    def find_path(self, sx, sy, gx, gy):
        """Find path between two points using movement system"""
        return self.movement_system.find_path(sx, sy, gx, gy)

    def is_water_tile(self, gx: int, gy: int) -> bool:
        """Check if tile is water using utilities"""
        return self.utilities.is_water_tile(gx, gy)

    def find_valid_land_tile(self, tile_list, max_attempts: int = 500):
        """Find valid land tile using entity manager"""
        return self.entity_manager.find_valid_land_tile(tile_list, max_attempts)

    def send_biped_to_collect(self, drop_obj):
        """Send biped to collect drop using entity manager"""
        self.entity_manager.send_biped_to_collect(drop_obj)

    def pick_up_drop(self, drop_obj):
        """Pick up drop using entity manager"""
        self.entity_manager.pick_up_drop(drop_obj)

    def _propagate_zoom(self):
        """Propagate zoom changes using utilities"""
        self.utilities.propagate_zoom()

    ##########################################################
    # Persistence and State Management
    ##########################################################

    def save_before_exit(self):
        """Save state before exiting using state manager"""
        self.state_manager.save_before_exit()

    def on_scene_exit(self):
        """Called when leaving this scene"""
        self.save_before_exit()

    def _serialize_state(self):
        """Serialize current state using state manager"""
        return self.state_manager.serialize_state()

    def _load_state(self, state):
        """Load state using state manager"""
        self.state_manager.load_state(state, self.surface, True)

    ##########################################################
    # Auto-save and Tracking Methods
    ##########################################################

    def _auto_save_trigger(self, reason="unknown"):
        """Trigger auto-save using entity manager"""
        self.entity_manager.auto_save_trigger(reason)

    def on_biped_moved(self, biped):
        """Called when biped moves using entity manager"""
        self.entity_manager.on_biped_moved(biped)

    def on_biped_command(self, biped, command_type):
        """Called when biped receives command using entity manager"""
        self.entity_manager.on_biped_command(biped, command_type)

    def _get_units_by_mission(self):
        """Get units by mission using entity manager"""
        return self.entity_manager.get_units_by_mission()

    ##########################################################
    # Debug and Diagnostics
    ##########################################################

    def get_debug_info(self):
        """Get comprehensive debug information"""
        debug_info = {
            "scene": {
                "simulation_mode": self.simulation_mode,
                "use_layered_terrain": self.use_layered_terrain,
                "mining_mode": getattr(self, 'mining_mode', False),
                "zoom_scale": self.zoom_scale,
            },
            "world": self.utilities.get_debug_info(),
            "movement": self.movement_system.get_movement_debug_info(),
            "rendering": self.renderer.get_render_stats(),
            "entities": {
                "bipeds": len(self.unit_manager.units),
                "animals": len(self.animal_manager.animals),
                "drops": len(getattr(self, 'drops', [])),
                "trees": len(getattr(self, 'trees', [])),
                "houses": len(getattr(self, 'houses', [])),
            }
        }
        
        return debug_info

    def validate_scene_state(self):
        """Validate that the scene state is consistent"""
        issues = []
        
        # Validate world state
        world_issues = self.utilities.validate_world_state()
        issues.extend(world_issues)
        
        # Validate module initialization
        required_modules = [
            'world_generator', 'state_manager', 'entity_manager',
            'movement_system', 'event_handler', 'renderer', 'utilities'
        ]
        
        for module_name in required_modules:
            if not hasattr(self, module_name):
                issues.append(f"Missing module: {module_name}")
        
        # Validate managers
        required_managers = ['unit_manager', 'animal_manager']
        for manager_name in required_managers:
            if not hasattr(self, manager_name):
                issues.append(f"Missing manager: {manager_name}")
        
        return issues

    def optimize_performance(self):
        """Optimize scene performance"""
        print("[PlanetScene] Optimizing performance...")
        
        # Optimize blocked tiles calculation
        self.utilities.optimize_blocked_tiles()
        
        # Clean up dead entities
        self.utilities.cleanup_dead_entities()
        
        # Validate and fix any movement issues
        self.movement_system.validate_movement_state()
        
        print("[PlanetScene] Performance optimization complete")

    ##########################################################
    # Module Access Methods (for backward compatibility)
    ##########################################################

    def get_world_generator(self):
        """Get world generator module"""
        return self.world_generator

    def get_state_manager(self):
        """Get state manager module"""
        return self.state_manager

    def get_entity_manager(self):
        """Get entity manager module"""
        return self.entity_manager

    def get_movement_system(self):
        """Get movement system module"""
        return self.movement_system

    def get_event_handler(self):
        """Get event handler module"""
        return self.event_handler

    def get_renderer(self):
        """Get renderer module"""
        return self.renderer

    def get_utilities(self):
        """Get utilities module"""
        return self.utilities

    ##########################################################
    # Legacy Method Support (for compatibility)
    ##########################################################

    def _calculate_blocked_tiles_layered(self):
        """Legacy method - now delegated to world generator"""
        if hasattr(self.world_generator, '_calculate_blocked_tiles_layered'):
            return self.world_generator._calculate_blocked_tiles_layered()
        else:
            return self.utilities.optimize_blocked_tiles()

    def _simulate_movement_progress(self, biped, time_away_seconds):
        """Legacy method - now delegated to entity manager"""
        return self.entity_manager.simulate_movement_progress(biped, time_away_seconds)

    def _handle_path_completion(self, biped):
        """Legacy method - now delegated to entity manager"""
        return self.entity_manager.handle_path_completion(biped)

    def _resume_biped_movement(self, biped):
        """Legacy method - now delegated to state manager"""
        return self.state_manager._resume_biped_movement(biped)

    ##########################################################
    # Module Configuration Methods
    ##########################################################

    def set_simulation_mode(self, mode):
        """Set simulation mode (paused or realtime)"""
        if mode in ["paused", "realtime"]:
            self.simulation_mode = mode
            print(f"[PlanetScene] Simulation mode set to {mode.upper()}")
        else:
            print(f"[PlanetScene] Invalid simulation mode: {mode}")

    def toggle_terrain_system(self):
        """Toggle terrain system (for testing)"""
        self.use_layered_terrain = not self.use_layered_terrain
        print(f"[PlanetScene] Layered terrain: {'ON' if self.use_layered_terrain else 'OFF'}")
        print("[PlanetScene] Note: Regenerate world (Ctrl+R) to apply terrain changes")

    def toggle_mining_mode(self):
        """Toggle mining mode"""
        if self.use_layered_terrain:
            self.mining_mode = not self.mining_mode
            print(f"[PlanetScene] Mining mode: {'ON' if self.mining_mode else 'OFF'}")
            if self.mining_mode:
                print("[PlanetScene] Left-click on terrain to dig/mine")
        else:
            print("[PlanetScene] Mining mode requires layered terrain")

    def regenerate_world(self):
        """Regenerate the world (for testing)"""
        print("[PlanetScene] Regenerating world...")
        self.meta.state = None  # Clear saved state
        self._generate_new_world()
        self.meta.state = self.state_manager.serialize_state()
        print("[PlanetScene] World regeneration complete")

    ##########################################################
    # Performance Monitoring
    ##########################################################

    def get_performance_stats(self):
        """Get performance statistics"""
        stats = {
            "frame_time": getattr(self, '_last_frame_time', 0),
            "update_time": getattr(self, '_last_update_time', 0),
            "render_time": getattr(self, '_last_render_time', 0),
            "entity_count": len(self.unit_manager.units) + len(self.animal_manager.animals),
            "memory_usage": self._estimate_memory_usage(),
        }
        
        return stats

    def _estimate_memory_usage(self):
        """Estimate memory usage of major collections"""
        usage = {
            "iso_objects": len(getattr(self, 'iso_objects', [])),
            "blocked_tiles": len(getattr(self, 'blocked_tiles', set())),
            "terrain_stacks": len(getattr(self, 'terrain', type('obj', (object,), {'terrain_stacks': {}})).terrain_stacks),
            "units": len(self.unit_manager.units),
            "animals": len(self.animal_manager.animals),
            "drops": len(getattr(self, 'drops', [])),
        }
        
        return usage

    ##########################################################
    # Error Handling and Recovery
    ##########################################################

    def handle_critical_error(self, error, context="unknown"):
        """Handle critical errors gracefully"""
        print(f"[PlanetScene] Critical error in {context}: {error}")
        
        try:
            # Attempt to save current state
            self.save_before_exit()
            print("[PlanetScene] Emergency save completed")
        except Exception as save_error:
            print(f"[PlanetScene] Emergency save failed: {save_error}")
        
        # Attempt to recover by reinitializing modules
        try:
            self._initialize_modules()
            print("[PlanetScene] Module reinitialization completed")
        except Exception as init_error:
            print(f"[PlanetScene] Module reinitialization failed: {init_error}")

    def recover_from_corruption(self):
        """Attempt to recover from data corruption"""
        print("[PlanetScene] Attempting corruption recovery...")
        
        # Validate current state
        issues = self.validate_scene_state()
        if not issues:
            print("[PlanetScene] No corruption detected")
            return True
        
        print(f"[PlanetScene] Found {len(issues)} issues: {issues[:3]}...")
        
        try:
            # Regenerate world if corruption is severe
            if len(issues) > 5:
                print("[PlanetScene] Severe corruption detected, regenerating world")
                self.regenerate_world()
                return True
            
            # Attempt targeted fixes
            self.optimize_performance()
            
            # Revalidate
            remaining_issues = self.validate_scene_state()
            if len(remaining_issues) < len(issues):
                print(f"[PlanetScene] Corruption recovery successful, {len(remaining_issues)} issues remain")
                return True
            else:
                print("[PlanetScene] Corruption recovery failed")
                return False
                
        except Exception as e:
            print(f"[PlanetScene] Corruption recovery error: {e}")
            return False

    ##########################################################
    # Loading Screen Integration
    ##########################################################

    def set_surface(self, surface):
        """Set the surface for loading screen display"""
        self.surface = surface
    
    def has_loading_screen_support(self):
        """Check if loading screen is available"""
        return self.surface is not None
        
    def reload_with_loading_screen(self, surface):
        """Reload the current world with loading screen"""
        self.surface = surface
        if self.meta.state:
            print("[PlanetScene] Reloading world with loading screen")
            self.state_manager.load_state(self.meta.state, surface, True)
        else:
            print("[PlanetScene] Regenerating world with loading screen")
            self._generate_new_world()
            self.meta.state = self.state_manager.serialize_state()