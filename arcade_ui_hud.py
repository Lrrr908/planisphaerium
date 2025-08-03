# arcade_ui_hud.py - Arcade 3.3.2 UI HUD
import arcade
from typing import Dict, Optional

class ArcadeUIHud:
    """UI HUD system for Arcade 3.3.2"""
    
    PANEL_WIDTH = 300
    INVENTORY_MAX_LINES = 10
    
    def __init__(self, screen_width: int, screen_height: int, scenes: Dict, manager):
        self.width = self.PANEL_WIDTH
        self.height = screen_height
        self.x = screen_width - self.width
        self.y = 0
        
        self.scenes = scenes or {}
        self.manager = manager
        self._scene = None
        
        # Resources
        self.credits = 0
        
        # Mini-map placeholder
        self.mini_map_rect = (self.x + 10, self.y + 50, self.width - 20, 150)
        
        # Build menu
        self.categories = ["Structures", "Defenses", "Units"]
        self.selected_category_idx = 0
        self.build_items = {
            "Structures": ["Power Plant", "Refinery", "Barracks"],
            "Defenses": ["Turret", "Sandbags", "Wall"],
            "Units": ["Soldier", "Tank", "APC"],
        }
        
        # Layer buttons
        self.layer_buttons = [
            ("Planet", self.x + 10, self.y + 400, 60, 30),
            ("System", self.x + 75, self.y + 400, 60, 30),
            ("Galaxy", self.x + 140, self.y + 400, 60, 30),
            ("Universe", self.x + 205, self.y + 400, 80, 30),
        ]
        
        # Biped selector
        self.biped_names = ["BP1", "BP2", "BP3", "BP4"]
        self.unlocked_biped_count = 2
        self.selected_biped_idx = 0
        self.biped_button_rects = []
        
    def update_resources(self, amount: int):
        """Update credits display"""
        self.credits = amount
        
    def unlock_biped(self, idx: int):
        """Called by UnitManager when a new biped is created (0-based)"""
        self.unlocked_biped_count = max(self.unlocked_biped_count, idx + 1)
        
    def refresh_bipeds(self, alive_count: int):
        """Called by UnitManager whenever its unit list shrinks"""
        self.unlocked_biped_count = min(alive_count, len(self.biped_names))
        if self.selected_biped_idx >= self.unlocked_biped_count:
            self.selected_biped_idx = max(0, self.unlocked_biped_count - 1)
            
    def handle_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> bool:
        """Handle mouse press events - returns True if handled"""
        if x < self.x:
            return False
            
        # Check mini-map
        if self._point_in_rect(x, y, self.mini_map_rect):
            return True
            
        # Check layer buttons
        if self._handle_layer_buttons(x, y):
            return True
            
        # Check biped buttons
        if self._handle_biped_buttons(x, y):
            return True
            
        # Check build menu
        if self._handle_build_menu_click(x, y):
            return True
            
        return False
        
    def _point_in_rect(self, x: int, y: int, rect) -> bool:
        """Check if point is inside rectangle"""
        rx, ry, rw, rh = rect
        return rx <= x <= rx + rw and ry <= y <= ry + rh
        
    def _handle_layer_buttons(self, mx: int, my: int) -> bool:
        """Handle layer button clicks"""
        for i, (name, x, y, w, h) in enumerate(self.layer_buttons):
            if self._point_in_rect(mx, my, (x, y, w, h)):
                if self.manager and hasattr(self.manager, 'switch_to_scene'):
                    self.manager.switch_to_scene(name)
                return True
        return False
        
    def _handle_biped_buttons(self, mx: int, my: int) -> bool:
        """Handle biped button clicks"""
        for i, rect in enumerate(self.biped_button_rects):
            if i < self.unlocked_biped_count and self._point_in_rect(mx, my, rect):
                self.selected_biped_idx = i
                return True
        return False
        
    def _handle_build_menu_click(self, mx: int, my: int) -> bool:
        """Handle build menu clicks"""
        # Check category tabs
        tab_y = self.y + 250
        tab_height = 25
        for i, category in enumerate(self.categories):
            tab_x = self.x + 10 + i * 90
            if self._point_in_rect(mx, my, (tab_x, tab_y, 80, tab_height)):
                self.selected_category_idx = i
                return True
                
        # Check build items
        items_y = self.y + 280
        item_height = 20
        current_items = self.build_items[self.categories[self.selected_category_idx]]
        for i, item in enumerate(current_items):
            item_x = self.x + 10
            if self._point_in_rect(mx, my, (item_x, items_y + i * item_height, self.width - 20, item_height)):
                print(f"[ArcadeUIHud] Selected build item: {item}")
                return True
                
        return False
        
    def draw(self):
        """Draw the HUD"""
        # Draw background panel
        arcade.draw_lbwh_rectangle_filled(
            self.x, self.y, self.width, self.height,
            (40, 40, 60, 200)
        )
        
        # Draw border
        arcade.draw_lbwh_rectangle_outline(
            self.x, self.y, self.width, self.height,
            (100, 100, 120), 2
        )
        
        # Draw title
        arcade.draw_text(
            "UNIVERSE HUD", self.x + 10, self.y + self.height - 30,
            (255, 255, 255), 16, bold=True
        )
        
        # Draw mini-map placeholder
        arcade.draw_lbwh_rectangle_filled(
            self.mini_map_rect[0], self.mini_map_rect[1],
            self.mini_map_rect[2], self.mini_map_rect[3],
            (20, 20, 40)
        )
        arcade.draw_lbwh_rectangle_outline(
            self.mini_map_rect[0], self.mini_map_rect[1],
            self.mini_map_rect[2], self.mini_map_rect[3],
            (100, 100, 120), 1
        )
        arcade.draw_text(
            "Mini-Map", self.mini_map_rect[0] + 5, self.mini_map_rect[1] + 5,
            (150, 150, 150), 12
        )
        
        # Draw build menu
        self._draw_build_tabs()
        self._draw_build_icons()
        
        # Draw layer buttons
        self._draw_layer_buttons()
        
        # Draw biped buttons
        self._draw_biped_buttons()
        
        # Draw inventory
        self._draw_inventory()
        
    def _draw_build_tabs(self):
        """Draw build menu category tabs"""
        tab_y = self.y + 250
        tab_height = 25
        
        for i, category in enumerate(self.categories):
            tab_x = self.x + 10 + i * 90
            color = (80, 80, 100) if i == self.selected_category_idx else (60, 60, 80)
            
            arcade.draw_lbwh_rectangle_filled(
                tab_x, tab_y, 80, tab_height, color
            )
            arcade.draw_lbwh_rectangle_outline(
                tab_x, tab_y, 80, tab_height, (100, 100, 120), 1
            )
            arcade.draw_text(
                category, tab_x + 5, tab_y + 5,
                (255, 255, 255), 10
            )
            
    def _draw_build_icons(self):
        """Draw build menu items"""
        items_y = self.y + 280
        item_height = 20
        current_items = self.build_items[self.categories[self.selected_category_idx]]
        
        for i, item in enumerate(current_items):
            item_x = self.x + 10
            arcade.draw_lbwh_rectangle_filled(
                item_x, items_y + i * item_height,
                self.width - 20, item_height,
                (50, 50, 70)
            )
            arcade.draw_text(
                item, item_x + 5, items_y + i * item_height + 2,
                (200, 200, 200), 10
            )
            
    def _draw_layer_buttons(self):
        """Draw layer navigation buttons"""
        for name, x, y, w, h in self.layer_buttons:
            arcade.draw_lbwh_rectangle_filled(x, y, w, h, (60, 60, 80))
            arcade.draw_lbwh_rectangle_outline(x, y, w, h, (100, 100, 120), 1)
            arcade.draw_text(
                name, x + 5, y + 5,
                (255, 255, 255), 10
            )
            
    def _draw_biped_buttons(self):
        """Draw biped selection buttons"""
        self.biped_button_rects = []
        button_y = self.y + 450
        button_height = 25
        
        for i, name in enumerate(self.biped_names):
            if i >= self.unlocked_biped_count:
                break
                
            button_x = self.x + 10 + (i % 2) * 140
            button_y_offset = button_y + (i // 2) * 30
            button_width = 130
            
            color = (80, 80, 100) if i == self.selected_biped_idx else (60, 60, 80)
            
            arcade.draw_lbwh_rectangle_filled(
                button_x, button_y_offset, button_width, button_height, color
            )
            arcade.draw_lbwh_rectangle_outline(
                button_x, button_y_offset, button_width, button_height,
                (100, 100, 120), 1
            )
            arcade.draw_text(
                name, button_x + 5, button_y_offset + 5,
                (255, 255, 255), 10
            )
            
            self.biped_button_rects.append((button_x, button_y_offset, button_width, button_height))
            
    def _draw_inventory(self):
        """Draw inventory and resources"""
        # Draw credits
        arcade.draw_text(
            f"Credits: {self.credits}", self.x + 10, self.y + 10,
            (255, 255, 0), 14, bold=True
        )
        
        # Draw inventory placeholder
        inventory_y = self.y + 600
        arcade.draw_lbwh_rectangle_filled(
            self.x + 10, inventory_y, self.width - 20, 100,
            (30, 30, 50)
        )
        arcade.draw_lbwh_rectangle_outline(
            self.x + 10, inventory_y, self.width - 20, 100,
            (100, 100, 120), 1
        )
        arcade.draw_text(
            "Inventory", self.x + 15, inventory_y + 5,
            (150, 150, 150), 12
        ) 