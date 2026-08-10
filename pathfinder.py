"""Pathfinding module for the FLY-ing drone simulation.

Implements Dijkstra-based pathfinding with hub penalties to distribute
drone traffic across the map and avoid congestion at intermediate hubs.
"""

from __future__ import annotations
import heapq
from collections import defaultdict
from typing import Optional

from models import MapData, ZoneType


def find_path(
    data: MapData,
    start: str,
    end: str,
    hub_penalty: Optional[dict[str, int]] = None,
) -> list[str]:
    """Find the lowest-cost path between two hubs using Dijkstra's algorithm.

    The search respects zone costs, optional hub penalties, and avoids
    blocked zones. Priority zones receive a slight cost bonus to encourage
    routing through them.

    Args:
        data: The map data containing hubs, connections, and zone information.
        start: Name of the starting hub.
        end: Name of the destination hub.
        hub_penalty: Optional dictionary mapping hub names to additional
            cost penalties, used to discourage reusing congested hubs.

    Returns:
        A list of hub names from start to end inclusive, or an empty list
        if no valid path exists.
    """
    if hub_penalty is None:
        hub_penalty = {}

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
            if hub is None or hub.zone_type == ZoneType.BLOCKED:
                continue

            zone_cost = data.get_zone_cost(neighbor)
            penalty = hub_penalty.get(neighbor, 0)
            priority_bonus = (
                -0.1 if hub.zone_type == ZoneType.PRIORITY else 0.0)
            new_cost = cost + zone_cost + penalty + priority_bonus
            heapq.heappush(pq, (new_cost, neighbor, path + [neighbor]))

    return []


def assign_paths(data: MapData) -> list[list[str]]:
    """Assign an independent path for each drone from start to end.

    Paths are computed sequentially with increasing penalties on hubs
    already used by previous drones, promoting route diversity and
    reducing hub congestion.

    Args:
        data: The map data for the simulation.

    Returns:
        A list of paths, one per drone. Each path is a list of hub names.
        If start or end hubs are missing, returns a list of empty paths.
    """
    if data.start_hub is None or data.end_hub is None:
        return [[] for _ in range(data.nb_drones)]

    paths: list[list[str]] = []
    hub_penalty: dict[str, int] = defaultdict(int)

    for _ in range(data.nb_drones):
        path = find_path(data, data.start_hub, data.end_hub, dict(hub_penalty))
        if not path:
            path = []
        paths.append(path)
        for hub_name in path[1:-1]:
            hub_penalty[hub_name] += 2

    return paths
