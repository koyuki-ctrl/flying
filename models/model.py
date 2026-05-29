class Hub:
    def __init__(self, name, x, y, zone_type, color, max_drones, neighbors):
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones
        self.neighbors = neighbors


class Connection:
    def __init__(self, source, target, capacity):
        self.source = source
        self.target = target
        self.capacity = capacity


class Drone:
    def __init__(self, drone_id, current_hub, destination_hub):
        self.drone_id = drone_id
        self.current_hub = current_hub
        self.destination_hub = destination_hub


class Graph:
    def __init__(self, drones_nbr, start_hub_name, end_hub_name):
        self.hubs = {}
        self.connections = []
        self.drone_nbr = drones_nbr
        self.start_hub = start_hub_name
        self.end_hub = end_hub_name

    def add_hub(self, hub):
        self.hubs[hub.name] = hub

    def add_connection(self, connection):
        self.connections.append(connection)
