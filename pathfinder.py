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
