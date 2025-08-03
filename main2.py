# main.py
import os
import random
import pygame
import time

def show_startup_loading():
    """Show beautiful startup loading screen"""
    try:
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
            
            # Actually initialize pygame mixer here
            pygame.mixer.init()
            
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
            global SceneManager, PlanetScene, GalaxyScene, SystemScene, UIHud, PlanetMeta, PlanetStorage
            from scene_manager import SceneManager
            from planet_scene import PlanetScene
            from galaxy_scene import GalaxyScene
            from system_scene import SystemScene
            from ui_hud import UIHud
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
        
        if success:
            print("[Startup] ✅ Startup loading completed")
            return True
        else:
            print("[Startup] ❌ Startup loading failed")
            return False
            
    except ImportError:
        print("[Startup] Loading screen not available, starting directly...")
        # Still need to import modules
        global SceneManager, PlanetScene, GalaxyScene, SystemScene, UIHud, PlanetMeta, PlanetStorage
        from scene_manager import SceneManager
        from planet_scene import PlanetScene
        from galaxy_scene import GalaxyScene
        from system_scene import SystemScene
        from ui_hud import UIHud
        from planet_meta import PlanetMeta
        from planet_storage import PlanetStorage
        pygame.init()
        return True
    except Exception as e:
        print(f"[Startup] Loading screen error: {e}")
        # Fallback imports
        global SceneManager, PlanetScene, GalaxyScene, SystemScene, UIHud, PlanetMeta, PlanetStorage
        from scene_manager import SceneManager
        from planet_scene import PlanetScene
        from galaxy_scene import GalaxyScene
        from system_scene import SystemScene
        from ui_hud import UIHud
        from planet_meta import PlanetMeta
        from planet_storage import PlanetStorage
        pygame.init()
        return True

def main() -> None:
    # Show startup loading screen first
    startup_success = show_startup_loading()
    
    if not startup_success:
        print("Startup failed, exiting...")
        return

    # --------------------------------------------------
    # 1) Window / clock - modules already imported during loading
    # --------------------------------------------------
    manager = SceneManager(width=1920, height=1024, fps=60)

    # Path to your PNG/SVG assets
    assets_dir = os.path.join(os.path.dirname(__file__), "assets", "images")

    # --------------------------------------------------
    # 1.5) NEW: Initialize centralized planet storage
    # --------------------------------------------------
    planet_storage = PlanetStorage()

    # --------------------------------------------------
    # 2) Build scenes
    # --------------------------------------------------
    #   PlanetScene now needs a PlanetMeta bundle
    size_choices  = [(60, 60), (100, 100), (200, 200), (300, 300)]
    size_weights  = [0.08, 0.20, 0.15, 0.01]

    planet_meta = PlanetMeta(
        seed  = random.randrange(2**32),
        tiles = random.choices(size_choices, weights=size_weights, k=1)[0],
    )

    # Pass surface to planet scene for loading screen support
    planet_scene = PlanetScene(assets_dir, planet_meta, manager.surface)
    # Pass storage reference to planet scene
    planet_scene.planet_storage = planet_storage
    
    galaxy_scene = GalaxyScene(manager, assets_dir)
    system_scene = SystemScene(manager, assets_dir, planet_storage)  # Pass storage to system scene

    scenes_dict = {
        "Planet": planet_scene,
        "System": system_scene,
        "Galaxy": galaxy_scene,
    }

    manager.set_scene(planet_scene)           # default start view

    # --------------------------------------------------
    # 3) HUD (shared across scenes)
    # --------------------------------------------------
    hud = UIHud(
        screen_width  = 1920,
        screen_height = 1024,
        scenes        = scenes_dict,
        manager       = manager,
    )

    # Let every scene talk to the HUD if desired
    planet_scene.hud = hud
    system_scene.hud = hud
    galaxy_scene.hud = hud

    print("[Main] Starting main game loop...")

    # --------------------------------------------------
    # 4) Main loop – update scene & HUD
    # --------------------------------------------------
    while True:
        dt     = manager.clock.tick(manager.fps)
        events = pygame.event.get()

        if not manager.current_scene:
            continue

        # HUD gets events first (UI buttons, tabs, etc.)
        hud.handle_events(events, manager.current_scene)

        # Scene handles game-world events
        manager.current_scene.handle_events(events)

        if not manager.current_scene.running:
            break

        manager.current_scene.update(dt)

        manager.surface.fill((0, 0, 0))  # Use surface consistently
        manager.current_scene.render(manager.surface)
        hud.render(manager.surface)

        pygame.display.flip()

    print("[Main] Game ended, cleaning up...")
    pygame.quit()


if __name__ == "__main__":
    print("=== UNIVERSE SIMULATION STARTING ===")
    main()
    print("=== UNIVERSE SIMULATION ENDED ===")
