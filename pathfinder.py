"""Pathfinding module for the FLY-ing drone simulation.

Uses Dijkstra's algorithm with zone costs and hub penalties
to find optimal paths.

CHANGE vs. the original version: instead of computing one path per
drone with a penalty that keeps accumulating over all `nb_drones`
calls (which drags later drones onto increasingly long detours),
`assign_paths` now:

1. Computes a small pool of mutually diverse "lane" paths, penalizing
   `restricted` hubs specifically (a `restricted` hub only lets one
   drone through every 2 turns, so funneling everyone through the same
   one silently halves throughput -- a plain capacity-1 normal hub
   doesn't have that problem, since drones pass through it in 1 turn
   each and are already spaced out by upstream bottlenecks).
2. Round-robins drones across that lane pool for a few candidate pool
   sizes, actually *simulates* each candidate assignment, and keeps
   whichever pool size produced the fewest total turns.

This is a cheap form of the feedback loop described earlier: rather
than guessing the right amount of path diversity, let the simulator
itself judge which candidate is best.
"""

from __future__ import annotations
import heapq
from collections import defaultdict
from typing import Optional

from models import MapData, ZoneType
RESTRICTED_PENALTY_WEIGHT = 6.0
MAX_LANES = 6


def get_zone_cost(hub_name: str, data: MapData) -> (int | float):
    """Return the movement cost (in turns) to enter this hub's zone.

    - Normal: 1
    - Priority: 1
    - Restricted: 2
    - Blocked: infinite (not traversable)
    """
    hub = data.hubs.get(hub_name)
    if hub is None:
        return 1
    if hub.zone_type == ZoneType.BLOCKED:
        return float('inf')
    if hub.zone_type == ZoneType.RESTRICTED:
        return 2
    return 1


def find_path(
    data: MapData,
    start: str,
    end: str,
    hub_penalty: Optional[dict[str, float]] = None,
) -> list[str]:
    """Find the lowest-cost path using Dijkstra with zone costs and penalties.

    The cost of a path is the sum of costs to enter each hub (including the end
    but excluding the start). Restricted zones cost 2 turns,
    normal/priority cost 1.
    Priority zones receive a small bonus to encourage their use.

    Args:
        data: The map data containing hubs and connections.
        start: Name of the starting hub.
        end: Name of the destination hub.
        hub_penalty: Optional penalties to discourage congested hubs.

    Returns:
        A list of hub names from start to end inclusive, or an empty list.
    """
    if hub_penalty is None:
        hub_penalty = {}

    PRIORITY_BONUS = -0.1

    pq: list[tuple[float, str, list[str]]] = [(0.0, start, [start])]
    visited: set[str] = set()

    while pq:
        cost, current, path = heapq.heappop(pq)

        if current == end:
            return path

        if current in visited:
            continue
        visited.add(current)

        for neighbor in data.neighbors.get(current, set()):
            hub = data.hubs.get(neighbor)
            if hub is None:
                continue

            zone_cost = get_zone_cost(neighbor, data)
            if zone_cost == float('inf'):
                continue

            penalty = hub_penalty.get(neighbor, 0)
            priority_bonus = (
                PRIORITY_BONUS if hub.zone_type == ZoneType.PRIORITY else 0.0)

            new_cost = cost + zone_cost + penalty + priority_bonus
            heapq.heappush(pq, (new_cost, neighbor, path + [neighbor]))

    return []


def _build_lane_pool(data: MapData, size: int) -> list[list[str]]:
    """Compute up to `size` mutually diverse start-to-end lane paths.

    Each successive lane is found with restricted hubs already used by
    earlier lanes penalized, so later lanes tend to route around them
    instead of adding to their congestion.

    Args:
        data: The map data for the simulation.
        size: The desired number of lanes.

    Returns:
        A list of up to `size` distinct paths (fewer if the graph
        doesn't offer that many alternatives).
    """
    assert data.start_hub is not None and data.end_hub is not None
    hub_penalty: dict[str, float] = defaultdict(float)
    lanes: list[list[str]] = []

    for _ in range(size):
        path = find_path(data, data.start_hub, data.end_hub, dict(hub_penalty))
        if not path:
            break
        lanes.append(path)
        for hub_name in path[1:-1]:
            hub = data.hubs.get(hub_name)
            if hub is not None and hub.zone_type == ZoneType.RESTRICTED:
                hub_penalty[hub_name] += RESTRICTED_PENALTY_WEIGHT

    return lanes


def assign_paths(data: MapData) -> list[list[str]]:
    """Assign an independent path for each drone from start to end.

    Rather than compute one increasingly-penalized path per drone, this
    builds a small pool of diverse lane paths, round-robins drones
    across it, and picks the pool size that actually minimizes the
    simulated turn count -- letting real congestion (not a fixed
    heuristic) decide how much route diversity is worth it.

    Args:
        data: The map data for the simulation.

    Returns:
        A list of paths, one per drone. Each path is a list of hub names.
    """
    if data.start_hub is None or data.end_hub is None:
        return [[] for _ in range(data.nb_drones)]

    from simulation import Simulation

    best_paths: Optional[list[list[str]]] = None
    best_turns = float('inf')

    for size in range(1, MAX_LANES + 1):
        lanes = _build_lane_pool(data, size)
        if not lanes:
            continue
        candidate = [
            lanes[i % len(lanes)] for i in range(data.nb_drones)
        ]
        sim = Simulation(data, candidate)
        turns = sim.run()
        if sim.finished and len(turns) < best_turns:
            best_turns = len(turns)
            best_paths = candidate
        if len(lanes) < size:
            break

    if best_paths is not None:
        return best_paths

    single = find_path(data, data.start_hub, data.end_hub)
    return [single for _ in range(data.nb_drones)]
