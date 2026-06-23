def main() -> None:
    pass


if __name__ == "__main__":
    try:
        main()
    except FileExistsError as file_exist_error:
        print(file_exist_error)
    except Exception as e:
        print(e)
    except KeyboardInterrupt as keyboard:
        print(keyboard)
