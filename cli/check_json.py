import json
import sys

from openslides_backend.models.checker import Checker, CheckException


def main() -> int:
    files = sys.argv[1:]

    if not files:
        print("No files specified.")
        return 1

    possible_modes = tuple(f"--{mode}" for mode in Checker.modes)
    modes = tuple(mode[2:] for mode in possible_modes if mode in files)
    if len(modes) == 0:
        mode = "all"
    elif len(modes) > 1:
        print(f"You can only choose one mode of {', '.join(possible_modes)}.")
        exit(1)
    else:
        mode = modes[0]

    if len(modes):
        files = [x for x in files if x not in possible_modes]

    failed = False
    for f in files:
        with open(f) as data:
            try:
                Checker(
                    json.load(data),
                    mode=mode,
                ).run_check()
            except CheckException as e:
                print(f"Check for {f} failed:\n", e)
                failed = True
            else:
                print(f"Check for {f} successful.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
