"""Menu Scene for FLY-ing the program.

Display menu scene (welcome scene), running before drone simulation,
loads title, shaders, animations, camera.
"""

from __future__ import annotations
import math
try:
    from pyray import (
        load_shader,
        get_shader_location,
        gen_mesh_plane,
        load_model_from_mesh,
        get_frame_time,
        get_key_pressed,
        is_mouse_button_pressed,
        is_key_pressed,
        clear_background,
        set_shader_value,
        begin_mode_3d,
        end_mode_3d,
        draw_model,
        get_screen_height,
        get_screen_width,
        measure_text,
        draw_text,
        unload_model,
        unload_shader,
        Camera3D,
        Vector3,
        CameraProjection,
        MouseButton,
        KeyboardKey,
        Color,
        ShaderUniformDataType,
        GOLD,
        WHITE,
        ffi
    )
except ModuleNotFoundError as no_module:
    print(no_module)
except Exception as execption:
    print(execption)


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

        self.water_shader = load_shader("water.vert", "water.frag")
        self.loc_water_time = get_shader_location(self.water_shader, "time")
        water_mesh = gen_mesh_plane(500.0, 500.0, 80, 80)
        self.water_model = load_model_from_mesh(water_mesh)
        for i in range(self.water_model.materialCount):
            self.water_model.materials[i].shader = self.water_shader
        self.water_time_ptr = ffi.new("float *", 0.0)

        self.menu_camera = Camera3D()
        self.menu_camera.position = Vector3(10.0, 10.0, 10.0)
        self.menu_camera.target = Vector3(0.0, 0.0, 0.0)
        self.menu_camera.up = Vector3(0, 1, 0)
        self.menu_camera.fovy = 25.0
        self.menu_camera.projection = CameraProjection.CAMERA_ORTHOGRAPHIC

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
        self.time += get_frame_time()
        if get_key_pressed() != 0 or is_mouse_button_pressed(
            MouseButton.MOUSE_BUTTON_LEFT
        ):
            return "start"
        if is_key_pressed(KeyboardKey.KEY_ESCAPE):
            return "quit"
        return None

    def draw(self) -> None:
        """Render the menu frame.

        Clears the background, updates the water shader with the current
        time, draws the animated water plane, and renders the title and
        blinking prompt text.
        """
        clear_background(Color(5, 20, 40, 255))
        self.water_time_ptr[0] = self.time
        set_shader_value(
            self.water_shader,
            self.loc_water_time,
            self.water_time_ptr,
            ShaderUniformDataType.SHADER_UNIFORM_FLOAT
        )
        begin_mode_3d(self.menu_camera)
        draw_model(
            self.water_model, Vector3(0.0, -0.8, 0.0), 1.0, WHITE
        )
        end_mode_3d()

        screen_w = get_screen_width()
        screen_h = get_screen_height()

        title = "Flying"
        title_size = 120
        tw = measure_text(title, title_size)
        draw_text(
            title,
            screen_w // 2 - tw // 2,
            screen_h // 3 - title_size // 2,
            title_size,
            GOLD
        )

        tw = measure_text(self.press_text, self.press_size)
        alpha = int(180 + 75 * math.sin(self.time * 3.0))
        press_color = Color(255, 255, 255, alpha)
        draw_text(
            self.press_text,
            screen_w // 2 - tw // 2,
            int(screen_h * 0.8),
            self.press_size,
            press_color
        )

    def cleanup(self) -> None:
        """Release GPU resources allocated by the menu scene.

        Unloads the water model and its associated shader to free VRAM.
        """
        unload_model(self.water_model)
        unload_shader(self.water_shader)
