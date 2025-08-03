# arcade_galaxy_scene.py - Arcade 3.3.2 Galaxy Scene
import arcade
import random
import math

class ArcadeGalaxyScene(arcade.View):
    """Galaxy scene using Arcade 3.3.2"""
    
    def __init__(self, assets_dir: str):
        super().__init__()
        
        # Core properties
        self.assets_dir = assets_dir
        self.hud = None
        
        # Camera and view
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        
        # Mouse state
        self.mouse_dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # Galaxy data
        self.stars = []
        self.systems = []
        
        # Sprite lists
        self.star_sprites = arcade.SpriteList()
        self.system_sprites = arcade.SpriteList()
        
        # Initialize the scene
        self._generate_galaxy()
        self._center_camera()
        
        print("[ArcadeGalaxyScene] Initialized")
        
    def _generate_galaxy(self):
        """Generate galaxy data"""
        # Generate background stars
        star_count = 1000
        for i in range(star_count):
            # Spiral galaxy distribution
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, 800)
            
            # Add spiral arm effect
            spiral_offset = math.sin(angle * 3) * 100
            distance += spiral_offset
            
            star = {
                'x': math.cos(angle) * distance,
                'y': math.sin(angle) * distance,
                'size': random.randint(1, 3),
                'color': self._get_random_star_color(),
                'brightness': random.uniform(0.3, 1.0)
            }
            self.stars.append(star)
            
        # Generate star systems
        system_count = 20
        for i in range(system_count):
            # Place systems in spiral arms
            angle = (i / system_count) * 2 * math.pi
            distance = 100 + (i % 5) * 150
            
            # Add spiral arm effect
            spiral_offset = math.sin(angle * 3) * 50
            distance += spiral_offset
            
            system = {
                'x': math.cos(angle) * distance,
                'y': math.sin(angle) * distance,
                'size': random.randint(8, 15),
                'color': (255, 255, 255),
                'name': f'System {i+1}',
                'planet_count': random.randint(1, 8)
            }
            self.systems.append(system)
            
        # Create sprites
        self._create_sprites()
        
    def _get_random_star_color(self):
        """Get a random star color"""
        colors = [
            (255, 255, 255),  # White
            (255, 255, 200),  # Yellow-white
            (255, 200, 100),  # Yellow
            (255, 150, 50),   # Orange
            (255, 100, 100),  # Red
            (200, 200, 255),  # Blue-white
            (150, 150, 255),  # Blue
        ]
        return random.choice(colors)
        
    def _create_sprites(self):
        """Create Arcade sprites for galaxy objects"""
        # Create star sprites
        self.star_sprites.clear()
        for star in self.stars:
            star_sprite = GalaxyStarSprite(
                star['x'], star['y'],
                star['size'], star['color'],
                star['brightness']
            )
            self.star_sprites.append(star_sprite)
            
        # Create system sprites
        self.system_sprites.clear()
        for system in self.systems:
            system_sprite = SystemSprite(
                system['x'], system['y'],
                system['size'], system['color'],
                system['name'],
                system['planet_count']
            )
            self.system_sprites.append(system_sprite)
            
    def _center_camera(self):
        """Center camera on the galaxy"""
        self.camera_x = -self.window.width // 2
        self.camera_y = -self.window.height // 2
        
    def on_draw(self):
        """Render the galaxy scene"""
        arcade.set_background_color((5, 5, 15))
        
        # Draw spiral arms
        self._draw_spiral_arms()
        
        # Draw sprites
        self.star_sprites.draw()
        self.system_sprites.draw()
        
        # Draw UI (not affected by camera)
        self._draw_ui()
        

        
    def _draw_spiral_arms(self):
        """Draw spiral arm indicators"""
        for arm in range(3):
            for i in range(0, 360, 10):
                angle = math.radians(i)
                distance = 100 + arm * 200
                spiral_offset = math.sin(angle * 3) * 50
                distance += spiral_offset
                
                x = math.cos(angle) * distance
                y = math.sin(angle) * distance
                
                arcade.draw_circle_filled(
                    x, y, 1,
                    (50, 50, 100, 100)
                )
                
    def _draw_ui(self):
        """Draw UI elements"""
        # Draw camera info
        arcade.draw_text(
            f"Camera: ({self.camera_x:.0f}, {self.camera_y:.0f}) Zoom: {self.zoom:.1f}",
            10, self.window.height - 30,
            (255, 255, 255), 14
        )
        
        # Draw galaxy info
        arcade.draw_text(
            f"Stars: {len(self.stars)} Systems: {len(self.systems)}",
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
        # Add subtle twinkling effect to stars
        for i, star in enumerate(self.stars):
            if i < len(self.star_sprites):
                # Randomly adjust brightness
                if random.random() < 0.01:  # 1% chance per frame
                    star['brightness'] = random.uniform(0.3, 1.0)
                    self.star_sprites[i].brightness = star['brightness']
                    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """Handle mouse press"""
        # Handle galaxy scene mouse events
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
        if 0.2 <= new_zoom <= 5.0:
            self.zoom = new_zoom
            
    def on_key_press(self, key: int, modifiers: int):
        """Handle key press"""
        if key == arcade.key.R:
            # Regenerate galaxy
            self._generate_galaxy()
            print("[ArcadeGalaxyScene] Galaxy regenerated")


class GalaxyStarSprite(arcade.Sprite):
    """Galaxy star sprite"""
    
    def __init__(self, x: float, y: float, size: int, color: tuple, brightness: float):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.radius = size
        self.color = color
        self.brightness = brightness
        # Set sprite dimensions
        self.width = size * 2
        self.height = size * 2
        
    def draw(self):
        """Draw the star sprite"""
        # Apply brightness
        adjusted_color = tuple(int(c * self.brightness) for c in self.color)
        
        arcade.draw_circle_filled(
            self.center_x, self.center_y, self.radius,
            adjusted_color
        )


class SystemSprite(arcade.Sprite):
    """Star system sprite"""
    
    def __init__(self, x: float, y: float, size: int, color: tuple, name: str, planet_count: int):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.radius = size
        self.color = color
        self.name = name
        self.planet_count = planet_count
        # Set sprite dimensions
        self.width = size * 2
        self.height = size * 2
        
    def draw(self):
        """Draw the system sprite"""
        # Draw system glow
        arcade.draw_circle_filled(
            self.center_x, self.center_y, self.radius * 2,
            (*self.color, 30)  # Semi-transparent
        )
        
        # Draw system core
        arcade.draw_circle_filled(
            self.center_x, self.center_y, self.radius,
            self.color
        )
        arcade.draw_circle_outline(
            self.center_x, self.center_y, self.radius,
            (255, 255, 255), 2
        )
        
        # Draw system name
        arcade.draw_text(
            self.name, self.center_x - 20, self.center_y + self.radius + 5,
            (255, 255, 255), 10
        )
        
        # Draw planet count
        arcade.draw_text(
            f"{self.planet_count} planets", self.center_x - 25, self.center_y - self.radius - 15,
            (200, 200, 200), 8
        ) 