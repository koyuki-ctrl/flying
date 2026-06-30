from abc import ABC, abstractmethod
from typing import TypedDict, Tuple, List, Union, Any, TypeAlias, Dict
from enum import Enum
import re


class ErrorParser(Exception):
    def __init__(self, message: Any) -> None:
        super().__init__(message)


class Parser(ABC):
    def __init__(self, argument: Any) -> None:
        self.argument = argument

    @abstractmethod
    def type_parser(self) -> Any:
        pass

    def verify_parse(self) -> bool:
        return isinstance(self.argument, str)


class HubType(Enum):
    START_HUB = "start_hub"
    HUB = "hub"
    END_HUB = "end_hub"


class HubOption(Enum):
    COLOR = "color"
    ZONE = "zone"
    MAX_DRONES = "max_drones"


HubValue: TypeAlias = Union[str, int]


class ParseFile(TypedDict):
    nbr_drone: int
    hub: List[Tuple[HubType, str, int, int, Dict[HubOption, HubValue]]]
    connection: List[Tuple[str, str]]


class Drone_parser(Parser):
    def __init__(self, argument: str) -> None:
        super().__init__(argument)

    def type_parser(self) -> int:
        if not self.verify_parse():
            raise ErrorParser("Drone parsing error")

        nb_drone: int = 0

        with open(self.argument, "r") as file:
            for line in file:
                line = line.strip().lower()

                if line.startswith("nb_drones"):
                    parts = line.split(":")
                    if len(parts) != 2:
                        raise ErrorParser(
                            "Parsing error: one value is required"
                        )

                    try:
                        nb_drone = int(parts[1].strip())
                    except ValueError:
                        raise ErrorParser("nb_drones doit être un entier")

        return nb_drone


class Hub_parser(Parser):
    def __init__(self, argument: str):
        super().__init__(argument)

    def type_parser(self) -> (
            List[Tuple[HubType, str, int, int, Dict[HubOption, HubValue]]]
            ):
        if not self.verify_parse():
            raise ErrorParser("Hub parsing error")

        hub = []
        seen_hubs = set()
        has_start_hub = False
        has_end_hub = False

        with open(self.argument, "r") as file:
            for line in file:
                line = line.strip().lower()

                if (
                    line.startswith(HubType.START_HUB.value)
                    or line.startswith(HubType.HUB.value)
                    or line.startswith(HubType.END_HUB.value)
                ):
                    parts = line.split(":")
                    if len(parts) != 2:
                        raise ErrorParser("Ligne hub Error.")

                    hub_values = parts[1].strip().split(" ", 3)
                    if len(hub_values) != 4:
                        raise ErrorParser("Ligne hub Error.")

                    try:
                        hub_type = HubType(parts[0])
                    except ValueError:
                        raise ErrorParser("Type de hub invalide.")
                    if hub_type == HubType.START_HUB:
                        if has_start_hub:
                            raise ErrorParser(
                                "Duplicate start_hub: " +
                                "only one start_hub is allowed"
                            )
                        has_start_hub = True

                    if hub_type == HubType.END_HUB:
                        if has_end_hub:
                            raise ErrorParser(
                                "Duplicate end_hub: " +
                                "only one end_hub is allowed"
                            )
                        has_end_hub = True

                    name = hub_values[0]
                    x = int(hub_values[1])
                    y = int(hub_values[2])

                    options = hub_values[3]

                    if not (options.startswith("[") and options.endswith("]")):
                        raise ErrorParser("Options hub invalides.")

                    options = options[1:-1]

                    attributes: dict[HubOption, HubValue] = {
                        HubOption.COLOR: "none",
                        HubOption.ZONE: "normal",
                        HubOption.MAX_DRONES: 1
                    }

                    for item in options.split():
                        if "=" not in item:
                            raise ErrorParser(" invalid attribut hub.")

                        key, raw_value = item.split("=", 1)

                        try:
                            option = HubOption(key)
                        except ValueError:
                            raise ErrorParser(f"Unknown hub option : {key}")

                        if option == HubOption.MAX_DRONES:
                            try:
                                value: HubValue = int(raw_value)
                            except ValueError:
                                raise ErrorParser(
                                    "max_drones could be int."
                                )
                        else:
                            value = raw_value

                        attributes[option] = value

                    hub_key = (hub_type, name, x, y, tuple(sorted(
                        (
                            (opt.value, str(val))
                            for opt, val in attributes.items()
                        )
                    )))

                    if hub_key in seen_hubs:
                        raise ErrorParser(f"Duplicate hub detected: {name}")

                    seen_hubs.add(hub_key)
                    hub.append((hub_type, name, x, y, attributes))

        if not hub:
            raise ErrorParser("No Hub found in file")

        return hub


class Connection_parser(Parser):
    def __init__(self, argument: str) -> None:
        super().__init__(argument)

    def type_parser(self) -> List[Tuple[str, str]]:
        if not self.verify_parse():
            raise ErrorParser("Connection parsing error")

        connections = []
        seen_connections = set()

        with open(self.argument, "r") as file:
            for line in file:
                line = line.strip().lower()

                if line.startswith("connection"):
                    parts = line.split(":", 1)
                    if len(parts) != 2:
                        raise ErrorParser("Parsing connection error")

                    conn_value = parts[1].strip()
                    conn_value = re.sub(r"\[.*?\]", "", conn_value).strip()

                    if "-" not in conn_value:
                        raise ErrorParser(f"Invalid Connection: {conn_value}")

                    hub1, hub2 = map(str.strip, conn_value.split("-", 1))

                    if not hub1 or not hub2:
                        raise ErrorParser(
                            "Invalid connection: Hub name not found"
                        )

                    conn_key = tuple(sorted([hub1, hub2]))

                    if conn_key in seen_connections:
                        raise ErrorParser(
                            f"Duplicate connection detected: {hub1}-{hub2}"
                        )

                    seen_connections.add(conn_key)
                    connections.append((hub1, hub2))

        if not connections:
            raise ErrorParser("No connection found in file")

        return connections
