import json
import sys

from openslides_backend.models.checker import Checker, CheckException


def main() -> int:
    files = sys.argv[1:]

    if not files:
        print("No files specified.")
        return 1

    is_import = "--import" in files
    if is_import:
        files = [x for x in files if x != "--import"]

    is_partial = "--partial" in files
    if is_partial:
        files = [x for x in files if x != "--partial"]

    failed = False
    for f in files:
        with open(f) as data:
            try:
                Checker(
                    json.load(data), is_import=is_import, is_partial=is_partial
                ).run_check()
            except CheckException as e:
                print(f"Check for {f} failed:\n", e)
                failed = True
            else:
                print(f"Check for {f} successful.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
