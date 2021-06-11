from pathlib import Path
from typing import Union


def read_file(path: Union[str, Path], encoding: str = "UTF-8") -> str:
    with open(path, "rb") as file_handle:
        return file_handle.read().decode(encoding)
