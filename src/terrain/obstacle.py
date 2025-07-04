"""
Terrain obstacle classes for collision detection and rendering.
"""

import math
from typing import List, Tuple
import pygame

# Import pymunk for physics integration
try:
    import pymunk
    PYMUNK_AVAILABLE = True
except ImportError:
    PYMUNK_AVAILABLE = False


class FlowingTerrainObstacle:
    """Flowing terrain obstacle using height field"""
    
    def __init__(self, height_field: List[List[float]], threshold: float, scale_x: float, scale_y: float, base_color: Tuple[int, int, int] = (100, 100, 100)):
        self.height_field = height_field
        self.threshold = threshold
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.base_color = base_color
        self.grid_height = len(height_field)
        self.grid_width = len(height_field[0]) if height_field else 0
    
    def check_collision(self, marble_x: float, marble_y: float, marble_radius: float) -> bool:
        """Check collision with flowing terrain using comprehensive sampling"""
        # Calculate world bounds based on our grid dimensions and scale
        world_width = self.grid_width * self.scale_x
        world_height = self.grid_height * self.scale_y
        
        # Check if marble (including radius) is outside world bounds
        if (marble_x - marble_radius < 0 or marble_x + marble_radius > world_width or 
            marble_y - marble_radius < 0 or marble_y + marble_radius > world_height):
            return True
        
        # Convert marble position to grid coordinates
        grid_x = int(marble_x / self.scale_x)
        grid_y = int(marble_y / self.scale_y)
        
        # Safety check for grid bounds
        if grid_x < 0 or grid_x >= self.grid_width or grid_y < 0 or grid_y >= self.grid_height:
            return True
        
        # Quick check: if marble center is in solid terrain, collision
        if self.height_field[grid_y][grid_x] > self.threshold:
            return True
        
        # More thorough collision detection - sample points within marble radius
        # Use reasonable sampling to balance accuracy and performance
        samples_per_radius = 2  # Sufficient sampling for most cases
        step_size = marble_radius / samples_per_radius
        
        # Sample in a circle around the marble center
        num_angular_samples = 8  # 8 directions around the marble
        for i in range(num_angular_samples):
            angle = (2 * math.pi * i) / num_angular_samples
            
            # Sample points along this angle from center to edge of marble
            for r in range(1, samples_per_radius + 1):
                sample_radius = r * step_size
                sample_x = marble_x + sample_radius * math.cos(angle)
                sample_y = marble_y + sample_radius * math.sin(angle)
                
                # Convert to grid coordinates
                sample_grid_x = int(sample_x / self.scale_x)
                sample_grid_y = int(sample_y / self.scale_y)
                
                # Check bounds
                if (sample_grid_x < 0 or sample_grid_x >= self.grid_width or 
                    sample_grid_y < 0 or sample_grid_y >= self.grid_height):
                    return True  # Hit boundary
                
                # Check if this sample point hits terrain
                if self.height_field[sample_grid_y][sample_grid_x] > self.threshold:
                    return True
        
        return False
    
    def check_swept_collision(self, start_x: float, start_y: float, end_x: float, end_y: float, marble_radius: float) -> bool:
        """Check collision along a path from start to end position"""
        # Calculate the distance and direction
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance == 0:
            return self.check_collision(start_x, start_y, marble_radius)
        
        # Sample points along the path
        # Use smaller steps than the marble radius to catch thin walls
        step_size = min(marble_radius * 0.3, self.scale_x * 0.5, self.scale_y * 0.5)
        num_steps = max(1, int(distance / step_size))
        
        for i in range(num_steps + 1):
            t = i / max(1, num_steps)
            sample_x = start_x + t * dx
            sample_y = start_y + t * dy
            
            if self.check_collision(sample_x, sample_y, marble_radius):
                return True
        
        return False
    
    def get_collision_normal(self, marble_x: float, marble_y: float) -> Tuple[float, float]:
        """Get collision normal with improved boundary and terrain handling"""
        # Calculate world bounds
        world_width = self.grid_width * self.scale_x
        world_height = self.grid_height * self.scale_y
        
        # Handle world boundaries with clear, unambiguous normals
        boundary_margin = 10.0
        
        if marble_x < boundary_margin:
            return (1.0, 0.0)  # Push right from left boundary
        elif marble_x > world_width - boundary_margin:
            return (-1.0, 0.0)  # Push left from right boundary
        elif marble_y < boundary_margin:
            return (0.0, 1.0)  # Push down from top boundary
        elif marble_y > world_height - boundary_margin:
            return (0.0, -1.0)  # Push up from bottom boundary
        
        # For interior terrain, calculate gradient-based normal
        grid_x = int(marble_x / self.scale_x)
        grid_y = int(marble_y / self.scale_y)
        
        # Clamp to valid grid range for gradient calculation
        grid_x = max(1, min(self.grid_width - 2, grid_x))
        grid_y = max(1, min(self.grid_height - 2, grid_y))
        
        # Calculate gradient using simple central differences
        gradient_x = (self.height_field[grid_y][grid_x + 1] - self.height_field[grid_y][grid_x - 1]) * 0.5
        gradient_y = (self.height_field[grid_y + 1][grid_x] - self.height_field[grid_y - 1][grid_x]) * 0.5
        
        # Normal points away from higher terrain (negative gradient direction)
        normal_x = -gradient_x
        normal_y = -gradient_y
        
        # Normalize the normal vector
        length = math.sqrt(normal_x * normal_x + normal_y * normal_y)
        if length > 0.001:
            return (normal_x / length, normal_y / length)
        
        # Fallback: if gradient is too small, find direction to nearest open space
        return self._find_escape_direction_simple(marble_x, marble_y)
    
    def _find_escape_direction_simple(self, marble_x: float, marble_y: float) -> Tuple[float, float]:
        """Simple escape direction calculation"""
        grid_x = int(marble_x / self.scale_x)
        grid_y = int(marble_y / self.scale_y)
        
        # Check 4 cardinal directions to find open space
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # Up, Right, Down, Left
        
        for dx, dy in directions:
            check_x = grid_x + dx
            check_y = grid_y + dy
            
            if (0 <= check_x < self.grid_width and 0 <= check_y < self.grid_height):
                if self.height_field[check_y][check_x] <= self.threshold:
                    return (float(dx), float(dy))
        
        # If no clear direction, default to pushing right
        return (1.0, 0.0)

    
    def get_closest_point(self, marble_x: float, marble_y: float) -> Tuple[float, float]:
        """Get the closest point on the terrain surface to the marble"""
        # Convert to grid coordinates
        grid_x = int(marble_x / self.scale_x)
        grid_y = int(marble_y / self.scale_y)
        
        # Clamp to grid bounds
        grid_x = max(0, min(self.grid_width - 1, grid_x))
        grid_y = max(0, min(self.grid_height - 1, grid_y))
        
        # Find the closest surface point by checking a small neighborhood
        closest_x, closest_y = marble_x, marble_y
        min_distance = float('inf')
        
        # Search in a small radius around the marble
        search_radius = 3
        for dy in range(-search_radius, search_radius + 1):
            for dx in range(-search_radius, search_radius + 1):
                sample_x = grid_x + dx
                sample_y = grid_y + dy
                
                if (0 <= sample_x < self.grid_width and 0 <= sample_y < self.grid_height):
                    height = self.height_field[sample_y][sample_x]
                    
                    # If this is a surface point (near the threshold)
                    if abs(height - self.threshold) < 0.1:
                        world_x = sample_x * self.scale_x
                        world_y = sample_y * self.scale_y
                        distance = math.sqrt((marble_x - world_x)**2 + (marble_y - world_y)**2)
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_x, closest_y = world_x, world_y
        
        return (closest_x, closest_y)
    
    def render(self, screen: pygame.Surface, color: Tuple[int, int, int] = (100, 100, 100)):
        """Render the flowing terrain with a smooth color gradient based on height."""
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                height = self.height_field[y][x]
                if height > self.threshold:
                    world_x = x * self.scale_x
                    world_y = y * self.scale_y
                    # Start gradient at a bright version of the base color (e.g., 60% base color, 40% white)
                    t = (height - self.threshold) / (1.0 - self.threshold)
                    t = max(0.0, min(1.0, t))
                    # Interpolate from bright (base color + white) to base color
                    bright_color = (
                        int(self.base_color[0] * 0.6 + 255 * 0.4),
                        int(self.base_color[1] * 0.6 + 255 * 0.4),
                        int(self.base_color[2] * 0.6 + 255 * 0.4)
                    )
                    terrain_color = (
                        int(bright_color[0] * (1 - t) + self.base_color[0] * t),
                        int(bright_color[1] * (1 - t) + self.base_color[1] * t),
                        int(bright_color[2] * (1 - t) + self.base_color[2] * t)
                    )
                    rect = pygame.Rect(
                        int(world_x),
                        int(world_y),
                        int(self.scale_x) + 1,
                        int(self.scale_y) + 1
                    )
                    pygame.draw.rect(screen, terrain_color, rect)
    
    def get_pymunk_shapes(self, body):
        """
        Generate pymunk collision shapes for this terrain obstacle.
        
        For flowing terrain, we'll create a simplified collision representation
        using segments to approximate the terrain boundaries.
        """
        if not PYMUNK_AVAILABLE:
            return []
        
        shapes = []
        
        # Create boundary segments for the world edges
        world_width = self.grid_width * self.scale_x
        world_height = self.grid_height * self.scale_y
        
        # World boundary segments
        boundary_segments = [
            # Left boundary (x=0)
            pymunk.Segment(body, (0, 0), (0, world_height), 2),
            # Right boundary  
            pymunk.Segment(body, (world_width, 0), (world_width, world_height), 2),
            # Top boundary (y=0)
            pymunk.Segment(body, (0, 0), (world_width, 0), 2),
            # Bottom boundary
            pymunk.Segment(body, (0, world_height), (world_width, world_height), 2)
        ]
        
        shapes.extend(boundary_segments)
        
        # For interior terrain, we'll create a simplified representation
        # Sample the terrain at regular intervals and create collision segments
        # for transitions between solid and non-solid areas
        
        sample_step = 1  # Check every cell boundary for maximum accuracy
        
        # Horizontal segments (for vertical terrain boundaries)
        for y in range(0, self.grid_height, sample_step):
            for x in range(self.grid_width - 1):
                current_solid = self.height_field[y][x] > self.threshold
                next_solid = self.height_field[y][x + 1] > self.threshold
                
                # Create vertical segment when transitioning from open to solid
                if not current_solid and next_solid:
                    world_x = (x + 1) * self.scale_x
                    world_y1 = y * self.scale_y
                    world_y2 = min((y + sample_step) * self.scale_y, world_height)
                    
                    segment = pymunk.Segment(body, (world_x, world_y1), (world_x, world_y2), 1)
                    shapes.append(segment)
                    
                # Create vertical segment when transitioning from solid to open  
                elif current_solid and not next_solid:
                    world_x = (x + 1) * self.scale_x
                    world_y1 = y * self.scale_y
                    world_y2 = min((y + sample_step) * self.scale_y, world_height)
                    
                    segment = pymunk.Segment(body, (world_x, world_y1), (world_x, world_y2), 1)
                    shapes.append(segment)
        
        # Vertical segments (for horizontal terrain boundaries)
        for x in range(0, self.grid_width, sample_step):
            for y in range(self.grid_height - 1):
                current_solid = self.height_field[y][x] > self.threshold
                next_solid = self.height_field[y + 1][x] > self.threshold
                
                # Create horizontal segment when transitioning from open to solid
                if not current_solid and next_solid:
                    world_x1 = x * self.scale_x
                    world_x2 = min((x + sample_step) * self.scale_x, world_width)
                    world_y = (y + 1) * self.scale_y
                    
                    segment = pymunk.Segment(body, (world_x1, world_y), (world_x2, world_y), 1)
                    shapes.append(segment)
                    
                # Create horizontal segment when transitioning from solid to open
                elif current_solid and not next_solid:
                    world_x1 = x * self.scale_x
                    world_x2 = min((x + sample_step) * self.scale_x, world_width)
                    world_y = (y + 1) * self.scale_y
                    
                    segment = pymunk.Segment(body, (world_x1, world_y), (world_x2, world_y), 1)
                    shapes.append(segment)
        
        return shapes
