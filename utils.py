"""Utility constants and helper functions for the FLY-ing program.

Provides color mappings for ground rendering, drone color palettes,
and small conversion utilities used across the application.
"""

from __future__ import annotations
from pyray import Color
from parse import MapParser
from pathfinder import PathFinder
from simulation import Simulation
from models import MapData


GROUND_COLOR_MAP = {
    "green":    (0.3, 0.7, 0.2),
    "blue":     (0.2, 0.4, 0.8),
    "yellow":   (0.9, 0.8, 0.2),
    "orange":   (0.9, 0.5, 0.1),
    "red":      (0.8, 0.2, 0.15),
    "purple":   (0.6, 0.2, 0.7),
    "cyan":     (0.2, 0.7, 0.8),
    "black":    (0.1, 0.1, 0.1),
    "maroon":   (0.5, 0.1, 0.15),
    "brown":    (0.55, 0.35, 0.2),
    "gold":     (0.9, 0.75, 0.2),
    "darkred":  (0.55, 0.05, 0.05),
    "violet":   (0.6, 0.3, 0.8),
    "crimson":  (0.86, 0.08, 0.24),
    "lime":     (0.2, 0.8, 0.2),
    "magenta":  (0.8, 0.2, 0.8),
    "gray":     (0.5, 0.5, 0.5),
    "none":     (0.55, 0.35, 0.2),
}
"""Mapping from color name to normalized RGB
tuple for ground plane rendering."""

DRONE_COLORS = [
    Color(255, 255, 255, 255),
    Color(255, 80, 80, 255),
    Color(80, 150, 255, 255),
    Color(80, 255, 120, 255),
    Color(255, 220, 80, 255),
    Color(255, 150, 50, 255),
    Color(200, 100, 255, 255),
    Color(255, 200, 50, 255),
    Color(0, 255, 255, 255),
    Color(255, 0, 200, 255),
]
"""Palette of distinct colors assigned
to drones for visual differentiation."""


class Utils:
    """Utility class containing static helper methods and constants.

    This class groups frequently used functions for color conversion,
    map loading, and animation helpers. All methods are static and
    can be called without instantiating the class.
    """

    @staticmethod
    def to_byte(c: float) -> int:
        """Convert a normalized color component to an 8-bit integer.

        Values less than or equal to 1.0 are scaled by 255; values above 1.0
        are truncated directly to integer.

        Args:
            c: A color component, typically in the range [0.0, 1.0].

        Returns:
            An integer in the range [0, 255].
        """
        if c <= 1.0:
            return int(c * 255)
        return int(c)

    @staticmethod
    def load_map(filepath: str) -> tuple[
                MapData,
                list[list[str]],
                Simulation,
                list[str]]:
        """Load a map file and prepare the discrete simulation.

        Parses the map, assigns paths to drones, runs the simulation,
        builds the state history, and initializes visual drone objects.

        Args:
            filepath: Path to the map definition file.
        """
        parser = MapParser()
        data = parser.parse_map(filepath)
        finder = PathFinder(data)
        paths = finder.assign_paths()
        sim = Simulation(data, paths)
        turns = sim.run(True)
        print("")
        for line in turns:
            print(line)
        print(f"\nTotal turns: {len(turns)}\n")
        return (data, paths, sim, turns)
