"""
Collision detection utilities for the marble race simulation.
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
        """Detect and resolve all marble-to-terrain collisions"""
        from config import get_config
        cfg = get_config()
        
        for marble in marbles:
            for obstacle in terrain_obstacles:
                if obstacle.check_collision(marble.x, marble.y, marble.radius):
                    CollisionDetector._resolve_terrain_collision(marble, obstacle, cfg, arena_width, arena_height)
    
    @staticmethod
    def _resolve_terrain_collision(marble: Marble, obstacle, cfg, arena_width: int, arena_height: int):
        """Resolve a single marble-terrain collision with smooth response"""
        # Get collision normal
        nx, ny = obstacle.get_collision_normal(marble.x, marble.y)
        
        # Calculate how deep we are in the obstacle
        # This gives us a smoother response based on penetration depth
        closest_x, closest_y = obstacle.get_closest_point(marble.x, marble.y)
        distance_to_surface = math.sqrt((marble.x - closest_x)**2 + (marble.y - closest_y)**2)
        penetration_depth = max(0, marble.radius - distance_to_surface)
        
        if penetration_depth > 0:
            # Calculate dot product of velocity and normal
            dot_product = marble.velocity_x * nx + marble.velocity_y * ny
            
            # Only apply collision response if moving towards the obstacle
            if dot_product < 0:
                # Softer velocity reflection with damping
                reflection_strength = cfg.simulation.TERRAIN_REFLECTION_STRENGTH
                marble.velocity_x -= reflection_strength * dot_product * nx
                marble.velocity_y -= reflection_strength * dot_product * ny
                
                # Ensure constant speed is maintained
                marble._normalize_velocity()
            
            # Gradual push-out based on penetration depth
            # Use smaller steps for smoother movement
            push_strength = cfg.simulation.TERRAIN_PUSH_STRENGTH
            separation_force = min(penetration_depth * push_strength, cfg.simulation.MAX_TERRAIN_PUSH)
            
            marble.x += nx * separation_force
            marble.y += ny * separation_force
            
            # Keep within arena bounds
            marble.x = max(marble.radius, min(arena_width - marble.radius, marble.x))
            marble.y = max(marble.radius, min(arena_height - marble.radius, marble.y))
