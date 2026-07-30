from __future__ import annotations
import sys

import pyray as rl
from os.path import join

from window import Window
from main_window import MainMenu, MENU, GAME


def main() -> int:
    w, h = 1200, 800

    rl.init_window(w, h, "FLYING")
    rl.set_target_fps(60)

    scene = MENU
    menu = MainMenu(w, h)
    game: Window | None = None
    sky = rl.load_texture(join("assets", "sky.jpg"))

    map_file = (
        sys.argv[1] if len(sys.argv) > 1 else "maps/easy/01_linear_path.txt"
    )

    while not rl.window_should_close():
        if scene == MENU:
            action = menu.update()
            if action == "start":
                game = Window(w, h)
                game.load_map(map_file)
                scene = GAME
            elif action == "quit":
                break

            rl.begin_drawing()
            menu.draw()
            rl.end_drawing()

        elif scene == GAME:
            dt = rl.get_frame_time()
            if game:
                game.update(dt)

            rl.begin_drawing()
            rl.clear_background(rl.BLANK)
            rl.draw_texture(sky, 0, 0, rl.WHITE)

            if game:
                rl.begin_mode_3d(game.camera)
                game.draw()
                rl.end_mode_3d()
                game.draw_drone_labels()
                game.draw_panel()
                game.draw_command()

            rl.end_drawing()

    if menu:
        menu.cleanup()
    if game:
        game.cleanup()
    rl.close_window()
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
