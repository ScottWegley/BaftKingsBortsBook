"""
Physics module for the marble race simulation.

This module contains all physics-related classes and functionality,
including marble physics, collision detection, and physics constants.
"""

from .marble import Marble
from .collision import CollisionDetector

__all__ = ['Marble', 'CollisionDetector']
