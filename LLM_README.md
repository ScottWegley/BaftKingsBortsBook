
# Marble Race Simulation

A modular, physics-based simulation of marbles racing on procedurally generated flowing terrain.

## Structure

- `src/`
  - `main.py`: CLI entry point
  - `config.py`: Centralized configuration for all simulation, terrain, and rendering parameters. Supports game mode-specific overrides and runtime changes.
  - `rng.py`: Random number generation (seeded, deterministic, supports date/random/user-set modes)
  - `physics/`: Marble physics, collision detection (custom and pymunk-based), and marble object logic
  - `terrain/`: Terrain generation (height fields, obstacles, noise, carving, and validation)
  - `rendering/`: Pygame-based graphics and UI rendering
  - `simulation/`: Simulation orchestration, marble management, and run modes
  - `game_modes/`: Game logic, zone validation, and extensible game mode support

## Core Concepts

- **Configuration System**: All simulation, terrain, and rendering parameters are centralized in `config.py` using a class-based system. Supports global, per-game-mode, and runtime overrides. Easily extensible for new game modes.
- **Marble Physics**: Constant speed, elastic collisions, boundary handling. Physics can use custom or pymunk-based collision systems.
- **Terrain**: Procedurally generated using noise, carving, and validation for realistic, flowing arenas. Terrain complexity and features are highly configurable.
- **Zones**: Spawn/goal zones are placed and validated for clear paths and fair starts/goals using exhaustive search and wave simulation.
- **Simulation**: Supports both real-time graphics and fast headless execution. Results and progress can be saved and analyzed.


## Usage

- CLI options: number of marbles, terrain complexity, arena size, execution mode, RNG seed/mode.
- Game mode can be set at runtime; configuration is accessible via `get_config()` and can be changed with `set_game_mode()`.
- Results and simulation progress can be saved for later analysis.
- `--output` saves a video (MP4) of the simulation to the output folder. GIF output is no longer supported.

## Dependencies

- Required: `pygame`
- Optional (for advanced terrain): `numpy`, `scipy`, `scikit-image`


## Character System

- Marbles are now characters, each with an `id`, `name`, and a list of `costumes` (must include "default").
- Character assets are stored in `assets/characters/{id}/{costume}.png` (e.g., `assets/characters/redbird/default.png`).
- The number of marbles is capped at the number of available characters. If more are requested, only as many as there are characters will spawn.
- To add a character, edit `src/characters.py` and add to the `CHARACTERS` list.
- Each character image should be a 30x30 PNG (matching the marble's diameter), with the main visual centered and fitting within a 15px radius circle.
- The marble's collision shape remains a circle; only the visual changes.

## Extensibility & Customization

- Modular design: Physics, terrain, rendering, simulation, and characters are decoupled for easy extension/testing.
- **Game Modes**: Add new game modes by subclassing the configuration classes and adding logic in `game_modes/`. Register new modes in `config.py`'s `GAME_MODE_CONFIGS`.
- **Configuration**: All parameters (marble size, speed, terrain complexity, zone placement, etc.) are easily adjustable in `config.py` or at runtime.

## Configuration System Overview

The configuration system is class-based and supports both global and per-game-mode overrides. Main config classes:

- `SimulationConfig`: Physics and simulation parameters (marble count, speed, collision, etc.)
- `TerrainConfig`: Arena size, terrain complexity, noise, carving, and obstacle parameters
- `RenderingConfig`: Graphics/UI settings (window, colors, FPS, etc.)
- Game mode-specific configs (e.g., `IndivRaceSimulationConfig`) inherit from these and override as needed.
- The global `Config` object manages the active configuration and can be switched at runtime.

To access or change configuration in code:

```python
from config import get_config, set_game_mode
cfg = get_config()
set_game_mode("indiv_race")  # or your custom mode
print(cfg.simulation.NUM_MARBLES)
```
