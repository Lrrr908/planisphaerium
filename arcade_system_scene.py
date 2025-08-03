# arcade_system_scene.py - Arcade 3.3.2 System Scene
import arcade
import random
from planet_storage import PlanetStorage
import math

class ArcadeSystemScene(arcade.View):
    """System scene using Arcade 3.3.2"""
    
    def __init__(self, assets_dir: str, planet_storage: PlanetStorage):
        super().__init__()
        
        # Core properties
        self.assets_dir = assets_dir
        self.planet_storage = planet_storage
        self.hud = None
        
        # Camera and view
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        
        # Mouse state
        self.mouse_dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # System data
        self.planets = []
        self.stars = []
        
        # Sprite lists
        self.planet_sprites = arcade.SpriteList()
        self.star_sprites = arcade.SpriteList()
        
        # Initialize the scene
        self._generate_system()
        self._center_camera()
        
        print("[ArcadeSystemScene] Initialized")
        
    def _generate_system(self):
        """Generate solar system data"""
        # Generate star
        star = {
            'x': 0,
            'y': 0,
            'size': 50,
            'color': (255, 255, 0),  # Yellow
            'name': 'Sol'
        }
        self.stars.append(star)
        
        # Generate planets
        planet_count = random.randint(3, 8)
        for i in range(planet_count):
            # Calculate orbital position
            angle = (i / planet_count) * 2 * 3.14159
            distance = 150 + i * 80
            
            planet = {
                'x': math.cos(angle) * distance,
                'y': math.sin(angle) * distance,
                'size': random.randint(15, 35),
                'color': self._get_random_planet_color(),
                'name': f'Planet {i+1}',
                'orbit_radius': distance,
                'orbit_angle': angle,
                'orbit_speed': random.uniform(0.001, 0.005)
            }
            self.planets.append(planet)
            
        # Create sprites
        self._create_sprites()
        
    def _get_random_planet_color(self):
        """Get a random planet color"""
        colors = [
            (139, 69, 19),   # Brown
            (255, 140, 0),   # Orange
            (0, 191, 255),   # Light blue
            (255, 20, 147),  # Pink
            (128, 0, 128),   # Purple
            (255, 215, 0),   # Gold
            (0, 255, 127),   # Green
            (255, 69, 0),    # Red-orange
        ]
        return random.choice(colors)
        
    def _create_sprites(self):
        """Create Arcade sprites for system objects"""
        # Create star sprites
        self.star_sprites.clear()
        for star in self.stars:
            star_sprite = StarSprite(
                star['x'], star['y'],
                star['size'], star['color'],
                star['name']
            )
            self.star_sprites.append(star_sprite)
            
        # Create planet sprites
        self.planet_sprites.clear()
        for planet in self.planets:
            planet_sprite = PlanetSprite(
                planet['x'], planet['y'],
                planet['size'], planet['color'],
                planet['name']
            )
            self.planet_sprites.append(planet_sprite)
            
    def _center_camera(self):
        """Center camera on the system"""
        self.camera_x = -self.window.width // 2
        self.camera_y = -self.window.height // 2
        
    def on_draw(self):
        """Render the system scene"""
        arcade.set_background_color((10, 10, 30))
        
        # Draw orbits
        self._draw_orbits()
        
        # Draw sprites
        self.star_sprites.draw()
        self.planet_sprites.draw()
        
        # Draw UI (not affected by camera)
        self._draw_ui()
        

        
    def _draw_orbits(self):
        """Draw planetary orbits"""
        for planet in self.planets:
            arcade.draw_circle_outline(
                0, 0, planet['orbit_radius'],
                (50, 50, 100), 1
            )
            
    def _draw_ui(self):
        """Draw UI elements"""
        # Draw camera info
        arcade.draw_text(
            f"Camera: ({self.camera_x:.0f}, {self.camera_y:.0f}) Zoom: {self.zoom:.1f}",
            10, self.window.height - 30,
            (255, 255, 255), 14
        )
        
        # Draw system info
        arcade.draw_text(
            f"Planets: {len(self.planets)} Stars: {len(self.stars)}",
            10, self.window.height - 50,
            (255, 255, 255), 14
        )
        
        # Draw instructions
        arcade.draw_text(
            "Mouse: Pan | Scroll: Zoom | R: Regenerate",
            10, 10,
            (200, 200, 200), 12
        )
        
    def on_update(self, delta_time: float):
        """Update game logic"""
        # Update planet positions (orbital motion)
        for i, planet in enumerate(self.planets):
            planet['orbit_angle'] += planet['orbit_speed']
            planet['x'] = math.cos(planet['orbit_angle']) * planet['orbit_radius']
            planet['y'] = math.sin(planet['orbit_angle']) * planet['orbit_radius']
            
            # Update sprite position
            if i < len(self.planet_sprites):
                self.planet_sprites[i].center_x = planet['x']
                self.planet_sprites[i].center_y = planet['y']
                
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse press"""
        # Handle system scene mouse events
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse_dragging = True
            self.last_mouse_x = x
            self.last_mouse_y = y
            
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse release"""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse_dragging = False
            
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        """Handle mouse motion"""
        if self.mouse_dragging:
            # Pan camera
            self.camera_x -= dx
            self.camera_y -= dy
            
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        """Handle mouse scroll (zoom)"""
        zoom_change = scroll_y * 0.1
        new_zoom = self.zoom + zoom_change
        
        # Clamp zoom
        if 0.5 <= new_zoom <= 3.0:
            self.zoom = new_zoom
            
    def on_key_press(self, key: int, modifiers: int):
        """Handle key press"""
        if key == arcade.key.R:
            # Regenerate system
            self._generate_system()
            print("[ArcadeSystemScene] System regenerated")


class StarSprite(arcade.Sprite):
    """Star sprite"""
    
    def __init__(self, x: float, y: float, size: int, color: tuple, name: str):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.radius = size
        self.color = color
        self.name = name
        # Set sprite dimensions
        self.width = size * 2
        self.height = size * 2
        
    def draw(self):
        """Draw the star sprite"""
        # Draw star glow
        arcade.draw_circle_filled(
            self.center_x, self.center_y, self.radius * 1.5,
            (*self.color, 50)  # Semi-transparent
        )
        
        # Draw star core
        arcade.draw_circle_filled(
            self.center_x, self.center_y, self.radius,
            self.color
        )
        
        # Draw star name
        arcade.draw_text(
            self.name, self.center_x - 20, self.center_y + self.radius + 5,
            (255, 255, 255), 12
        )


class PlanetSprite(arcade.Sprite):
    """Planet sprite"""
    
    def __init__(self, x: float, y: float, size: int, color: tuple, name: str):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.radius = size
        self.color = color
        self.name = name
        # Set sprite dimensions
        self.width = size * 2
        self.height = size * 2
        
    def draw(self):
        """Draw the planet sprite"""
        # Draw planet
        arcade.draw_circle_filled(
            self.center_x, self.center_y, self.radius,
            self.color
        )
        arcade.draw_circle_outline(
            self.center_x, self.center_y, self.radius,
            (255, 255, 255), 2
        )
        
        # Draw planet name
        arcade.draw_text(
            self.name, self.center_x - 20, self.center_y + self.radius + 5,
            (255, 255, 255), 10
        ) 