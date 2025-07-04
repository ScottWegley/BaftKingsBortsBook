"""
Pymunk-based collision detection and resolution system for marble race simulation.

This is a compatibility layer that imports the new pymunk collision system
while maintaining the same API as the original collision system.
"""

# Import the new pymunk collision system
from .pymunk_collision import CollisionDetector

# Re-export for compatibility
__all__ = ['CollisionDetector']
