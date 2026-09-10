"""Map file parser for the FLY-ing drone simulation.

Provides a `MapParser` class that reads and validates map definition
files, transforming textual descriptions into structured MapData
objects.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

from models import Connection, Hub, HubType, MapData, ZoneType


class ParseError(Exception):
    """Exception raised when a map file contains invalid syntax or logic."""

    pass


class MapParser:
    """Parses a single map definition file into a `MapData` object.

    A `MapParser` instance owns all state needed to validate a map
    while it is being read: which hub names, coordinates, and
    connections have already been seen, plus the running count of
    start/end hubs. Create one instance per file parsed.

    Attributes:
        data: The `MapData` being built up as the file is read.
        seen_hubs: Names of hubs already defined, for duplicate checks.
        seen_connections: Canonical keys of connections already defined.
        seen_coords: (x, y) coordinates already used by a hub.
        start_count: Number of `start_hub:` lines seen so far.
        end_count: Number of `end_hub:` lines seen so far.
    """

    HUB_OPTIONS = {"color", "zone", "max_drones"}
    CONNECTION_OPTIONS = {"max_link_capacity"}

    def __init__(self) -> None:
        """Initialize a fresh parser with empty tracking state."""
        self.data: MapData = MapData()
        self.seen_hubs: set[str] = set()
        self.seen_connections: set[tuple[str, ...]] = set()
        self.seen_coords: set[tuple[int, int]] = set()
        self.start_count = 0
        self.end_count = 0

    def parse_map(self, filepath: str) -> MapData:
        """Parse a complete map file and return a validated MapData object.

        Reads the file line by line, extracting drone count, hub
        definitions, and connection definitions. Performs validation
        for duplicates, coordinate overlaps, missing references, and
        required fields.

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

        with open(path, "r", encoding="utf-8") as f:
            for line_no, raw_line in enumerate(f, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                self._parse_line(line, line_no)

        if self.data.nb_drones == 0:
            raise ParseError("nb_drones must be defined and positive")
        if self.start_count != 1:
            raise ParseError("Exactly one start_hub required")
        if self.end_count != 1:
            raise ParseError("Exactly one end_hub required")

        for hub in self.data.hubs.values():
            if hub.max_drones is None:
                if hub.hub_type in (HubType.START, HubType.END):
                    hub.max_drones = self.data.nb_drones
                else:
                    hub.max_drones = 1

        return self.data

    def _parse_line(self, line: str, line_no: int) -> None:
        """Dispatch a single non-blank, non-comment line to its handler.

        Args:
            line: The stripped line text.
            line_no: The line number, for error reporting.

        Raises:
            ParseError: If the line does not match any known directive.
        """
        if line.startswith("nb_drones:"):
            self._parse_nb_drones(line[len("nb_drones:"):], line_no)
        elif line.startswith("start_hub:"):
            self._register_hub(
                "start_hub", line[len("start_hub:"):], line_no)
        elif line.startswith("end_hub:"):
            self._register_hub(
                "end_hub", line[len("end_hub:"):], line_no)
        elif line.startswith("hub:"):
            self._register_hub(
                "hub", line[len("hub:"):], line_no)
        elif line.startswith("connection:"):
            self._register_connection(line[len("connection:"):], line_no)
        else:
            raise ParseError(f"Line {line_no}: Unknown directive")

    def _parse_nb_drones(self, rest: str, line_no: int) -> None:
        """Parse the value portion of an `nb_drones:` line.

        Args:
            rest: The raw text following the `nb_drones` keyword's colon.
            line_no: The line number for error reporting.

        Raises:
            ParseError: If the value is missing or not a positive integer.
        """
        try:
            self.data.nb_drones = int(rest.strip())
            if self.data.nb_drones < 1:
                raise ValueError
        except ValueError as exc:
            raise ParseError(f"Line {line_no}: Invalid nb_drones") from exc

    def _register_hub(self, keyword: str, rest: str, line_no: int) -> None:
        """Parse a hub line, validate it against seen state, and store it.

        Args:
            keyword: The directive keyword (`start_hub`, `end_hub`, or `hub`),
                already stripped of surrounding whitespace.
            rest: The raw text following the keyword's colon.
            line_no: The line number for error reporting.

        Raises:
            ParseError: If the hub name or coordinates are duplicates.
        """
        hub = self._parse_hub(keyword, rest, line_no)
        if hub.name in self.seen_hubs:
            raise ParseError(f"Line {line_no}: Duplicate hub name: {hub.name}")
        self.seen_hubs.add(hub.name)

        if (
                hub.hub_type in (HubType.START, HubType.END)
                and hub.zone_type == ZoneType.BLOCKED
        ):
            raise ParseError(
                f"Line {line_no}: {hub.hub_type.value} '{hub.name}' "
                f"cannot be in a blocked zone"
            )

        coord = (hub.x, hub.y)
        if coord in self.seen_coords:
            raise ParseError(
                f"Line {line_no}: Duplicate hub coordinates "
                f"({hub.x}, {hub.y}): "
                f"'{hub.name}' overlaps with another hub"
            )
        self.seen_coords.add(coord)
        self.data.hubs[hub.name] = hub

        if hub.hub_type == HubType.START:
            self.start_count += 1
            self.data.start_hub = hub.name
        elif hub.hub_type == HubType.END:
            self.end_count += 1
            self.data.end_hub = hub.name

    def _register_connection(self, rest: str, line_no: int) -> None:
        """Parse a connection line, validate it, and store it.

        Args:
            rest: The raw text following the `connection` keyword's colon.
            line_no: The line number for error reporting.

        Raises:
            ParseError: If the connection is a duplicate or references
                an undefined hub.
        """
        conn = self._parse_connection(rest, line_no)
        if conn.key() in self.seen_connections:
            raise ParseError(
                f"Line {line_no}: "
                f"Duplicate connection: {conn.hub1}-{conn.hub2}"
            )
        if conn.hub1 not in self.seen_hubs or conn.hub2 not in self.seen_hubs:
            raise ParseError(
                f"Line {line_no}: Connection references unknown hub"
            )
        self.seen_connections.add(conn.key())
        self.data.connections.append(conn)
        self.data.neighbors.setdefault(conn.hub1, set()).add(conn.hub2)
        self.data.neighbors.setdefault(conn.hub2, set()).add(conn.hub1)

    @staticmethod
    def _parse_options(
        options_str: Optional[str],
        allowed: set[str],
    ) -> dict[str, str]:
        """Parse a bracketed options string into a key-value dictionary.

        Args:
            options_str: Raw string like "zone=restricted max_drones=3",
                or None if no options are present.
            allowed: Set of valid option keys. Any other key raises ParseError.

        Returns:
            A dictionary of parsed option keys and values.

        Raises:
            ParseError: If an option lacks an '=' separator, a key is
                duplicated, or a key is not in `allowed`.
        """
        opts: dict[str, str] = {}
        if not options_str:
            return opts
        for item in options_str.split():
            if "=" not in item:
                raise ParseError(f"Invalid option format: {item}")
            key, value = item.split("=", 1)
            if key not in allowed:
                raise ParseError(
                    f"Unknown option '{key}' "
                    f"(allowed: {', '.join(sorted(allowed))})"
                )
            if key in opts:
                raise ParseError(
                    "Duplicate metadata key "
                    f"'{key}' in hub options")
            opts[key] = value
        return opts

    @classmethod
    def _parse_hub(cls, keyword: str, rest: str, line_no: int) -> Hub:
        """Parse a single hub definition line into a Hub object.

        Args:
            keyword: The directive keyword (`start_hub`, `end_hub`, or `hub`),
                already stripped of surrounding whitespace, used to
                determine the resulting hub's type.
            rest: The raw text following the keyword's colon.
            line_no: The line number for error reporting.

        Returns:
            A fully constructed Hub instance.

        Raises:
            ParseError: If the line format is invalid, coordinates are
                malformed, the hub name contains a dash, or options are
                invalid.
        """
        raw = rest.strip()
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

        if keyword == "start_hub":
            hub_type = HubType.START
        elif keyword == "end_hub":
            hub_type = HubType.END
        else:
            hub_type = HubType.HUB

        opts = cls._parse_options(opts_raw, cls.HUB_OPTIONS)

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

        max_drones = None
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

    @classmethod
    def _parse_connection(cls, rest: str, line_no: int) -> Connection:
        """Parse a single connection definition line into a Connection object.

        Args:
            rest: The raw text following the `connection` keyword's colon.
            line_no: The line number for error reporting.

        Returns:
            A fully constructed Connection instance.

        Raises:
            ParseError: If the syntax is invalid or options are malformed.
        """
        raw = rest.strip()
        match = re.match(r"^(\S+)-(\S+)(?:\s+\[(.*?)\])?$", raw)
        if not match:
            raise ParseError(
                f"Line {line_no}: Invalid connection syntax: {raw}")

        hub1, hub2, opts_raw = match.groups()
        opts = cls._parse_options(opts_raw, cls.CONNECTION_OPTIONS)

        max_link_capacity = 1
        if "max_link_capacity" in opts:
            try:
                max_link_capacity = int(opts["max_link_capacity"])
                if max_link_capacity < 1:
                    raise ValueError
            except ValueError as exc:
                raise ParseError(
                    f"Line {line_no}: "
                    "max_link_capacity must be a positive integer"
                ) from exc

        return Connection(
            hub1=hub1, hub2=hub2, max_link_capacity=max_link_capacity
        )
