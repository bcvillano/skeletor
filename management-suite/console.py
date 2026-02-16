#!/usr/bin/python3
 
from pathlib import Path

CURRENT_PATH = Path(__file__).resolve().parent
LOGO_PATH = CURRENT_PATH.parent / "resources" / "logo.txt"


def init():
    print("Initializing Skeletor Console..."+"\n"*3)
    if LOGO_PATH.exists():
        print(LOGO_PATH.read_text(encoding='utf-8'),end="\n"*4)


def main():
    init()
    while True:
        userin = input("> ").strip()
        match userin:
            case userin if userin in ["exit","quit","q"]:
                confirm = input("Are you sure you want to quit the console? ").strip()
                if confirm in ["y","yes"]:
                    quit()
                else:
                    continue
            case _:
                print("Received input: ",userin)

if __name__ == "__main__":
    main()