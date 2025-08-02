import pygame
import time
import math
import random
import threading
from typing import Callable, Any, List, Tuple

# Try to import your planet asset
try:
    from planet import generate_asset as generate_planet_asset
    HAS_PLANET_ASSET = True
except ImportError:
    HAS_PLANET_ASSET = False
    print("[Loading] Planet asset not found, using procedural planet")

class RetroLoadingScreen:
    """Loading screen that matches the PLANISPHAERA image exactly"""
    
    def __init__(self, surface):
        self.surface = surface
        self.width = surface.get_width()
        self.height = surface.get_height()
        
        # Colors matching the image
        self.bg_color = (15, 20, 45)  # Deep space blue
        self.star_colors = [
            (255, 255, 255),  # White stars
            (200, 220, 255),  # Blue-white stars  
            (255, 255, 200),  # Yellow stars
            (255, 200, 150),  # Orange stars
        ]
        
        # Progress tracking (compatibility with original)
        self.current_step = 0
        self.total_steps = 0
        self.current_status = "Initializing..."
        self.sub_progress = 0.0
        self.sub_status = ""
        
        # Generate fixed star field like in the image
        self.stars = self._generate_stars()
        
        # Animation timing
        self.start_time = time.time()
        self.dots_animation = 0
        
        # Fonts (for compatibility)
        try:
            self.title_font = pygame.font.Font(None, 48)
            self.status_font = pygame.font.Font(None, 24)
            self.progress_font = pygame.font.Font(None, 20)
        except:
            self.title_font = None
            self.status_font = None
            self.progress_font = None
    
    def set_total_steps(self, total: int):
        """Set the total number of loading steps"""
        self.total_steps = total
        self.current_step = 0
        
    def update_progress(self, step: int, status: str, sub_progress: float = 0.0, sub_status: str = ""):
        """Update the loading progress"""
        self.current_step = step
        self.current_status = status
        self.sub_progress = sub_progress
        self.sub_status = sub_status
        
    def next_step(self, status: str, sub_progress: float = 0.0, sub_status: str = ""):
        """Move to the next step"""
        self.current_step += 1
        self.current_status = status
        self.sub_progress = sub_progress
        self.sub_status = sub_status
        
    def _generate_stars(self):
        """Generate stars positioned like in the reference image"""
        stars = []
        random.seed(42)  # Fixed seed for consistent star field
        
        # Scatter stars across the screen, avoiding the center area
        for _ in range(60):
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 200)  # Avoid title area
            
            # Skip center area where planet will be
            center_x, center_y = self.width // 2, self.height // 2 - 50
            if abs(x - center_x) < 150 and abs(y - center_y) < 150:
                continue
                
            size = random.choice([2, 3, 4, 5])
            color = random.choice(self.star_colors)
            star_type = random.choice(['cross', 'dot', 'plus'])
            
            stars.append((x, y, size, color, star_type))
            
        return stars
    
    def draw_stars(self):
        """Draw the star field exactly like the image"""
        for x, y, size, color, star_type in self.stars:
            if star_type == 'cross' or star_type == 'plus':
                # Draw cross/plus shaped stars
                # Horizontal line
                start_x = x - size
                end_x = x + size
                pygame.draw.line(self.surface, color, (start_x, y), (end_x, y), 2)
                
                # Vertical line  
                start_y = y - size
                end_y = y + size
                pygame.draw.line(self.surface, color, (x, start_y), (x, end_y), 2)
                
            else:
                # Draw dot stars
                pygame.draw.rect(self.surface, color, (x-1, y-1, 3, 3))
    
    def draw_3d_planet(self, center_x, center_y, time_offset=0):
        """Draw the detailed planet asset with optional animations"""
        # Generate the detailed planet asset
        planet_asset = self._generate_planet_asset()
        
        # Optional: Add gentle rotation animation
        if time_offset > 0:
            # Create a slightly larger surface for rotation without clipping
            size = max(planet_asset.get_width(), planet_asset.get_height()) + 40
            rotated_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            
            # Rotate the planet slowly
            angle = (time_offset * 10) % 360  # 10 degrees per second
            rotated_planet = pygame.transform.rotate(planet_asset, angle)
            
            # Center the rotated planet
            rect = rotated_planet.get_rect(center=(size//2, size//2))
            rotated_surface.blit(rotated_planet, rect)
            
            # Blit to main surface
            asset_rect = rotated_surface.get_rect(center=(center_x, center_y))
            self.surface.blit(rotated_surface, asset_rect)
        else:
            # Static planet
            asset_rect = planet_asset.get_rect(center=(center_x, center_y))
            self.surface.blit(planet_asset, asset_rect)
        
        # Add atmospheric glow effect
        self._add_planet_atmosphere(center_x, center_y, 100)
    
    def _generate_planet_asset(self):
        """Generate the detailed planet asset using polygon primitives"""
        if HAS_PLANET_ASSET:
            # Use your detailed planet asset
            return generate_planet_asset()
        else:
            # Fallback to simplified procedural planet
            return self._generate_simple_planet()
    
    def _generate_simple_planet(self):
        """Generate a simple procedural planet as fallback"""
        width, height = 400, 300
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        center_x, center_y = width // 2, height // 2
        radius = 120
        
        # Ocean base
        pygame.draw.circle(surf, (40, 80, 120), (center_x, center_y), radius)
        
        # Simple continents
        continent_colors = [(60, 140, 60), (80, 160, 80), (100, 180, 60)]
        for i in range(5):
            angle = (2 * math.pi * i) / 5
            cont_x = center_x + int(radius * 0.4 * math.cos(angle))
            cont_y = center_y + int(radius * 0.4 * math.sin(angle))
            cont_size = radius // 4
            color = random.choice(continent_colors)
            pygame.draw.circle(surf, color, (cont_x, cont_y), cont_size)
        
        return surf
    
    def _add_planet_atmosphere(self, center_x, center_y, radius):
        """Add atmospheric glow around the detailed planet"""
        # Multiple layers for smooth glow effect
        for i in range(8):
            glow_radius = radius + (i + 1) * 4
            alpha = max(0, 50 - i * 6)
            glow_color = (100, 150, 255, alpha)
            
            # Create a surface for alpha blending
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), glow_radius)
            
            self.surface.blit(glow_surface, (center_x - glow_radius, center_y - glow_radius), 
                            special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def draw_radiating_star(self, x, y, time_offset=0):
        """Draw the radiating star exactly like in the image"""
        # Bright yellow/white center
        core_color = (255, 255, 150)
        ray_color = (255, 255, 100)
        
        # Draw the main cross rays (longer)
        ray_length = 40
        ray_width = 4
        
        # Main 4 rays (up, down, left, right)
        main_rays = [0, 90, 180, 270]
        for angle in main_rays:
            rad = math.radians(angle)
            end_x = x + int(ray_length * math.cos(rad))
            end_y = y + int(ray_length * math.sin(rad))
            
            # Draw thick ray
            pygame.draw.line(self.surface, ray_color, (x, y), (end_x, end_y), ray_width)
        
        # Draw diagonal rays (shorter)
        diag_length = 25
        diag_rays = [45, 135, 225, 315]
        for angle in diag_rays:
            rad = math.radians(angle)
            end_x = x + int(diag_length * math.cos(rad))
            end_y = y + int(diag_length * math.sin(rad))
            
            # Draw thinner diagonal ray
            pygame.draw.line(self.surface, ray_color, (x, y), (end_x, end_y), 2)
        
        # Bright center core
        pygame.draw.circle(self.surface, core_color, (x, y), 8)
        pygame.draw.circle(self.surface, (255, 255, 255), (x, y), 4)
    
    def draw_pixel_title(self, center_x, y):
        """Draw PLANISPHAERA in pixel font exactly like the image"""
        # Letter patterns (5x7 pixel grid)
        letters = {
            'P': [
                "████ ",
                "█   █",
                "█   █", 
                "████ ",
                "█    ",
                "█    ",
                "█    "
            ],
            'L': [
                "█    ",
                "█    ",
                "█    ",
                "█    ",
                "█    ",
                "█    ",
                "█████"
            ],
            'A': [
                " ███ ",
                "█   █",
                "█   █",
                "█████",
                "█   █",
                "█   █", 
                "█   █"
            ],
            'N': [
                "█   █",
                "██  █",
                "█ █ █",
                "█  ██",
                "█   █",
                "█   █",
                "█   █"
            ],
            'I': [
                "█████",
                "  █  ",
                "  █  ",
                "  █  ",
                "  █  ",
                "  █  ",
                "█████"
            ],
            'S': [
                " ████",
                "█    ",
                "█    ",
                " ███ ",
                "    █",
                "    █",
                "████ "
            ],
            'H': [
                "█   █",
                "█   █",
                "█   █",
                "█████",
                "█   █",
                "█   █",
                "█   █"
            ],
            'E': [
                "█████",
                "█    ",
                "█    ",
                "████ ",
                "█    ",
                "█    ",
                "█████"
            ],
            'R': [
                "████ ",
                "█   █",
                "█   █",
                "████ ",
                "█ █  ",
                "█  █ ",
                "█   █"
            ]
        }
        
        # Title color - warm yellow like in image
        title_color = (255, 255, 150)
        pixel_size = 6
        
        title = "PLANISPHAERA"
        letter_width = 6 * pixel_size
        letter_spacing = 8
        total_width = len(title) * letter_width + (len(title) - 1) * letter_spacing
        
        start_x = center_x - total_width // 2
        
        current_x = start_x
        for char in title:
            if char == ' ':
                current_x += letter_width
                continue
                
            if char in letters:
                pattern = letters[char]
                for row_idx, row in enumerate(pattern):
                    for col_idx, pixel in enumerate(row):
                        if pixel == '█':
                            pixel_x = current_x + col_idx * pixel_size
                            pixel_y = y + row_idx * pixel_size
                            
                            # Draw pixel block
                            pygame.draw.rect(self.surface, title_color,
                                           (pixel_x, pixel_y, pixel_size, pixel_size))
                
            current_x += letter_width + letter_spacing
    
    def render(self):
        """Render the complete loading screen (compatible with original interface)"""
        # Clear with space background
        self.surface.fill(self.bg_color)
        
        # Get animation time
        elapsed = time.time() - self.start_time
        self.dots_animation = int(elapsed * 2) % 4
        
        # Draw star field
        self.draw_stars()
        
        # Draw 3D planet in center
        planet_x = self.width // 2
        planet_y = self.height // 2 - 50
        self.draw_3d_planet(planet_x, planet_y, elapsed)
        
        # Draw radiating star (upper right)
        star_x = self.width // 2 + 150
        star_y = self.height // 2 - 120
        self.draw_radiating_star(star_x, star_y, elapsed)
        
        # Draw title at bottom
        title_y = self.height - 150
        self.draw_pixel_title(self.width // 2, title_y)
        
        # Add subtitle if fonts available
        if self.status_font:
            subtitle = self.status_font.render("Procedural Universe Simulation", True, (180, 180, 120))
            subtitle_rect = subtitle.get_rect(center=(self.width // 2, title_y + 80))
            self.surface.blit(subtitle, subtitle_rect)
        
        # Main progress bar
        if self.total_steps > 0:
            main_progress = self.current_step / self.total_steps
            self._draw_progress_bar(
                self.width//2 - 300, self.height - 200, 600, 30,
                main_progress, 
                f"Step {self.current_step}/{self.total_steps}"
            )
        
        # Current status with animated dots
        if self.status_font:
            dots = "." * self.dots_animation
            status_with_dots = f"{self.current_status}{dots}"
            status_surface = self.status_font.render(status_with_dots, True, (150, 200, 255))
            status_rect = status_surface.get_rect(center=(self.width//2, self.height - 140))
            self.surface.blit(status_surface, status_rect)
        
        # Sub-progress bar
        if self.sub_progress > 0 and self.sub_status:
            self._draw_progress_bar(
                self.width//2 - 250, self.height - 100, 500, 20,
                self.sub_progress,
                self.sub_status,
                is_sub=True
            )
        
        pygame.display.flip()
    
    def _draw_progress_bar(self, x, y, width, height, progress, label, is_sub=False):
        """Draw a progress bar with retro styling (compatible with original)"""
        # Background with border
        bg_color = (60, 70, 90)
        border_color = (200, 200, 150)
        fill_color = (100, 200, 255) if not is_sub else (80, 150, 200)
        
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.surface, bg_color, bg_rect)
        pygame.draw.rect(self.surface, border_color, bg_rect, 2)
        
        # Fill with animated segments
        if progress > 0:
            fill_width = int(width * min(progress, 1.0))
            fill_rect = pygame.Rect(x, y, fill_width, height)
            pygame.draw.rect(self.surface, fill_color, fill_rect)
            
            # Add animated scanline effect
            scanline_x = x + int((time.time() * 100) % width)
            if scanline_x < x + fill_width:
                bright_color = tuple(min(255, c + 50) for c in fill_color)
                pygame.draw.line(self.surface, bright_color, 
                               (scanline_x, y), (scanline_x, y + height), 2)
        
        # Percentage text
        if not is_sub and self.progress_font:
            percent_text = f"{int(progress * 100)}%"
            percent_surface = self.progress_font.render(percent_text, True, border_color)
            percent_rect = percent_surface.get_rect(center=(x + width//2, y + height//2))
            self.surface.blit(percent_surface, percent_rect)
        
        # Label
        if label and self.progress_font:
            font = self.progress_font if is_sub else self.status_font
            if font:
                label_surface = font.render(label, True, (220, 220, 220))
                label_y = y - 25 if not is_sub else y - 20
                label_rect = label_surface.get_rect(center=(x + width//2, label_y))
                self.surface.blit(label_surface, label_rect)

class LoadingManager:
    """Manages loading processes with progress tracking - Compatible Version"""
    
    def __init__(self, surface):
        self.surface = surface
        self.loading_screen = RetroLoadingScreen(surface)  # Use retro version
        
    def load_with_progress(self, 
                          load_function: Callable = None, 
                          loading_steps: List[Tuple[str, Callable, Any]] = None, 
                          title: str = "Loading..."):
        """
        Execute a loading process with progress tracking
        
        Args:
            load_function: Main function to call with progress callback
            loading_steps: List of (status_message, function, args) tuples
            title: Loading screen title
        """
        if loading_steps is None:
            loading_steps = PLANET_GENERATION_STEPS
            
        self.loading_screen.set_total_steps(len(loading_steps))
        
        # Progress callback for the loading function
        def progress_callback(step, status, sub_progress=0.0, sub_status=""):
            self.loading_screen.update_progress(step, status, sub_progress, sub_status)
            self.loading_screen.render()
            pygame.event.pump()  # Keep pygame responsive
        
        try:
            # Execute loading steps
            for i, (status, func, args) in enumerate(loading_steps):
                self.loading_screen.next_step(status)
                self.loading_screen.render()
                pygame.event.pump()
                
                # Execute the step
                if callable(func):
                    if args:
                        result = func(*args, progress_callback=progress_callback)
                    else:
                        result = func(progress_callback=progress_callback)
                else:
                    result = None
                
                # Brief pause to show progress
                time.sleep(0.1)
            
            # Final completion
            self.loading_screen.update_progress(len(loading_steps), "Complete!", 1.0, "Ready to explore!")
            self.loading_screen.render()
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"[LoadingManager] Error during loading: {e}")
            self.loading_screen.update_progress(
                self.loading_screen.current_step, 
                f"Error: {str(e)[:50]}...", 
                0.0, 
                "Loading failed"
            )
            self.loading_screen.render()
            time.sleep(2.0)
            return False

# Enhanced loading sequences with space themes (maintain compatibility)
PLANET_GENERATION_STEPS = [
    ("Calibrating quantum substrate", None, None),
    ("Seeding genetic algorithms", None, None), 
    ("Terraforming biome matrices", None, None),
    ("Spawning primordial life", None, None),
    ("Balancing ecosystem dynamics", None, None),
    ("Stabilizing atmospheric composition", None, None),
    ("Activating geological processes", None, None),
    ("Finalizing planetary parameters", None, None),
]

PLANET_LOADING_STEPS = [
    ("Scanning orbital telemetry", None, None),
    ("Reconstructing surface topology", None, None),
    ("Reviving cryogenic organisms", None, None),
    ("Synchronizing temporal fields", None, None),
    ("Restoring biosphere state", None, None),
    ("Initializing simulation matrix", None, None),
]

GAME_START_STEPS = [
    ("Initializing universe engine", None, None),
    ("Loading stellar cartography", None, None),
    ("Preparing exploration systems", None, None),
    ("Calibrating sensors", None, None),
    ("Ready for interstellar travel", None, None),
]

# Legacy class alias for backward compatibility
LoadingScreen = RetroLoadingScreen
EnhancedLoadingScreen = RetroLoadingScreen

# Example usage
def demo_loading_screen():
    """Demo the PLANISPHAERA loading screen"""
    pygame.init()
    
    # Create screen 
    screen = pygame.display.set_mode((1000, 700))
    pygame.display.set_caption("PLANISPHAERA - Loading")
    
    # Create loading screen
    loading_screen = RetroLoadingScreen(screen)
    
    # Demo with simulated loading
    clock = pygame.time.Clock()
    running = True
    start_time = time.time()
    
    loading_steps = [
        "Initializing quantum matrix...",
        "Generating planetary systems...", 
        "Seeding primordial life...",
        "Calibrating physics engine...",
        "Preparing universe...",
        "Loading complete!"
    ]
    
    current_step = 0
    step_duration = 2.0  # seconds per step
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Calculate progress
        elapsed = time.time() - start_time
        total_progress = elapsed / (len(loading_steps) * step_duration)
        current_step = min(int(elapsed / step_duration), len(loading_steps) - 1)
        
        if total_progress >= 1.0:
            # Loading complete - show final screen for a moment then restart
            loading_screen.render()
            pygame.time.wait(2000)
            start_time = time.time()  # Restart demo
        else:
            status = loading_steps[current_step] if current_step < len(loading_steps) else "Complete!"
            loading_screen.update_progress(current_step, status, total_progress, "")
            loading_screen.render()
        
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    demo_loading_screen()