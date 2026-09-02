"""Entry point for the FLY-ing program.

Initializes and displays the window, handles keyboard input,
and displays the first scene it also keeps the window open.
read maps with arguments.
"""

from __future__ import annotations
import sys
from pyray import (
    set_trace_log_level, init_window, set_target_fps, toggle_fullscreen,
    load_texture, window_should_close, is_key_pressed, get_frame_time,
    begin_drawing, end_drawing, clear_background, draw_texture,
    begin_mode_3d, end_mode_3d, close_window, BLANK, WHITE,
)
from raylib import LOG_NONE, KEY_F
from window import Window
from menu_window import MainMenu
from models import SceneModel


def main() -> int:
    """Run the full app and initializes and display window.

    Initializes and shows all scenes, window, texture, window loop,
    load maps, draw, forms and textures, and handle keyboard inputs.

    Raises:
        KeyboardInterrupt: Gracefully handled with timing summary,
        IsADirectoryError: Insure the program read files not directories,
        FileNotFoundError: Handle all files are not empty,
        PermissionError: Handle the files has readable permission,
        Exception: Handle another error.
    """
    w, h = 1200, 800

    set_trace_log_level(LOG_NONE)
    init_window(w, h, "FLYING")
    set_target_fps(60)
    toggle_fullscreen()

    scene = SceneModel.MENU.value
    menu = MainMenu(w, h)
    game: Window | None = None
    sky = load_texture("sky.jpg")
    args = sys.argv[1:]
    if args:
        map_file = args[0]
    else:
        map_file = "maps/easy/01_linear_path.txt"

    while not window_should_close():
        if is_key_pressed(KEY_F):
            toggle_fullscreen()
        if scene == SceneModel.MENU.value:
            action = menu.update()
            if action == "start":
                game = Window(w, h)
                game.load_map(map_file)
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
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
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
