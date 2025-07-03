"""
Marble factory for creating and positioning marbles in the simulation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import math
from typing import List, Tuple
import rng
from physics import Marble


class MarbleFactory:
    """Factory class for creating and positioning marbles"""
    
    @staticmethod
    def generate_colors(count: int) -> List[Tuple[int, int, int]]:
        """Generate visually distinct colors for marbles"""
        from config import get_config
        cfg = get_config()
        
        colors = []
        for i in range(count):
            # Use simple HSV to RGB conversion with configurable saturation and value
            hue = (i * 360 / count) % 360
            saturation = cfg.simulation.MARBLE_COLOR_SATURATION
            value = cfg.simulation.MARBLE_COLOR_VALUE
            
            # Convert HSV to RGB
            c = value * saturation
            x = c * (1 - abs((hue / 60) % 2 - 1))
            m = value - c
            
            if 0 <= hue < 60:
                r, g, b = c, x, 0
            elif 60 <= hue < 120:
                r, g, b = x, c, 0
            elif 120 <= hue < 180:
                r, g, b = 0, c, x
            elif 180 <= hue < 240:
                r, g, b = 0, x, c
            elif 240 <= hue < 300:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x
            
            # Convert to 0-255 range and ensure valid values
            red = max(0, min(255, int((r + m) * 255)))
            green = max(0, min(255, int((g + m) * 255)))
            blue = max(0, min(255, int((b + m) * 255)))
            
            colors.append((red, green, blue))
        
        return colors
    
    @staticmethod
    def create_marbles(num_marbles: int, marble_radius: float, marble_speed: float, 
                      arena_width: int, arena_height: int, terrain_obstacles: List,
                      colors: List[Tuple[int, int, int]]) -> List[Marble]:
        """Create marbles with random positions that don't overlap with terrain"""
        marbles = []
        
        for i in range(num_marbles):
            attempts = 0
            while attempts < 200:  # More attempts due to terrain
                x = rng.uniform(marble_radius + 10, arena_width - marble_radius - 10)
                y = rng.uniform(marble_radius + 10, arena_height - marble_radius - 10)
                
                # Check if this position overlaps with existing marbles
                valid_position = True
                for existing_marble in marbles:
                    distance = math.sqrt((x - existing_marble.x)**2 + (y - existing_marble.y)**2)
                    if distance < (marble_radius + existing_marble.radius + 5):  # 5px buffer
                        valid_position = False
                        break
                
                # Check if this position overlaps with terrain
                if valid_position:
                    for obstacle in terrain_obstacles:
                        if obstacle.check_collision(x, y, marble_radius + 5):  # Extra buffer
                            valid_position = False
                            break
                
                if valid_position:
                    marble = Marble(x, y, marble_radius, colors[i], marble_speed)
                    marbles.append(marble)
                    break
                
                attempts += 1
        
        return marbles
