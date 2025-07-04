"""
Optimal terrain zone validator using exhaustive search and wave simulation.
Places spawn and goal zones at the furthest valid positions from center that can reach each other.
"""

import math

from typing import List, Optional, Tuple, Set
from collections import deque
import rng
from config import get_config
from terrain.obstacle import FlowingTerrainObstacle
from .base import Zone


class OptimalTerrainValidator:
    """
    Optimal terrain validator that finds the furthest reachable spawn/goal positions.
    
    Algorithm:
    1. Generate all valid positions for spawn zone (no terrain collision)
    2. Sort by distance from canvas center (furthest first)
    3. Generate all valid positions for goal zone
    4. Sort by distance from canvas center (furthest first)  
    5. For each spawn position (starting with furthest), test goal positions
    6. Use wave simulation to verify reachability
    7. Return first valid pair (furthest spawn + furthest reachable goal)
    """
    
    def __init__(self, arena_width: int, arena_height: int):
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.center_x = arena_width / 2
        self.center_y = arena_height / 2
        
        cfg = get_config()
        self.marble_radius = cfg.simulation.MARBLE_RADIUS
        
        # Zone sizing - spawn zone needs space for 8 marbles, goal can be small
        self.spawn_zone_radius = self.marble_radius * 2.5  # Enough for 8 marbles
        self.goal_zone_radius = self.marble_radius * 1.5   # Small goal zone
        
        # Wave simulation parameters - use finer resolution for better pathfinding
        self.wave_step_size = self.marble_radius * 0.4  # Much finer resolution for wave simulation
        
    def validate_indiv_race_terrain(self, terrain_obstacles: List[FlowingTerrainObstacle]) -> Optional[Tuple[Zone, Zone]]:
        """
        Find optimal spawn and goal zones using exhaustive search and wave simulation.
        """
        if not terrain_obstacles:
            return None
            
        terrain = terrain_obstacles[0]
        
        print("Starting optimal terrain validation...")
        print(f"Arena: {self.arena_width}x{self.arena_height}, Center: ({self.center_x}, {self.center_y})")
        print(f"Spawn zone radius: {self.spawn_zone_radius}, Goal zone radius: {self.goal_zone_radius}")
        
        # Step 1: Find all valid spawn positions
        spawn_candidates = self._find_all_valid_positions(terrain, self.spawn_zone_radius, "spawn")
        if not spawn_candidates:
            print("No valid spawn positions found")
            return None
            
        print(f"Found {len(spawn_candidates)} valid spawn positions")
        
        # Step 2: Find all valid goal positions  
        goal_candidates = self._find_all_valid_positions(terrain, self.goal_zone_radius, "goal")
        if not goal_candidates:
            print("No valid goal positions found")
            return None
            
        print(f"Found {len(goal_candidates)} valid goal positions")
        
        # Step 3: Sort spawn candidates by distance from center (furthest first)
        spawn_candidates.sort(key=lambda pos: self._distance_from_center(pos[0], pos[1]), reverse=True)
        
        print(f"Testing reachability with spawn furthest from center, goal furthest from spawn...")
        
        # Step 4: Test reachability between spawn and goal positions
        for i, spawn_pos in enumerate(spawn_candidates):
            spawn_x, spawn_y = spawn_pos
            spawn_distance = self._distance_from_center(spawn_x, spawn_y)
            
            if i % 10 == 0:  # Progress update every 10 spawn positions
                print(f"Testing spawn position {i+1}/{len(spawn_candidates)} (distance from center: {spawn_distance:.1f})")
            
            # Sort goal candidates by distance from this specific spawn position (furthest first)
            goal_candidates.sort(key=lambda pos: self._distance_between_points(spawn_pos, pos), reverse=True)
            
            for j, goal_pos in enumerate(goal_candidates):
                goal_x, goal_y = goal_pos
                goal_distance_from_center = self._distance_from_center(goal_x, goal_y)
                goal_distance_from_spawn = self._distance_between_points(spawn_pos, goal_pos)
                
                # Use wave simulation to test reachability
                if self._can_reach_via_wave_simulation(terrain, spawn_pos, goal_pos):
                    # Found a valid pair!
                    spawn_zone = Zone(spawn_x, spawn_y, self.spawn_zone_radius, "spawn")
                    goal_zone = Zone(goal_x, goal_y, self.goal_zone_radius, "goal")
                    
                    print(f"Success! Found optimal zones:")
                    print(f"  Spawn: ({spawn_x:.1f}, {spawn_y:.1f}) distance from center: {spawn_distance:.1f}")
                    print(f"  Goal: ({goal_x:.1f}, {goal_y:.1f}) distance from center: {goal_distance_from_center:.1f}")
                    print(f"  Distance between zones: {goal_distance_from_spawn:.1f}")
                    
                    return spawn_zone, goal_zone
        
        print("No reachable spawn/goal pair found")
        return None
    
    def _find_all_valid_positions(self, terrain: FlowingTerrainObstacle, zone_radius: float, zone_type: str) -> List[Tuple[float, float]]:
        """
        Find all valid positions for a zone by testing every position on the terrain.
        Returns list of (x, y) coordinates that don't intersect with terrain.
        """
        valid_positions = []
        
        # Use a grid step based on zone radius to ensure good coverage
        step_size = zone_radius * 0.3  # Overlap positions for thorough coverage
        
        # Calculate bounds with zone radius buffer
        min_x = zone_radius
        max_x = self.arena_width - zone_radius
        min_y = zone_radius  
        max_y = self.arena_height - zone_radius
        
        x = min_x
        while x <= max_x:
            y = min_y
            while y <= max_y:
                if self._is_zone_position_valid(terrain, x, y, zone_radius):
                    valid_positions.append((x, y))
                y += step_size
            x += step_size
            
        print(f"Tested grid from ({min_x}, {min_y}) to ({max_x}, {max_y}) with step {step_size:.1f}")
        print(f"Found {len(valid_positions)} valid {zone_type} positions")
        
        return valid_positions
    
    def _is_zone_position_valid(self, terrain: FlowingTerrainObstacle, x: float, y: float, zone_radius: float) -> bool:
        """
        Check if a zone position is valid (doesn't intersect terrain).
        Tests multiple points within the zone for thorough collision detection.
        Also ensures there's enough surrounding open space to prevent isolated pockets.
        """
        # Test center
        if terrain.check_collision(x, y, self.marble_radius):
            return False
        
        # Test points around the zone perimeter with higher density
        num_test_points = 16  # More points for better detection
        for i in range(num_test_points):
            angle = (2 * math.pi * i) / num_test_points
            test_x = x + (zone_radius * 0.95) * math.cos(angle)  # Almost at edge
            test_y = y + (zone_radius * 0.95) * math.sin(angle)
            
            if terrain.check_collision(test_x, test_y, self.marble_radius):
                return False
        
        # Test multiple concentric circles inside the zone
        for radius_factor in [0.2, 0.4, 0.6, 0.8]:
            num_circle_points = 8
            for i in range(num_circle_points):
                angle = (2 * math.pi * i) / num_circle_points
                test_x = x + (zone_radius * radius_factor) * math.cos(angle)
                test_y = y + (zone_radius * radius_factor) * math.sin(angle)
                
                if terrain.check_collision(test_x, test_y, self.marble_radius):
                    return False
        
        # Additional validation: check that the zone has enough nearby accessible area
        # This helps prevent placement in tiny isolated pockets
        accessible_points = 0
        test_radius = zone_radius * 1.5  # Check slightly beyond the zone
        num_access_tests = 12
        
        for i in range(num_access_tests):
            angle = (2 * math.pi * i) / num_access_tests
            test_x = x + test_radius * math.cos(angle)
            test_y = y + test_radius * math.sin(angle)
            
            # Only test if within arena bounds
            if (0 <= test_x < terrain.grid_width * terrain.scale_x and 
                0 <= test_y < terrain.grid_height * terrain.scale_y):
                if not terrain.check_collision(test_x, test_y, self.marble_radius):
                    accessible_points += 1
        
        # Require at least 50% of surrounding area to be accessible
        required_accessible = num_access_tests * 0.5
        if accessible_points < required_accessible:
            return False
        
        return True
    
    def _distance_from_center(self, x: float, y: float) -> float:
        """Calculate distance from center of canvas"""
        return math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)
    
    def _distance_between_points(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance between two points"""
        x1, y1 = point1
        x2, y2 = point2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    def _can_reach_via_wave_simulation(self, terrain: FlowingTerrainObstacle, start_pos: Tuple[float, float], goal_pos: Tuple[float, float]) -> bool:
        """
        Use wave simulation (BFS) to determine if goal is reachable from start.
        This simulates a wave expanding from the start position until it reaches the goal.
        """
        start_x, start_y = start_pos
        goal_x, goal_y = goal_pos
        
        # Convert to grid coordinates for wave simulation
        grid_start_x = int(start_x / self.wave_step_size)
        grid_start_y = int(start_y / self.wave_step_size)
        grid_goal_x = int(goal_x / self.wave_step_size)
        grid_goal_y = int(goal_y / self.wave_step_size)
        
        # Calculate Manhattan distance for early termination if too far
        max_distance = int((self.arena_width + self.arena_height) / self.wave_step_size)
        
        # BFS wave simulation
        visited = set()
        queue = deque([(grid_start_x, grid_start_y, 0)])  # Add distance tracking
        visited.add((grid_start_x, grid_start_y))
        
        # 8-directional movement (including diagonals)
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        
        while queue:
            current_x, current_y, distance = queue.popleft()
            
            # Check if we reached the goal (allow small tolerance)
            goal_distance = abs(current_x - grid_goal_x) + abs(current_y - grid_goal_y)
            if goal_distance <= 2:  # Allow some tolerance for goal detection
                return True
            
            # Prevent infinite search
            if distance > max_distance:
                continue
            
            # Expand to neighbors
            for dx, dy in directions:
                next_x = current_x + dx
                next_y = current_y + dy
                
                if (next_x, next_y) in visited:
                    continue
                
                # Convert back to world coordinates for collision check
                world_x = next_x * self.wave_step_size
                world_y = next_y * self.wave_step_size
                
                # Check bounds with proper margin
                if (world_x < self.marble_radius or world_x >= self.arena_width - self.marble_radius or 
                    world_y < self.marble_radius or world_y >= self.arena_height - self.marble_radius):
                    continue
                
                # Check terrain collision with marble radius
                if terrain.check_collision(world_x, world_y, self.marble_radius):
                    continue
                
                # Add to queue
                visited.add((next_x, next_y))
                queue.append((next_x, next_y, distance + 1))
        
        # Goal not reachable
        return False
