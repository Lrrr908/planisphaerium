# ui_hud.py  ·  v2025-07-07g  (auto-shrink biped list)
import pygame


class UIHud:
    """
    Side-panel HUD
        • Shared inventory
        • Biped selector – buttons appear when units spawn
          and disappear when units die
        • Mini-map placeholder, build menu, layer switcher
    """

    PANEL_WIDTH, INVENTORY_MAX_LINES = 300, 10

    # ────────────────────────────────────────────────────
    #  Constructor
    # ────────────────────────────────────────────────────
    def __init__(self, screen_width, screen_height, scenes=None, manager=None):
        self.width  = self.PANEL_WIDTH
        self.height = screen_height
        self.x, self.y = screen_width - self.width, 0

        self.scenes  = scenes or {}
        self.manager = manager
        self._scene  = None           # set in handle_events(..)

        pygame.font.init()
        self.font_small  = pygame.font.SysFont(None, 20)
        self.font_medium = pygame.font.SysFont(None, 24)
        self.font_large  = pygame.font.SysFont(None, 30)

        # resources
        self.credits = 0

        # mini-map placeholder
        self.mini_map_rect = pygame.Rect(self.x + 10, self.y + 50,
                                         self.width - 20, 150)

        # build menu
        self.categories            = ["Structures", "Defenses", "Units"]
        self.selected_category_idx = 0
        self.build_items = {
            "Structures": ["Power Plant", "Refinery", "Barracks"],
            "Defenses":   ["Turret", "Sandbags", "Wall"],
            "Units":      ["Soldier", "Tank", "APC"],
        }

        # layer buttons
        self.layer_buttons = [
            ("Planet",   self.x + 10,  self.y + 400, 60, 30),
            ("System",   self.x + 75,  self.y + 400, 60, 30),
            ("Galaxy",   self.x + 140, self.y + 400, 60, 30),
            ("Universe", self.x + 205, self.y + 400, 80, 30),
        ]

        # biped selector
        self.biped_names          = ["BP1", "BP2", "BP3", "BP4"]
        self.unlocked_biped_count = 2       # UnitManager will unlock slots
        self.selected_biped_idx   = 0
        self.biped_button_rects   = []      # rebuilt every frame

    # ────────────────────────────────────────────────────
    #  Public helpers
    # ────────────────────────────────────────────────────
    def update_resources(self, amount: int):
        self.credits = amount

    def unlock_biped(self, idx: int):
        """Called by UnitManager when a new biped is created (0-based)."""
        self.unlocked_biped_count = max(self.unlocked_biped_count, idx + 1)

    def refresh_bipeds(self, alive_count: int):
        """
        Called by UnitManager whenever its unit list shrinks
        (e.g. a biped dies).  Trim buttons & fix highlight.
        """
        self.unlocked_biped_count = min(alive_count, len(self.biped_names))
        if self.selected_biped_idx >= self.unlocked_biped_count:
            self.selected_biped_idx = max(0, self.unlocked_biped_count - 1)

    # ────────────────────────────────────────────────────
    #  Event handling
    # ────────────────────────────────────────────────────
    def handle_events(self, events, current_scene):
        self._scene = current_scene
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                if mx < self.x:
                    continue
                if self.mini_map_rect.collidepoint(mx, my):
                    return
                if self._handle_layer_buttons(mx, my):
                    return
                if self._handle_biped_buttons(mx, my):
                    return
                self._handle_build_menu_click(mx, my)

    def _handle_layer_buttons(self, mx, my):
        for lbl, bx, by, bw, bh in self.layer_buttons:
            if pygame.Rect(bx, by, bw, bh).collidepoint(mx, my):
                if self.manager and lbl in self.scenes:
                    self.manager.set_scene(self.scenes[lbl])
                return True
        return False

    def _handle_biped_buttons(self, mx, my):
        for idx, rect in enumerate(self.biped_button_rects):
            if rect.collidepoint(mx, my):
                prev = self.selected_biped_idx
                self.selected_biped_idx = idx
                ok = hasattr(self._scene, "unit_manager") and \
                     self._scene.unit_manager.select_unit_by_index(idx)
                if not ok:
                    self.selected_biped_idx = prev
                return True
        return False

    def _handle_build_menu_click(self, mx, my):
        for i in range(len(self.categories)):
            if pygame.Rect(self.x + 10 + i * 70, self.y + 210,
                           60, 30).collidepoint(mx, my):
                self.selected_category_idx = i
                return
        icon, gap, area_y = 48, 10, 250
        items = self.build_items[self.categories[self.selected_category_idx]]
        for idx, item in enumerate(items):
            row, col = divmod(idx, 2)
            bx = self.x + 10 + col * (icon + gap)
            by = area_y + row * (icon + gap)
            if pygame.Rect(bx, by, icon, icon).collidepoint(mx, my):
                print(f"Build request: {item}")
                return

    # ────────────────────────────────────────────────────
    #  Render
    # ────────────────────────────────────────────────────
    def render(self, surface):
        pygame.draw.rect(surface, (40, 40, 40),
                         (self.x, self.y, self.width, self.height))

        # credits
        cr = self.font_large.render(f"₡ {self.credits}", True, (255, 215, 0))
        surface.blit(cr, (self.x + 10, self.y + 10))

        # mini-map placeholder
        pygame.draw.rect(surface, (25, 25, 25), self.mini_map_rect)
        mm = self.font_small.render("Mini-Map", True, (200, 200, 200))
        surface.blit(mm, (self.mini_map_rect.centerx - mm.get_width()  // 2,
                          self.mini_map_rect.centery - mm.get_height() // 2))

        self._draw_build_tabs(surface)
        self._draw_build_icons(surface)
        self._draw_layer_buttons(surface)
        self._draw_biped_buttons(surface)
        self._draw_inventory(surface)

    # —— draw helpers ————————————————————————————————
    def _draw_build_tabs(self, surface):
        y = self.y + 210
        for i, cat in enumerate(self.categories):
            rect = pygame.Rect(self.x + 10 + i * 70, y, 60, 30)
            col  = (100, 100, 100) if i == self.selected_category_idx else (70, 70, 70)
            pygame.draw.rect(surface, col, rect)
            lbl = self.font_small.render(cat[:8], True, (255, 255, 255))
            surface.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                               rect.centery - lbl.get_height() // 2))

    def _draw_build_icons(self, surface):
        icon, gap, off_y = 48, 10, 250
        items = self.build_items[self.categories[self.selected_category_idx]]
        for idx, item in enumerate(items):
            row, col = divmod(idx, 2)
            bx = self.x + 10 + col * (icon + gap)
            by = off_y + row * (icon + gap)
            pygame.draw.rect(surface, (60, 60, 60), (bx, by, icon, icon))
            lbl = self.font_small.render(item[:6], True, (230, 230, 230))
            surface.blit(lbl, (bx + icon // 2 - lbl.get_width() // 2,
                               by + icon // 2 - lbl.get_height() // 2))

    def _draw_layer_buttons(self, surface):
        for lbl, bx, by, bw, bh in self.layer_buttons:
            pygame.draw.rect(surface, (30, 60, 120), (bx, by, bw, bh))
            txt = self.font_small.render(lbl, True, (255, 255, 255))
            surface.blit(txt, (bx + bw // 2 - txt.get_width() // 2,
                               by + bh // 2 - txt.get_height() // 2))

    def _draw_biped_buttons(self, surface):
        start_y, btn_w, btn_h, gap = self.y + 450, 60, 26, 8
        self.biped_button_rects.clear()
        for idx in range(self.unlocked_biped_count):
            name = self.biped_names[idx]
            bx = self.x + 10 + (idx % 2) * (btn_w + gap)
            by = start_y + (idx // 2) * (btn_h + gap)
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            self.biped_button_rects.append(rect)
            selected = idx == self.selected_biped_idx
            col = (100, 160, 100) if selected else (50, 110, 50)
            pygame.draw.rect(surface, col, rect)
            txt = self.font_small.render(name, True, (255, 255, 255))
            surface.blit(txt, (rect.centerx - txt.get_width() // 2,
                               rect.centery - txt.get_height() // 2))

    def _draw_inventory(self, surface):
        if not self._scene or not hasattr(self._scene, "inventory"):
            return
        inv    = self._scene.inventory
        base_y = self.y + 530
        title  = self.font_medium.render("Inventory", True, (255, 255, 255))
        surface.blit(title, (self.x + 10, base_y))
        line_h = 22
        for i, (res, amt) in enumerate(list(inv.items())[:self.INVENTORY_MAX_LINES]):
            txt = self.font_small.render(f"{res}: {amt}", True, (220, 220, 220))
            surface.blit(txt, (self.x + 20, base_y + (i + 1) * line_h))
        if len(inv) > self.INVENTORY_MAX_LINES:
            dots = self.font_small.render("…", True, (200, 200, 200))
            surface.blit(dots, (self.x + 20,
                                base_y + (self.INVENTORY_MAX_LINES + 1) * line_h))
