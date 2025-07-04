"""
Noise generation utilities for terrain creation.
"""

import math


class NoiseGenerator:
    """Simple noise generation for terrain features"""
    
    @staticmethod
    def perlin_noise_2d(x: float, y: float, scale: float = 1.0) -> float:
        """Generate Perlin-like noise at given coordinates"""
        # Use deterministic pseudo-random values based on coordinates
        x_scaled = x * scale
        y_scaled = y * scale
        
        # Get integer grid points
        x0 = int(x_scaled)
        y0 = int(y_scaled)
        x1 = x0 + 1
        y1 = y0 + 1
        
        # Get fractional parts
        fx = x_scaled - x0
        fy = y_scaled - y0
        
        # Generate corner values using hash-like function
        def noise_at(xi: int, yi: int) -> float:
            # Simple hash function for consistent pseudo-random values
            seed = ((xi * 374761393) ^ (yi * 668265263)) & 0x7FFFFFFF
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            return (seed / 0x7FFFFFFF) * 2.0 - 1.0
        
        # Get corner values
        n00 = noise_at(x0, y0)
        n10 = noise_at(x1, y0)
        n01 = noise_at(x0, y1)
        n11 = noise_at(x1, y1)
        
        # Smooth interpolation
        def smoothstep(t: float) -> float:
            return t * t * (3 - 2 * t)
        
        sx = smoothstep(fx)
        sy = smoothstep(fy)
        
        # Bilinear interpolation
        nx0 = n00 + sx * (n10 - n00)
        nx1 = n01 + sx * (n11 - n01)
        
        return nx0 + sy * (nx1 - nx0)
    
    @staticmethod
    def octave_noise(x: float, y: float, octaves: int = 4, persistence: float = 0.5, 
                    scale: float = 1.0) -> float:
        """Generate noise with multiple octaves for more complex patterns"""
        value = 0.0
        amplitude = 1.0
        frequency = scale
        max_value = 0.0
        
        for _ in range(octaves):
            value += NoiseGenerator.perlin_noise_2d(x, y, frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2.0
        
        return value / max_value
