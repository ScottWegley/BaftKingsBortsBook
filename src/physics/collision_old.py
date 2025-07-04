"""
Robust collision detection and resolution system for marble race simulation.

This system prioritizes accuracy and stability over performance, ensuring:
- No wall glitches or teleporting
- No jittering or oscillation
- Proper separation and elastic collisions
- Minimal complexity while maintaining robustness
"""

import math
from typing import List, Tuple, Optional
from .marble import Marble
from config import get_config


class CollisionDetector:
    """Handles collision detection and resolution with emphasis on accuracy and stability"""
    
    def __init__(self):
        """Initialize collision detector with configuration values"""
        cfg = get_config()
        self.position_tolerance = cfg.simulation.COLLISION_POSITION_TOLERANCE
        self.max_separation_iterations = cfg.simulation.COLLISION_MAX_SEPARATION_ITERATIONS
        self.velocity_damping = cfg.simulation.COLLISION_VELOCITY_DAMPING
        self.separation_factor = cfg.simulation.COLLISION_SEPARATION_FACTOR
        self.max_passes = cfg.simulation.COLLISION_MAX_PASSES
        self.boundary_precision = cfg.simulation.COLLISION_BOUNDARY_PRECISION
        self.terrain_step_size = cfg.simulation.COLLISION_TERRAIN_STEP_SIZE
    
    @staticmethod
    def detect_and_resolve_marble_collisions(marbles: List[Marble]):
        """
        Detect and resolve all marble-to-marble collisions using iterative separation
        to ensure no overlaps remain after resolution.
        """
        if len(marbles) < 2:
            return
        
        detector = CollisionDetector()
        
        # Multiple passes to handle chain collisions properly
        for _ in range(detector.max_passes):
            collision_occurred = False
            
            for i in range(len(marbles)):
                for j in range(i + 1, len(marbles)):
                    if detector._resolve_marble_collision(marbles[i], marbles[j]):
                        collision_occurred = True
            
            # If no collisions occurred in this pass, we're done
            if not collision_occurred:
                break
    
    def _resolve_marble_collision(self, marble1: Marble, marble2: Marble) -> bool:
        """
        Simplified marble collision resolution to reduce jittering
        """
        # Calculate distance between marble centers
        dx = marble2.x - marble1.x
        dy = marble2.y - marble1.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Check if marbles are colliding
        min_distance = marble1.radius + marble2.radius + self.position_tolerance
        if distance >= min_distance:
            return False  # No collision
        
        # Handle the edge case where marbles are at exactly the same position
        if distance < self.position_tolerance:
            # Separate them in a deterministic direction
            angle = math.atan2(marble2.y - marble1.y + 0.1, marble2.x - marble1.x + 0.1)
            dx = math.cos(angle)
            dy = math.sin(angle)
            distance = self.position_tolerance
        else:
            # Normalize the collision vector
            dx /= distance
            dy /= distance
        
        # Calculate overlap and separate marbles
        overlap = min_distance - distance
        separation_distance = overlap / 2  # Simple half-separation
        
        # Move marbles apart
        marble1.x -= dx * separation_distance
        marble1.y -= dy * separation_distance
        marble2.x += dx * separation_distance
        marble2.y += dy * separation_distance
        
        # Calculate relative velocity along collision normal
        rel_vel_x = marble2.velocity_x - marble1.velocity_x
        rel_vel_y = marble2.velocity_y - marble1.velocity_y
        relative_speed = rel_vel_x * dx + rel_vel_y * dy
        
        # Only resolve if marbles are moving toward each other
        if relative_speed >= 0:
            return True  # Collision occurred but no velocity change needed
        
        # Simple elastic collision: exchange velocity components along collision normal
        # For equal masses, velocities are exchanged
        marble1.velocity_x += relative_speed * dx
        marble1.velocity_y += relative_speed * dy
        marble2.velocity_x -= relative_speed * dx
        marble2.velocity_y -= relative_speed * dy
        
        # Normalize velocities to maintain constant speed
        self._normalize_velocity(marble1)
        self._normalize_velocity(marble2)
        
        return True
    
    @staticmethod
    def detect_and_resolve_terrain_collisions(marbles: List[Marble], terrain_obstacles: List, 
                                            arena_width: int, arena_height: int):
        """
        Simple terrain collision resolution - one collision at a time
        """
        detector = CollisionDetector()
        
        for marble in marbles:
            # Handle arena boundary collisions first
            detector._resolve_boundary_collisions(marble, arena_width, arena_height)
            
            # Handle terrain obstacles - only one per frame to avoid conflicts
            for obstacle in terrain_obstacles:
                if detector._resolve_single_terrain_collision_simple(marble, obstacle):
                    break  # Only handle one collision per frame
    
    def _resolve_boundary_collisions(self, marble: Marble, arena_width: int, arena_height: int):
        """
        Handle boundary collisions with simple, predictable behavior
        """
        collision_occurred = False
        
        # Left boundary
        if marble.x - marble.radius <= 0:
            marble.x = marble.radius + self.position_tolerance
            if marble.velocity_x < 0:
                marble.velocity_x = abs(marble.velocity_x)
                collision_occurred = True
        
        # Right boundary  
        elif marble.x + marble.radius >= arena_width:
            marble.x = arena_width - marble.radius - self.position_tolerance
            if marble.velocity_x > 0:
                marble.velocity_x = -abs(marble.velocity_x)
                collision_occurred = True
        
        # Top boundary
        if marble.y - marble.radius <= 0:
            marble.y = marble.radius + self.position_tolerance
            if marble.velocity_y < 0:
                marble.velocity_y = abs(marble.velocity_y)
                collision_occurred = True
        
        # Bottom boundary
        elif marble.y + marble.radius >= arena_height:
            marble.y = arena_height - marble.radius - self.position_tolerance
            if marble.velocity_y > 0:
                marble.velocity_y = -abs(marble.velocity_y)
                collision_occurred = True
        
        # Normalize velocity if collision occurred
        if collision_occurred:
            self._normalize_velocity(marble)
    
    def _resolve_terrain_collision(self, marble: Marble, obstacle) -> bool:
        """
        Simplified terrain collision resolution to reduce sliding and jittering
        """
        if not obstacle.check_collision(marble.x, marble.y, marble.radius):
            return False
        
        # Get the collision normal from the obstacle
        normal_x, normal_y = obstacle.get_collision_normal(marble.x, marble.y)
        
        # Normalize the normal vector (safety check)
        normal_length = math.sqrt(normal_x**2 + normal_y**2)
        if normal_length < self.position_tolerance:
            # Invalid normal, use upward direction as fallback
            normal_x, normal_y = 0, -1
        else:
            normal_x /= normal_length
            normal_y /= normal_length
        
        # Separate marble from obstacle first (more aggressive separation)
        separation_step = marble.radius * self.terrain_step_size
        
        for _ in range(self.max_separation_iterations):
            if not obstacle.check_collision(marble.x, marble.y, marble.radius):
                break  # Successfully separated
            
            # Move marble along the normal direction
            marble.x += normal_x * separation_step
            marble.y += normal_y * separation_step
        
        # Calculate velocity component along the normal
        velocity_along_normal = marble.velocity_x * normal_x + marble.velocity_y * normal_y
        
        # Reflect velocity if moving into the surface
        if velocity_along_normal < 0:
            # Simple elastic reflection: v' = v - 2(v·n)n
            marble.velocity_x -= 2 * velocity_along_normal * normal_x
            marble.velocity_y -= 2 * velocity_along_normal * normal_y
            
            # Normalize velocity to maintain constant speed
            self._normalize_velocity(marble)
        
        return True
    
    def _resolve_single_terrain_collision_simple(self, marble: Marble, obstacle) -> bool:
        """
        Super simple terrain collision - just bounce and separate, nothing fancy
        """
        if not obstacle.check_collision(marble.x, marble.y, marble.radius):
            return False
        
        # Get normal from obstacle
        normal_x, normal_y = obstacle.get_collision_normal(marble.x, marble.y)
        
        # Normalize normal (safety)
        normal_length = math.sqrt(normal_x**2 + normal_y**2)
        if normal_length < 0.01:  # Use a larger threshold
            normal_x, normal_y = 0, -1  # Default upward
        else:
            normal_x /= normal_length
            normal_y /= normal_length
        
        # Simple separation - push marble out aggressively
        separation_distance = marble.radius * 0.3  # 30% of radius per step
        for _ in range(5):  # Max 5 steps
            if not obstacle.check_collision(marble.x, marble.y, marble.radius):
                break
            marble.x += normal_x * separation_distance
            marble.y += normal_y * separation_distance
        
        # Simple velocity reflection
        dot_product = marble.velocity_x * normal_x + marble.velocity_y * normal_y
        if dot_product < 0:  # Only reflect if moving toward surface
            marble.velocity_x -= 2 * dot_product * normal_x
            marble.velocity_y -= 2 * dot_product * normal_y
        
        # Maintain speed
        self._normalize_velocity(marble)
        return True

    def _normalize_velocity(self, marble: Marble):
        """
        Normalize marble velocity to maintain constant speed.
        This is crucial for the physics model of the simulation.
        """
        current_speed = math.sqrt(marble.velocity_x**2 + marble.velocity_y**2)
        
        if current_speed < self.position_tolerance:
            # If marble has no velocity, give it a deterministic direction based on position
            # This avoids random behavior that could cause inconsistent results
            angle = math.atan2(marble.y, marble.x) + 1.0  # Slight offset to avoid zero angle
            marble.velocity_x = math.cos(angle) * marble.speed
            marble.velocity_y = math.sin(angle) * marble.speed
        else:
            # Scale velocity to maintain target speed
            scale = marble.speed / current_speed
            marble.velocity_x *= scale
            marble.velocity_y *= scale
