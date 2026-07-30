from __future__ import annotations
from collections import defaultdict
from models import Drone, MapData


class Simulation:
    def __init__(self, data: MapData, paths: list[list[str]]) -> None:
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
        return (a, b) if a <= b else (b, a)

    def _zone_capacity(self, hub_name: str) -> int:
        if self.data.is_capacity_unlimited(hub_name):
            return 999999
        hub = self.data.hubs.get(hub_name)
        return hub.max_drones if hub else 1

    def _link_capacity(self, hub1: str, hub2: str) -> int:
        return self.data.get_link_capacity(hub1, hub2)

    def _zone_cost(self, hub_name: str) -> int:
        return self.data.get_zone_cost(hub_name)

    def run(self) -> list[str]:
        max_turns = 10000
        turn_count = 0

        while turn_count < max_turns:
            turn_count += 1
            moves: list[str] = []

            # Step 1: drones in transit arrive
            for d in self.drones:
                if d.state == "transit":
                    d.transit_turns -= 1
                    if d.transit_turns <= 0:
                        target = d.transit_target
                        if target:
                            d.state = "idle"
                            d.path_index += 1
                            d.transit_target = None
                            if target == self.data.end_hub:
                                d.state = "arrived"
                            else:
                                self.zone_occupancy[target].add(d.name)
                            moves.append(f"{d.name}-{target}")

            # Step 2: plan simultaneous movements
            link_usage: dict[tuple[str, str], int] = defaultdict(int)
            zone_departures: dict[str, int] = defaultdict(int)
            zone_arrivals: dict[str, int] = defaultdict(int)

            candidates = [
                d for d in self.drones
                if d.state == "idle"
                and d.path
                and d.path_index < len(d.path) - 1
            ]
            candidates.sort(key=lambda d: d.drone_id)
            planned: list[tuple[Drone, str, bool]] = []

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
                is_restricted = self._zone_cost(next_hub) == 2
                if not is_restricted:
                    zone_arrivals[next_hub] += 1
                planned.append((d, current, is_restricted))

            for d, current, is_restricted in planned:
                next_hub = d.path[d.path_index + 1]
                self.zone_occupancy[current].discard(d.name)

                if is_restricted:
                    d.state = "transit"
                    d.transit_target = next_hub
                    d.transit_turns = 1
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
