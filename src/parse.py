import sys
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Any, Tuple


class InvalidArgument(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ErrorParser(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class Parser(ABC):
    def __init__(self, argument):
        self.argument = argument

    @abstractmethod
    def type_parser(self) -> Any:
        pass

    def verify_parse(self) -> bool:
        return isinstance(self.argument, str)


class Drone_parser(Parser):
    def __init__(self, argument):
        self.nbr_drone = 0
        super().__init__(argument)

    def type_parser(self) -> int:
        if self.verify_parse():
            with open(self.argument, "r") as file:
                for line in file:
                    line = (line.strip()).lower()
                    if line.startswith("nb_drones"):
                        list_line = line.split(":")
                        try:
                            if len(list_line) == 2:
                                nb_drone: int = int(list_line[1])
                            else:
                                raise ErrorParser(
                                    "Parsing error: one value is required"
                                )
                        except ValueError as value_error:
                            print(value_error)
                        except ErrorParser as droneError:
                            print(droneError)
                        except Exception as exception:
                            print(exception)
            return nb_drone
        else:
            raise ErrorParser("Drone parsing error")


class Hub_parser(Parser):
    def __init__(self, argument):
        super().__init__(argument)

    def type_parser(self) -> Tuple[str, int, int, str]:
        if self.verify_parse():
            with open(self.argument, 'r') as file:
                for line in file:
                    line = (line.strip()).lower()
                    if (
                        line.startswith("start_hub") or
                        line.startswith('hub') or
                        line.startswith('end_hub')
                    ):
                        list_line = line.split(":")
                        try:
                            if len(list_line) == 5:
                                name: str = list_line[1]
                                x: int = int(list_line[2])
                                y: int = int(list_line[3])
                                color_dict: str = list_line[4]
                                color_list: list[str] = color_dict.split('=')
                                color: str = color_list[2]
                        except Exception as exception:
                            print(exception)
            return (name, x, y, color)
        else:
            raise ErrorParser("Hub parsing error")


def parse_file() -> None:
    if len(sys.argv) == 2:
        argument = sys.argv[1]
        if Path(argument).exists():
            nbr_drone: int = Drone_parser(argument).type_parser()
            print(nbr_drone)

        else:
            raise FileExistsError(f"file {argument} does not exist")
    else:
        raise InvalidArgument(f"Argument invalid: {sys.argv[0]} <path map>")
