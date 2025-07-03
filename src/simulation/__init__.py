"""
Simulation module for the marble race simulation.

This module contains all simulation-related classes and functionality,
including simulation management, marble creation, and run modes.
"""

from .manager import SimulationManager
from .runner import run_graphics_mode, run_headless_mode
from .marble_factory import MarbleFactory

__all__ = ['SimulationManager', 'run_graphics_mode', 'run_headless_mode', 'MarbleFactory']
