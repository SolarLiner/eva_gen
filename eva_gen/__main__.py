from argparse import ArgumentParser
from pathlib import Path

import eva_gen


def path_of_string(s: str):
    return Path(s).resolve()


def setup():
    parser = ArgumentParser(description=eva_gen.__doc__)
    parser.add_argument(
        "-S", action="store_true", default=False, help="Output EVA assembly"
    )
    parser.add_argument("input", type=path_of_string, help="Input file")
    parser.add_argument("-o", metavar="output", type=path_of_string, help="Output file")
    return parser


def main():
    args = setup().parse_args()
    print(repr(args))


if __name__ == "__main__":
    main()
