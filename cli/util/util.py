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

META_PATH = "./meta"
SOURCE_META = f"{META_PATH}/models.yml"
SOURCE_COLLECTIONS = f"{META_PATH}/collections"


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


def get_merged_models_yml() -> dict[str, dict[str, Any]]:
    with open(SOURCE_META) as file:
        models_file_content: str = file.read()
    filenames = sorted(get_filenames(SOURCE_COLLECTIONS))
    for filename in filenames:
        if os.path.isfile(
            path := f"{SOURCE_COLLECTIONS}/{filename}"
        ) and filename.endswith(".yml"):
            collection = filename[:-4]
            with open(path) as file:
                content = "\n  ".join(file.read().split("\n"))
            if content:
                models_file_content = (
                    f"{models_file_content}\n{collection}:\n  {content}"
                )
        else:
            # TODO: Consider what may be done alternatively here (see open_yml_file)
            raise Exception(f"Path {path} was not a yml file")
    return yaml.safe_load(models_file_content)


def get_filenames(dirpath: str) -> list[str]:
    return os.listdir(dirpath)


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
