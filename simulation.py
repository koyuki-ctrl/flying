"""Discrete simulation engine for the FLY-ing drone program.

Runs turn-based drone movement across a map, respecting hub capacities
and link capacities while advancing drones toward the destination hub.

CHANGES vs. the original version:
- Entering a `restricted` zone now genuinely costs 2 simulation turns
  (previously `Drone.transit_target` / `transit_turns` were defined in
  models.py but never actually used in `run()`, so every move cost 1
  turn regardless of zone type).
- A drone that finishes a multi-turn transit this turn can no longer be
  re-selected as a movement candidate in that same turn (previously it
  could "land" and immediately depart again in the same turn, silently
  cancelling the 2-turn cost).
"""

from __future__ import annotations
from collections import defaultdict
from models import Drone, MapData, ZoneType


class Simulation:
    """Manages the turn-based movement of drones across a map.

    Tracks drone states, zone occupancy, and link usage to compute
    a valid sequence of moves from the start hub to the end hub.

    Attributes:
        data: The map data defining hubs, connections, and capacities.
        drones: List of Drone objects participating in the simulation.
        zone_occupancy: Mapping from hub name to set of drone names present.
        turns: List of turn strings representing completed moves.
        finished: True when all drones have reached the end hub.
    """

    def __init__(self, data: MapData, paths: list[list[str]]) -> None:
        """Initialize the simulation with map data and precomputed paths.

        Args:
            data: Parsed map data containing hubs and connections.
            paths: List of routes, one per drone, as lists of hub names.
        """
        self.data = data
        self.drones: list[Drone] = []
        for i, path in enumerate(paths, start=1):
            self.drones.append(Drone(drone_id=i, path=path))

        self.zone_occupancy: dict[str, set[str]] = defaultdict(set)
        if data.start_hub:
            for d in self.drones:
                self.zone_occupancy[data.start_hub].add(d.name)

        self.turns: list[str] = []
        self.finished = False

    def _link_key(self, a: str, b: str) -> tuple[str, str]:
        """Return a canonical ordered tuple for a link between two hubs.

        Args:
            a: Name of the first hub.
            b: Name of the second hub.

        Returns:
            A tuple with hub names in lexicographical order.
        """
        return (a, b) if a <= b else (b, a)

    def _zone_capacity(self, hub_name: str) -> int:
        """Get the effective drone capacity for a hub.

        Start and end hubs are treated as having unlimited capacity.

        Args:
            hub_name: Name of the hub to query.

        Returns:
            The maximum number of drones allowed, or a very large number
            for unlimited-capacity hubs.
        """
        if self.data.is_capacity_unlimited(hub_name):
            return 999999
        hub = self.data.hubs.get(hub_name)
        return hub.max_drones if hub else 1

    def _link_capacity(self, hub1: str, hub2: str) -> int:
        """Get the maximum number of drones allowed on a link per turn.

        Args:
            hub1: Name of the first hub.
            hub2: Name of the second hub.

        Returns:
            The link capacity as defined in the map data, defaulting to 1.
        """
        return self.data.get_link_capacity(hub1, hub2)

    def _is_restricted_entry(self, hub_name: str) -> bool:
        """Check whether moving into this hub should cost 2 turns.

        The end hub is always treated as a normal (1-turn) arrival, even
        if it happens to be tagged `restricted`, since drones delivered
        to the end hub are immediately considered arrived.

        Args:
            hub_name: Name of the destination hub.

        Returns:
            True if entering this hub requires a 2-turn transit.
        """
        if hub_name == self.data.end_hub:
            return False
        hub = self.data.hubs.get(hub_name)
        return hub is not None and hub.zone_type == ZoneType.RESTRICTED

    def run(self) -> list[str]:
        """Execute the simulation until all drones arrive
        or a limit is reached.

        Each turn, eligible idle drones attempt to move to the next hub
        in their path, subject to link and zone capacity constraints.
        Moves into a `restricted` zone take 2 turns: the connection and
        the destination slot are reserved on departure, and the drone
        cannot be reassigned to a new move until it actually arrives.

        Returns:
            A list of turn strings,
            each containing space-separated move tokens.
        """
        max_turns = 10000
        turn_count = 0

        while turn_count < max_turns:
            turn_count += 1
            moves: list[str] = []
            just_arrived: set[str] = set()
            for d in self.drones:
                if d.state == "transit":
                    d.transit_turns -= 1
                    if d.transit_turns <= 0:
                        target = d.transit_target
                        if target:
                            d.state = "idle"
                            d.path_index += 1
                            d.transit_target = None
                            just_arrived.add(d.name)
                            if target == self.data.end_hub:
                                d.state = "arrived"
                            else:
                                self.zone_occupancy[target].add(d.name)
                            moves.append(f"{d.name}-{target}")

            link_usage: dict[tuple[str, str], int] = defaultdict(int)
            zone_departures: dict[str, int] = defaultdict(int)
            zone_arrivals: dict[str, int] = defaultdict(int)
            candidates = [
                d for d in self.drones
                if d.state == "idle"
                and d.name not in just_arrived
                and d.path
                and d.path_index < len(d.path) - 1
            ]
            candidates.sort(key=lambda d: d.drone_id)
            planned: list[tuple[Drone, str]] = []

            for d in candidates:
                current = d.path[d.path_index]
                next_hub = d.path[d.path_index + 1]

                lk = self._link_key(current, next_hub)
                if link_usage[lk] >= self._link_capacity(current, next_hub):
                    continue

                if not self.data.is_capacity_unlimited(next_hub):
                    occ = len(self.zone_occupancy.get(next_hub, set()))
                    leaving = zone_departures.get(next_hub, 0)
                    arriving = zone_arrivals.get(next_hub, 0)
                    available = (
                        self._zone_capacity(next_hub) -
                        (occ - leaving + arriving)
                    )
                    if available <= 0:
                        continue

                link_usage[lk] += 1
                zone_departures[current] += 1
                zone_arrivals[next_hub] += 1
                planned.append((d, current))

            for d, current in planned:
                next_hub = d.path[d.path_index + 1]
                self.zone_occupancy[current].discard(d.name)

                if self._is_restricted_entry(next_hub):
                    d.state = "transit"
                    d.transit_target = next_hub
                    d.transit_turns = 1
                    self.zone_occupancy[next_hub].add(d.name)
                    moves.append(f"{d.name}-{current}-{next_hub}")
                else:
                    d.path_index += 1
                    if next_hub == self.data.end_hub:
                        d.state = "arrived"
                    else:
                        self.zone_occupancy[next_hub].add(d.name)
                    moves.append(f"{d.name}-{next_hub}")

            if moves:
                self.turns.append(" ".join(moves))

            if all(d.state == "arrived" for d in self.drones):
                self.finished = True
                break

        return self.turns
