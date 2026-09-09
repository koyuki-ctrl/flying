"""Entry point for the FLY-ing program.

Initializes and displays the window, handles keyboard input,
and displays the first scene it also keeps the window open.
read maps with arguments.
"""

from __future__ import annotations
import sys

try:
    from pyray import (
        BLANK,
        WHITE,
        begin_drawing,
        begin_mode_3d,
        clear_background,
        close_window,
        draw_texture,
        end_drawing,
        end_mode_3d,
        get_frame_time,
        init_window,
        is_key_pressed,
        load_texture,
        set_target_fps,
        set_trace_log_level,
        toggle_fullscreen,
        window_should_close,
    )
    from raylib import KEY_F, LOG_NONE
    from menu_window import MainMenu
    from models import SceneModel
    from game_window import GameScene
    from utils import Utils
except ModuleNotFoundError as no_module:
    print(no_module)
except Exception as execption:
    print(execption)


class App:
    """Main app object that run first on program execution.

    Take map on argument, initialize and display window.
    """

    def __init__(self) -> None:
        """Init app and set defaults width, height and map path."""
        self.w, self.h = 1200, 800
        self.map_file = "maps/easy/01_linear_path.txt"

    def take_map(self) -> None:
        """Take argument and get map path."""
        args = sys.argv[1:]
        if args:
            self.map_file = args[0]

    def run(self, show_window: bool = True) -> None:
        """Run the full app and initializes and display window.

        Initializes and shows all scenes, window, texture, window loop,
        load maps, draw, forms and textures, and handle keyboard inputs.

        ARG:
            show_window: decide to show window or not
        """
        data, paths, sim, turns = Utils.load_map(self.map_file)
        if show_window:
            set_trace_log_level(LOG_NONE)
            init_window(self.w, self.h, "FLYING")
            set_target_fps(60)
            toggle_fullscreen()

            scene = SceneModel.MENU.value
            menu = MainMenu(self.w, self.h)
            game: GameScene | None = None
            sky = load_texture("sky.jpg")

            while not window_should_close():
                if is_key_pressed(KEY_F):
                    toggle_fullscreen()
                if scene == SceneModel.MENU.value:
                    action = menu.update()
                    if action == "start":
                        game = GameScene(
                            self.w, self.h, data, paths, sim, turns)
                        scene = SceneModel.GAME.value
                    elif action == "quit":
                        break

                    begin_drawing()
                    menu.draw()
                    end_drawing()

                elif scene == SceneModel.GAME.value:
                    dt = get_frame_time()
                    if game:
                        game.update(dt)

                    begin_drawing()
                    clear_background(BLANK)
                    draw_texture(sky, 0, 0, WHITE)

                    if game:
                        begin_mode_3d(game.camera)
                        game.draw()
                        end_mode_3d()
                        game.draw_drone_labels()
                        game.draw_panel()
                        game.draw_command()

                    end_drawing()

            if menu:
                menu.cleanup()
            if game:
                game.cleanup()
            close_window()


if __name__ == "__main__":
    try:
        app = App()
        app.take_map()
        app.run(False)
    except KeyboardInterrupt:
        print("Program was interrupted")
    except IsADirectoryError as directory_error:
        print(directory_error)
    except FileNotFoundError as not_found:
        print(not_found)
    except PermissionError as permission:
        print(permission)
    except Exception as exception:
        print(exception)
