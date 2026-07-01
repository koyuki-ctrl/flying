from pyray import (
    init_window, begin_drawing, end_drawing, window_should_close,
    close_window, set_target_fps, draw_circle, draw_line, WHITE, Camera2D,
    Vector2, get_mouse_wheel_move, is_mouse_button_down, MouseButton,
    get_mouse_delta, begin_mode_2d, end_mode_2d, clear_background, BLACK
)
from .utils import (
    parse_file, get_start_hub, get_end_hub, get_hub_name,
    get_hub_position, get_hub_color, get_color, get_all_hubs,
    get_all_connections, get_hub_by_name
)
from .models import MapColor


class Window:
    def __init__(self, width: int, height: int, title: str):
        self.scale = 150
        self.radius = 30

        self.data = parse_file()
        self.start_hub = get_start_hub(self.data)
        self.end_hub = get_end_hub(self.data)

        if self.start_hub:
            self.start_name = get_hub_name(self.start_hub)
            print(f"Start hub: {self.start_name}")

        init_window(width, height, title)
        set_target_fps(60)

        self.camera = Camera2D()
        self.camera.offset = Vector2(width // 2, height // 2)
        self.camera.target = Vector2(0, 0)
        self.camera.zoom = 1.0

    def mouse_action(self):
        # Zoom
        wheel = get_mouse_wheel_move()
        if wheel != 0:
            self.camera.zoom += wheel * 0.1
            if self.camera.zoom < 0.1:
                self.camera.zoom = 0.1

        # Pan (clic droit)
        if is_mouse_button_down(MouseButton.MOUSE_BUTTON_LEFT):
            mouse = get_mouse_delta()
            self.camera.target.x -= mouse.x / self.camera.zoom
            self.camera.target.y -= mouse.y / self.camera.zoom

    def draw_hub(self, hub):
        x, y = get_hub_position(hub)
        color_str = get_hub_color(hub)

        try:
            map_color = MapColor(color_str)
            color = get_color(map_color)
        except ValueError:
            color = get_color()

        # PAS DE _pos() ! Dessine direct en coordonnées monde
        # Multiplie juste par scale pour espacer les hubs
        world_x = x * self.scale
        world_y = y * self.scale

        draw_circle(int(world_x), int(world_y), self.radius, color)

    def draw_connections(self):
        for conn in get_all_connections(self.data):
            hub1 = get_hub_by_name(self.data, conn[0])
            hub2 = get_hub_by_name(self.data, conn[1])

            if hub1 and hub2:
                x1, y1 = get_hub_position(hub1)
                x2, y2 = get_hub_position(hub2)

                # Coordonnées monde directement
                draw_line(
                    int(x1 * self.scale), int(y1 * self.scale),
                    int(x2 * self.scale), int(y2 * self.scale),
                    WHITE
                )

    def draw(self):
        self.draw_connections()
        for hub in get_all_hubs(self.data):
            self.draw_hub(hub)

    def run(self):
        while not window_should_close():
            self.mouse_action()

            begin_drawing()
            clear_background(BLACK)
            begin_mode_2d(self.camera)
            self.draw()
            end_mode_2d()
            end_drawing()

        close_window()
