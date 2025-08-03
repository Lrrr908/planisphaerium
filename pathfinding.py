"""
A* Pathfinding System for Isometric Grid
"""

from typing import List, Tuple, Set, Dict, Optional
import heapq
import math

class Node:
    """A node in the pathfinding grid"""
    def __init__(self, x: int, y: int, g_cost: float = float('inf'), h_cost: float = 0):
        self.x = x
        self.y = y
        self.g_cost = g_cost  # Cost from start to this node
        self.h_cost = h_cost  # Heuristic cost from this node to goal
        self.f_cost = g_cost + h_cost  # Total cost
        self.parent: Optional[Node] = None
        
    def __lt__(self, other):
        return self.f_cost < other.f_cost
        
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
        
    def __hash__(self):
        return hash((self.x, self.y))

class Pathfinder:
    """A* Pathfinding implementation for isometric grid"""
    
    def __init__(self, grid_width: int, grid_height: int):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.obstacles: Set[Tuple[int, int]] = set()
        
    def add_obstacle(self, x: int, y: int):
        """Add an obstacle at the given position"""
        self.obstacles.add((x, y))
        
    def remove_obstacle(self, x: int, y: int):
        """Remove an obstacle at the given position"""
        self.obstacles.discard((x, y))
        
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a position is walkable"""
        # Check bounds
        if not (-self.grid_width//2 <= x < self.grid_width//2 and 
                -self.grid_height//2 <= y < self.grid_height//2):
            return False
        # Check obstacles
        return (x, y) not in self.obstacles
        
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Get walkable neighbors of a position"""
        neighbors = []
        # 8-directional movement (including diagonals)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                new_x, new_y = x + dx, y + dy
                if self.is_walkable(new_x, new_y):
                    neighbors.append((new_x, new_y))
        return neighbors
        
    def heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Calculate heuristic distance between two points (Manhattan distance)"""
        return abs(x1 - x2) + abs(y1 - y2)
        
    def find_path(self, start_x: int, start_y: int, goal_x: int, goal_y: int) -> Optional[List[Tuple[int, int]]]:
        """Find path from start to goal using A* algorithm"""
        if not self.is_walkable(start_x, start_y) or not self.is_walkable(goal_x, goal_y):
            return None
            
        # Initialize start node
        start_node = Node(start_x, start_y, 0, self.heuristic(start_x, start_y, goal_x, goal_y))
        
        # Open and closed sets
        open_set = [start_node]
        closed_set: Set[Tuple[int, int]] = set()
        
        # Keep track of all nodes for path reconstruction
        all_nodes: Dict[Tuple[int, int], Node] = {(start_x, start_y): start_node}
        
        while open_set:
            # Get node with lowest f_cost
            current = heapq.heappop(open_set)
            
            # Check if we reached the goal
            if current.x == goal_x and current.y == goal_y:
                return self.reconstruct_path(current)
                
            # Add to closed set
            closed_set.add((current.x, current.y))
            
            # Check neighbors
            for neighbor_x, neighbor_y in self.get_neighbors(current.x, current.y):
                if (neighbor_x, neighbor_y) in closed_set:
                    continue
                    
                # Calculate movement cost (diagonal movement costs more)
                dx, dy = abs(neighbor_x - current.x), abs(neighbor_y - current.y)
                movement_cost = 1.4 if dx == 1 and dy == 1 else 1.0
                new_g_cost = current.g_cost + movement_cost
                
                # Get or create neighbor node
                neighbor_key = (neighbor_x, neighbor_y)
                if neighbor_key in all_nodes:
                    neighbor = all_nodes[neighbor_key]
                else:
                    neighbor = Node(neighbor_x, neighbor_y)
                    neighbor.h_cost = self.heuristic(neighbor_x, neighbor_y, goal_x, goal_y)
                    all_nodes[neighbor_key] = neighbor
                    
                # Check if this path is better
                if new_g_cost < neighbor.g_cost:
                    neighbor.parent = current
                    neighbor.g_cost = new_g_cost
                    neighbor.f_cost = new_g_cost + neighbor.h_cost
                    
                    # Add to open set if not already there
                    if neighbor_key not in [(n.x, n.y) for n in open_set]:
                        heapq.heappush(open_set, neighbor)
                        
        # No path found
        return None
        
    def reconstruct_path(self, end_node: Node) -> List[Tuple[int, int]]:
        """Reconstruct path from end node back to start"""
        path = []
        current = end_node
        while current:
            path.append((current.x, current.y))
            current = current.parent
        return list(reversed(path))
        
    def get_next_step(self, start_x: int, start_y: int, goal_x: int, goal_y: int) -> Optional[Tuple[int, int]]:
        """Get the next step towards the goal (for smooth movement)"""
        path = self.find_path(start_x, start_y, goal_x, goal_y)
        if path and len(path) > 1:
            return path[1]  # Return the next step
        return None 