*This project has been created as part of the 42 curriculum by ainradan.*

# Fly-in

## Description
Fly-in routes a fleet of drones from a start zone to an end zone through a network of connected zones. It minimizes simulation turns while respecting zone capacities, link capacities, and movement constraints (normal, restricted, priority, blocked zones).

The project includes both a **discrete turn-based simulation engine** (for scoring) and a **3D real-time visualization** using raylib/pyray.

## Instructions
```bash
# Install dependencies
make install

# Run the 3D visualization (default map: maps/easy/01_linear_path.txt)
make run

# Run with a custom map
make run MAP=maps/example.txt

# Or directly
python3 main.py maps/example.txt

# Debug mode
make debug

# Linting
make lint
make lint-strict
```

## Algorithm
- **Pathfinding**: Dijkstra with zone-cost weighting and greedy load-balancing penalties so drones spread across multiple paths.
- **Simulation**: Discrete turn-based engine. Each turn:
  1. Drones in transit (restricted zones) arrive at their destination.
  2. All idle drones attempt to move simultaneously.
  3. Movements are validated against zone occupancy (`max_drones`) and link capacity (`max_link_capacity`).
  4. Drones that cannot move wait in place.
- **Scoring**: Fewer total turns = better score. The exact turn-by-turn output is printed to stdout.

## Visual Representation
- 3D scene with animated water shader, cel-shaded hubs, and drone models.
- Click a hub to inspect its properties.
- Use **Space** to play/pause the simulation, or **Prev/Next** buttons to step through turns manually.

## Resources
- Dijkstra's shortest-path algorithm
- Python `typing` module & `mypy` static analysis
- PEP 257 docstring conventions
- raylib / pyray for 3D rendering

## AI Usage
AI was used to scaffold the simulation engine architecture and ensure type safety. All pathfinding logic, capacity rules, turn-based mechanics, and visual integration were designed and verified manually.
