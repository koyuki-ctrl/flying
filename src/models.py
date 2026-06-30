from __future__ import annotations
from enum import Enum
from typing import List, Tuple, Optional


class ZoneType(Enum):
    NORMAL = 'normal'
    RESTRICTED = 'restricted'
    PRIORITY = 'priority'
    BLOCKED = 'blocked'


class MapColor(Enum):
    GREEN = 'green'
    BLUE = 'blue'
    YELLOW = 'yellow'
    ORANGE = 'orange'
    RED = 'red'
    PURPLE = 'purple'
    CYAN = 'cyan'


class Hub:
    def __init__(
        self,
        name: str = "",
        x: int = 0,
        y: int = 0,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: Optional[MapColor] = None,
        max_drones: int = 1,
        neighbors: Optional[List[Hub]] = None
    ) -> None:
        self.name: str = name
        self.coordinate: Tuple[int, int] = (x, y)
        self.zone_type: ZoneType = zone_type
        self.color: Optional[MapColor] = color
        self.max_drones: int = max_drones
        self.neighbors: List[Hub] = neighbors if neighbors is not None else []


class Connection:
    def __init__(
        self,
        source: Optional[Hub] = None,
        target: Optional[Hub] = None
    ) -> None:
        self.source: Optional[Hub] = source
        self.target: Optional[Hub] = target


class DroneState(Enum):
    IDLE = 'idle'
    MOVING = 'moving'
    WAITING = 'waiting'


class Drone:
    def __init__(
        self,
        drone_id: str,
        current_hub: Optional[Hub] = None,
        path: List[Hub] | None = None,
        state: DroneState = DroneState.IDLE,
        remaining_turns: int = 0
    ) -> None:
        self.drone_id: str = drone_id
        self.current_hub: Optional[Hub] = current_hub
        self.path: List[Hub] = path if path is not None else []
        self.state: DroneState = state
        self.remaining_turns: int = remaining_turns


class Graph:
    def __init__(self) -> None:
        self.hubs: List[Hub] = []
        self.connections: List[Connection] = []

    def add_hub(self, hub: Hub) -> None:
        self.hubs.append(hub)

    def add_connection(self, connection: Connection) -> None:
        self.connections.append(connection)
