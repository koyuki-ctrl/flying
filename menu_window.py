"""Menu Scene for FLY-ing the program.

Display menu scene (welcome scene), running before drone simulation,
loads title, shaders, animations, camera.
"""

from __future__ import annotations
import math
import pyray as rl


MENU = 0
GAME = 1


class MainMenu:
    """Main menu scene rendered before the drone simulation starts.

    Displays an animated water background with a 3D orthographic camera,
    the game title, and a blinking prompt to start the game.
    """

    def __init__(self, w: int, h: int):
        """Initialize the main menu scene.

        Args:
            w: Screen width in pixels.
            h: Screen height in pixels.
        """
        self.w = w
        self.h = h
        self.time = 0.0

        self.water_shader = rl.load_shader("water.vert", "water.frag")
        self.loc_water_time = rl.get_shader_location(self.water_shader, "time")
        water_mesh = rl.gen_mesh_plane(500.0, 500.0, 80, 80)
        self.water_model = rl.load_model_from_mesh(water_mesh)
        for i in range(self.water_model.materialCount):
            self.water_model.materials[i].shader = self.water_shader
        self.water_time_ptr = rl.ffi.new("float *", 0.0)

        self.menu_camera = rl.Camera3D()
        self.menu_camera.position = rl.Vector3(10.0, 10.0, 10.0)
        self.menu_camera.target = rl.Vector3(0.0, 0.0, 0.0)
        self.menu_camera.up = rl.Vector3(0, 1, 0)
        self.menu_camera.fovy = 25.0
        self.menu_camera.projection = rl.CameraProjection.CAMERA_ORTHOGRAPHIC

        self.press_text = "PRESS ANY BUTTON"
        self.press_size = 24

    def update(self) -> str | None:
        """Update menu logic and handle user input.

        Increments the internal timer and checks for keyboard or mouse
        events to transition out of the menu.

        Returns:
            "start" if the player pressed any key or the left mouse button.
            "quit" if the Escape key was pressed.
            None if no relevant input occurred.
        """
        self.time += rl.get_frame_time()
        if rl.get_key_pressed() != 0 or rl.is_mouse_button_pressed(
            rl.MouseButton.MOUSE_BUTTON_LEFT
        ):
            return "start"
        if rl.is_key_pressed(rl.KeyboardKey.KEY_ESCAPE):
            return "quit"
        return None

    def draw(self) -> None:
        """Render the menu frame.

        Clears the background, updates the water shader with the current
        time, draws the animated water plane, and renders the title and
        blinking prompt text.
        """
        rl.clear_background(rl.Color(5, 20, 40, 255))
        self.water_time_ptr[0] = self.time
        rl.set_shader_value(
            self.water_shader,
            self.loc_water_time,
            self.water_time_ptr,
            rl.ShaderUniformDataType.SHADER_UNIFORM_FLOAT
        )
        rl.begin_mode_3d(self.menu_camera)
        rl.draw_model(
            self.water_model, rl.Vector3(0.0, -0.8, 0.0), 1.0, rl.WHITE
        )
        rl.end_mode_3d()

        title = "Flying"
        title_size = 120
        tw = rl.measure_text(title, title_size)
        rl.draw_text(title, self.w // 2 - tw // 2, 150, title_size, rl.GOLD)

        tw = rl.measure_text(self.press_text, self.press_size)
        alpha = int(180 + 75 * math.sin(self.time * 3.0))
        press_color = rl.Color(255, 255, 255, alpha)
        rl.draw_text(
            self.press_text,
            self.w // 2 - tw // 2,
            650,
            self.press_size,
            press_color
        )

    def cleanup(self) -> None:
        """Release GPU resources allocated by the menu scene.

        Unloads the water model and its associated shader to free VRAM.
        """
        rl.unload_model(self.water_model)
        rl.unload_shader(self.water_shader)
