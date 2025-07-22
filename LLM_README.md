

# Marble Race Simulation

A modular, physics-based simulation of marbles racing on procedurally generated flowing terrain.

---


## Project Overview

- All functionality runs through `src/main.py`.
- Discord notifications are integrated and sent automatically when using the `--output` flag (unless `--no-discord` is specified).
- Functionality is organized into modules for integrations, results, simulation, terrain, physics, and rendering.
- GitHub Actions workflows are streamlined for CI/CD.
- Results are saved to the correct directory based on the `--canon` flag.
- All settings are centralized and configurable in `src/config.py`.

---


## Usage

Run the simulation with:
```bash
python src/main.py --canon --output --headless
```

Options:
- `--no-discord` - Disables Discord notifications even with `--output`
- `--canon` - Saves results to `results/canon/` instead of `results/misc/`

---


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
  - `integrations/`: External service integrations (Discord webhooks)
  - `results/`: Results storage and management


---


## Core Concepts

- **Configuration System**: All simulation, terrain, and rendering parameters are centralized in `config.py` using a class-based system. Supports global, per-game-mode, and runtime overrides. Easily extensible for new game modes.
- **Marble Physics**: Constant speed, elastic collisions, boundary handling. Physics can use custom or pymunk-based collision systems.
- **Terrain**: Procedurally generated using noise, carving, and validation for realistic, flowing arenas. Terrain complexity and features are highly configurable.
- **Zones**: Spawn/goal zones are placed and validated for clear paths and fair starts/goals using exhaustive search and wave simulation.
- **Simulation**: Supports both real-time graphics and fast headless execution. Results and progress can be saved and analyzed.



---



## Dependencies

- Required: `pygame`, `requests`
- Optional (for advanced terrain): `numpy`, `scipy`, `scikit-image`

---



## Discord Integration

- Configure Discord webhook URLs in a `.env` file or environment variables
- Set `DEV_REPORT_WEBHOOK_URL` for race notifications
- Discord notifications are sent automatically when using the `--output` flag (unless `--no-discord` is specified)
- Race start, completion with video, and winner announcement messages are included

Configuration options:
- `.env` file with `DEV_REPORT_WEBHOOK_URL`
- Environment variables
- Config classes in `src/config.py`



---


## Character System

- Each marble is a character, with an `id`, `name`, and a list of `costumes` (must include "default").
- Character assets are stored in `assets/characters/{id}/{costume}.png` (e.g., `assets/characters/redbird/default.png`).
- The number of marbles is capped at the number of available characters. If more are requested, only as many as there are characters will spawn.
- To add a character, edit `src/characters.py` and add to the `CHARACTERS` list.
- Each character image should be a 30x30 PNG (matching the marble's diameter), with the main visual centered and fitting within a 15px radius circle.
- The marble's collision shape is always a circle; only the visual changes.


---


## Extensibility & Customization

- The modular design allows physics, terrain, rendering, simulation, and characters to be extended or tested independently.
- **Game Modes**: Add new game modes by subclassing the configuration classes and adding logic in `game_modes/`. Register new modes in `config.py`'s `GAME_MODE_CONFIGS`.
- **Configuration**: All parameters (marble size, speed, terrain complexity, zone placement, etc.) are easily adjustable in `config.py` or at runtime.


---


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
