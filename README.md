# Fly-in

*This project has been created as part of the 42 curriculum by ainradan.*

---

## Description

**Fly-in** is a drone routing and simulation project that moves a fleet of drones from a
designated *start hub* to an *end hub* through a network of interconnected zones. The goal
is to compute and display the **smallest possible number of simulation turns** required to
deliver every drone, while strictly respecting:

- **Zone capacities** (`max_drones`) — how many drones may occupy a hub simultaneously.
- **Link capacities** (`max_link_capacity`) — how many drones may traverse a connection
  during a single turn.
- **Zone types** — `normal`, `priority`, `restricted` (costs 2 turns to enter), and
  `blocked` (impassable).
- **Movement rules** — drones move one hop per turn; multi-turn transits into restricted
  zones are honored end-to-end.

The project ships two tightly integrated components:

1. **A discrete, turn-based simulation engine** — deterministic, score-oriented, and
   fully printable to stdout. This is what determines the answer.
2. **A real-time 3D visualization** — built on `raylib`/`pyray`, providing an interactive
   window where the user can watch the fleet execute the computed solution turn-by-turn.

### Goals

- Minimize the number of turns to route all drones end-to-end.
- Never violate capacity, zone, or link constraints at any turn.
- Provide a clear, interactive view of the solution for debugging and demonstration.

---

## Features

- Dijkstra-based pathfinding with zone-cost weighting.
- Greedy load-balancing penalties to spread drones across distinct lanes.
- Feedback-loop lane-pool selection: the simulator itself judges which candidate
  assignment wins (see *Algorithm* below).
- Fully deterministic, turn-based simulation engine with capacity validation.
- Support for `normal`, `restricted`, `priority`, and `blocked` zone types.
- Per-hub metadata: `color`, `zone`, `max_drones`.
- Per-connection metadata: `max_link_capacity`.
- Interactive 3D visualization:
  - Animated water shader background.
  - Cel-shaded hub models with ground planes.
  - Rotating drone models with color-coded labels.
  - Click any hub to inspect its properties.
  - Play/pause the simulation with the space bar.
  - Fullscreen toggle with `F`.
- Comprehensive map parser with strict validation and helpful error messages.

---

## Instructions

### Requirements

- **Python 3.10+**
- A working OpenGL context (for the 3D visualization).
- The `raylib` / `pyray` Python bindings (installed via `make install`).

### Installation

```bash
# Install dependencies into your environment
make install
```

### Running

```bash
# Run with the default map
make run

# Run with a specific map
make run MAP=maps/example.txt

# Or invoke the entry point directly
python3 main.py maps/example.txt
```

> The program accepts a map path as its **first positional argument**. If omitted, it
> defaults to `maps/easy/01_linear_path.txt`.

### Other Makefile Targets

```bash
make debug        # Run under the debugger / with verbose output
make lint         # Standard linting
make lint-strict  # Strict linting (CI-equivalent)
make re           # Clean and reinstall
make freeze       # Freeze dependencies into requirements.txt
```

### Controls (in the 3D scene)

| Input                     | Action                                   |
|---------------------------|------------------------------------------|
| **Left Mouse Drag**       | Pan the camera across the map            |
| **Mouse Wheel**           | Zoom (adjust camera field of view)       |
| **Left Click on Hub**     | Open the hub info panel                  |
| **Left Click elsewhere**  | Close the info panel                     |
| **Space**                 | Play / Pause the simulation              |
| **Space (after end)**     | Restart the simulation from turn 0       |
| **F**                     | Toggle fullscreen                        |
| **Esc**                   | Quit the program                         |

### Example Input

```
nb_drones: 4
start_hub: start 0 0 [color=green]
end_hub:   goal  8 8 [color=red]
hub:       mid1  4 0 [zone=priority]
hub:       mid2  4 4 [zone=restricted]
hub:       mid3  4 8

connection: start-mid1
connection: mid1-mid2
connection: mid2-mid3
connection: mid3-goal
```

### Example Output (stdout excerpt)

```
D1-mid1 D2-mid1 D3-mid1 D4-mid1
D1-mid2 D2-mid2
D3-mid2 D4-mid2
D1-mid3 D2-mid3
D3-mid3 D4-mid3
D1-goal D2-goal
D3-goal D4-goal

Total turns: 7
```

Each line is one simulation turn; each token `Dn-hub` (or `Dn-src-dst` for a
multi-turn restricted-zone transit) is one drone move.

---

## Algorithm

### Overview

The solver combines **Dijkstra's shortest-path algorithm**, **greedy load-balancing
penalties**, and a **simulation-driven feedback loop** to pick the best amount of route
diversity.

### 1. Zone-cost weighted Dijkstra

`PathFinder.find_path(start, end, hub_penalty)` runs Dijkstra over the hub graph. The cost
model is:

| Zone type    | Entry cost          |
|--------------|---------------------|
| `normal`     | `1`                 |
| `priority`   | `1 - 0.1` (bonus)   |
| `restricted` | `2`                 |
| `blocked`    | `∞` (not enterable) |

Additionally, a caller-supplied `hub_penalty` dict adds a per-hub surcharge to discourage
routes through hubs that are already congested.

### 2. Lane-pool construction

`PathFinder._build_lane_pool(size)` generates up to `size` **mutually diverse** start→end
paths. After each lane is computed, every intermediate hub on that lane receives a penalty
proportional to:

```
weight = RESTRICTED_PENALTY_WEIGHT / hub.max_drones
       (+ RESTRICTED_PENALTY_WEIGHT if the hub is restricted)
```

So subsequent lanes naturally route *around* hubs used by earlier lanes instead of piling
onto them.

### 3. Simulate-the-candidate feedback loop

Rather than committing to a fixed number of lanes, `assign_paths()`:

1. Builds lane pools of size `1, 2, …, MAX_LANES (= 6)`.
2. Round-robins the drones across each pool (`lanes[i % len(lanes)]`).
3. Silently runs a full `Simulation` on each candidate.
4. Keeps the candidate with the **fewest simulated turns**.

This is a cheap feedback loop: rather than guessing the right amount of path diversity,
the *actual* simulator judges which candidate is best. The caller then runs the winning
assignment once through the public `Simulation` (optionally verbose) to display it.

### 4. Turn-based simulation

Each turn of `Simulation.run()` processes drones in three ordered phases:

1. **Transit resolution** — drones in a restricted-zone transit decrement
   `transit_turns`; those reaching 0 arrive at their target and are marked
   `just_arrived` (so they cannot be re-selected this same turn — this preserves the
   2-turn cost).
2. **Movement planning** — idle drones (sorted by `drone_id` for determinism) attempt
   to advance one hop. A move is planned only if both the link capacity and the
   destination zone capacity (accounting for in-flight departures and arrivals within
   the same turn) permit it.
3. **Commit** — planned moves are applied. Restricted-zone entries enter the
   `transit` state, reserving both the link and the destination slot until arrival.

The loop exits when all drones reach the end hub or after `max_turns = 10000`.

### Complexity

- Single Dijkstra call: **O((V + E) · log V)** where V = hubs, E = connections.
- Lane-pool build (≤ 6 Dijkstras): **O(6 · (V + E) · log V)** — constant factor.
- Candidate simulation: **O(T · D)** per candidate, where T = turns and D = drones.
- Global assignment: **O((V + E) · log V + D · V)** in practice, with a small constant
  from the bounded lane-pool size.
- **Space**: **O(D · V)** to store all drone paths.

### Scoring

**Fewer total turns = better score.** The full turn-by-turn transcript is printed to
stdout so the result is human-auditable.

---

## Visual Representation

The 3D window is not just decoration — it makes the abstract solution **auditable at a
glance**:

- **Animated water plane** (custom GLSL shader) — frames the scene and gives immediate
  spatial context; the same shader runs on the menu screen.
- **Hub models** — loaded from `hub.glb` and scaled; each hub draws a colored ground
  plane beneath it whose color comes from the map's `color=` metadata, or animates as a
  rainbow hue cycling when `color=rainbow`.
- **Connection lines** — drawn as 3D lines, so the graph topology is visible without
  having to read the map file.
- **Drone models** — each drone is drawn from `Drone.glb` with a small colored sphere
  underneath in its palette color; drones rotate continuously so they are clearly
  identifiable.
- **Drone labels** — drawn in screen space above each drone, matching its palette color,
  so the user can correlate tokens in the stdout transcript with the visual scene.
- **Hub info panel** — clicking a hub opens a floating panel showing its name,
  coordinates, `max_drones`, color, and zone type.
- **Turn counter / status bar** — always shows `Turn N / M`, `Ready`, or
  `Done in M turns`, plus the controls hint.
- **Play/pause stepping** — the space bar toggles playback; when the simulation is
  finished, pressing space again restarts it from turn 0.

Together, these features turn a turn-based integer transcript into a **visual story**:
where drones start, which lanes they take, where congestion occurs, and how the solver
distributed them.

---

## Technical Choices

- **Dijkstra over A\*** — the graph is small and non-spatial (heuristics are weak on
  weighted zone costs), so A\* buys little. Dijkstra is simpler and exact.
- **Feedback loop over fixed lane count** — the number of useful lanes depends heavily on
  the map topology; hard-coding it either over- or under-uses links. Simulating candidates
  is cheap (graphs are small) and provably picks the best of the tried pool sizes.
- **Deterministic tie-breaking** — candidates are sorted by `drone_id` before planning,
  making simulations reproducible for any given path assignment.
- **Restricted-zone 2-turn cost enforced in the engine** — the `transit` state is a
  first-class simulation concept, not a post-processing hack. Drones cannot "land and
  immediately re-depart" in the same turn.
- **Strict parser** — duplicates, unknown directives, malformed options, and invalid zone
  types all raise `ParseError` with the offending line number, so map authors get precise
  feedback.

---

## Project Structure

```
.
├── main.py           # Entry point, window loop, scene switching
├── menu_window.py    # Animated main menu scene
├── game_window.py    # 3D simulation scene (camera, rendering, playback)
├── models.py         # Dataclasses: Hub, Connection, Drone, MapData, enums
├── parse.py          # MapParser — strict map-file reader
├── pathfinder.py     # PathFinder — Dijkstra + lane-pool assignment
├── simulation.py     # Simulation — turn-based engine
├── utils.py          # Constants, color maps, load_map helper
├── water.vert/.frag  # Animated water shader
├── hub.glb, Drone.glb, sky.jpg
├── maps/             # Example maps (easy / medium / hard / …)
└── README.md
```

---

## Example input and expected output demonstrating

Map representation
```txt
# Easy Level 1: Simple linear path
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```
---

Input:
```shell
# running with make file
$% make run MAP=maps/easy/01_linear_path.txt

# running with python3 ensure venv is activated
(.venv) $% python3 main.py maps/easy/01_linear_path.txt
```

---

Output:
```shell
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal

Total turns: 4
```

## Resources

### Documentation & Tutorials

- [Dijkstra's shortest-path algorithm (video)](https://www.youtube.com/watch?v=bZkzH5x0SKU&t=83s)
- [raylib Python (pyray) documentation](https://electronstudio.github.io/raylib-python-cffi/)
- [PEP 257 — Docstring conventions](https://peps.python.org/pep-0257/)
- [OpenGL Shading Language reference](https://www.khronos.org/opengl/wiki/OpenGL_Shading_Language)
- [Python `heapq` documentation](https://docs.python.org/3/library/heapq.html)
- [Python `dataclasses` documentation](https://docs.python.org/3/library/dataclasses.html)

### AI Usage

AI was used to across the codebase (type hints, dataclass design, enum layout). It was also used to
draft the initial docstring structure following PEP 257.

Every algorithmic decision — Dijkstra weighting, the lane-pool feedback loop, deterministic
tie-breaking, and the `just_arrived` guard — was reasoned through by the author and tested
against concrete maps.

---