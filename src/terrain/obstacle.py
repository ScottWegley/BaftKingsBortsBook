"""
Terrain obstacle classes for collision detection and rendering.
"""

import math
from typing import List, Tuple
import pygame


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
        """Check collision with flowing terrain"""
        # Convert world coordinates to grid coordinates
        grid_x = int(marble_x / self.scale_x)
        grid_y = int(marble_y / self.scale_y)
        
        # Check bounds
        if grid_x < 0 or grid_x >= self.grid_width or grid_y < 0 or grid_y >= self.grid_height:
            return False
        
        # Sample height at marble position
        height = self.height_field[grid_y][grid_x]
        
        # Check if marble is inside terrain (height above threshold)
        if height > self.threshold:
            return True
        
        # Check nearby points for radius collision
        radius_samples = max(1, int(marble_radius / min(self.scale_x, self.scale_y)))
        
        for dy in range(-radius_samples, radius_samples + 1):
            for dx in range(-radius_samples, radius_samples + 1):
                sample_x = grid_x + dx
                sample_y = grid_y + dy
                
                if (0 <= sample_x < self.grid_width and 0 <= sample_y < self.grid_height):
                    # Check if this sample point is within marble radius
                    world_sample_x = sample_x * self.scale_x
                    world_sample_y = sample_y * self.scale_y
                    distance = math.sqrt((marble_x - world_sample_x)**2 + (marble_y - world_sample_y)**2)
                    
                    if distance <= marble_radius and self.height_field[sample_y][sample_x] > self.threshold:
                        return True
        
        return False
    
    def get_collision_normal(self, marble_x: float, marble_y: float) -> Tuple[float, float]:
        """Get collision normal from height field gradient"""
        # Convert to grid coordinates
        grid_x = int(marble_x / self.scale_x)
        grid_y = int(marble_y / self.scale_y)
        
        # Calculate gradient (surface normal)
        if 1 <= grid_x < self.grid_width - 1 and 1 <= grid_y < self.grid_height - 1:
            gradient_x = (self.height_field[grid_y][grid_x + 1] - self.height_field[grid_y][grid_x - 1]) * 0.5
            gradient_y = (self.height_field[grid_y + 1][grid_x] - self.height_field[grid_y - 1][grid_x]) * 0.5
            
            # Normal points away from higher terrain
            normal_x = -gradient_x
            normal_y = -gradient_y
            
            # Normalize
            length = math.sqrt(normal_x * normal_x + normal_y * normal_y)
            if length > 0:
                return (normal_x / length, normal_y / length)
        
        return (1, 0)  # Default normal
    
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
