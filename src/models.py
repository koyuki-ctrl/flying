from enum import Enum
from typing import List


class ZoneType(Enum):
    NORMAL = 'normal'
    RESTRICED = 'restricted'
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
            color: MapColor | None = None,
            max_drones: int = 1,
            neighbors: List['Hub'] | None = None
    ):
        self.name = name
        self.coordinate = (x, y)
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones
        self.neighbors = neighbors


class Connection:
    def __init__(self, source: Hub | None = None, target: Hub | None = None):
        self.source = source
        self.target = target


class Drone:
    def __init__(self, id, current_hub, path, state, remaining_turns):
        self.droneId = id
        self.current_hub = current_hub
        self.path = path
        self.state = state
        self.remaining_turns = remaining_turns


class Graph:
    def __init__(self):
        self.hubs = []
        self.connections = []

    def add_hub(self, hub: Hub) -> None:
        self.hubs.append(hub)

    def add_connection(self, connection: Connection) -> None:
        self.connections.append(connection)
