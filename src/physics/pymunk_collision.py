"""
Pymunk-based collision detection and resolution system for marble race simulation.

This system uses the pymunk physics library while maintaining:
- Deterministic behavior across headless and graphics modes
- Constant speed physics model (no gravity)
- Elastic collisions
- Same physics behavior as the original custom system
"""

import math
import pymunk
from typing import List, Dict, Optional
from .marble import Marble
from config import get_config


class PymunkCollisionSystem:
    """
    Pymunk-based collision system that maintains deterministic, constant-speed physics.
    
    This system creates a pymunk space for collision detection but maintains control
    over marble velocities to ensure constant speed and deterministic behavior.
    """
    
    def __init__(self, arena_width: int, arena_height: int):
        self.cfg = get_config()
        self.arena_width = arena_width
        self.arena_height = arena_height
        
        # Create pymunk space with no gravity (we want constant speed motion)
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)  # No gravity for constant speed physics
        
        # Store mapping between pymunk bodies and our marbles
        self.body_to_marble = {}  # type: Dict[pymunk.Body, Marble]
        self.marble_to_body = {}  # type: Dict[int, pymunk.Body]  # marble id -> body
        
        # Create static boundaries
        self._create_boundaries()
        
        # Store terrain obstacles (will be added as static bodies)
        self.terrain_bodies = []  # type: List[pymunk.Body]
        
        # Collision handler for marbles
        self._setup_collision_handlers()
    
    def _create_boundaries(self):
        """Create static boundary walls for the arena"""
        # Create static body for boundaries
        boundary_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        
        # Define boundary segments: left, right, top, bottom
        boundaries = [
            # Left wall
            pymunk.Segment(boundary_body, (0, 0), (0, self.arena_height), 1),
            # Right wall  
            pymunk.Segment(boundary_body, (self.arena_width, 0), (self.arena_width, self.arena_height), 1),
            # Top wall
            pymunk.Segment(boundary_body, (0, 0), (self.arena_width, 0), 1),
            # Bottom wall
            pymunk.Segment(boundary_body, (0, self.arena_height), (self.arena_width, self.arena_height), 1)
        ]
        
        # Set boundary properties for elastic collision
        for boundary in boundaries:
            boundary.friction = 0.0  # No friction for constant speed
            boundary.elasticity = 1.0  # Perfectly elastic
            boundary.collision_type = 1  # Boundary collision type
        
        # Add boundaries to space
        self.space.add(boundary_body, *boundaries)
    
    def _setup_collision_handlers(self):
        """Setup collision handlers to maintain constant speed physics"""
        # In pymunk 7+, we use the on_collision event system instead of add_collision_handler
        # For simplicity, we'll handle all collision logic in the update_physics method
        # and let pymunk handle the basic collision resolution
        pass
    
    def add_marble(self, marble: Marble, marble_id: int):
        """Add a marble to the pymunk space"""
        # Create a dynamic body for the marble
        moment = pymunk.moment_for_circle(1.0, 0, marble.radius)  # Unit mass
        body = pymunk.Body(1.0, moment)  # mass=1.0 for simplicity
        body.position = marble.x, marble.y
        body.velocity = marble.velocity_x, marble.velocity_y
        
        # Create circular shape
        shape = pymunk.Circle(body, marble.radius)
        shape.friction = 0.0  # No friction for constant speed
        shape.elasticity = 1.0  # Perfectly elastic
        shape.collision_type = 2  # Marble collision type
        
        # Store mappings
        self.body_to_marble[body] = marble
        self.marble_to_body[marble_id] = body
        
        # Add to space
        self.space.add(body, shape)
    
    def add_terrain_obstacles(self, terrain_obstacles: List):
        """Add terrain obstacles as static bodies to the pymunk space"""
        for obstacle in terrain_obstacles:
            try:
                # Create static body for terrain
                body = pymunk.Body(body_type=pymunk.Body.STATIC)
                
                # Check if obstacle supports pymunk integration
                if hasattr(obstacle, 'get_pymunk_shapes'):
                    shapes = obstacle.get_pymunk_shapes(body)
                    for shape in shapes:
                        shape.friction = 0.0
                        shape.elasticity = 1.0
                        shape.collision_type = 3  # Terrain collision type
                    
                    if shapes:  # Only add if we have shapes
                        self.space.add(body, *shapes)
                        self.terrain_bodies.append(body)
                else:
                    # Fallback: create a simple boundary representation
                    # This ensures compatibility with terrain obstacles that don't support pymunk
                    print(f"Warning: Terrain obstacle {type(obstacle)} doesn't support pymunk integration")
                    # We could create a simplified collision shape here if needed
                    
            except Exception as e:
                print(f"Error adding terrain obstacle to pymunk space: {e}")
                # Continue with other obstacles even if one fails
    
    def update_physics(self, dt: float):
        """
        Update physics simulation while maintaining constant speed constraint.
        
        This is the key method that ensures deterministic, constant-speed behavior.
        """
        # Store original speeds before physics step
        original_speeds = {}
        for body, marble in self.body_to_marble.items():
            original_speeds[body] = marble.speed
        
        # Step the physics simulation (this handles collisions)
        self.space.step(dt)
        
        # After physics step, restore constant speeds and sync with marble objects
        for body, marble in self.body_to_marble.items():
            # Get the new position from pymunk
            marble.x, marble.y = body.position
            
            # Get velocity direction from pymunk but maintain constant speed
            vx, vy = body.velocity
            speed = math.sqrt(vx*vx + vy*vy)
            
            if speed > 0.001:  # Avoid division by zero
                # Normalize and scale to maintain constant speed
                target_speed = original_speeds[body]
                scale = target_speed / speed
                marble.velocity_x = vx * scale
                marble.velocity_y = vy * scale
                
                # Update pymunk body velocity to match
                body.velocity = marble.velocity_x, marble.velocity_y
            else:
                # Handle case where velocity is near zero (shouldn't happen in normal operation)
                # Give a deterministic direction based on position
                angle = math.atan2(marble.y, marble.x) + 1.0
                marble.velocity_x = math.cos(angle) * original_speeds[body]
                marble.velocity_y = math.sin(angle) * original_speeds[body]
                body.velocity = marble.velocity_x, marble.velocity_y
    
    def _marble_collision_handler(self, arbiter, space, data):
        """Handle marble-to-marble collisions - not used in pymunk 7+"""
        return True
    
    def _boundary_collision_handler(self, arbiter, space, data):
        """Handle marble-to-boundary collisions - not used in pymunk 7+"""
        return True
    
    def _terrain_collision_handler(self, arbiter, space, data):
        """Handle marble-to-terrain collisions - not used in pymunk 7+"""
        return True
    
    def remove_marble(self, marble_id: int):
        """Remove a marble from the physics space"""
        if marble_id in self.marble_to_body:
            body = self.marble_to_body[marble_id]
            
            # Remove from space
            for shape in body.shapes:
                self.space.remove(shape)
            self.space.remove(body)
            
            # Clean up mappings
            del self.body_to_marble[body]
            del self.marble_to_body[marble_id]
    
    def clear_terrain(self):
        """Remove all terrain obstacles from the space"""
        for body in self.terrain_bodies:
            for shape in body.shapes:
                self.space.remove(shape)
            self.space.remove(body)
        self.terrain_bodies.clear()


class CollisionDetector:
    """
    Drop-in replacement for the original CollisionDetector that uses pymunk internally.
    
    This maintains the same API as the original system while using pymunk for 
    robust collision detection and resolution.
    """
    
    _pymunk_system = None  # Global pymunk system instance
    _initialized_for_arena = None  # Track which arena size we're initialized for
    
    @staticmethod
    def _ensure_pymunk_system(arena_width: int, arena_height: int, marbles: List[Marble], terrain_obstacles: List):
        """Ensure pymunk system is initialized and up to date"""
        # Check if we need to reinitialize (different arena size or first time)
        if (CollisionDetector._pymunk_system is None or 
            CollisionDetector._initialized_for_arena != (arena_width, arena_height)):
            
            # Create new pymunk system
            CollisionDetector._pymunk_system = PymunkCollisionSystem(arena_width, arena_height)
            CollisionDetector._initialized_for_arena = (arena_width, arena_height)
            
            # Add terrain obstacles first
            CollisionDetector._pymunk_system.add_terrain_obstacles(terrain_obstacles)
            
            # Add current marbles to the system
            for i, marble in enumerate(marbles):
                CollisionDetector._pymunk_system.add_marble(marble, i)
        else:
            # System exists, but check if marble count has changed
            current_marble_count = len(CollisionDetector._pymunk_system.body_to_marble)
            if current_marble_count != len(marbles):
                # Clear existing marbles and re-add all of them
                # This handles both marble additions and removals
                for marble_id in list(CollisionDetector._pymunk_system.marble_to_body.keys()):
                    CollisionDetector._pymunk_system.remove_marble(marble_id)
                
                # Re-add all current marbles
                for i, marble in enumerate(marbles):
                    CollisionDetector._pymunk_system.add_marble(marble, i)
    
    @staticmethod
    def detect_and_resolve_marble_collisions(marbles: List[Marble]):
        """
        Marble collision detection and resolution using pymunk.
        
        This is now handled as part of the unified physics update.
        This method is kept for API compatibility but doesn't do anything
        since collisions are handled in detect_and_resolve_terrain_collisions.
        """
        pass  # Collisions are handled in the unified update method
    
    @staticmethod
    def detect_and_resolve_terrain_collisions(marbles: List[Marble], terrain_obstacles: List, 
                                            arena_width: int, arena_height: int):
        """
        Unified collision detection and resolution using pymunk.
        
        This method now handles ALL collisions (marble-marble, marble-terrain, marble-boundary)
        using the pymunk physics engine while maintaining constant speed physics.
        """
        # Ensure pymunk system is ready
        CollisionDetector._ensure_pymunk_system(arena_width, arena_height, marbles, terrain_obstacles)
        
        # Update physics using fixed timestep for determinism
        cfg = get_config()
        dt = cfg.simulation.FIXED_TIMESTEP
        
        # Perform physics update (handles all collision types)
        CollisionDetector._pymunk_system.update_physics(dt)
