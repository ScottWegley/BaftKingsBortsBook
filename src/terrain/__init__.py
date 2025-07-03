"""
Terrain generation module for the marble race simulation.

This module contains all terrain-related classes and functionality,
including procedural generation, height fields, and terrain obstacles.
"""

from .generator import FlowingTerrainGenerator
from .obstacle import FlowingTerrainObstacle

__all__ = ['FlowingTerrainGenerator', 'FlowingTerrainObstacle']
