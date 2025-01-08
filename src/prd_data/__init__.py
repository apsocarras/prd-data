import inspect
import json
import os
from collections import defaultdict
from importlib import resources as imp_resources
from pathlib import PosixPath
from typing import Any, Callable, Literal, Optional, Union
from warnings import warn

from prd_data import data

__DATA_DIR = imp_resources.files(data)
__PARQUET_DIR = __DATA_DIR.joinpath("parquet")
__PARQUET_DIR


def get_file_directory() -> PosixPath:
    """Returns directory containing files from package resources"""
    return __PARQUET_DIR


def print_file_tree(startpath: str = str(get_file_directory())):
    str_path = str(startpath)
    for root, dirs, files in os.walk(str_path):
        level = root.replace(str_path, "").count(os.sep)
        indent = " " * 4 * (level)
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 4 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")


def get_file_tree_dict(
    startpath: str = str(get_file_directory()),
    file_key: str = "files",
    include_start_path: bool = True,
    start_key: Literal["base", "abs", "rel"] = "abs",
) -> dict:
    """
    Recursively generate directory tree as dict.

    Args:
        startpath (str): (Absolute) path to a directory tree in your file system.
        file_key (str): Name for the key which separates files from any directories at that level.
            - Ensure not to use a file_key which shares a name with one of the directories in your tree.
        include_start_path (bool): Whether to include startpath itself in the directory tree.
        start_key (Literal[&quot;base&quot;, &quot;abs&quot;, &quot;rel&quot;], optional): If include_start_path, determines how to format the starting key. Defaults to False.

    Returns:
        dict: Representation of file tree as dict.
    """

    def build_tree(
        cur_path: str,
    ) -> dict:
        tree = defaultdict(list)
        for entry in os.scandir(cur_path):
            if entry.name == file_key:
                warn(f"Current entry name matches file_key: {file_key}")
            if entry.is_dir():
                # Recursively build tree for subdirectory
                tree[entry.name] = build_tree(entry.path)
            else:
                # Add file name to tree
                tree[file_key].append(entry.name)
        return dict(tree)

    str_path = str(startpath)

    if include_start_path:
        match start_key:
            case "abs":
                _start_key = os.path.abspath(str_path)
            case "rel":
                _start_key = os.path.relpath(str_path)
            case "base":
                _start_key = os.path.basename(str_path)
            case _:
                return ValueError(
                    f"`start_key` must be one of 'abs', 'rel', 'base' (given: {start_key})"
                )

        return {_start_key: build_tree(str_path)}

    return build_tree(str_path)


def __format_signature(func: Callable, include_signature: bool = False) -> str:
    s = func.__name__
    if include_signature:
        s += inspect.signature(func)
    else:
        s += "(...)"
    return s


if __name__ == "__main__":
    print(f"PRD Data Path: {get_file_directory()}")
    print("Show File Tree: " + __format_signature(print_file_tree))
    print("Return as JSON Structure: " + __format_signature(get_file_tree_dict))
    print("\n")
    print("Showing File Tree: ")
    print("\n")
    print_file_tree()
