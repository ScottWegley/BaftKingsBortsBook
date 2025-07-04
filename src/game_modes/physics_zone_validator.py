"""
Physics-based zone placement using marble simulation.
"""

import math
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Optional, Tuple, Set
import rng
from config import get_config
from terrain.obstacle import FlowingTerrainObstacle
from physics.marble import Marble
from physics.collision import CollisionDetector
from .base import Zone


class PhysicsZoneValidator:
    """Uses physics simulation to find optimal spawn/goal positions"""
    
    def __init__(self, arena_width: int, arena_height: int):
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.cfg = get_config()
        self.marble_radius = self.cfg.simulation.MARBLE_RADIUS
        self.marble_speed = self.cfg.simulation.MARBLE_SPEED
        self.collision_detector = CollisionDetector()
    
    def find_optimal_zones(self, terrain_obstacles: List[FlowingTerrainObstacle]) -> Optional[Tuple[Zone, Zone]]:
        """
        Find optimal spawn and goal zones using physics simulation.
        """
        if not terrain_obstacles:
            return None
        
        terrain = terrain_obstacles[0]
        
        # Step 1: Find valid center position for initial spawn
        center_position = self._find_valid_center_position(terrain)
        if not center_position:
            return None
        
        # Try multiple attempts with progressively more relaxed requirements
        max_attempts = 5
        for attempt in range(max_attempts):
            print(f"\n=== Attempt {attempt + 1}/{max_attempts} ===")
            
            # Step 2: Simulate from center to find optimal spawn position
            spawn_position = self._simulate_to_find_farthest(center_position, terrain, simulation_name="spawn")
            if not spawn_position:
                print(f"Attempt {attempt + 1}: Failed to find spawn position")
                continue
            
            # Step 3: Simulate from spawn to find optimal goal position
            goal_position = self._simulate_to_find_farthest(spawn_position, terrain, simulation_name="goal")
            if not goal_position:
                print(f"Attempt {attempt + 1}: Failed to find goal position")
                continue
            
            # Step 4: Validate distance and create zones
            distance = math.sqrt((goal_position[0] - spawn_position[0])**2 + 
                               (goal_position[1] - spawn_position[1])**2)
            
            # Relax distance requirements on later attempts
            distance_factor = max(0.15, self.cfg.terrain.MIN_SPAWN_GOAL_DISTANCE_FACTOR - (attempt * 0.05))
            min_distance = distance_factor * math.sqrt(self.arena_width**2 + self.arena_height**2)
            
            if distance < min_distance:
                print(f"Attempt {attempt + 1}: Distance {distance:.1f} too small (min: {min_distance:.1f})")
                continue
            
            print(f"Distance validation passed: {distance:.1f} >= {min_distance:.1f}")
            
            # Create zones with progressively smaller radii on later attempts
            size_reduction = attempt * 0.2
            spawn_zone_radius = max(self.marble_radius, self.marble_radius * (2.0 - size_reduction))
            goal_zone_radius = max(self.marble_radius * 0.8, self.marble_radius * (1.5 - size_reduction))
            
            print(f"Attempt {attempt + 1}: Using spawn radius {spawn_zone_radius:.1f}, goal radius {goal_zone_radius:.1f}")
            
            # Final validation - ensure zones don't intersect terrain
            spawn_valid = self._is_zone_valid(terrain, spawn_position, spawn_zone_radius)
            goal_valid = self._is_zone_valid(terrain, goal_position, goal_zone_radius)
            
            print(f"Spawn zone valid: {spawn_valid}, Goal zone valid: {goal_valid}")
            
            if spawn_valid and goal_valid:
                spawn_zone = Zone(spawn_position[0], spawn_position[1], spawn_zone_radius, "spawn")
                goal_zone = Zone(goal_position[0], goal_position[1], goal_zone_radius, "goal")
                
                print(f"Success on attempt {attempt + 1}! Spawn: ({spawn_position[0]:.1f}, {spawn_position[1]:.1f}), "
                      f"Goal: ({goal_position[0]:.1f}, {goal_position[1]:.1f}), Distance: {distance:.1f}")
                
                return spawn_zone, goal_zone
            else:
                print(f"Attempt {attempt + 1}: Zone validation failed - zones intersect with terrain")
        
        print("All attempts failed to find valid zones")
        return None
    
    def _find_valid_center_position(self, terrain: FlowingTerrainObstacle) -> Optional[Tuple[float, float]]:
        """Find the closest valid position to the arena center"""
        center_x = self.arena_width / 2
        center_y = self.arena_height / 2
        
        # First try the exact center
        if not terrain.check_collision(center_x, center_y, self.marble_radius):
            return (center_x, center_y)
        
        # Start from center and spiral outward to find valid position
        max_search_radius = min(self.arena_width, self.arena_height) // 3
        
        for radius in range(2, max_search_radius, 2):  # Fine-grained search
            for angle_deg in range(0, 360, 8):  # Check every 8 degrees for better coverage
                angle_rad = math.radians(angle_deg)
                test_x = center_x + radius * math.cos(angle_rad)
                test_y = center_y + radius * math.sin(angle_rad)
                
                # Check bounds with margin
                margin = self.marble_radius * 2
                if (margin <= test_x <= self.arena_width - margin and
                    margin <= test_y <= self.arena_height - margin):
                    
                    # Check if position is valid (not in terrain)
                    if not terrain.check_collision(test_x, test_y, self.marble_radius):
                        print(f"Found valid center position: ({test_x:.1f}, {test_y:.1f}) at radius {radius}")
                        return (test_x, test_y)
        
        print("No valid center position found!")
        return None
    
    def _simulate_to_find_farthest(self, start_position: Tuple[float, float], 
                                   terrain: FlowingTerrainObstacle, 
                                   simulation_name: str = "sim") -> Optional[Tuple[float, float]]:
        """
        Simulate multiple marbles from start position to find the farthest reachable point.
        Uses systematic exploration with multiple marbles to ensure we reach very far positions.
        """
        start_x, start_y = start_position
        num_marbles = 24  # More marbles for better exploration
        simulation_steps = 15000  # Longer simulation for thorough exploration
        timestep = self.cfg.simulation.FIXED_TIMESTEP
        
        print(f"Running {simulation_name} simulation from ({start_x:.1f}, {start_y:.1f})...")
        print(f"Using {num_marbles} marbles for {simulation_steps} steps each")
        
        farthest_distance = 0
        farthest_position = None
        all_positions = []  # Track all final positions for analysis
        
        # Try multiple marbles with systematic initial directions
        for marble_idx in range(num_marbles):
            # More diverse direction distribution to avoid clustering
            if marble_idx < num_marbles // 2:
                # First half: systematic directions
                base_angle = marble_idx * 360 / (num_marbles // 2)
                angle = base_angle + rng.uniform(-20, 20)  # Larger random variation
            else:
                # Second half: fully random directions for diversity
                angle = rng.uniform(0, 360)
            
            angle_rad = math.radians(angle)
            
            # Create marble with specific direction and varied speed
            speed_variation = rng.uniform(0.8, 1.3)  # Larger speed variation for exploration
            marble = Marble(
                x=start_x,
                y=start_y,
                radius=self.marble_radius,
                color=(255, 0, 0),
                speed=self.marble_speed * speed_variation,
                initial_angle=angle_rad
            )
            
            # Simulate marble movement with enhanced exploration
            max_distance_this_marble = 0
            best_position_this_marble = (start_x, start_y)
            stuck_counter = 0
            last_position = (start_x, start_y)
            
            for step in range(simulation_steps):
                # Update marble position (handles boundary collisions)
                marble.update(timestep, self.arena_width, self.arena_height)
                
                # Handle terrain collisions with energy preservation
                if terrain.check_collision(marble.x, marble.y, marble.radius):
                    # Get collision normal and reflect
                    normal_x, normal_y = terrain.get_collision_normal(marble.x, marble.y)
                    
                    # Reflect velocity with slight energy retention
                    dot_product = marble.velocity_x * normal_x + marble.velocity_y * normal_y
                    marble.velocity_x -= 2 * dot_product * normal_x
                    marble.velocity_y -= 2 * dot_product * normal_y
                    
                    # Push marble out of terrain
                    push_distance = self.marble_radius * 1.2
                    marble.x += normal_x * push_distance
                    marble.y += normal_y * push_distance
                    
                    # Ensure within bounds
                    marble.x = max(marble.radius, min(self.arena_width - marble.radius, marble.x))
                    marble.y = max(marble.radius, min(self.arena_height - marble.radius, marble.y))
                    
                    # Re-normalize velocity to maintain consistent speed
                    marble._normalize_velocity()
                
                # Check if this is the farthest position, but penalize positions too close to edges
                distance = math.sqrt((marble.x - start_x)**2 + (marble.y - start_y)**2)
                
                # Apply edge penalty to discourage positions too close to boundaries
                min_zone_radius = self.marble_radius * 2.0  # Estimate minimum zone size needed
                required_margin = min_zone_radius + 25  # Larger buffer for zone placement
                
                edge_penalty = 0
                # Calculate distance from each edge
                dist_to_left = marble.x
                dist_to_right = self.arena_width - marble.x
                dist_to_top = marble.y
                dist_to_bottom = self.arena_height - marble.y
                
                min_edge_distance = min(dist_to_left, dist_to_right, dist_to_top, dist_to_bottom)
                
                # Apply stronger penalty if too close to any edge
                if min_edge_distance < required_margin:
                    edge_penalty = (required_margin - min_edge_distance) * 4  # Stronger penalty factor
                
                # Additional penalty for being in corners
                corner_penalty = 0
                corner_distance = min(
                    math.sqrt(marble.x**2 + marble.y**2),  # Top-left corner
                    math.sqrt((self.arena_width - marble.x)**2 + marble.y**2),  # Top-right corner
                    math.sqrt(marble.x**2 + (self.arena_height - marble.y)**2),  # Bottom-left corner
                    math.sqrt((self.arena_width - marble.x)**2 + (self.arena_height - marble.y)**2)  # Bottom-right corner
                )
                if corner_distance < required_margin * 1.5:
                    corner_penalty = (required_margin * 1.5 - corner_distance) * 2
                
                # Effective distance considers actual distance minus penalties
                effective_distance = distance - edge_penalty - corner_penalty
                
                if effective_distance > max_distance_this_marble:
                    max_distance_this_marble = effective_distance
                    best_position_this_marble = (marble.x, marble.y)
                
                # Anti-stuck mechanism: check if marble is stuck
                current_pos = (marble.x, marble.y)
                if step > 100:  # Allow initial settling
                    pos_diff = math.sqrt((current_pos[0] - last_position[0])**2 + 
                                       (current_pos[1] - last_position[1])**2)
                    if pos_diff < 2.0:  # Very small movement
                        stuck_counter += 1
                    else:
                        stuck_counter = 0
                    
                    # If stuck for too long, add exploration impulse
                    if stuck_counter > 100:
                        impulse_angle = rng.uniform(0, 2 * math.pi)
                        impulse_strength = self.marble_speed * 0.3
                        marble.velocity_x += math.cos(impulse_angle) * impulse_strength
                        marble.velocity_y += math.sin(impulse_angle) * impulse_strength
                        marble._normalize_velocity()
                        stuck_counter = 0
                
                last_position = current_pos
                
                # Periodic exploration boost to reach further areas and avoid clustering
                if step % 300 == 0 and step > 0:
                    # Add larger random velocity component to encourage exploration
                    exploration_angle = rng.uniform(0, 2 * math.pi)
                    exploration_strength = self.marble_speed * rng.uniform(0.2, 0.5)  # Variable strength
                    marble.velocity_x += math.cos(exploration_angle) * exploration_strength
                    marble.velocity_y += math.sin(exploration_angle) * exploration_strength
                    marble._normalize_velocity()
                
                # Additional exploration every 1000 steps - major direction change
                if step % 1000 == 0 and step > 0:
                    # Bias direction away from edges to find more central positions
                    center_x = self.arena_width / 2
                    center_y = self.arena_height / 2
                    
                    # Calculate direction towards center
                    to_center_x = center_x - marble.x
                    to_center_y = center_y - marble.y
                    center_dist = math.sqrt(to_center_x**2 + to_center_y**2)
                    
                    if center_dist > 0:
                        # Normalize direction to center
                        to_center_x /= center_dist
                        to_center_y /= center_dist
                        
                        # Random direction with bias towards center
                        random_angle = rng.uniform(0, 2 * math.pi)
                        random_x = math.cos(random_angle)
                        random_y = math.sin(random_angle)
                        
                        # Mix random direction with center bias (50% center bias for stronger pull)
                        bias_factor = 0.5
                        final_x = (1 - bias_factor) * random_x + bias_factor * to_center_x
                        final_y = (1 - bias_factor) * random_y + bias_factor * to_center_y
                        
                        # Normalize and apply
                        final_length = math.sqrt(final_x**2 + final_y**2)
                        if final_length > 0:
                            marble.velocity_x = (final_x / final_length) * marble.speed
                            marble.velocity_y = (final_y / final_length) * marble.speed
            
            # Store final position and update overall farthest
            all_positions.append(best_position_this_marble)
            if max_distance_this_marble > farthest_distance:
                farthest_distance = max_distance_this_marble
                farthest_position = best_position_this_marble
            
            # Progress reporting every 6 marbles
            if (marble_idx + 1) % 6 == 0:
                print(f"  Completed {marble_idx + 1}/{num_marbles} marbles, best effective distance so far: {farthest_distance:.1f}")
        
        if farthest_position:
            # Calculate actual distance for reporting
            actual_distance = math.sqrt((farthest_position[0] - start_x)**2 + (farthest_position[1] - start_y)**2)
            print(f"{simulation_name} complete: farthest position ({farthest_position[0]:.1f}, {farthest_position[1]:.1f}), actual distance: {actual_distance:.1f}, effective distance: {farthest_distance:.1f}")
            
            # Check if the selected position can accommodate a zone
            min_zone_radius = self.marble_radius * 2.0
            required_margin = min_zone_radius + 10
            
            x, y = farthest_position
            if (not terrain.check_collision(x, y, self.marble_radius) and
                required_margin <= x <= self.arena_width - required_margin and
                required_margin <= y <= self.arena_height - required_margin):
                return farthest_position
            else:
                print(f"Selected position cannot accommodate zone, finding alternative...")
            
            # Find alternative positions that can actually accommodate zones
            print(f"Searching through {len(all_positions)} positions for zone-compatible alternative...")
            
            # Score all positions by: actual_distance - edge_penalty, filter by zone compatibility
            scored_positions = []
            for pos in all_positions:
                x, y = pos
                
                # Check basic requirements
                if terrain.check_collision(x, y, self.marble_radius):
                    continue
                
                # Check zone accommodation with different zone sizes
                for zone_factor in [2.0, 1.5, 1.0, 0.8]:  # Try larger zones first, then smaller
                    zone_radius = self.marble_radius * zone_factor
                    margin = zone_radius + 15  # Consistent with the stronger requirements
                    
                    if (margin <= x <= self.arena_width - margin and
                        margin <= y <= self.arena_height - margin):
                        
                        actual_distance = math.sqrt((x - start_x)**2 + (y - start_y)**2)
                        # Larger bonus for being away from edges
                        min_edge_dist = min(x, self.arena_width - x, y, self.arena_height - y)
                        edge_bonus = min_edge_dist / 5  # Larger bonus for being away from edges
                        
                        score = actual_distance + edge_bonus
                        scored_positions.append((pos, score, zone_factor))
                        break  # Found a compatible zone size
            
            if scored_positions:
                # Sort by score and return the best position
                scored_positions.sort(key=lambda item: item[1], reverse=True)
                best_pos, best_score, zone_factor = scored_positions[0]
                actual_distance = math.sqrt((best_pos[0] - start_x)**2 + (best_pos[1] - start_y)**2)
                print(f"Selected zone-compatible position: ({best_pos[0]:.1f}, {best_pos[1]:.1f}), distance: {actual_distance:.1f}, zone factor: {zone_factor:.1f}")
                return best_pos
        
        print(f"{simulation_name} failed: no valid position found")
        return None
    
    def _is_zone_valid(self, terrain: FlowingTerrainObstacle, position: Tuple[float, float], radius: float) -> bool:
        """Check if a zone position is valid (no terrain collision) with thorough validation"""
        x, y = position
        
        # Check that zone is within arena bounds with reasonable margin
        edge_margin = self.marble_radius + 10  # Minimum distance from arena edges
        zone_margin = radius + 15  # Additional margin for the zone itself (matching simulation requirements)
        total_margin = max(edge_margin, zone_margin)
        
        if (x - radius < total_margin or x + radius > self.arena_width - total_margin or
            y - radius < total_margin or y + radius > self.arena_height - total_margin):
            print(f"Zone validation failed: bounds check at ({x:.1f}, {y:.1f}) with radius {radius:.1f}, margin {total_margin:.1f}")
            return False
        
        # Check center first - most important
        if terrain.check_collision(x, y, self.marble_radius):
            print(f"Zone validation failed: center collision at ({x:.1f}, {y:.1f})")
            return False
        
        # Check multiple points around the zone perimeter
        check_points = 12  # More points for better coverage
        for i in range(check_points):
            angle = 2 * math.pi * i / check_points
            check_x = x + radius * 0.8 * math.cos(angle)  # Check at 80% of radius
            check_y = y + radius * 0.8 * math.sin(angle)
            
            if terrain.check_collision(check_x, check_y, self.marble_radius):
                print(f"Zone validation failed: perimeter collision at ({check_x:.1f}, {check_y:.1f})")
                return False
        
        print(f"Zone validation passed at ({x:.1f}, {y:.1f}) with radius {radius:.1f}")
        return True
