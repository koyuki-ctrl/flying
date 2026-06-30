from .models import MapColor
from .parse import (
    HubOption,
    ParseFile,
    Drone_parser,
    HubValue,
    HubType,
    Hub_parser,
    Connection_parser
)
import sys
from typing import Any, Dict, Tuple, List
from pathlib import Path
from pyray import (
    GREEN,
    BLUE,
    YELLOW,
    ORANGE,
    RED,
    PURPLE,
    Color
)


class InvalidArgument(Exception):
    def __init__(self, message: Any) -> None:
        super().__init__(message)


def parse_file() -> ParseFile:
    if len(sys.argv) != 2:
        raise InvalidArgument(f"Argument invalid: {sys.argv[0]} <path map>")

    argument: str = sys.argv[1]

    if not Path(argument).exists():
        raise FileExistsError(f"file {argument} does not exist")

    nbr_drone: int = Drone_parser(argument).type_parser()

    hubs: Hub_parser = Hub_parser(argument)
    hub: (
        List[Tuple[HubType, str, int, int, Dict[HubOption, HubValue]]]
        ) = hubs.type_parser()

    connections: Connection_parser = Connection_parser(argument)
    connection: List[Tuple[str, str]] = connections.type_parser()

    file_parser: ParseFile = {
        "nbr_drone": nbr_drone,
        'hub': hub,
        "connection": connection
        }

    return file_parser


def get_hub_by_name(data: ParseFile, name: str):
    """Récupère un hub par son nom."""
    for hub in data['hub']:
        if hub[1] == name.lower():
            return hub
    return None


def get_start_hub(data: ParseFile):
    """Récupère le hub de départ."""
    for hub in data['hub']:
        if hub[0] == HubType.START_HUB:
            return hub
    return None


def get_end_hub(data: ParseFile):
    """Récupère le hub d'arrivée."""
    for hub in data['hub']:
        if hub[0] == HubType.END_HUB:
            return hub
    return None


def get_hub_name(hub) -> str:
    """Récupère le nom d'un hub."""
    return hub[1]


def get_hub_position(hub) -> Tuple[int, int]:
    """Récupère les coordonnées (x, y) d'un hub."""
    return (hub[2], hub[3])


def get_hub_x(hub) -> int:
    """Récupère la coordonnée x d'un hub."""
    return hub[2]


def get_hub_y(hub) -> int:
    """Récupère la coordonnée y d'un hub."""
    return hub[3]


def get_hub_options(hub) -> Dict[HubOption, HubValue]:
    """Récupère les options d'un hub."""
    return hub[4]


def get_hub_color(hub) -> str:
    """Récupère la couleur d'un hub."""
    return hub[4][HubOption.COLOR]


def get_hub_zone(hub) -> str:
    """Récupère le type de zone d'un hub."""
    return hub[4][HubOption.ZONE]


def get_hub_max_drones(hub) -> int:
    """Récupère le max de drones d'un hub."""
    return hub[4][HubOption.MAX_DRONES]


def get_all_hub_names(data: ParseFile) -> List[str]:
    """Récupère tous les noms des hubs."""
    return [hub[1] for hub in data['hub']]


def get_all_hubs(data: ParseFile) -> List[Tuple]:
    """Récupère tous les hubs."""
    return data['hub']


def get_connections_from(data: ParseFile, hub_name: str) -> List[str]:
    """Récupère tous les hubs connectés depuis un hub donné."""
    result = []
    for conn in data['connection']:
        if conn[0] == hub_name:
            result.append(conn[1])
    return result


def get_connections_to(data: ParseFile, hub_name: str) -> List[str]:
    """Récupère tous les hubs qui se connectent vers un hub donné."""
    result = []
    for conn in data['connection']:
        if conn[1] == hub_name:
            result.append(conn[0])
    return result


def get_all_connections(data: ParseFile) -> List[Tuple[str, str]]:
    """Récupère toutes les connections."""
    return data['connection']


def get_hub_neighbors(data: ParseFile, hub_name: str) -> List[str]:
    """Récupère tous les voisins d'un hub (connections bidirectionnelles)."""
    neighbors = set()
    for conn in data['connection']:
        if conn[0] == hub_name:
            neighbors.add(conn[1])
        if conn[1] == hub_name:
            neighbors.add(conn[0])
    return list(neighbors)


def get_hub_by_position(data: ParseFile, x: int, y: int):
    """Récupère un hub par ses coordonnées."""
    for hub in data['hub']:
        if hub[2] == x and hub[3] == y:
            return hub
    return None


def get_nbr_drones(data: ParseFile) -> int:
    """Récupère le nombre de drones."""
    return data['nbr_drone']


def get_color(map_color: MapColor | None = None) -> Color:
    """Convertit MapColor en Color Raylib"""
    if map_color is None:
        return Color(128, 128, 128, 255)

    color_map: dict[MapColor, Color] = {
        MapColor.GREEN: GREEN,
        MapColor.BLUE: BLUE,
        MapColor.YELLOW: YELLOW,
        MapColor.ORANGE: ORANGE,
        MapColor.RED: RED,
        MapColor.PURPLE: PURPLE,
        MapColor.CYAN: Color(0, 255, 255, 255),
    }

    return color_map.get(map_color, Color(128, 128, 128, 255))
