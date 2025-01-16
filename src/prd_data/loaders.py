import importlib
import importlib.resources
import keyword
import re
from io import BytesIO
from types import ModuleType
from typing import Optional, Union

import prd_data.data as _data_resources
from prd_data._types import PathSequence


def _load_file_bytes(
    file_name: str,
    dirs: Optional[PathSequence] = None,
) -> BytesIO:
    dir_path = importlib.resources.files(_data_resources)
    dirs = dirs if dirs is not None else []
    for d in dirs:
        dir_path = dir_path / d

    file_path = dir_path / file_name

    with file_path.open("rb") as f:
        file_data = f.read()

    return BytesIO(file_data)


def check_if_package_installed(m: Union[str, ModuleType]) -> bool:
    """Check if a package (module) is importable"""
    module_name = m.__name__ if isinstance(m, ModuleType) else m
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def get_clean_object_name(
    s: str,
    regex_separators: Optional[str] = None,
    regex_exclude: Optional[str] = None,
) -> str:
    regex_separators = regex_separators or r"\/|\.|-|,|\\"
    regex_exclude = regex_exclude or re.compile(
        # invalid python object name characters
        "^([^a-zA-Z_]+[^a-zA-Z_]*)|[^a-zA-Z0-9_]+"
        # reserved python keywords
        + "\b(?:"
        + "|".join(re.escape(word) for word in keyword.kwlist)
        + ")\b"
    )
    s = re.sub(regex_separators, "_", s)
    s = re.sub(regex_exclude, "", s)
    if len(s) == 0:
        raise ValueError(
            f"Unable to parse string '{s}' to valid python object/attribute name."
        )
    return s


if DV_GROUPER_INSTALLED := check_if_package_installed("dv_grouper"):
    pass  # TODO
