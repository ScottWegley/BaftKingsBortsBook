"""
Fast terrain zone validator with optimized algorithms.
"""

from typing import List, Optional, Tuple
import math
import rng
from config import get_config
from terrain.obstacle import FlowingTerrainObstacle
from .base import Zone
import heapq


class TerrainZoneValidator:
    """Validates terrain for game mode requirements with fast algorithms"""
    
    def __init__(self, arena_width: int, arena_height: int):
        self.arena_width = arena_width
        self.arena_height = arena_height
    
    def validate_indiv_race_terrain(self, terrain_obstacles: List[FlowingTerrainObstacle]) -> Optional[Tuple[Zone, Zone]]:
        """
        Fast validation for individual race mode with optimized zone placement.
        """
        if not terrain_obstacles:
            return None
            
        terrain = terrain_obstacles[0]        
        cfg = get_config()
        marble_radius = cfg.simulation.MARBLE_RADIUS
        min_path_width = marble_radius * 1.5  # 1.5x marble diameter clearance
        
        # Fast zone placement - try strategic positions first, then refine
        zones = self._find_zones_fast(terrain, marble_radius, min_path_width)
        if zones:
            spawn_zone, goal_zone = zones
            # Quick path validation
            if self._validate_path_fast(terrain, spawn_zone, goal_zone, min_path_width):
                return spawn_zone, goal_zone
            
        return None

    def _calculate_score(self, distance: float, complexity_score: float) -> float:
        """
        Calculate score based on distance and complexity.
        """
        max_distance = math.sqrt(self.arena_width**2 + self.arena_height**2)
        distance_score = distance / max_distance

        # Final score: 80% distance, 20% complexity (prioritize distance heavily)
        return distance_score * 0.8 + complexity_score * 0.2

    def _find_zones_fast(self, terrain: FlowingTerrainObstacle, marble_radius: float, min_path_width: float) -> Optional[Tuple[Zone, Zone]]:
        """
        Simplified zone placement logic.
        """
        spawn_zone_radius = marble_radius * 4
        goal_zone_radius = marble_radius * 3
        min_edge_distance = max(spawn_zone_radius, goal_zone_radius) + 20

        corner_positions = [
            (min_edge_distance, min_edge_distance),
            (self.arena_width - min_edge_distance, min_edge_distance),
            (min_edge_distance, self.arena_height - min_edge_distance),
            (self.arena_width - min_edge_distance, self.arena_height - min_edge_distance),
        ]

        best_score = 0
        best_zones = None

        for spawn_pos in corner_positions:
            if not self._is_position_valid(terrain, spawn_pos[0], spawn_pos[1], spawn_zone_radius, marble_radius):
                continue

            spawn_zone = Zone(spawn_pos[0], spawn_pos[1], spawn_zone_radius, "spawn")

            for goal_pos in corner_positions:
                if spawn_pos == goal_pos:
                    continue

                if not self._is_position_valid(terrain, goal_pos[0], goal_pos[1], goal_zone_radius, marble_radius):
                    continue

                goal_zone = Zone(goal_pos[0], goal_pos[1], goal_zone_radius, "goal")

                # Use Euclidean distance for now (simpler and more reliable)
                euclidean_distance = math.sqrt((goal_pos[0] - spawn_pos[0])**2 + (goal_pos[1] - spawn_pos[1])**2)

                complexity_score = self._calculate_path_complexity(terrain, spawn_zone, goal_zone, min_path_width)
                total_score = self._calculate_score(euclidean_distance, complexity_score)

                if total_score > best_score:
                    best_score = total_score
                    best_zones = (spawn_zone, goal_zone)

        return best_zones

    def _try_edge_positions(self, terrain: FlowingTerrainObstacle, marble_radius: float, min_path_width: float) -> Optional[Tuple[Zone, Zone]]:
        """
        Simplified edge position logic.
        """
        spawn_zone_radius = marble_radius * 4
        goal_zone_radius = marble_radius * 3
        edge_buffer = max(spawn_zone_radius, goal_zone_radius) + 20

        edge_positions = {
            "top": [(self.arena_width * i / 4, edge_buffer) for i in range(1, 4)],
            "bottom": [(self.arena_width * i / 4, self.arena_height - edge_buffer) for i in range(1, 4)],
            "left": [(edge_buffer, self.arena_height * i / 4) for i in range(1, 4)],
            "right": [(self.arena_width - edge_buffer, self.arena_height * i / 4) for i in range(1, 4)],
        }

        best_score = 0
        best_zones = None

        for side, spawn_positions in edge_positions.items():
            goal_positions = edge_positions["bottom"] if side == "top" else edge_positions["top"]

            for spawn_pos in spawn_positions:
                if not self._is_position_valid(terrain, spawn_pos[0], spawn_pos[1], spawn_zone_radius, marble_radius):
                    continue

                spawn_zone = Zone(spawn_pos[0], spawn_pos[1], spawn_zone_radius, "spawn")

                for goal_pos in goal_positions:
                    if not self._is_position_valid(terrain, goal_pos[0], goal_pos[1], goal_zone_radius, marble_radius):
                        continue

                    goal_zone = Zone(goal_pos[0], goal_pos[1], goal_zone_radius, "goal")

                    # Use Euclidean distance for now
                    euclidean_distance = math.sqrt((goal_pos[0] - spawn_pos[0])**2 + (goal_pos[1] - spawn_pos[1])**2)

                    complexity_score = self._calculate_path_complexity(terrain, spawn_zone, goal_zone, min_path_width)
                    total_score = self._calculate_score(euclidean_distance, complexity_score)

                    if total_score > best_score:
                        best_score = total_score
                        best_zones = (spawn_zone, goal_zone)

        return best_zones
    
    def _try_random_positions(self, terrain: FlowingTerrainObstacle, marble_radius: float, min_path_width: float, max_attempts: int = 100) -> Optional[Tuple[Zone, Zone]]:
        """
        Simplified random position logic.
        """
        spawn_zone_radius = marble_radius * 4
        goal_zone_radius = marble_radius * 3
        min_edge_distance = max(spawn_zone_radius, goal_zone_radius) + 20

        best_score = 0
        best_zones = None

        for _ in range(max_attempts):
            spawn_x = rng.uniform(min_edge_distance, self.arena_width - min_edge_distance)
            spawn_y = rng.uniform(min_edge_distance, self.arena_height - min_edge_distance)

            if not self._is_position_valid(terrain, spawn_x, spawn_y, spawn_zone_radius, marble_radius):
                continue

            spawn_zone = Zone(spawn_x, spawn_y, spawn_zone_radius, "spawn")

            for _ in range(20):
                goal_x = rng.uniform(min_edge_distance, self.arena_width - min_edge_distance)
                goal_y = rng.uniform(min_edge_distance, self.arena_height - min_edge_distance)

                if not self._is_position_valid(terrain, goal_x, goal_y, goal_zone_radius, marble_radius):
                    continue

                goal_zone = Zone(goal_x, goal_y, goal_zone_radius, "goal")

                # Use Euclidean distance for now
                euclidean_distance = math.sqrt((goal_x - spawn_x)**2 + (goal_y - spawn_y)**2)

                complexity_score = self._calculate_path_complexity(terrain, spawn_zone, goal_zone, min_path_width)
                total_score = self._calculate_score(euclidean_distance, complexity_score)

                if total_score > best_score:
                    best_score = total_score
                    best_zones = (spawn_zone, goal_zone)
                    break

        return best_zones
    
    def _is_position_valid(self, terrain: FlowingTerrainObstacle, x: float, y: float, zone_radius: float, marble_radius: float) -> bool:
        """Fast position validation with minimal checks"""
        # Bounds check
        if (x - zone_radius < 0 or x + zone_radius >= self.arena_width or 
            y - zone_radius < 0 or y + zone_radius >= self.arena_height):
            return False
        
        # Quick terrain collision check - only check center and a few key points
        test_points = [
            (x, y),  # Center
            (x - zone_radius * 0.5, y),  # Left
            (x + zone_radius * 0.5, y),  # Right
            (x, y - zone_radius * 0.5),  # Top
            (x, y + zone_radius * 0.5),  # Bottom
        ]
        
        for test_x, test_y in test_points:
            if terrain.check_collision(test_x, test_y, marble_radius):
                return False
        
        return True
    
    def _validate_path_fast(self, terrain: FlowingTerrainObstacle, spawn_zone: Zone, goal_zone: Zone, min_width: float) -> bool:
        """
        Relaxed path validation to allow more flexibility.
        """
        start_x, start_y = spawn_zone.center_x, spawn_zone.center_y
        end_x, end_y = goal_zone.center_x, goal_zone.center_y

        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance == 0:
            return False

        dx /= distance
        dy /= distance

        step_size = min_width * 0.8
        num_steps = int(distance / step_size)

        if num_steps < 3:
            return False

        clear_samples = 0
        for i in range(1, num_steps):
            sample_x = start_x + dx * i * step_size
            sample_y = start_y + dy * i * step_size

            if terrain.check_collision(sample_x, sample_y, min_width / 2):
                return False

            clear_samples += 1

        return clear_samples >= num_steps * 0.5  # Require 50% clear path (more lenient)
    
    def _calculate_path_complexity(self, terrain: FlowingTerrainObstacle, spawn_zone: Zone, goal_zone: Zone, min_width: float) -> float:
        """
        Calculate terrain complexity score along the path between zones.
        Returns a score from 0.0 to 1.0 where higher values indicate more interesting terrain.
        """
        start_x, start_y = spawn_zone.center_x, spawn_zone.center_y
        end_x, end_y = goal_zone.center_x, goal_zone.center_y
        
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance == 0:
            return 0.0
        
        dx /= distance
        dy /= distance
        
        step_size = min_width * 0.5
        num_steps = int(distance / step_size)
        
        if num_steps < 2:
            return 0.0
        
        complexity_points = 0
        total_samples = 0
        
        # Perpendicular directions for sampling around the path
        perp_dx = -dy
        perp_dy = dx
        
        for i in range(1, num_steps):
            sample_x = start_x + dx * i * step_size
            sample_y = start_y + dy * i * step_size
            
            # Sample in multiple directions around each point
            terrain_density = 0
            sample_count = 0
            
            # Check in a cross pattern around the path
            for angle_offset in [0, 45, 90, 135, 180, 225, 270, 315]:
                angle_rad = math.radians(angle_offset)
                check_distance = min_width * 1.5
                
                check_x = sample_x + math.cos(angle_rad) * check_distance
                check_y = sample_y + math.sin(angle_rad) * check_distance
                
                if (0 <= check_x < self.arena_width and 0 <= check_y < self.arena_height):
                    sample_count += 1
                    if terrain.check_collision(check_x, check_y, min_width / 4):
                        terrain_density += 1
            
            if sample_count > 0:
                # Calculate local terrain density (0.0 to 1.0)
                local_density = terrain_density / sample_count
                
                # Ideal complexity is around 0.4-0.6 (some terrain but not too dense)
                if 0.2 <= local_density <= 0.8:
                    complexity_points += local_density
                elif local_density > 0.8:
                    complexity_points += 0.3  # Too dense, but still some points
                
                total_samples += 1
        
        if total_samples == 0:
            return 0.0
        
        # Normalize to 0-1 range
        average_complexity = complexity_points / total_samples
        return min(average_complexity, 1.0)
    
    def _calculate_traversable_distance(self, terrain: FlowingTerrainObstacle, start: Tuple[int, int], end: Tuple[int, int]) -> float:
        """
        Calculate the traversable distance between two points using A* pathfinding.
        Returns the distance or float('inf') if no path exists.
        """
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == end:
                return g_score[current]

            for neighbor in terrain.get_neighbors(current):
                tentative_g_score = g_score[current] + terrain.get_cost(current, neighbor)

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + math.sqrt((end[0] - neighbor[0])**2 + (end[1] - neighbor[1])**2)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return float('inf')  # No path found
