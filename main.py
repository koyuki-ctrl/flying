from src.parse import parse_file


def main() -> None:
    parse_file()


if __name__ == "__main__":
    try:
        main()
    except FileExistsError as file_exist_error:
        print(file_exist_error)
    except Exception as e:
        print(e)
    except KeyboardInterrupt as keyboard:
        print(keyboard)
