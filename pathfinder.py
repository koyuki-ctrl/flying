"""Pathfinding module for the FLY-ing drone simulation.

Provides a `PathFinder` class that uses Dijkstra's algorithm with zone
costs and hub penalties to find optimal paths, and to assign a full
set of drone paths for a map.

This is a cheap form of a feedback loop: rather than guessing the
right amount of path diversity, let the simulator itself judge which
candidate is best.
"""

from __future__ import annotations
import heapq
from collections import defaultdict
from typing import Optional
from simulation import Simulation

from models import MapData, ZoneType


class PathFinder:
    """Computes drone paths across a single map.

    A `PathFinder` is bound to one `MapData` instance and exposes
    Dijkstra-based single-path search as well as full-fleet path
    assignment that uses a simulated feedback loop to pick the best
    amount of route diversity.

    Attributes:
        data: The map data this pathfinder searches over.
    """

    RESTRICTED_PENALTY_WEIGHT = 3.0
    """Extra cost added to a restricted hub each time a lane uses it,
    so later lanes are encouraged to route around it."""

    MAX_LANES = 6
    """Largest lane-pool size tried when assigning paths."""

    PRIORITY_BONUS = -0.1
    """Small cost discount applied to priority-zone hubs during search."""

    def __init__(self, data: MapData) -> None:
        """Bind this pathfinder to a map.

        Args:
            data: The map data containing hubs and connections.
        """
        self.data = data

    def get_zone_cost(self, hub_name: str) -> int | float:
        """Return the movement cost (in turns) to enter this hub's zone.

        - Normal: 1
        - Priority: 1
        - Restricted: 2
        - Blocked: infinite (not traversable)

        Args:
            hub_name: Name of the hub to evaluate.

        Returns:
            The cost, or float('inf') if the hub cannot be entered.
        """
        hub = self.data.hubs.get(hub_name)
        if hub is None:
            return 1
        if hub.zone_type == ZoneType.BLOCKED:
            return float('inf')
        if hub.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1

    def find_path(
        self,
        start: str,
        end: str,
        hub_penalty: Optional[dict[str, float]] = None,
    ) -> list[str]:
        """Find the lowest-cost path using Dijkstra with zone costs.

        The cost of a path is the sum of costs to enter each hub
        (including the end but excluding the start). Restricted zones
        cost 2 turns, normal/priority cost 1. Priority zones receive a
        small bonus to encourage their use.

        Args:
            start: Name of the starting hub.
            end: Name of the destination hub.
            hub_penalty: Optional penalties to discourage congested hubs.

        Returns:
            A list of hub names from start to end inclusive, or an
            empty list if no path exists.
        """
        if hub_penalty is None:
            hub_penalty = {}

        priority_q: list[
            tuple[float, str, list[str]]] = [(0.0, start, [start])]
        visited: set[str] = set()

        while priority_q:
            cost, current, path = heapq.heappop(priority_q)
            if current == end:
                return path

            if current in visited:
                continue
            visited.add(current)

            for neighbor in self.data.neighbors.get(current, set()):
                neighbors = self.data.hubs.get(neighbor)
                if neighbors is None:
                    continue

                zone_cost = self.get_zone_cost(neighbor)
                if zone_cost == float('inf'):
                    continue

                penalty = hub_penalty.get(neighbor, 0)
                priority_bonus = (
                    self.PRIORITY_BONUS
                    if neighbors.zone_type == ZoneType.PRIORITY else 0.0
                )

                new_cost = cost + zone_cost + penalty + priority_bonus
                heapq.heappush(
                    priority_q, (new_cost, neighbor, path + [neighbor])
                )
        return []

    def _build_lane_pool(self, size: int) -> list[list[str]]:
        """Compute up to `size` mutually diverse start-to-end lane paths.

        Each successive lane is found with restricted hubs already used
        by earlier lanes penalized, so later lanes tend to route around
        them instead of adding to their congestion.

        Args:
            size: The desired number of lanes.

        Returns:
            A list of up to `size` distinct paths (fewer if the graph
            doesn't offer that many alternatives).
        """
        assert self.data.start_hub is not None
        assert self.data.end_hub is not None
        hub_penalty: dict[str, float] = defaultdict(float)
        lanes: list[list[str]] = []

        for _ in range(size):
            path = self.find_path(
                self.data.start_hub, self.data.end_hub, dict(hub_penalty)
            )
            if not path:
                break
            lanes.append(path)
            for hub_name in path[1:-1]:
                hub = self.data.hubs.get(hub_name)
                if hub is None:
                    continue
                capacity = hub.max_drones or 1
                weight = self.RESTRICTED_PENALTY_WEIGHT / capacity
                if hub.zone_type == ZoneType.RESTRICTED:
                    weight += self.RESTRICTED_PENALTY_WEIGHT
                hub_penalty[hub_name] += weight

        return lanes

    def _simulate_candidate(self, candidate: list[list[str]]) -> Simulation:
        """Run a silent simulation of a candidate path assignment.

        Args:
            candidate: One path per drone.

        Returns:
            The `Simulation` instance after running to completion (or
            hitting the turn limit).
        """
        sim = Simulation(self.data, candidate)
        sim.run()
        return sim

    def assign_paths(self) -> list[list[str]]:
        """Assign an independent path for each drone from start to end.

        Rather than compute one increasingly-penalized path per drone,
        this builds a small pool of diverse lane paths, round-robins
        drones across it, and picks the pool size that actually
        minimizes the simulated turn count -- letting real congestion
        (not a fixed heuristic) decide how much route diversity is
        worth it.

        Every candidate pool size tried here is simulated silently
        (`verbose=False`): this is just an internal search to pick the
        best lane count, not the simulation that should be shown to
        the user. The caller is expected to run the returned paths
        through its own `Simulation` once (optionally with
        `verbose=True`) to display the turn-by-turn output exactly
        one time.

        Returns:
            A list of paths, one per drone. Each path is a list of hub
            names.
        """
        if self.data.start_hub is None or self.data.end_hub is None:
            return [[] for _ in range(self.data.nb_drones)]

        best_paths: Optional[list[list[str]]] = None
        best_turns = float('inf')

        for size in range(1, self.MAX_LANES + 1):
            lanes = self._build_lane_pool(size)
            if not lanes:
                continue
            candidate = [
                lanes[i % len(lanes)] for i in range(self.data.nb_drones)
            ]
            sim = self._simulate_candidate(candidate)
            if sim.finished and len(sim.turns) < best_turns:
                best_turns = len(sim.turns)
                best_paths = candidate
            if len(lanes) < size:
                break

        if best_paths is not None:
            return best_paths

        single = self.find_path(self.data.start_hub, self.data.end_hub)
        return [single for _ in range(self.data.nb_drones)]
