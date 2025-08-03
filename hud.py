"""
HUD System
Heads-up display for game information and controls - LCARS Style
"""

import arcade
import math
from typing import Optional, List, Dict
from ..core.constants import *
from ..entities.entity import EntityType
from ..entities.biped import Biped
from ..entities.animal import Animal

class HUD:
    """Heads-up display for game information and controls - LCARS Style"""
    
    def __init__(self, planet_view):
        self.planet_view = planet_view
        self.game_state = planet_view.game_state
        
        # UI elements
        self.buttons = {}
        self.current_tab = "main"
        self.tabs = ["main", "build", "craft", "research"]
        
        # Animation variables
        self.time = 0
        self.pulse_alpha = 0
        
        # LCARS Color scheme
        self.colors = {
            'primary': (255, 153, 0),      # LCARS Orange
            'secondary': (153, 204, 255),   # LCARS Blue
            'accent': (255, 102, 102),      # LCARS Red
            'success': (102, 255, 102),     # LCARS Green
            'warning': (255, 255, 102),     # LCARS Yellow
            'background': (15, 15, 35),     # Dark background
            'panel': (26, 26, 46),          # Panel background
            'text': (220, 220, 255),        # Light text
            'disabled': (80, 80, 100),      # Disabled elements
        }
        
        # Button definitions
        self.setup_buttons()
        
    def setup_buttons(self):
        """Set up UI buttons"""
        # Main tab buttons
        self.buttons["main"] = {
            "build_house": {"x": 10, "y": 200, "width": 80, "height": 30, "text": "BUILD HOUSE", "color": "accent"},
            "change_job": {"x": 10, "y": 160, "width": 80, "height": 30, "text": "CHANGE JOB", "color": "secondary"},
            "tab_build": {"x": 10, "y": 120, "width": 80, "height": 30, "text": "BUILD", "color": "primary"},
            "tab_craft": {"x": 10, "y": 80, "width": 80, "height": 30, "text": "CRAFT", "color": "primary"},
            "tab_research": {"x": 10, "y": 40, "width": 80, "height": 30, "text": "RESEARCH", "color": "primary"},
        }
        
        # Build tab buttons
        self.buttons["build"] = {
            "house": {"x": 10, "y": 200, "width": 80, "height": 30, "text": "HOUSE", "cost": {"wood": 20, "stone": 10}, "color": "accent"},
            "farm": {"x": 10, "y": 160, "width": 80, "height": 30, "text": "FARM", "cost": {"wood": 15, "stone": 5}, "color": "success"},
            "factory": {"x": 10, "y": 120, "width": 80, "height": 30, "text": "FACTORY", "cost": {"wood": 30, "stone": 20, "metal": 10}, "color": "warning"},
            "lab": {"x": 10, "y": 80, "width": 80, "height": 30, "text": "LAB", "cost": {"wood": 25, "stone": 15, "metal": 15}, "color": "secondary"},
            "spaceport": {"x": 10, "y": 40, "width": 80, "height": 30, "text": "SPACEPORT", "cost": {"wood": 50, "stone": 40, "metal": 30}, "color": "primary"},
            "back": {"x": 10, "y": 10, "width": 80, "height": 25, "text": "< BACK", "color": "disabled"},
        }
        
        # Craft tab buttons
        self.buttons["craft"] = {
            "axe": {"x": 10, "y": 200, "width": 80, "height": 30, "text": "AXE", "cost": {"wood": 5, "stone": 2}, "color": "accent"},
            "pickaxe": {"x": 10, "y": 160, "width": 80, "height": 30, "text": "PICKAXE", "cost": {"wood": 3, "stone": 5}, "color": "accent"},
            "sword": {"x": 10, "y": 120, "width": 80, "height": 30, "text": "SWORD", "cost": {"metal": 10, "wood": 5}, "color": "warning"},
            "armor": {"x": 10, "y": 80, "width": 80, "height": 30, "text": "ARMOR", "cost": {"metal": 15, "leather": 5}, "color": "success"},
            "back": {"x": 10, "y": 10, "width": 80, "height": 25, "text": "< BACK", "color": "disabled"},
        }
        
        # Research tab buttons
        self.buttons["research"] = {
            "agriculture": {"x": 10, "y": 200, "width": 80, "height": 30, "text": "AGRICULTURE", "cost": {"science": 50}, "color": "success"},
            "metallurgy": {"x": 10, "y": 160, "width": 80, "height": 30, "text": "METALLURGY", "cost": {"science": 100}, "color": "warning"},
            "spaceflight": {"x": 10, "y": 120, "width": 80, "height": 30, "text": "SPACEFLIGHT", "cost": {"science": 500}, "color": "secondary"},
            "back": {"x": 10, "y": 10, "width": 80, "height": 25, "text": "< BACK", "color": "disabled"},
        }
        
    def draw_rounded_rect(self, x: float, y: float, width: float, height: float, color, radius: float = 10):
        """Draw a rounded rectangle with LCARS styling"""
        # Ensure radius doesn't exceed half the smallest dimension
        radius = min(radius, min(width, height) / 2)
        
        # Ensure coordinates are in correct order
        left = x
        right = x + width
        bottom = y
        top = y + height
        
        # Main rectangle (center part)
        if width > 2 * radius:
            arcade.draw_lrbt_rectangle_filled(left + radius, right - radius, bottom, top, color)
        if height > 2 * radius:
            arcade.draw_lrbt_rectangle_filled(left, right, bottom + radius, top - radius, color)
        
        # Corners (only if radius > 0)
        if radius > 0:
            arcade.draw_circle_filled(left + radius, bottom + radius, radius, color)
            arcade.draw_circle_filled(right - radius, bottom + radius, radius, color)
            arcade.draw_circle_filled(left + radius, top - radius, radius, color)
            arcade.draw_circle_filled(right - radius, top - radius, radius, color)
        
    def draw_glow_effect(self, x: float, y: float, width: float, height: float, color, intensity: float = 0.3):
        """Draw a glowing effect around a rectangle"""
        # Simplified glow effect using lines since alpha blending is complex
        glow_color = color
        for i in range(3):
            offset = (i + 1) * 2
            glow_width = width + offset * 2
            glow_height = height + offset * 2
            glow_x = x - offset
            glow_y = y - offset
            # Draw simple rectangle for glow
            arcade.draw_lrbt_rectangle_filled(glow_x, glow_x + glow_width, glow_y, glow_y + glow_height, glow_color)
        
    def draw(self):
        """Draw the HUD with LCARS styling"""
        # Calculate HUD position
        left = self.planet_view.width - HUD_WIDTH
        right = self.planet_view.width
        bottom = 0
        top = self.planet_view.height
        
        # Draw main HUD background with gradient effect
        self.draw_rounded_rect(left, bottom, HUD_WIDTH, self.planet_view.height, self.colors['background'])
        
        # Draw accent border with glow
        border_color = self.colors['primary']
        arcade.draw_line(left, bottom, left, top, border_color, 4)
        
        # Draw animated accent lines
        pulse = abs(math.sin(self.time * 2)) * 0.5 + 0.5
        accent_color = self.colors['primary']
        
        # Top accent
        self.draw_rounded_rect(left + 5, top - 40, HUD_WIDTH - 10, 30, accent_color, 15)
        
        # Side accents
        for i in range(5):
            y_pos = top - 100 - (i * 80)
            if y_pos > 50:
                accent_width = 20 + (i % 2) * 10
                self.draw_rounded_rect(left + 5, y_pos, accent_width, 40, accent_color, 20)
        
        # Draw title with futuristic font effect
        title_y = top - 25
        arcade.draw_text("LCARS", left + 15, title_y, self.colors['text'], 18, bold=True)
        arcade.draw_text("HUD SYSTEM", left + 80, title_y, self.colors['primary'], 12, bold=True)
        
        # Draw resources with enhanced styling
        self.draw_resources(left)
        
        # Draw current tab content
        if self.current_tab == "main":
            self.draw_main_tab(left)
        elif self.current_tab == "build":
            self.draw_build_tab(left)
        elif self.current_tab == "craft":
            self.draw_craft_tab(left)
        elif self.current_tab == "research":
            self.draw_research_tab(left)
            
        # Draw selected entities info
        self.draw_selected_info(left)
        
    def draw_resources(self, hud_x: float):
        """Draw resource information with LCARS styling"""
        y_start = self.planet_view.height - 80
        
        # Resource panel background
        panel_height = 140
        self.draw_rounded_rect(hud_x + 5, y_start - panel_height, HUD_WIDTH - 10, panel_height, self.colors['panel'], 8)
        
        # Title with accent bar
        arcade.draw_text("RESOURCES", hud_x + 15, y_start - 20, self.colors['text'], 14, bold=True)
        self.draw_rounded_rect(hud_x + 15, y_start - 25, 80, 2, self.colors['primary'])
        
        # Resource list with bars
        resources = [
            ("FOOD", self.game_state.get_resource_amount(RESOURCE_FOOD), self.colors['success']),
            ("WOOD", self.game_state.get_resource_amount(RESOURCE_WOOD), self.colors['accent']),
            ("STONE", self.game_state.get_resource_amount(RESOURCE_STONE), self.colors['disabled']),
            ("METAL", self.game_state.get_resource_amount(RESOURCE_METAL), self.colors['warning']),
            ("ENERGY", self.game_state.get_resource_amount(RESOURCE_ENERGY), self.colors['secondary']),
            ("SCIENCE", self.game_state.get_resource_amount(RESOURCE_SCIENCE), self.colors['primary']),
        ]
        
        for i, (name, amount, color) in enumerate(resources):
            y = y_start - 40 - (i * 18)
            
            # Resource name and amount
            arcade.draw_text(f"{name}:", hud_x + 15, y, self.colors['text'], 10, bold=True)
            arcade.draw_text(f"{amount}", hud_x + 80, y, color, 10, bold=True)
            
            # Resource bar background
            bar_width = 60
            bar_height = 4
            self.draw_rounded_rect(hud_x + 130, y + 2, bar_width, bar_height, self.colors['disabled'], 2)
            
            # Resource bar fill (simplified representation)
            fill_width = min(bar_width, max(2, amount / 10))
            if fill_width > 2:
                self.draw_rounded_rect(hud_x + 130, y + 2, fill_width, bar_height, color, 2)
            
    def draw_main_tab(self, hud_x: float):
        """Draw main tab content with LCARS styling"""
        y_start = self.planet_view.height - 250
        
        # Panel background
        panel_height = 200
        self.draw_rounded_rect(hud_x + 5, y_start - panel_height + 50, HUD_WIDTH - 10, panel_height, self.colors['panel'], 8)
        
        # Title
        arcade.draw_text("COMMAND CENTER", hud_x + 15, y_start, self.colors['text'], 14, bold=True)
        self.draw_rounded_rect(hud_x + 15, y_start - 5, 120, 2, self.colors['secondary'])
        
        # Draw buttons
        for button_id, button in self.buttons["main"].items():
            self.draw_lcars_button(hud_x + button["x"], y_start - button["y"], button["width"], button["height"], 
                                 button["text"], button.get("color", "primary"))
            
    def draw_build_tab(self, hud_x: float):
        """Draw build tab content with LCARS styling"""
        y_start = self.planet_view.height - 250
        
        # Panel background
        panel_height = 220
        self.draw_rounded_rect(hud_x + 5, y_start - panel_height + 50, HUD_WIDTH - 10, panel_height, self.colors['panel'], 8)
        
        # Title
        arcade.draw_text("CONSTRUCTION", hud_x + 15, y_start, self.colors['text'], 14, bold=True)
        self.draw_rounded_rect(hud_x + 15, y_start - 5, 110, 2, self.colors['accent'])
        
        # Draw buttons
        for button_id, button in self.buttons["build"].items():
            if button_id == "back":
                self.draw_lcars_button(hud_x + button["x"], button["y"], button["width"], button["height"], 
                                     button["text"], button.get("color", "disabled"))
            else:
                can_afford = self.can_afford_costs(button.get("cost", {}))
                color = button.get("color", "primary") if can_afford else "disabled"
                self.draw_lcars_button(hud_x + button["x"], y_start - button["y"], button["width"], button["height"], 
                                     button["text"], color, can_afford)
                
    def draw_craft_tab(self, hud_x: float):
        """Draw craft tab content with LCARS styling"""
        y_start = self.planet_view.height - 250
        
        # Panel background
        panel_height = 200
        self.draw_rounded_rect(hud_x + 5, y_start - panel_height + 50, HUD_WIDTH - 10, panel_height, self.colors['panel'], 8)
        
        # Title
        arcade.draw_text("FABRICATION", hud_x + 15, y_start, self.colors['text'], 14, bold=True)
        self.draw_rounded_rect(hud_x + 15, y_start - 5, 100, 2, self.colors['warning'])
        
        # Draw buttons
        for button_id, button in self.buttons["craft"].items():
            if button_id == "back":
                self.draw_lcars_button(hud_x + button["x"], button["y"], button["width"], button["height"], 
                                     button["text"], button.get("color", "disabled"))
            else:
                can_afford = self.can_afford_costs(button.get("cost", {}))
                color = button.get("color", "primary") if can_afford else "disabled"
                self.draw_lcars_button(hud_x + button["x"], y_start - button["y"], button["width"], button["height"], 
                                     button["text"], color, can_afford)
                               
    def draw_research_tab(self, hud_x: float):
        """Draw research tab content with LCARS styling"""
        y_start = self.planet_view.height - 250
        
        # Panel background
        panel_height = 180
        self.draw_rounded_rect(hud_x + 5, y_start - panel_height + 50, HUD_WIDTH - 10, panel_height, self.colors['panel'], 8)
        
        # Title
        arcade.draw_text("RESEARCH LAB", hud_x + 15, y_start, self.colors['text'], 14, bold=True)
        self.draw_rounded_rect(hud_x + 15, y_start - 5, 105, 2, self.colors['secondary'])
        
        # Draw buttons
        for button_id, button in self.buttons["research"].items():
            if button_id == "back":
                self.draw_lcars_button(hud_x + button["x"], button["y"], button["width"], button["height"], 
                                     button["text"], button.get("color", "disabled"))
            else:
                can_afford = self.can_afford_costs(button.get("cost", {}))
                color = button.get("color", "primary") if can_afford else "disabled"
                self.draw_lcars_button(hud_x + button["x"], y_start - button["y"], button["width"], button["height"], 
                                     button["text"], color, can_afford)
                               
    def draw_selected_info(self, hud_x: float):
        """Draw information about selected entities with LCARS styling"""
        if not self.planet_view.selected_entities:
            return
            
        y_start = 250
        
        # Panel background
        panel_height = 160
        self.draw_rounded_rect(hud_x + 5, y_start - panel_height, HUD_WIDTH - 10, panel_height, self.colors['panel'], 8)
        
        # Title
        arcade.draw_text("ENTITY SCAN", hud_x + 15, y_start - 20, self.colors['text'], 14, bold=True)
        self.draw_rounded_rect(hud_x + 15, y_start - 25, 90, 2, self.colors['primary'])
        
        # Show info for first selected entity
        entity_id = list(self.planet_view.selected_entities)[0]
        entity = self.planet_view.get_entity_by_id(entity_id)
        
        if entity:
            y = y_start - 45
            
            # Entity type
            arcade.draw_text(f"TYPE:", hud_x + 15, y, self.colors['text'], 10, bold=True)
            arcade.draw_text(f"{entity.entity_type.value.upper()}", hud_x + 80, y, self.colors['secondary'], 10, bold=True)
            y -= 20
            
            # Health with bar
            health_percent = entity.stats.health / entity.stats.max_health
            arcade.draw_text(f"HEALTH:", hud_x + 15, y, self.colors['text'], 10, bold=True)
            arcade.draw_text(f"{entity.stats.health}/{entity.stats.max_health}", hud_x + 80, y, self.colors['success'], 10, bold=True)
            
            # Health bar
            bar_width = 80
            bar_height = 6
            self.draw_rounded_rect(hud_x + 15, y - 15, bar_width, bar_height, self.colors['disabled'], 3)
            health_bar_width = bar_width * health_percent
            if health_bar_width > 0:
                health_color = self.colors['success'] if health_percent > 0.5 else self.colors['warning'] if health_percent > 0.25 else self.colors['accent']
                self.draw_rounded_rect(hud_x + 15, y - 15, health_bar_width, bar_height, health_color, 3)
            y -= 30
            
            # Job (for bipeds)
            if entity.entity_type == EntityType.BIPED:
                arcade.draw_text(f"JOB:", hud_x + 15, y, self.colors['text'], 10, bold=True)
                arcade.draw_text(f"{entity.job.value.upper()}", hud_x + 80, y, self.colors['warning'], 10, bold=True)
                y -= 20
                
            # State
            arcade.draw_text(f"STATE:", hud_x + 15, y, self.colors['text'], 10, bold=True)
            arcade.draw_text(f"{entity.state.value.upper()}", hud_x + 80, y, self.colors['primary'], 10, bold=True)
            
    def draw_lcars_button(self, x: float, y: float, width: float, height: float, text: str, color_key: str = "primary", enabled: bool = True):
        """Draw a LCARS-style button"""
        color = self.colors[color_key] if enabled else self.colors['disabled']
        
        # Button background with rounded corners
        self.draw_rounded_rect(x, y, width, height, color, 8)
        
        # Glow effect for enabled buttons
        if enabled and color_key != "disabled":
            pulse = abs(math.sin(self.time * 3)) * 0.2 + 0.1
            self.draw_glow_effect(x, y, width, height, color, pulse)
        
        # Button highlight
        highlight_color = tuple(min(255, c + 30) for c in color[:3])
        self.draw_rounded_rect(x + 2, y + height - 6, width - 4, 4, highlight_color, 4)
        
        # Center text
        text_x = x + width / 2
        text_y = y + height / 2
        text_color = self.colors['background'] if enabled else self.colors['text']
        arcade.draw_text(text, text_x, text_y, text_color, 9, anchor_x="center", anchor_y="center", bold=True)
        
    def can_afford_costs(self, costs: Dict[str, int]) -> bool:
        """Check if player can afford the costs"""
        return self.game_state.can_afford(costs)
        
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """Handle mouse press in HUD area"""
        if button != arcade.MOUSE_BUTTON_LEFT:
            return
            
        hud_x = self.planet_view.width - HUD_WIDTH
        local_x = x - hud_x
        
        # Check current tab buttons
        if self.current_tab in self.buttons:
            for button_id, button_data in self.buttons[self.current_tab].items():
                if self.is_point_in_button(local_x, y, button_data):
                    self.handle_button_click(button_id)
                    return
                    
    def is_point_in_button(self, x: float, y: float, button_data: Dict) -> bool:
        """Check if point is inside button"""
        button_x = button_data["x"]
        button_y = button_data["y"]
        button_width = button_data["width"]
        button_height = button_data["height"]
        
        return (button_x <= x <= button_x + button_width and 
                button_y <= y <= button_y + button_height)
                
    def handle_button_click(self, button_id: str):
        """Handle button click"""
        if button_id == "tab_build":
            self.current_tab = "build"
        elif button_id == "tab_craft":
            self.current_tab = "craft"
        elif button_id == "tab_research":
            self.current_tab = "research"
        elif button_id == "back":
            self.current_tab = "main"
        elif button_id == "build_house":
            self.build_house()
        elif button_id == "change_job":
            self.change_job()
        elif button_id in ["house", "farm", "factory", "lab", "spaceport"]:
            self.start_building(button_id)
        elif button_id in ["axe", "pickaxe", "sword", "armor"]:
            self.craft_item(button_id)
        elif button_id in ["agriculture", "metallurgy", "spaceflight"]:
            self.research_technology(button_id)
            
    def build_house(self):
        """Build a house"""
        if self.game_state.build_house():
            # Add 4 more bipeds
            for i in range(4):
                import random
                x = random.randint(-10, 10)
                y = random.randint(-10, 10)
                job = random.choice(list(BipedJob))
                biped = Biped(f"biped_{len(self.planet_view.bipeds)}", x, y, job)
                self.planet_view.bipeds.append(biped)
                
    def change_job(self):
        """Change job of selected biped"""
        if not self.planet_view.selected_entities:
            return
            
        # Change job of first selected biped
        entity_id = list(self.planet_view.selected_entities)[0]
        entity = self.planet_view.get_entity_by_id(entity_id)
        
        if entity and entity.entity_type == EntityType.BIPED:
            import random
            new_job = random.choice(list(BipedJob))
            entity.change_job(new_job)
            
    def start_building(self, building_type: str):
        """Start building process"""
        # This would set building mode
        pass
        
    def craft_item(self, item_type: str):
        """Craft an item"""
        # This would craft items
        pass
        
    def research_technology(self, tech_type: str):
        """Research a technology"""
        # This would research technologies
        pass
        
    def update(self, delta_time: float):
        """Update HUD animations"""
        self.time += delta_time
        self.pulse_alpha = abs(math.sin(self.time * 2)) * 100 + 100