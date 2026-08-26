"""Map file parser for the FLY-ing drone simulation.

Provides functions to read and validate map definition files,
transforming textual descriptions into structured MapData objects.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

from models import Connection, Hub, HubType, MapData, ZoneType


class ParseError(Exception):
    """Exception raised when a map file contains invalid syntax or logic."""
    pass


def _parse_options(options_str: Optional[str]) -> dict[str, str]:
    """Parse a bracketed options string into a key-value dictionary.

    Args:
        options_str: Raw string like "zone=restricted max_drones=3",
            or None if no options are present.

    Returns:
        A dictionary of parsed option keys and values.

    Raises:
        ParseError: If an option lacks an '=' separator or a key is duplicated.
    """
    opts: dict[str, str] = {}
    if not options_str:
        return opts
    for item in options_str.split():
        if "=" not in item:
            raise ParseError(f"Invalid option format: {item}")
        key, value = item.split("=", 1)
        if key in opts:
            raise ParseError(
                "Duplicate metadata key "
                f"'{key}' in hub options")
        opts[key] = value
    return opts


def _parse_hub(line: str, line_no: int) -> Hub:
    """Parse a single hub definition line into a Hub object.

    Args:
        line: The raw text line from the map file.
        line_no: The line number for error reporting.

    Returns:
        A fully constructed Hub instance.

    Raises:
        ParseError: If the line format is invalid, coordinates are malformed,
            the hub name contains a dash, or options are invalid.
    """
    parts = line.split(":", 1)
    if len(parts) != 2:
        raise ParseError(f"Line {line_no}: Invalid hub format")

    raw = parts[1].strip()
    match = re.match(
        r"^(\S+)\s+(-?\d+)\s+(-?\d+)(?:\s+\[(.*?)\])?$", raw
    )
    if not match:
        raise ParseError(f"Line {line_no}: Invalid hub syntax: {raw}")

    name, x_str, y_str, opts_raw = match.groups()
    x = int(x_str)
    y = int(y_str)

    if "-" in name:
        raise ParseError(
            f"Line {line_no}: Hub name cannot contain dash: {name}")

    hub_type = HubType.HUB
    if line.startswith("start_hub:"):
        hub_type = HubType.START
    elif line.startswith("end_hub:"):
        hub_type = HubType.END

    opts = _parse_options(opts_raw)

    zone_str = opts.get("zone", "normal")
    try:
        zone_type = ZoneType(zone_str)
    except ValueError as exc:
        raise ParseError(
            f"Line {line_no}: Invalid zone type: {zone_str}"
        ) from exc

    color = opts.get("color")
    if color == "none":
        color = None

    max_drones = 1
    if "max_drones" in opts:
        try:
            max_drones = int(opts["max_drones"])
            if max_drones < 1:
                raise ValueError
        except ValueError as exc:
            raise ParseError(
                f"Line {line_no}: max_drones must be a positive integer"
            ) from exc

    return Hub(
        name=name, x=x, y=y, hub_type=hub_type,
        zone_type=zone_type, color=color, max_drones=max_drones,
    )


def _parse_connection(line: str, line_no: int) -> Connection:
    """Parse a single connection definition line into a Connection object.

    Args:
        line: The raw text line from the map file.
        line_no: The line number for error reporting.

    Returns:
        A fully constructed Connection instance.

    Raises:
        ParseError: If the syntax is invalid or options are malformed.
    """
    parts = line.split(":", 1)
    if len(parts) != 2:
        raise ParseError(f"Line {line_no}: Invalid connection format")

    raw = parts[1].strip()
    match = re.match(r"^(\S+)-(\S+)(?:\s+\[(.*?)\])?$", raw)
    if not match:
        raise ParseError(f"Line {line_no}: Invalid connection syntax: {raw}")

    hub1, hub2, opts_raw = match.groups()
    opts = _parse_options(opts_raw)

    max_link_capacity = 1
    if "max_link_capacity" in opts:
        try:
            max_link_capacity = int(opts["max_link_capacity"])
            if max_link_capacity < 1:
                raise ValueError
        except ValueError as exc:
            raise ParseError(
                f"Line {line_no}: max_link_capacity must be a positive integer"
            ) from exc

    return Connection(
        hub1=hub1, hub2=hub2, max_link_capacity=max_link_capacity
    )


def parse_map(filepath: str) -> MapData:
    """Parse a complete map file and return a validated MapData object.

    Reads the file line by line, extracting drone count, hub definitions,
    and connection definitions. Performs validation for duplicates,
    coordinate overlaps, missing references, and required fields.

    Args:
        filepath: Path to the map definition file.

    Returns:
        A populated and validated MapData instance.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ParseError: If the file contains syntax errors, duplicates,
            missing required fields, or logical inconsistencies.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    data = MapData()
    seen_hubs: set[str] = set()
    seen_connections: set[tuple[str, ...]] = set()
    seen_coords: set[tuple[int, int]] = set()
    start_count = 0
    end_count = 0

    with open(path, "r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("nb_drones:"):
                try:
                    data.nb_drones = int(line.split(":", 1)[1].strip())
                    if data.nb_drones < 1:
                        raise ValueError
                except (IndexError, ValueError) as exc:
                    raise ParseError(
                        f"Line {line_no}: Invalid nb_drones") from exc

            elif line.startswith(("start_hub:", "end_hub:", "hub:")):
                hub = _parse_hub(line, line_no)
                if hub.name in seen_hubs:
                    raise ParseError(
                        f"Line {line_no}: Duplicate hub name: {hub.name}")
                seen_hubs.add(hub.name)
                coord = (hub.x, hub.y)
                if coord in seen_coords:
                    raise ParseError(
                        f"Line {line_no}: Duplicate hub coordinates "
                        f"({hub.x}, {hub.y}): " +
                        f"'{hub.name}' overlaps with another hub"
                    )
                seen_coords.add(coord)
                data.hubs[hub.name] = hub

                if hub.hub_type == HubType.START:
                    start_count += 1
                    data.start_hub = hub.name
                elif hub.hub_type == HubType.END:
                    end_count += 1
                    data.end_hub = hub.name

            elif line.startswith("connection:"):
                conn = _parse_connection(line, line_no)
                if conn.key() in seen_connections:
                    raise ParseError(
                        f"Line {line_no}: " +
                        f"Duplicate connection: {conn.hub1}-{conn.hub2}"
                    )
                if conn.hub1 not in seen_hubs or conn.hub2 not in seen_hubs:
                    raise ParseError(
                        f"Line {line_no}: Connection references unknown hub"
                    )
                seen_connections.add(conn.key())
                data.connections.append(conn)
                data.neighbors.setdefault(conn.hub1, set()).add(conn.hub2)
                data.neighbors.setdefault(conn.hub2, set()).add(conn.hub1)
            else:
                raise ParseError(f"Line {line_no}: Unknown directive")

    if data.nb_drones == 0:
        raise ParseError("nb_drones must be defined and positive")
    if start_count != 1:
        raise ParseError("Exactly one start_hub required")
    if end_count != 1:
        raise ParseError("Exactly one end_hub required")

    return data
