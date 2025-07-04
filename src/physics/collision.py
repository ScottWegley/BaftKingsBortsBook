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
        Resolve collision between two marbles if they overlap.
        Returns True if a collision was resolved, False otherwise.
        """
        # Calculate distance between marble centers
        dx = marble2.x - marble1.x
        dy = marble2.y - marble1.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Check if marbles are colliding
        min_distance = marble1.radius + marble2.radius
        if distance >= min_distance - self.position_tolerance:
            return False  # No collision
        
        # Handle the edge case where marbles are at exactly the same position
        if distance < self.position_tolerance:
            # Separate them in a deterministic direction to avoid randomness
            angle = math.atan2(marble2.y - marble1.y + 0.01, marble2.x - marble1.x + 0.01)
            dx = math.cos(angle)
            dy = math.sin(angle)
            distance = self.position_tolerance
        else:
            # Normalize the collision vector
            dx /= distance
            dy /= distance
        
        # Calculate overlap and separate marbles more gently
        overlap = min_distance - distance
        separation_distance = (overlap * self.separation_factor) / 2
        
        # Move marbles apart with gentler separation
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
        
        # Calculate elastic collision response (assuming equal masses)
        # For elastic collision with equal masses, velocities are exchanged along collision normal
        impulse = relative_speed  # Since mass = 1 for both marbles
        
        # Apply impulse to velocities
        marble1.velocity_x += impulse * dx
        marble1.velocity_y += impulse * dy
        marble2.velocity_x -= impulse * dx
        marble2.velocity_y -= impulse * dy
        
        # Normalize velocities to maintain constant speed
        self._normalize_velocity(marble1)
        self._normalize_velocity(marble2)
        
        # Apply slight damping to prevent energy buildup from numerical errors
        # Only apply damping if configured value is less than 1.0
        if self.velocity_damping < 1.0:
            marble1.velocity_x *= self.velocity_damping
            marble1.velocity_y *= self.velocity_damping
            marble2.velocity_x *= self.velocity_damping
            marble2.velocity_y *= self.velocity_damping
            
            # Re-normalize after damping
            self._normalize_velocity(marble1)
            self._normalize_velocity(marble2)
        
        return True
    
    @staticmethod
    def detect_and_resolve_terrain_collisions(marbles: List[Marble], terrain_obstacles: List, 
                                            arena_width: int, arena_height: int):
        """
        Detect and resolve terrain collisions for all marbles.
        Uses continuous collision detection to prevent tunneling.
        """
        detector = CollisionDetector()
        
        for marble in marbles:
            # Handle arena boundary collisions first (highest priority)
            detector._resolve_boundary_collisions(marble, arena_width, arena_height)
            
            # Handle terrain obstacle collisions
            for obstacle in terrain_obstacles:
                if detector._resolve_terrain_collision(marble, obstacle):
                    # Only handle one terrain collision per frame to avoid conflicts
                    break
    
    def _resolve_boundary_collisions(self, marble: Marble, arena_width: int, arena_height: int):
        """
        Handle collisions with arena boundaries using a robust method that prevents
        jittering and ensures marbles stay within bounds.
        """
        collision_occurred = False
        
        # Left boundary
        if marble.x - marble.radius < 0:
            if self.boundary_precision:
                marble.x = marble.radius  # Position exactly at boundary
            else:
                marble.x = marble.radius + self.position_tolerance
            if marble.velocity_x < 0:  # Only reflect if moving toward wall
                marble.velocity_x = -marble.velocity_x
                collision_occurred = True
        
        # Right boundary
        elif marble.x + marble.radius > arena_width:
            if self.boundary_precision:
                marble.x = arena_width - marble.radius  # Position exactly at boundary
            else:
                marble.x = arena_width - marble.radius - self.position_tolerance
            if marble.velocity_x > 0:  # Only reflect if moving toward wall
                marble.velocity_x = -marble.velocity_x
                collision_occurred = True
        
        # Top boundary
        if marble.y - marble.radius < 0:
            if self.boundary_precision:
                marble.y = marble.radius  # Position exactly at boundary
            else:
                marble.y = marble.radius + self.position_tolerance
            if marble.velocity_y < 0:  # Only reflect if moving toward wall
                marble.velocity_y = -marble.velocity_y
                collision_occurred = True
        
        # Bottom boundary
        elif marble.y + marble.radius > arena_height:
            if self.boundary_precision:
                marble.y = arena_height - marble.radius  # Position exactly at boundary
            else:
                marble.y = arena_height - marble.radius - self.position_tolerance
            if marble.velocity_y > 0:  # Only reflect if moving toward wall
                marble.velocity_y = -marble.velocity_y
                collision_occurred = True
        
        # Ensure speed is maintained after boundary reflection
        if collision_occurred:
            self._normalize_velocity(marble)
    
    def _resolve_terrain_collision(self, marble: Marble, obstacle) -> bool:
        """
        Resolve collision with a terrain obstacle.
        Returns True if a collision was resolved, False otherwise.
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
        
        # Calculate velocity component along the normal
        velocity_along_normal = marble.velocity_x * normal_x + marble.velocity_y * normal_y
        
        # Reflect velocity if moving into the surface
        if velocity_along_normal < 0:
            # Elastic reflection: v' = v - 2(v·n)n
            marble.velocity_x -= 2 * velocity_along_normal * normal_x
            marble.velocity_y -= 2 * velocity_along_normal * normal_y
            
            # Normalize velocity to maintain constant speed
            self._normalize_velocity(marble)
        
        # Separate marble from obstacle using iterative method with configurable step size
        separation_step = marble.radius * self.terrain_step_size
        
        for _ in range(self.max_separation_iterations):
            if not obstacle.check_collision(marble.x, marble.y, marble.radius):
                break  # Successfully separated
            
            # Move marble along the normal direction
            marble.x += normal_x * separation_step
            marble.y += normal_y * separation_step
        
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
