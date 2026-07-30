import math
from typing import Optional, Any

from pyray import (
    WHITE, Camera3D, Vector3, CameraProjection, load_model,
    draw_model, load_shader, unload_shader, get_shader_location,
    Color, set_shader_value, ShaderUniformDataType, KeyboardKey,
    is_mouse_button_down, MouseButton, get_mouse_delta, ffi, draw_line_3d,
    is_mouse_button_pressed, get_mouse_position, get_screen_to_world_ray,
    get_ray_collision_sphere, draw_rectangle, draw_rectangle_lines, draw_text,
    LIGHTGRAY, get_world_to_screen, get_mesh_bounding_box, color_from_hsv,
    gen_mesh_plane, load_model_from_mesh, draw_model_ex, is_key_pressed, lerp,
    unload_model, draw_sphere, get_mouse_wheel_move
)
from os.path import join
from models import Hub
from parse import parse_map
from pathfinder import assign_paths
from simulation import Simulation
from utils import to_byte, GROUND_COLOR_MAP, DRONE_COLORS


class Window:
    def __init__(self, width: int, height: int):
        self.data = parse_map("maps/easy/01_linear_path.txt")
        self.w = width
        self.h = height
        self.time = 0.0
        self.scale = 5.0

        self.camera = Camera3D()
        self.camera.position = Vector3(10.0, 10.0, 10.0)
        self.camera.target = Vector3(0.0, 0.0, 0.0)
        self.camera.up = Vector3(0, 1, 0)
        self.camera.fovy = 75.0
        self.camera.projection = CameraProjection.CAMERA_PERSPECTIVE

        self.camera_yaw = math.radians(85.0)
        self.camera_pitch = math.radians(75.264)
        self.camera_distance = 20.0
        self._update_camera()

        self.btn_px = 10

        self.pannel_visible = False
        self.pannel_width = 210
        self.pannel_height = 157
        self.selected_hub: Optional[Hub] = None

        self.hub = load_model(join("assets", "hub.glb"))
        self.drone = load_model(join("assets", "Drone.glb"))

        self.water_shader = load_shader("water.vert", "water.frag")
        self.loc_water_time = get_shader_location(self.water_shader, "time")
        water_mesh = gen_mesh_plane(500.0, 500.0, 80, 80)
        self.water_model = load_model_from_mesh(water_mesh)
        for i in range(self.water_model.materialCount):
            self.water_model.materials[i].shader = self.water_shader
        self.water_time_ptr = ffi.new("float *", 0.0)

        self.hub_local_bb = get_mesh_bounding_box(self.hub.meshes[0])

        # Simulation state
        self.sim: Optional[Simulation] = None
        self.turns: list[str] = []
        self.history: list[dict[str, tuple[str, str]]] = []
        self.anim_turn = -1
        self.anim_progress = 0.0
        self.turn_duration = 0.6
        self.playing = False
        self.all_finished = False

        # Visual drones
        self.vdrones: list[dict[str, Any]] = []

    def load_map(self, filepath: str) -> None:
        """Load a map file and prepare the discrete simulation."""
        self.data = parse_map(filepath)
        paths = assign_paths(self.data)
        self.sim = Simulation(self.data, paths)
        self.turns = self.sim.run()
        self._build_history()
        self._init_visual_drones()
        self._print_raw_output()

    def _print_raw_output(self) -> None:
        print("\n=== RAW SIMULATION OUTPUT ===")
        for line in self.turns:
            print(line)
        print(f"Total turns: {len(self.turns)}\n")

    def _build_history(self) -> None:
        """Build state history:
        history[0] = initial, history[i+1] = after turn i.
        """
        self.history = []
        state: dict[str, tuple[str, str]] = {}
        if self.sim and self.data.start_hub:
            for d in self.sim.drones:
                state[d.name] = (self.data.start_hub, "idle")
        self.history.append(state)

        for line in self.turns:
            new_state = dict(state)
            for token in line.split():
                parts = token.split("-")
                drone_name = parts[0]
                if len(parts) == 3:
                    new_state[drone_name] = (
                        f"{parts[1]}-{parts[2]}", "transit"
                    )
                else:
                    hub_name = parts[1]
                    if hub_name == self.data.end_hub:
                        new_state[drone_name] = (hub_name, "arrived")
                    else:
                        new_state[drone_name] = (hub_name, "idle")
            self.history.append(new_state)
            state = new_state

    def _compute_offset(self, index: int) -> tuple[float, float]:
        angle = (index % 8) * (2 * math.pi / 8)
        radius = 1.2 * ((index // 8) + 1)
        return (math.cos(angle) * radius, math.sin(angle) * radius)

    def _init_visual_drones(self) -> None:
        self.vdrones = []
        if not self.sim:
            return
        for i, d in enumerate(self.sim.drones):
            ox, oy = self._compute_offset(i)
            self.vdrones.append({
                "name": d.name,
                "offset": (ox, oy),
                "color": DRONE_COLORS[i % len(DRONE_COLORS)],
                "pos": Vector3(0, 1.5, 0),
                "from_pos": Vector3(0, 1.5, 0),
                "to_pos": Vector3(0, 1.5, 0),
            })
        self._apply_state_to_visuals(self.history[0], self.history[0])

    def _hub_pos(self, hub_name: str, ox: float, oy: float) -> Vector3:
        hub = self.data.hubs.get(hub_name)
        if hub is None:
            return Vector3(0, 1.5, 0)
        return Vector3(
            hub.x * self.scale + ox * 0.25,
            1.5,
            hub.y * self.scale + oy * 0.25,
        )

    def _conn_pos(self, h1: str, h2: str, ox: float, oy: float) -> Vector3:
        hub1 = self.data.hubs.get(h1)
        hub2 = self.data.hubs.get(h2)
        if hub1 is None or hub2 is None:
            return Vector3(0, 2.5, 0)
        mx = (hub1.x + hub2.x) / 2.0
        my = (hub1.y + hub2.y) / 2.0
        return Vector3(
            mx * self.scale + ox * 0.15,
            2.5,
            my * self.scale + oy * 0.15,
        )

    def _pos_for_location(self, loc: str, ox: float, oy: float) -> Vector3:
        if "-" in loc:
            parts = loc.split("-")
            return self._conn_pos(parts[0], parts[1], ox, oy)
        return self._hub_pos(loc, ox, oy)

    def _apply_state_to_visuals(
        self, from_state: dict[str, tuple[str, str]],
        to_state: dict[str, tuple[str, str]]
    ) -> None:
        start_hub = self.data.start_hub or ""
        for vd in self.vdrones:
            ox, oy = vd["offset"]
            floc, _ = from_state.get(vd["name"], (start_hub, "idle"))
            tloc, _ = to_state.get(vd["name"], (start_hub, "idle"))
            vd["from_pos"] = self._pos_for_location(floc, ox, oy)
            vd["to_pos"] = self._pos_for_location(tloc, ox, oy)

    def _update_camera(self) -> None:
        self.camera.position.x = (
            self.camera.target.x + self.camera_distance *
            math.cos(self.camera_yaw) * math.cos(self.camera_pitch)
        )
        self.camera.position.y = (
            self.camera.target.y + self.camera_distance *
            math.sin(self.camera_pitch)
        )
        self.camera.position.z = (
            self.camera.target.z + self.camera_distance *
            math.sin(self.camera_yaw) * math.cos(self.camera_pitch)
        )

    def mouse_action(self) -> None:
        wheel = get_mouse_wheel_move()
        if wheel != 0:
            self.camera.fovy -= wheel * 2.0
            if self.camera.fovy < 10.0:
                self.camera.fovy = 10.0
            if self.camera.fovy > 120.0:
                self.camera.fovy = 120.0

        if is_mouse_button_down(MouseButton.MOUSE_BUTTON_LEFT):
            delta = get_mouse_delta()
            pan_speed = 0.05 * (self.camera.fovy / 70.0)
            right_x = -math.sin(self.camera_yaw)
            right_z = math.cos(self.camera_yaw)
            forward_x = -math.cos(self.camera_yaw)
            forward_z = -math.sin(self.camera_yaw)
            dx = -delta.x * pan_speed
            dy = -delta.y * pan_speed / math.sin(self.camera_pitch)
            self.camera.target.x += right_x * dx + forward_x * dy
            self.camera.target.z += right_z * dx + forward_z * dy
            self._update_camera()

    def _advance_turn(self) -> None:
        """Advance to the next simulation turn."""
        if self.anim_turn < len(self.turns) - 1:
            self.anim_turn += 1
            self._apply_state_to_visuals(
                self.history[self.anim_turn],
                self.history[self.anim_turn + 1],
            )
        else:
            self.all_finished = True
            self.playing = False
            if self.anim_turn >= 0 and self.anim_progress < 1.0:
                self.anim_progress = 1.0

    def _go_back_turn(self) -> None:
        """Go back one simulation turn."""
        if self.anim_turn >= 0:
            self.anim_turn -= 1
            self.anim_progress = 0.0
            self.all_finished = False
            self._apply_state_to_visuals(
                self.history[self.anim_turn + 1],
                self.history[self.anim_turn + 2],
            )

    def update(self, dt: float) -> None:
        self.time += dt
        self.mouse_action()
        self.check_3d_click()

        if self.playing and not self.all_finished:
            self.anim_progress += dt / self.turn_duration
            if self.anim_progress >= 1.0:
                self._advance_turn()
                if self.all_finished:
                    self.anim_progress = 1.0
                else:
                    self.anim_progress = 0.0

        t = min(1.0, self.anim_progress)
        t = 1.0 - (1.0 - t) ** 3
        for vd in self.vdrones:
            fp = vd["from_pos"]
            tp = vd["to_pos"]
            vd["pos"] = Vector3(
                lerp(fp.x, tp.x, t),
                lerp(fp.y, tp.y, t),
                lerp(fp.z, tp.z, t),
            )

    def draw_connections(self) -> None:
        for conn in self.data.connections:
            hub1 = self.data.hubs.get(conn.hub1)
            hub2 = self.data.hubs.get(conn.hub2)
            if hub1 and hub2:
                pos1 = Vector3(hub1.x * self.scale, 0.1, hub1.y * self.scale)
                pos2 = Vector3(hub2.x * self.scale, 0.1, hub2.y * self.scale)
                draw_line_3d(pos1, pos2, WHITE)

    def draw_hub(self, hub: Hub) -> None:
        pos = Vector3(hub.x * self.scale, 0.0, hub.y * self.scale)
        map_color = hub.color

        if map_color is None:
            color = WHITE
        elif map_color == "rainbow":
            hue = (self.time * 60.0) % 360.0
            color = color_from_hsv(hue, 0.9, 1.0)
        else:
            r, g, b = GROUND_COLOR_MAP.get(map_color, (1.0, 1.0, 1.0))
            color = Color(to_byte(r), to_byte(g), to_byte(b), 255)

        draw_model(self.hub, pos, 0.6, color)

    def draw_drone(self) -> None:
        for vd in self.vdrones:
            rot = (self.time * 30.0) % 360.0
            z_axes = Vector3(0.0, 1.0, 0.0)
            c = vd["color"]
            sphere_color = c if hasattr(c, 'r') else Color(255, 255, 255, 255)
            pos = vd["pos"]
            draw_sphere(pos, 0.25, sphere_color)
            draw_model_ex(
                self.drone, pos, z_axes, rot, Vector3(1.2, 1.2, 1.2), WHITE
            )

    def draw_drone_labels(self) -> None:
        for vd in self.vdrones:
            screen = get_world_to_screen(vd["pos"], self.camera)
            label = vd["name"]
            c = vd["color"]
            label_color = c if hasattr(c, 'r') else Color(255, 255, 255, 255)
            draw_text(
                label, int(screen.x) - 25, int(screen.y) - 35, 12, label_color
            )

    def draw(self) -> None:
        self.water_time_ptr[0] = self.time
        set_shader_value(
            self.water_shader, self.loc_water_time,
            self.water_time_ptr, ShaderUniformDataType.SHADER_UNIFORM_FLOAT
        )
        draw_model(self.water_model, Vector3(0.0, -0.8, 0.0), 1.0, WHITE)

        for hub in self.data.hubs.values():
            self.draw_hub(hub)

        self.draw_connections()
        self.draw_drone()

    def check_3d_click(self) -> None:
        if is_mouse_button_pressed(MouseButton.MOUSE_BUTTON_LEFT):
            mouse_position = get_mouse_position()
            raycast = get_screen_to_world_ray(mouse_position, self.camera)
            for hub in self.data.hubs.values():
                center = Vector3(hub.x * self.scale, 0.5, hub.y * self.scale)
                collision = get_ray_collision_sphere(raycast, center, 1.2)
                if collision.hit:
                    self.pannel_visible = True
                    self.selected_hub = hub
                    break
            else:
                self.pannel_visible = False

    def draw_panel(self) -> None:
        if not self.pannel_visible or self.selected_hub is None:
            return
        hub = self.selected_hub
        world_pos = Vector3(
            (hub.x * self.scale) - 8, 0.5, hub.y * self.scale - 2
        )
        screen_pos = get_world_to_screen(world_pos, self.camera)
        px = int(screen_pos.x + 20)
        py = int(screen_pos.y - 100)
        px = max(10, min(px, self.w - self.pannel_width - 10))
        py = max(10, min(py, self.h - self.pannel_height - 10))
        draw_rectangle(
            px, py, self.pannel_width,
            self.pannel_height, Color(20, 20, 20, 220)
        )
        draw_rectangle_lines(
            px, py, self.pannel_width,
            self.pannel_height, WHITE
        )
        draw_text(hub.name, px + 10, py + 10, 18, WHITE)
        draw_text(f"X: {hub.x}  Y: {hub.y}", px + 10, py + 40, 16, LIGHTGRAY)
        draw_text(
            f"Max drones: {hub.max_drones}",
            px + 10, py + 70, 16, LIGHTGRAY)
        color_name = hub.color if hub.color else "none"
        draw_text(f"Color: {color_name}", px + 10, py + 100, 16, LIGHTGRAY)
        draw_text(
            f"Zone: {hub.zone_type.value}",
            px + 10, py + 130, 16, LIGHTGRAY
        )

    def draw_command(self) -> None:
        turn_text = f"Turn {self.anim_turn + 1} / {len(self.turns)}"
        if self.all_finished:
            turn_text = f"Done in {len(self.turns)} turns"
        elif self.anim_turn < 0:
            turn_text = "Ready"
        draw_text(turn_text, 15, 10, 25, WHITE)
        draw_text("SPACE BAR: PLAY / PAUSE", 20, self.h - 50, 15, WHITE)

        if is_key_pressed(KeyboardKey.KEY_SPACE):
            self.playing = not self.playing
            if self.all_finished:
                self.all_finished = False
                self.anim_turn = -1
                self.anim_progress = 0.0
                self._apply_state_to_visuals(self.history[0], self.history[0])
                self.playing = True

    def cleanup(self) -> None:
        unload_model(self.water_model)
        unload_shader(self.water_shader)
