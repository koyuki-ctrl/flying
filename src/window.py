from pyray import (
    init_window, begin_drawing, end_drawing, window_should_close,
    close_window, set_target_fps, WHITE, Camera3D,
    get_mouse_wheel_move, is_mouse_button_down, MouseButton, Vector3,
    get_mouse_delta, begin_mode_3d, end_mode_3d, clear_background, BLACK,
    draw_line_3d, CameraProjection, draw_cube, draw_cube_wires,
    rl_set_clip_planes, get_screen_width, get_screen_height,
    rl_enable_backface_culling, rl_disable_backface_culling,
    load_texture, unload_texture,
    draw_texture_pro, Vector2, Rectangle, load_model, get_frame_time,
    draw_model_ex
)
from .utils import (
    parse_file, get_start_hub, get_end_hub, get_hub_name,
    get_hub_position, get_hub_color, get_color, get_all_hubs,
    get_all_connections, get_hub_by_name
)
from .models import MapColor
import math


class Window:
    def __init__(self, width: int, height: int, title: str):
        self.scale = 150
        self.radius = 30
        self.win_width = width
        self.win_height = height
        self.rotation_y = 0.0

        self.ufo_scale = Vector3(20.0, 20.0, 20.0)

        self.data = parse_file()
        self.start_hub = get_start_hub(self.data)
        self.end_hub = get_end_hub(self.data)

        if self.start_hub:
            self.start_name = get_hub_name(self.start_hub)
            print(f"Start hub: {self.start_name}")

        init_window(width, height, title)
        self.background = load_texture("assets/bg.jpg")
        self.ufo = load_model("assets/UFO.glb")
        set_target_fps(60)

        print("Background texture ID:", self.background.id,
              "size:", self.background.width, "x", self.background.height)
        print("UFO mesh count:", self.ufo.meshCount)

        rl_enable_backface_culling()

        self.camera = Camera3D()

        hubs = get_all_hubs(self.data)
        if hubs:
            positions = [get_hub_position(h) for h in hubs]
            xs = [p[0] for p in positions]
            ys = [p[1] for p in positions]
            center_x = (min(xs) + max(xs)) / 2 * self.scale
            center_z = (min(ys) + max(ys)) / 2 * self.scale
        else:
            center_x, center_z = 0.0, 0.0

        self.scene_center = Vector3(center_x, 0.0, center_z)

        self.cam_distance = 2000.0
        self.cam_yaw = math.radians(45.0)
        self.cam_pitch = math.radians(35.26)

        self.camera.position = Vector3(
            self.scene_center.x + self.cam_distance * math.cos(self.cam_pitch) * math.sin(self.cam_yaw),
            self.scene_center.y + self.cam_distance * math.sin(self.cam_pitch),
            self.scene_center.z + self.cam_distance * math.cos(self.cam_pitch) * math.cos(self.cam_yaw)
        )
        self.camera.target = self.scene_center
        self.camera.up = Vector3(0.0, 1.0, 0.0)
        self.camera.projection = CameraProjection.CAMERA_ORTHOGRAPHIC

        rl_set_clip_planes(10.0, self.cam_distance * 2.0)

        self.camera.fovy = self._compute_fit_fovy()

        self.fovy_min = 40.0
        self.fovy_max = self.camera.fovy * 4.0

        self.pan_sensitivity = 1.0

        if self.start_hub:
            hx, hy = get_hub_position(self.start_hub)
            self.position = self._get_3d_position(hx, hy, self.radius * 2)
        else:
            self.position = Vector3(0.0, 0.0, 0.0)

        print("UFO position:", self.position.x, self.position.y, self.position.z)
        print("Camera position:", self.camera.position.x, self.camera.position.y, self.camera.position.z)
        print("Scene center:", self.scene_center.x, self.scene_center.y, self.scene_center.z)

    def _compute_fit_fovy(self, margin: float = 1.2) -> float:
        hubs = get_all_hubs(self.data)
        if not hubs:
            return 2000.0

        positions = [get_hub_position(h) for h in hubs]
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]

        extent_x = (max(xs) - min(xs)) * self.scale
        extent_y = (max(ys) - min(ys)) * self.scale

        world_extent = max(extent_x, extent_y, 1.0)

        screen_w = get_screen_width()
        screen_h = get_screen_height()
        aspect = (screen_w / screen_h) if screen_h != 0 else (self.win_width / self.win_height)

        diagonal = math.sqrt(extent_x**2 + extent_y**2)

        fovy_needed = diagonal * margin

        return fovy_needed

    def _update_camera_position(self):
        self.camera.position = Vector3(
            self.scene_center.x + self.cam_distance * math.cos(self.cam_pitch) * math.sin(self.cam_yaw),
            self.scene_center.y + self.cam_distance * math.sin(self.cam_pitch),
            self.scene_center.z + self.cam_distance * math.cos(self.cam_pitch) * math.cos(self.cam_yaw)
        )

    def mouse_action(self):
        wheel = get_mouse_wheel_move()
        if wheel != 0:
            self.camera.fovy -= wheel * self.camera.fovy * 0.1
            self.camera.fovy = max(self.fovy_min, min(self.camera.fovy, self.fovy_max))

        if is_mouse_button_down(MouseButton.MOUSE_BUTTON_LEFT):
            mouse_delta = get_mouse_delta()
            move_speed = self.camera.fovy / 500.0

            # === PAN CORRIGE ===
            # En isométrique 45°:
            # souris X+ (droite)  → monde X+ (droite en 3D)
            # souris Y+ (bas)     → monde Z+ (bas en 3D)
            # On projette le mouvement écran directement sur les axes monde
            # en tenant compte de l'angle de la caméra

            dx = mouse_delta.x * move_speed
            dy = mouse_delta.y * move_speed

            # Rotation de -45° pour aligner écran et monde
            # cos(-45) = sin(45) = sqrt(2)/2 ≈ 0.7071
            angle = -self.cam_yaw
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            world_dx = dx * cos_a - dy * sin_a
            world_dz = dx * sin_a + dy * cos_a

            self.scene_center.x += world_dx
            self.scene_center.z += world_dz
            self.camera.target = self.scene_center

            self._update_camera_position()

    def _get_3d_position(self, x, y, z=0.0):
        return Vector3(
            x * self.scale,
            z,
            y * self.scale
        )

    def draw_hub(self, hub):
        x, y = get_hub_position(hub)
        color_str = get_hub_color(hub)

        try:
            map_color = MapColor(color_str)
            color = get_color(map_color)
        except ValueError:
            color = get_color()

        pos = self._get_3d_position(x, y, self.radius)
        size = self.radius * 2
        wire_size = size * 1.02

        draw_cube(pos, size, size * 0.3, size, color)
        draw_cube_wires(pos, wire_size, size * 0.3 * 1.02, wire_size, BLACK)

    def draw_connections(self):
        for conn in get_all_connections(self.data):
            hub1 = get_hub_by_name(self.data, conn[0])
            hub2 = get_hub_by_name(self.data, conn[1])

            if hub1 and hub2:
                x1, y1 = get_hub_position(hub1)
                x2, y2 = get_hub_position(hub2)

                start = self._get_3d_position(x1, y1, self.radius * 1)
                end = self._get_3d_position(x2, y2, self.radius * 1)

                draw_line_3d(start, end, WHITE)

    def draw_ufo(self):
        rl_disable_backface_culling()
        draw_model_ex(
            self.ufo,
            self.position,
            Vector3(0, 1, 0),
            self.rotation_y,
            self.ufo_scale,
            WHITE
        )
        rl_enable_backface_culling()

    def draw(self):
        self.draw_connections()
        for hub in get_all_hubs(self.data):
            self.draw_hub(hub)
        self.draw_ufo()

    def run(self):
        while not window_should_close():
            self.mouse_action()
            dt = get_frame_time()
            self.rotation_y += 30 * dt

            begin_drawing()
            clear_background(BLACK)

            draw_texture_pro(
                self.background,
                Rectangle(0, 0, self.background.width, self.background.height),
                Rectangle(0, 0, get_screen_width(), get_screen_height()),
                Vector2(0, 0),
                0.0,
                WHITE
            )

            begin_mode_3d(self.camera)
            self.draw()
            end_mode_3d()

            end_drawing()

        unload_texture(self.background)
        close_window()