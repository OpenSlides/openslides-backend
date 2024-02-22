import os
import subprocess
from argparse import ArgumentParser, Namespace
from io import StringIO, TextIOBase
from typing import Any, cast

import requests
import yaml

ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
)


def parse_arguments(default: str) -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("filename", nargs="?", default=default)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def open_yml_file(file: str) -> Any:
    print(os.path.abspath(file))
    if os.path.isfile(file):
        with open(file, "rb") as x:
            models_yml = x.read()
    else:
        models_yml = requests.get(file).content
    return yaml.safe_load(models_yml)


def open_output(destination: str, check: bool) -> TextIOBase:
    if check:
        return StringIO()
    else:
        return open(destination, "w")


def assert_equal(stream: TextIOBase, destination: str) -> None:
    result = subprocess.run(
        ["black", "-c", cast(StringIO, stream).getvalue()],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    result.check_returncode()
    with open(destination) as f:
        assert f.read() == result.stdout
