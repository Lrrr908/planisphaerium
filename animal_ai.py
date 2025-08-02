import math
import random


class AnimalAI:
    def __init__(self, animal_unit):
        self.animal = animal_unit
        
        # Movement stability tracking
        self.last_path_update = 0.0
        self.path_update_cooldown = 2.0  # Only update paths every 2 seconds
        self.movement_direction_x = 0.0  # Track overall movement direction
        self.movement_direction_y = 0.0
        self.direction_samples = []  # Track recent directions for stability

    def update(self, dt):
        """
        Called every frame from AnimalUnit.update()
        """
        seconds = dt * 0.001

        if not self.animal.alive:
            return

        # Update path timing
        self.last_path_update += seconds

        # Check hunger damage
        if self.animal.hunger >= 1.0:
            self.animal.health -= 0.5
            if self.animal.health <= 0:
                self.animal._die()
                return

        # Run current mission with consistent timing
        if self.animal.mission == "ATTACK":
            self.animal._attack_logic(dt)
        elif self.animal.mission == "FLEE":
            self._flee_logic(dt)
        elif self.animal.mission == "SEEK_FOOD":
            self._seek_food_logic(dt)
        elif self.animal.mission == "ROAM":
            self._update_roam(seconds)
        else:
            self._think()

        # Handle attack animation timer
        if self.animal.in_attack_animation:
            self.animal.attack_anim_timer -= seconds
            if self.animal.attack_anim_timer <= 0:
                self.animal.in_attack_animation = False

    def _think(self):
        # If low health, flee from enemies
        if self.animal.health < 3:
            enemy = self._find_nearest_enemy(radius=self.animal.territory_radius)
            if enemy:
                self.animal.target_unit = enemy
                self.animal.mission = "FLEE"
                return

        # Seek food if hungry
        if self.animal.hunger > 0.5:
            self.animal.mission = "SEEK_FOOD"
            return

        # Attack if aggressive
        if self.animal.aggression > 0.5:
            enemy = self._find_nearest_enemy(radius=self.animal.territory_radius)
            if enemy:
                self.animal.target_unit = enemy
                self.animal.mission = "ATTACK"
                return

        # Otherwise roam
        self.animal.mission = "ROAM"

    def _find_nearest_enemy(self, radius=5):
        nearest_unit = None
        nearest_dist = radius + 1

        # If carnivore, prefer hunting herbivores first
        if self.animal.diet == "carnivore":
            for other in self.animal.scene.animal_manager.animals:
                if other is self.animal or not other.alive:
                    continue
                if other.diet == "herbivore":
                    dist = math.hypot(
                        other.x_f - self.animal.x_f,
                        other.y_f - self.animal.y_f
                    )
                    if dist < nearest_dist:
                        nearest_unit = other
                        nearest_dist = dist
            if nearest_unit:
                return nearest_unit

        # Otherwise search all non-same-species units
        all_units = (
            self.animal.scene.unit_manager.units +
            self.animal.scene.animal_manager.animals
        )
        for unit in all_units:
            if unit is self.animal or not unit.alive:
                continue
            if getattr(unit, "species_id", None) == self.animal.species_id:
                continue

            dist = math.hypot(
                unit.x_f - self.animal.x_f,
                unit.y_f - self.animal.y_f
            )
            if dist < nearest_dist:
                nearest_unit = unit
                nearest_dist = dist

        return nearest_unit

    def _seek_food_logic(self, dt):
        # Convert dt to seconds consistently
        seconds = dt * 0.001 if dt > 1 else dt
        
        # Only update path if enough time has passed or no current path
        if (not self.animal.path_tiles or 
            self.animal.path_index >= len(self.animal.path_tiles) or
            self.last_path_update > self.path_update_cooldown):
            
            food_pos = self._find_nearest_food_tile(radius=self.animal.territory_radius * 2)
            if food_pos:
                path = self.animal.scene.find_path(
                    int(round(self.animal.x_f)),
                    int(round(self.animal.y_f)),
                    food_pos[0],
                    food_pos[1]
                )
                if path:
                    self.animal.path_tiles = path
                    self.animal.path_index = 0
                    self.last_path_update = 0.0
            else:
                self.animal.mission = "ROAM"
                return

        # Use consistent movement timing
        self._stable_move_update(seconds)

        if self.animal.path_index >= len(self.animal.path_tiles):
            # Eat!
            self.animal.hunger -= 0.4
            self.animal.hunger = max(0, self.animal.hunger)
            self.animal.mission = "IDLE"

    def _find_nearest_food_tile(self, radius=10):
        best_pos = None
        best_dist = radius + 1

        for y in range(
            max(0, int(self.animal.grid_y - radius)),
            min(self.animal.scene.map.height, int(self.animal.grid_y + radius))
        ):
            for x in range(
                max(0, int(self.animal.grid_x - radius)),
                min(self.animal.scene.map.width, int(self.animal.grid_x + radius))
            ):
                if self.animal.scene.forest_map[y][x] > 0:
                    dist = math.hypot(x - self.animal.x_f, y - self.animal.y_f)
                    if dist < best_dist:
                        best_pos = (x, y)
                        best_dist = dist
        return best_pos

    def _update_roam(self, seconds):
        self.animal.roam_timer += seconds
        
        # Only update roam path if enough time has passed
        if (self.animal.roam_timer > 5.0 and 
            self.last_path_update > self.path_update_cooldown):
            
            self.animal.roam_timer = 0.0
            self.last_path_update = 0.0
            
            hx, hy = self.animal.home_tile
            chosen = None
            for _ in range(10):
                rx = random.randint(hx - self.animal.territory_radius, hx + self.animal.territory_radius)
                ry = random.randint(hy - self.animal.territory_radius, hy + self.animal.territory_radius)
                rx = max(0, min(rx, self.animal.scene.map.width - 1))
                ry = max(0, min(ry, self.animal.scene.map.height - 1))
                if (rx, ry) not in self.animal.scene.blocked_tiles:
                    chosen = (rx, ry)
                    break
                    
            if chosen:
                path = self.animal.scene.find_path(
                    int(round(self.animal.x_f)),
                    int(round(self.animal.y_f)),
                    chosen[0],
                    chosen[1]
                )
                if path:
                    self.animal.path_tiles = path
                    self.animal.path_index = 0

        # Use consistent movement timing
        self._stable_move_update(seconds)

    def _flee_logic(self, dt):
        # Convert dt to seconds consistently
        seconds = dt * 0.001 if dt > 1 else dt
        
        if not self.animal.target_unit or not self.animal.target_unit.alive:
            self.animal.mission = "IDLE"
            return

        # Only update flee path occasionally to prevent jittery movement
        if self.last_path_update > self.path_update_cooldown:
            dx = self.animal.x_f - self.animal.target_unit.x_f
            dy = self.animal.y_f - self.animal.target_unit.y_f
            mag = math.hypot(dx, dy)

            if mag == 0:
                mag = 0.1

            escape_x = self.animal.x_f + (dx / mag) * 3
            escape_y = self.animal.y_f + (dy / mag) * 3

            escape_x = max(0, min(self.animal.scene.map.width - 1, escape_x))
            escape_y = max(0, min(self.animal.scene.map.height - 1, escape_y))

            path = self.animal.scene.find_path(
                int(round(self.animal.x_f)),
                int(round(self.animal.y_f)),
                int(round(escape_x)),
                int(round(escape_y))
            )
            if path:
                self.animal.path_tiles = path
                self.animal.path_index = 0
                self.last_path_update = 0.0

        # Use consistent movement timing
        self._stable_move_update(seconds)

        if self.animal.path_index >= len(self.animal.path_tiles):
            self.animal.mission = "IDLE"

    def _stable_move_update(self, seconds):
        """
        Wrapper around _update_move that ensures stable movement direction tracking
        """
        # Track movement direction for stability
        if self.animal.path_tiles and self.animal.path_index < len(self.animal.path_tiles):
            tx, ty = self.animal.path_tiles[self.animal.path_index]
            dx = tx - self.animal.x_f
            dy = ty - self.animal.y_f
            
            # Add to direction samples for smoothing
            self.direction_samples.append((dx, dy))
            if len(self.direction_samples) > 5:
                self.direction_samples.pop(0)
            
            # Calculate average direction to smooth out jitter
            if len(self.direction_samples) >= 3:
                avg_dx = sum(d[0] for d in self.direction_samples) / len(self.direction_samples)
                avg_dy = sum(d[1] for d in self.direction_samples) / len(self.direction_samples)
                
                # Only update movement direction if change is significant
                if abs(avg_dx) > 0.5:
                    self.movement_direction_x = avg_dx
                if abs(avg_dy) > 0.5:
                    self.movement_direction_y = avg_dy

        # Call the actual movement update
        self.animal._update_move(seconds)