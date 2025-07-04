"""
Simple, clean collision detection utilities for the marble race simulation.
"""

import math
from typing import List
from .marble import Marble


class CollisionDetector:
    """Handles collision detection and resolution between marbles and terrain"""
    
    @staticmethod
    def detect_and_resolve_marble_collisions(marbles: List[Marble]):
        """Detect and resolve all marble-to-marble collisions"""
        for i in range(len(marbles)):
            for j in range(i + 1, len(marbles)):
                if CollisionDetector._check_marble_collision(marbles[i], marbles[j]):
                    CollisionDetector._resolve_marble_collision(marbles[i], marbles[j])
    
    @staticmethod
    def _check_marble_collision(marble1: Marble, marble2: Marble) -> bool:
        """Check if two marbles collide"""
        distance = math.sqrt((marble1.x - marble2.x)**2 + (marble1.y - marble2.y)**2)
        return distance <= (marble1.radius + marble2.radius)
    
    @staticmethod
    def _resolve_marble_collision(marble1: Marble, marble2: Marble):
        """Resolve collision between two marbles using elastic collision"""
        # Calculate distance and overlap
        dx = marble2.x - marble1.x
        dy = marble2.y - marble1.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance == 0:  # Prevent division by zero
            return
        
        # Normalize collision vector
        nx = dx / distance
        ny = dy / distance
        
        # Separate marbles to prevent overlap
        overlap = (marble1.radius + marble2.radius) - distance
        if overlap > 0:
            separation = overlap / 2
            marble1.x -= nx * separation
            marble1.y -= ny * separation
            marble2.x += nx * separation
            marble2.y += ny * separation
        
        # Calculate relative velocity in collision normal direction
        relative_velocity_x = marble2.velocity_x - marble1.velocity_x
        relative_velocity_y = marble2.velocity_y - marble1.velocity_y
        velocity_along_normal = relative_velocity_x * nx + relative_velocity_y * ny
        
        # Don't resolve if velocities are separating
        if velocity_along_normal > 0:
            return
        
        # Calculate impulse (assuming equal mass and perfectly elastic collision)
        impulse = velocity_along_normal
        
        # Update velocities
        marble1.velocity_x += impulse * nx
        marble1.velocity_y += impulse * ny
        marble2.velocity_x -= impulse * nx
        marble2.velocity_y -= impulse * ny
        
        # Ensure constant speed is maintained
        CollisionDetector._normalize_marble_velocity(marble1)
        CollisionDetector._normalize_marble_velocity(marble2)
    
    @staticmethod
    def _normalize_marble_velocity(marble: Marble):
        """Ensure marble velocity magnitude equals the desired speed"""
        current_speed = math.sqrt(marble.velocity_x**2 + marble.velocity_y**2)
        if current_speed > 0:
            marble.velocity_x = (marble.velocity_x / current_speed) * marble.speed
            marble.velocity_y = (marble.velocity_y / current_speed) * marble.speed
    
    @staticmethod
    def detect_and_resolve_terrain_collisions(marbles: List[Marble], terrain_obstacles: List, 
                                            arena_width: int, arena_height: int):
        """Simple terrain collision detection and resolution"""
        for marble in marbles:
            # Marble handles its own boundary collisions
            # Just handle terrain obstacles here
            for obstacle in terrain_obstacles:
                if obstacle.check_collision(marble.x, marble.y, marble.radius):
                    CollisionDetector._resolve_terrain_collision(marble, obstacle)
                    break  # Only handle one collision per frame
    
    @staticmethod
    def _resolve_terrain_collision(marble: Marble, obstacle):
        """Simple terrain collision resolution"""
        # Get collision normal
        normal_x, normal_y = obstacle.get_collision_normal(marble.x, marble.y)
        
        # Calculate velocity component toward surface
        velocity_normal = marble.velocity_x * normal_x + marble.velocity_y * normal_y
        
        # Only reflect if moving toward surface
        if velocity_normal < 0:
            # Perfect elastic reflection
            marble.velocity_x -= 2 * velocity_normal * normal_x
            marble.velocity_y -= 2 * velocity_normal * normal_y
            marble._normalize_velocity()
        
        # Small position correction
        push_distance = 1.5
        marble.x += normal_x * push_distance
        marble.y += normal_y * push_distance
