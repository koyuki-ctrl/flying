"""Data models for the FLY-ing drone simulation program.

Defines the core data structures used throughout the application,
including zone types, hub types, hubs, connections, drones, and map data.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ZoneType(Enum):
    """Enumeration of possible zone types for a hub.

    Each zone type affects drone movement behavior and pathfinding cost.
    """

    NORMAL = "normal"
    """Standard zone with no special restrictions."""

    RESTRICTED = "restricted"
    """Restricted zone with increased movement cost."""

    PRIORITY = "priority"
    """Priority zone that receives a cost bonus during pathfinding."""

    BLOCKED = "blocked"
    """Blocked zone that drones cannot traverse."""


class HubType(Enum):
    """Enumeration of hub types in the simulation map.

    Identifies whether a hub is a starting point,
    ending point, or intermediate node.
    """

    START = "start_hub"
    """The hub where all drones begin the simulation."""

    HUB = "hub"
    """An intermediate hub that drones may pass through."""

    END = "end_hub"
    """The destination hub that drones must reach."""


@dataclass
class Hub:
    """Represents a hub (node) in the simulation map.

    A hub has a position, type, zone characteristics,
    color, and drone capacity.

    Attributes:
        name: Unique identifier for the hub.
        x: X-coordinate on the map grid.
        y: Y-coordinate on the map grid.
        hub_type: Classification of the hub (start, end, or intermediate).
        zone_type: Zone behavior affecting drone movement.
        color: Optional display color name; None for default coloring.
        max_drones: Maximum number of drones allowed simultaneously.
    """

    name: str
    x: int
    y: int
    hub_type: HubType = HubType.HUB
    zone_type: ZoneType = ZoneType.NORMAL
    color: Optional[str] = None
    max_drones: int = 1

    def __hash__(self) -> int:
        """Return a hash based on the hub name for use in sets and dicts."""
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        """Check equality with another Hub based on name.

        Args:
            other: The object to compare against.

        Returns:
            True if the other object is a Hub with the same name.
        """
        if not isinstance(other, Hub):
            return NotImplemented
        return self.name == other.name


@dataclass
class Connection:
    """Represents a bidirectional connection (edge) between two hubs.

    Attributes:
        hub1: Name of the first connected hub.
        hub2: Name of the second connected hub.
        max_link_capacity: Maximum number of drones that can traverse
            this link simultaneously in a single turn.
    """

    hub1: str
    hub2: str
    max_link_capacity: int = 1

    def key(self) -> tuple[str, ...]:
        """Return a sorted tuple key for consistent connection identification.

        Returns:
            A tuple containing the two hub names in sorted order.
        """
        return tuple(sorted((self.hub1, self.hub2)))


@dataclass
class Drone:
    """Represents a drone navigating through the simulation map.

    Attributes:
        drone_id: Unique numeric identifier for the drone.
        path: Ordered list of hub names representing the planned route.
        path_index: Current position index within the path.
        state: Current state of the drone ("idle", "transit", or "arrived").
        transit_target: Hub name the drone is moving toward while in transit.
        transit_turns: Remaining turns until the drone completes transit.
    """

    drone_id: int
    path: list[str] = field(default_factory=list)
    path_index: int = 0
    state: str = "idle"
    transit_target: Optional[str] = None
    transit_turns: int = 0

    @property
    def name(self) -> str:
        """Return the drone's display name, formatted as e.g. 'D1' or 'D2'.

        Returns:
            A string prefixed with 'D' followed by the drone ID.
        """
        return f"D{self.drone_id}"

    @property
    def current_zone(self) -> Optional[str]:
        """Return the name of the hub the drone currently occupies.

        Returns:
            The current hub name, or None if the path is empty or exhausted.
        """
        if self.path and self.path_index < len(self.path):
            return self.path[self.path_index]
        return None

    @property
    def is_arrived(self) -> bool:
        """Check whether the drone has reached the destination.

        Returns:
            True if the drone state is "arrived".
        """
        return self.state == "arrived"

    @property
    def is_in_transit(self) -> bool:
        """Check whether the drone is currently moving between hubs.

        Returns:
            True if the drone state is "transit".
        """
        return self.state == "transit"


@dataclass
class MapData:
    """Aggregates all data describing a simulation map.

    Attributes:
        nb_drones: Total number of drones in the simulation.
        start_hub: Name of the starting hub, or None if not defined.
        end_hub: Name of the destination hub, or None if not defined.
        hubs: Dictionary mapping hub names to Hub instances.
        connections: List of all Connection instances in the map.
        neighbors: Adjacency list mapping each hub name
        to its connected neighbors.
    """

    nb_drones: int = 0
    start_hub: Optional[str] = None
    end_hub: Optional[str] = None
    hubs: dict[str, Hub] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)
    neighbors: dict[str, set[str]] = field(default_factory=dict)

    def get_hub(self, name: str) -> Optional[Hub]:
        """Retrieve a hub by its name.

        Args:
            name: The unique name of the hub to look up.

        Returns:
            The Hub instance if found, otherwise None.
        """
        return self.hubs.get(name)

    def get_link_capacity(self, hub1: str, hub2: str) -> int:
        """Get the maximum link capacity between two hubs.

        Args:
            hub1: Name of the first hub.
            hub2: Name of the second hub.

        Returns:
            The max_link_capacity of the connection, or 1 as default.
        """
        key = tuple(sorted((hub1, hub2)))
        for conn in self.connections:
            if conn.key() == key:
                return conn.max_link_capacity
        return 1

    def get_zone_cost(self, hub_name: str) -> int:
        """Calculate the movement cost for entering a hub's zone.

        Args:
            hub_name: Name of the hub to evaluate.

        Returns:
            2 for restricted zones, 1 for all other valid zones.
        """
        hub = self.hubs.get(hub_name)
        if hub is None:
            return 1
        if hub.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1

    def is_capacity_unlimited(self, hub_name: str) -> bool:
        """Check whether a hub has unlimited drone capacity.

        Start and end hubs are always treated as unlimited.

        Args:
            hub_name: Name of the hub to check.

        Returns:
            True if the hub is the start or end hub.
        """
        return hub_name == self.start_hub or hub_name == self.end_hub
