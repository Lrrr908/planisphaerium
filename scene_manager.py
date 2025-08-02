# scene_manager.py
import pygame

class Scene:
    """
    Base class for any scene (universe, galaxy, solar system, planet).
    We define empty methods that child classes override as needed.
    """
    def __init__(self):
        self.running = True

    def handle_events(self, events):
        pass

    def update(self, dt):
        pass

    def render(self, surface):
        pass


class SceneManager:
    """
    Manages the current scene and runs the main game loop.
    """
    def __init__(self, width=1920, height=1024, fps=60):
        self.width = width
        self.height = height
        self.fps = fps
        self.current_scene = None
        self.clock = pygame.time.Clock()

        # Initialize the window once here
        self.surface = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Universe Simulation")
        
        # Keep backward compatibility
        self.screen = self.surface
        
        # Debug output for loading screen
        print(f"[SceneManager] Surface created for loading screens: {self.surface is not None}")

    def set_scene(self, scene):
        """Set the current scene"""
        # Call exit handler on old scene
        if self.current_scene and hasattr(self.current_scene, 'on_scene_exit'):
            self.current_scene.on_scene_exit()
        
        self.current_scene = scene
        
        # Call enter handler on new scene
        if hasattr(scene, 'on_scene_enter'):
            scene.on_scene_enter()

    def run(self):
        while True:
            dt = self.clock.tick(self.fps)
            events = pygame.event.get()

            if not self.current_scene:
                continue  # if no scene yet, do nothing

            self.current_scene.handle_events(events)
            if not self.current_scene.running:
                # Scene ended, exit or switch to another scene
                break

            self.current_scene.update(dt)
            self.current_scene.render(self.surface)  # Use self.surface consistently

            pygame.display.flip()

        pygame.quit()