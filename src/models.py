from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ZoneType(Enum):
    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


class HubType(Enum):
    START = "start_hub"
    HUB = "hub"
    END = "end_hub"


@dataclass
class Hub:
    name: str
    x: int
    y: int
    hub_type: HubType = HubType.HUB
    zone_type: ZoneType = ZoneType.NORMAL
    color: Optional[str] = None
    max_drones: int = 1

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hub):
            return NotImplemented
        return self.name == other.name


@dataclass
class Connection:
    hub1: str
    hub2: str
    max_link_capacity: int = 1

    def key(self) -> tuple[str, str]:
        return tuple(sorted((self.hub1, self.hub2)))  # type: ignore[return-value]


@dataclass
class Drone:
    drone_id: int
    path: list[str] = field(default_factory=list)
    path_index: int = 0
    state: str = "idle"
    transit_target: Optional[str] = None
    transit_turns: int = 0

    @property
    def name(self) -> str:
        return f"D{self.drone_id}"

    @property
    def current_zone(self) -> Optional[str]:
        if self.path and self.path_index < len(self.path):
            return self.path[self.path_index]
        return None

    @property
    def is_arrived(self) -> bool:
        return self.state == "arrived"

    @property
    def is_in_transit(self) -> bool:
        return self.state == "transit"


@dataclass
class MapData:
    nb_drones: int = 0
    start_hub: Optional[str] = None
    end_hub: Optional[str] = None
    hubs: dict[str, Hub] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)
    neighbors: dict[str, set[str]] = field(default_factory=dict)

    def get_hub(self, name: str) -> Optional[Hub]:
        return self.hubs.get(name)

    def get_link_capacity(self, hub1: str, hub2: str) -> int:
        key = tuple(sorted((hub1, hub2)))
        for conn in self.connections:
            if conn.key() == key:
                return conn.max_link_capacity
        return 1

    def get_zone_cost(self, hub_name: str) -> int:
        hub = self.hubs.get(hub_name)
        if hub is None:
            return 1
        if hub.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1

    def is_capacity_unlimited(self, hub_name: str) -> bool:
        return hub_name == self.start_hub or hub_name == self.end_hub
