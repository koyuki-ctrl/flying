from src.window import Window


def main() -> None:
    window: Window = Window(1200, 800, "Fly-ing")
    window.draw()
    window.run()


if __name__ == "__main__":
    try:
        main()
    except FileExistsError as file_exist_error:
        print(file_exist_error)
    except Exception as e:
        print(e)
    except KeyboardInterrupt as keyboard:
        print(keyboard)
    except EOFError as eof:
        print(eof)
