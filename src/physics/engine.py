"""
Unified physics engine for marble race simulation.

This module consolidates all collision detection and physics updates into a single
pymunk-based system that handles marble-marble, marble-terrain, and marble-boundary
collisions deterministically.
"""

import math
import pymunk
from typing import List, Dict, Optional
from .marble import Marble
from config import get_config
import rng


class PhysicsEngine:
    """
    Unified physics engine using pymunk for all collision detection and resolution.
    
    This replaces the separate collision detection systems and provides a single
    interface for all physics operations while maintaining deterministic behavior.
    """
    
    def __init__(self, arena_width: int, arena_height: int):
        self.cfg = get_config()
        self.arena_width = arena_width
        self.arena_height = arena_height
        
        # Create pymunk space with no gravity (constant speed physics)
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        
        # Store mapping between pymunk bodies and our marbles
        self.body_to_marble = {}  # type: Dict[pymunk.Body, Marble]
        self.marble_to_body = {}  # type: Dict[int, pymunk.Body]
        
        # Create static boundaries
        self._create_boundaries()
        
        # Store terrain obstacles
        self.terrain_bodies = []  # type: List[pymunk.Body]
        
        # Store pre-collision velocities to detect stuck bouncing
        self.pre_collision_velocities = {}  # type: Dict[pymunk.Body, tuple]
        
        # Setup collision handlers for velocity variation
        self._setup_collision_handlers()
    
    def _create_boundaries(self):
        """Create static boundary walls for the arena"""
        boundary_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        
        # Define boundary segments
        boundaries = [
            pymunk.Segment(boundary_body, (0, 0), (0, self.arena_height), 1),
            pymunk.Segment(boundary_body, (self.arena_width, 0), (self.arena_width, self.arena_height), 1),
            pymunk.Segment(boundary_body, (0, 0), (self.arena_width, 0), 1),
            pymunk.Segment(boundary_body, (0, self.arena_height), (self.arena_width, self.arena_height), 1)
        ]
        
        for boundary in boundaries:
            boundary.friction = 0.0
            boundary.elasticity = 1.0
            boundary.collision_type = 1
        
        self.space.add(boundary_body, *boundaries)
    
    def _setup_collision_handlers(self):
        """Setup collision handlers - simplified for newer pymunk versions"""
        # We'll handle collision variation in the update_physics method instead
        # of using the deprecated collision handler API
        pass
    
    def add_marble(self, marble: Marble, marble_id: int):
        """Add a marble to the physics system"""
        moment = pymunk.moment_for_circle(1.0, 0, marble.radius)
        body = pymunk.Body(1.0, moment)
        body.position = marble.x, marble.y
        body.velocity = marble.velocity_x, marble.velocity_y
        
        shape = pymunk.Circle(body, marble.radius)
        shape.friction = 0.0
        shape.elasticity = 1.0
        shape.collision_type = 2
        
        self.body_to_marble[body] = marble
        self.marble_to_body[marble_id] = body
        
        self.space.add(body, shape)
    
    def add_terrain_obstacles(self, terrain_obstacles: List):
        """Add terrain obstacles to the physics system"""
        for obstacle in terrain_obstacles:
            try:
                body = pymunk.Body(body_type=pymunk.Body.STATIC)
                
                if hasattr(obstacle, 'get_pymunk_shapes'):
                    shapes = obstacle.get_pymunk_shapes(body)
                    for shape in shapes:
                        shape.friction = 0.0
                        shape.elasticity = 1.0
                        shape.collision_type = 3
                    
                    if shapes:
                        self.space.add(body, *shapes)
                        self.terrain_bodies.append(body)
                else:
                    print(f"Warning: Terrain obstacle {type(obstacle)} doesn't support pymunk integration")
                    
            except Exception as e:
                print(f"Error adding terrain obstacle to physics system: {e}")
    
    def update_physics(self, dt: float, marbles: List[Marble]):
        """
        Update physics simulation with constant speed constraint.
        
        This method handles ALL collision types in one unified update.
        """
        # Ensure marbles are in sync with physics system
        self._sync_marbles_to_physics(marbles)
        
        # Store original speeds before physics step
        original_speeds = {}
        for body, marble in self.body_to_marble.items():
            original_speeds[body] = marble.speed
        
        # Step the physics simulation
        self.space.step(dt)
        
        # Check for stuck bouncing patterns less frequently for better performance
        self._frame_counter = getattr(self, '_frame_counter', 0) + 1
        if self._frame_counter % 10 == 0:  # Check every 10 frames instead of every frame
            self._check_and_fix_stuck_bouncing()
        
        # Restore constant speeds and sync back to marble objects
        for body, marble in self.body_to_marble.items():
            marble.x, marble.y = body.position
            
            vx, vy = body.velocity
            speed = math.sqrt(vx*vx + vy*vy)
            
            if speed > 0.001:
                target_speed = original_speeds[body]
                scale = target_speed / speed
                marble.velocity_x = vx * scale
                marble.velocity_y = vy * scale
                body.velocity = marble.velocity_x, marble.velocity_y
            else:
                # Handle near-zero velocity
                angle = math.atan2(marble.y, marble.x) + 1.0
                marble.velocity_x = math.cos(angle) * original_speeds[body]
                marble.velocity_y = math.sin(angle) * original_speeds[body]
                body.velocity = marble.velocity_x, marble.velocity_y
    
    def _sync_marbles_to_physics(self, marbles: List[Marble]):
        """Ensure physics system has all current marbles"""
        current_marble_count = len(self.body_to_marble)
        if current_marble_count != len(marbles):
            # Clear and re-add all marbles
            for marble_id in list(self.marble_to_body.keys()):
                self.remove_marble(marble_id)
            
            for i, marble in enumerate(marbles):
                self.add_marble(marble, i)
    
    def remove_marble(self, marble_id: int):
        """Remove a marble from the physics system"""
        if marble_id in self.marble_to_body:
            body = self.marble_to_body[marble_id]
            
            for shape in body.shapes:
                self.space.remove(shape)
            self.space.remove(body)
            
            del self.body_to_marble[body]
            del self.marble_to_body[marble_id]
    
    def clear_terrain(self):
        """Remove all terrain obstacles"""
        for body in self.terrain_bodies:
            for shape in body.shapes:
                self.space.remove(shape)
            self.space.remove(body)
        self.terrain_bodies.clear()
    
    def _check_and_fix_stuck_bouncing(self):
        """
        Check each marble for stuck bouncing patterns and add variation if needed.
        
        This detects when marbles are moving primarily in one axis (horizontal 
        or vertical) which indicates they're stuck bouncing between parallel surfaces.
        """
        for body, marble in self.body_to_marble.items():
            vx, vy = body.velocity
            
            # Skip if marble is moving too slowly
            if abs(vx) < 0.1 and abs(vy) < 0.1:
                continue
            
            # Calculate the angle of movement
            movement_angle = math.atan2(abs(vy), abs(vx))
            
            # Check if movement is too close to purely horizontal or vertical
            # (within ~2 degrees of 0° or 90°)
            horizontal_threshold = math.radians(2)  # 2 degrees
            vertical_threshold = math.radians(88)   # 88 degrees (close to 90°)
            
            is_too_horizontal = movement_angle < horizontal_threshold
            is_too_vertical = movement_angle > vertical_threshold
            
            if is_too_horizontal or is_too_vertical:
                self._add_velocity_variation(body, marble.speed)
    
    def _add_velocity_variation(self, marble_body, target_speed):
        """
        Add small random variation to marble velocity to break stuck patterns.
        
        This adds a small angular variation to the velocity direction without
        changing the overall speed.
        """
        vx, vy = marble_body.velocity
        
        # Calculate current angle
        current_angle = math.atan2(vy, vx)
        
        # Add small random variation (±2 to ±5 degrees)
        variation_degrees = rng.uniform(2, 5)
        if rng.random_float() < 0.5:
            variation_degrees = -variation_degrees
        
        variation_radians = math.radians(variation_degrees)
        new_angle = current_angle + variation_radians
        
        # Apply new velocity with same speed
        new_vx = target_speed * math.cos(new_angle)
        new_vy = target_speed * math.sin(new_angle)
        
        marble_body.velocity = new_vx, new_vy


# Global physics engine instance
_physics_engine = None


def get_physics_engine(arena_width: int = None, arena_height: int = None):
    """Get or create the global physics engine instance"""
    global _physics_engine
    
    if _physics_engine is None or (arena_width and arena_height):
        if arena_width and arena_height:
            _physics_engine = PhysicsEngine(arena_width, arena_height)
        else:
            raise ValueError("Physics engine not initialized. Provide arena dimensions.")
    
    return _physics_engine


def initialize_physics_engine(arena_width: int, arena_height: int, terrain_obstacles: List):
    """Initialize the global physics engine with terrain"""
    global _physics_engine
    _physics_engine = PhysicsEngine(arena_width, arena_height)
    _physics_engine.add_terrain_obstacles(terrain_obstacles)
    return _physics_engine
