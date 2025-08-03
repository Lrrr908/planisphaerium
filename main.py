# main.py - Arcade Universe Simulation
import os
import random
import arcade
import time
import sys

def show_startup_loading():
    """Show beautiful startup loading screen (adapted for Arcade)"""
    try:
        # Try to use existing loading screen with pygame for compatibility
        import pygame
        from loading_screen import LoadingManager
        
        # Initialize pygame for loading screen
        pygame.init()
        surface = pygame.display.set_mode((1920, 1024))
        pygame.display.set_caption("Universe Simulation - Initializing")
        
        loading_manager = LoadingManager(surface)
        
        # Define startup steps with actual work
        def init_universe_engine(progress_callback=None):
            """Initialize core systems"""
            if progress_callback:
                progress_callback(0, "Initializing universe engine", 0.2, "Starting quantum processors")
            time.sleep(0.6)
            
            if progress_callback:
                progress_callback(0, "Initializing universe engine", 0.7, "Loading physics engine")
            time.sleep(0.5)
            
            if progress_callback:
                progress_callback(0, "Initializing universe engine", 1.0, "Engine online")
            time.sleep(0.3)
        
        def load_stellar_cartography(progress_callback=None):
            """Load game systems"""
            if progress_callback:
                progress_callback(1, "Loading stellar cartography", 0.3, "Scanning star charts")
            time.sleep(0.7)
            
            # Import heavy modules during loading screen
            global ArcadePlanetScene, PlanetMeta, PlanetStorage
            from arcade_planet_scene import ArcadePlanetScene
            from planet_meta import PlanetMeta
            from planet_storage import PlanetStorage
            
            if progress_callback:
                progress_callback(1, "Loading stellar cartography", 0.8, "Mapping hyperspace routes")
            time.sleep(0.4)
            
            if progress_callback:
                progress_callback(1, "Loading stellar cartography", 1.0, "Navigation systems ready")
            time.sleep(0.2)
        
        def prepare_exploration_systems(progress_callback=None):
            """Prepare exploration systems"""
            if progress_callback:
                progress_callback(2, "Preparing exploration systems", 0.4, "Initializing scene manager")
            time.sleep(0.6)
            
            if progress_callback:
                progress_callback(2, "Preparing exploration systems", 0.8, "Calibrating generators")
            time.sleep(0.4)
            
            if progress_callback:
                progress_callback(2, "Preparing exploration systems", 1.0, "Systems operational")
            time.sleep(0.3)
        
        def calibrate_sensors(progress_callback=None):
            """Final calibration"""
            if progress_callback:
                progress_callback(3, "Calibrating sensors", 0.5, "Running diagnostics")
            time.sleep(0.8)
            
            if progress_callback:
                progress_callback(3, "Calibrating sensors", 1.0, "All systems nominal")
            time.sleep(0.3)
        
        def ready_for_launch(progress_callback=None):
            """Ready for launch"""
            if progress_callback:
                progress_callback(4, "Ready for interstellar travel", 0.6, "Warming up warp drive")
            time.sleep(0.5)
            
            if progress_callback:
                progress_callback(4, "Ready for interstellar travel", 1.0, "Launch sequence initiated")
            time.sleep(0.5)
        
        startup_steps = [
            ("Initializing universe engine", init_universe_engine, None),
            ("Loading stellar cartography", load_stellar_cartography, None),
            ("Preparing exploration systems", prepare_exploration_systems, None),
            ("Calibrating sensors", calibrate_sensors, None),
            ("Ready for interstellar travel", ready_for_launch, None),
        ]
        
        def execute_startup(*args, progress_callback=None):
            """Execute startup sequence"""
            return True
        
        print("[Startup] Displaying startup loading screen...")
        success = loading_manager.load_with_progress(
            execute_startup,
            startup_steps,
            "Universe Simulation"
        )
        
        # Clean up pygame after loading screen
        pygame.quit()
        
        if success:
            print("[Startup] ✅ Startup loading completed")
            return True
        else:
            print("[Startup] ❌ Startup loading failed")
            return False
            
    except ImportError:
        print("[Startup] Loading screen not available, starting directly...")
        # Still need to import modules
        global ArcadePlanetScene, PlanetMeta, PlanetStorage
        from arcade_planet_scene import ArcadePlanetScene
        from planet_meta import PlanetMeta
        from planet_storage import PlanetStorage
        return True
    except Exception as e:
        print(f"[Startup] Loading screen error: {e}")
        # Fallback imports
        global ArcadePlanetScene, PlanetMeta, PlanetStorage
        from arcade_planet_scene import ArcadePlanetScene
        from planet_meta import PlanetMeta
        from planet_storage import PlanetStorage
        return True


class ArcadeSceneManager(arcade.Window):
    """Arcade-based scene manager that replaces the pygame SceneManager"""
    
    def __init__(self, width=1024, height=768, title="Universe Simulation"):
        super().__init__(width, height, title)
        
        # Scene management
        self.scenes = {}
        self.current_scene_name = None
        self.planet_storage = None
        self.hud = None
        
        # Performance tracking
        self.fps_target = 60
        self.performance_stats = {
            "frame_time": 0,
            "update_time": 0,
            "render_time": 0
        }
        
        print(f"[ArcadeSceneManager] Initialized {width}x{height} window")

    def add_scene(self, name, scene):
        """Add a scene to the manager"""
        self.scenes[name] = scene
        scene.scene_manager = self  # Give scene reference to manager
        print(f"[ArcadeSceneManager] Added scene: {name}")

    def switch_to_scene(self, scene_name):
        """Switch to a different scene"""
        if scene_name in self.scenes:
            # Save current scene state if it exists
            if self.current_view and hasattr(self.current_view, 'save_before_exit'):
                self.current_view.save_before_exit()
            
            # Switch to new scene
            new_scene = self.scenes[scene_name]
            self.show_view(new_scene)
            self.current_scene_name = scene_name
            
            print(f"[ArcadeSceneManager] Switched to scene: {scene_name}")
            return True
        else:
            print(f"[ArcadeSceneManager] Scene not found: {scene_name}")
            return False

    def get_current_scene(self):
        """Get the current scene"""
        return self.current_view

    def on_key_press(self, key, modifiers):
        """Handle global key presses"""
        # Scene switching hotkeys
        if key == arcade.key.F2:
            self.switch_to_scene("Planet")
        elif key == arcade.key.F3:
            self.switch_to_scene("System")
        elif key == arcade.key.F4:
            self.switch_to_scene("Galaxy")
        elif key == arcade.key.F1:
            self._show_help()
        elif key == arcade.key.F11:
            self.set_fullscreen(not self.fullscreen)
        elif key == arcade.key.F12:
            self._take_screenshot()
        
        # Forward to current scene
        if self.current_view and hasattr(self.current_view, 'on_key_press'):
            self.current_view.on_key_press(key, modifiers)

    def _show_help(self):
        """Show help information"""
        help_text = """
        ARCADE UNIVERSE SIMULATION - CONTROLS
        
        Scene Navigation:
        - F2: Planet Scene
        - F3: System Scene  
        - F4: Galaxy Scene
        
        Planet Scene:
        - Left Click + Drag: Move camera
        - Right Click: Move selected biped
        - Mouse Wheel: Zoom
        - H: Build house
        - T: Toggle simulation mode
        - Ctrl+R: Regenerate world
        - Space: Pause
        - I: Show debug info
        - C: Center camera
        
        System:
        - F1: Show this help
        - F11: Toggle fullscreen
        - F12: Take screenshot
        - Escape: Exit game
        """
        print(help_text)

    def _take_screenshot(self):
        """Take a screenshot"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"universe_screenshot_{timestamp}.png"
        
        try:
            image = arcade.get_image()
            image.save(filename)
            print(f"[ArcadeSceneManager] Screenshot saved: {filename}")
        except Exception as e:
            print(f"[ArcadeSceneManager] Failed to save screenshot: {e}")

    def on_close(self):
        """Handle window close"""
        print("[ArcadeSceneManager] Closing universe simulation...")
        
        # Save all scenes before closing
        for scene_name, scene in self.scenes.items():
            if hasattr(scene, 'save_before_exit'):
                print(f"[ArcadeSceneManager] Saving {scene_name} scene...")
                scene.save_before_exit()
        
        super().on_close()


class ArcadeSystemScene(arcade.View):
    """System scene adapted for Arcade (placeholder)"""
    
    def __init__(self, scene_manager, assets_dir, planet_storage):
        super().__init__()
        self.scene_manager = scene_manager
        self.assets_dir = assets_dir
        self.planet_storage = planet_storage
        self.hud = None
        
        print("[ArcadeSystemScene] Initialized")

    def on_draw(self):
        self.clear()
        
        # Draw a simple system view
        arcade.draw_circle_filled(self.window.width // 2, self.window.height // 2, 50, arcade.color.YELLOW)
        arcade.draw_text("SYSTEM SCENE", 
                        self.window.width // 2, self.window.height // 2 + 100,
                        arcade.color.WHITE, 24, anchor_x="center")
        arcade.draw_text("Press F2 for Planet Scene", 
                        self.window.width // 2, self.window.height // 2 - 100,
                        arcade.color.WHITE, 16, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE and self.scene_manager:
            self.scene_manager.switch_to_scene("Planet")

    def save_before_exit(self):
        """Save scene state"""
        print("[ArcadeSystemScene] Saving system scene state")


class ArcadeGalaxyScene(arcade.View):
    """Galaxy scene adapted for Arcade (placeholder)"""
    
    def __init__(self, scene_manager, assets_dir):
        super().__init__()
        self.scene_manager = scene_manager
        self.assets_dir = assets_dir
        self.hud = None
        
        print("[ArcadeGalaxyScene] Initialized")

    def on_draw(self):
        self.clear()
        
        # Draw a simple galaxy view
        for i in range(100):
            x = random.randint(0, self.window.width)
            y = random.randint(0, self.window.height)
            arcade.draw_circle_filled(x, y, 2, arcade.color.WHITE)
        
        arcade.draw_text("GALAXY SCENE", 
                        self.window.width // 2, self.window.height // 2 + 100,
                        arcade.color.WHITE, 24, anchor_x="center")
        arcade.draw_text("Press F2 for Planet Scene", 
                        self.window.width // 2, self.window.height // 2 - 100,
                        arcade.color.WHITE, 16, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE and self.scene_manager:
            self.scene_manager.switch_to_scene("Planet")

    def save_before_exit(self):
        """Save scene state"""
        print("[ArcadeGalaxyScene] Saving galaxy scene state")


class ArcadeUIHud:
    """Simple HUD system for Arcade (adapted from your UIHud)"""
    
    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.visible = True
        
    def render(self, view):
        """Render HUD elements"""
        if not self.visible:
            return
        
        # Draw simple HUD
        window = view.window
        
        # Scene indicator
        scene_name = getattr(self.scene_manager, 'current_scene_name', 'Unknown')
        arcade.draw_text(f"Scene: {scene_name}", 
                        10, window.height - 30,
                        arcade.color.WHITE, 14)
        
        # Instructions
        arcade.draw_text("F2/F3/F4: Switch Scenes | F1: Help", 
                        10, window.height - 50,
                        arcade.color.LIGHT_GRAY, 12)
        
        # Performance info
        fps = f"FPS: {arcade.get_fps():.1f}"
        arcade.draw_text(fps, 
                        window.width - 100, window.height - 30,
                        arcade.color.WHITE, 14)

    def handle_events(self, events, current_scene):
        """Handle HUD events (placeholder)"""
        pass


def main() -> None:
    # Show startup loading screen first
    startup_success = show_startup_loading()
    
    if not startup_success:
        print("Startup failed, exiting...")
        return

    print("[Main] Creating Arcade scene manager...")

    # --------------------------------------------------
    # 1) Create Arcade window/scene manager
    # --------------------------------------------------
    scene_manager = ArcadeSceneManager(width=1024, height=768, title="Universe Simulation")

    # Path to your assets
    assets_dir = os.path.join(os.path.dirname(__file__), "assets", "images")

    # --------------------------------------------------
    # 1.5) Initialize centralized planet storage
    # --------------------------------------------------
    planet_storage = PlanetStorage()
    scene_manager.planet_storage = planet_storage

    # --------------------------------------------------
    # 2) Build scenes
    # --------------------------------------------------
    size_choices = [(25, 25), (30, 30), (40, 40), (50, 50)]
    size_weights = [0.3, 0.4, 0.2, 0.1]

    planet_meta = PlanetMeta(
        seed=random.randrange(2**32),
        tiles=random.choices(size_choices, weights=size_weights, k=1)[0],
    )

    # Create planet scene using our Arcade modules
    planet_scene = ArcadePlanetScene(assets_dir, planet_meta, planet_storage)
    planet_scene.setup()  # Initialize cameras and world
    
    # Create other scenes (simplified for Arcade)
    system_scene = ArcadeSystemScene(scene_manager, assets_dir, planet_storage)
    galaxy_scene = ArcadeGalaxyScene(scene_manager, assets_dir)

    # Add scenes to manager
    scene_manager.add_scene("Planet", planet_scene)
    scene_manager.add_scene("System", system_scene)
    scene_manager.add_scene("Galaxy", galaxy_scene)

    # --------------------------------------------------
    # 3) HUD (simplified for Arcade)
    # --------------------------------------------------
    hud = ArcadeUIHud(scene_manager)
    scene_manager.hud = hud

    # Give scenes reference to HUD
    planet_scene.hud = hud
    system_scene.hud = hud
    galaxy_scene.hud = hud

    # --------------------------------------------------
    # 4) Start with planet scene
    # --------------------------------------------------
    print("[Main] Starting with Planet scene...")
    scene_manager.switch_to_scene("Planet")

    print("[Main] Starting Arcade game loop...")

    # --------------------------------------------------
    # 5) Run Arcade main loop
    # --------------------------------------------------
    try:
        arcade.run()
    except Exception as e:
        print(f"[Main] Error in game loop: {e}")
        import traceback
        traceback.print_exc()

    print("[Main] Game ended, cleaning up...")


def test_arcade_modules():
    """Test that all Arcade modules can be imported"""
    print("[Test] Testing Arcade module imports...")
    
    try:
        # Test core modules
        from arcade_planet_scene import ArcadePlanetScene
        print("✓ arcade_planet_scene")
        
        from arcade_world_generator import ArcadeWorldGenerator
        print("✓ arcade_world_generator")
        
        from arcade_entity_manager import ArcadeEntityManager
        print("✓ arcade_entity_manager")
        
        from arcade_movement_system import ArcadeMovementSystem
        print("✓ arcade_movement_system")
        
        from arcade_event_handler import ArcadeEventHandler
        print("✓ arcade_event_handler")
        
        from arcade_renderer import ArcadeRenderer
        print("✓ arcade_renderer")
        
        from arcade_utilities import ArcadeUtilities
        print("✓ arcade_utilities")
        
        from arcade_state_manager import ArcadeStateManager
        print("✓ arcade_state_manager")
        
        from arcade_unit_manager import ArcadeUnitManager
        print("✓ arcade_unit_manager")
        
        from arcade_animals import ArcadeAnimalManager
        print("✓ arcade_animals")
        
        print("[Test] All Arcade modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"[Test] Import error: {e}")
        print("[Test] Make sure all Arcade module files are in the same directory")
        return False


def check_compatibility():
    """Check if existing modules are available for compatibility"""
    print("[Compatibility] Checking existing modules...")
    
    try:
        from planet_meta import PlanetMeta
        print("✓ planet_meta (compatible)")
    except ImportError:
        print("⚠ planet_meta not found - creating simple version")
        # Could create a simple fallback here
    
    try:
        from planet_storage import PlanetStorage
        print("✓ planet_storage (compatible)")
    except ImportError:
        print("⚠ planet_storage not found - creating simple version")
        # Could create a simple fallback here
    
    try:
        from loading_screen import LoadingManager
        print("✓ loading_screen (compatible)")
    except ImportError:
        print("⚠ loading_screen not found - will skip loading screen")


if __name__ == "__main__":
    print("=== ARCADE UNIVERSE SIMULATION STARTING ===")
    
    # Check compatibility with existing systems
    check_compatibility()
    
    # Test Arcade modules
    if not test_arcade_modules():
        print("[Main] Arcade module test failed - exiting")
        sys.exit(1)
    
    # Run the game
    try:
        main()
    except KeyboardInterrupt:
        print("[Main] Interrupted by user")
    except Exception as e:
        print(f"[Main] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("=== ARCADE UNIVERSE SIMULATION ENDED ===")
