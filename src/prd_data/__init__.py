"""
## prd_data

A package for distributing the datasets in the Policy Rules Database (PRD) in an accessible format for programmers and data scientists.
Original data comes from the AFRB's [Policy Rules Database GitHub Repository](https://github.com/Research-Division/policy-rules-database).

See `loaders.py` for convenient data loaders to work with the datasets in the package.

#### View Available Files:

```python
import prd_data as prd

prd.get_file_directory() # Show destination for extracted files
>>> {unzipped_parquet_destination}

prd.print_file_tree() # Show file tree of available files
>>> {file_tree}

prd.get_file_tree_dict() # Get JSON/dict representation of file tree
>>> {file_tree_dict}

# Utilities to list (absolute, flattened) paths to available files for loading by category
list_expenses_files()
list_jobs_files()
list_geog_files()
list_taxes_files()
list_parameter_defaults_files()
list_benefits_files()
```

#### Load Data:

```python
from prd_data import loaders

# ...
```
"""

import importlib
import importlib.resources
import inspect
import json
import os
from collections import defaultdict
from functools import partial
from io import StringIO
from pathlib import PosixPath
from typing import Callable, Literal, Optional
from warnings import warn

import data as _data_resources

_DATA_DIR = importlib.resources.files(_data_resources)
_PARQUET_DIR = _DATA_DIR.joinpath("parquet")


def get_file_directory() -> PosixPath:
    """Returns directory containing files from package resources"""
    return _PARQUET_DIR


def print_file_tree(
    startpath: Optional[str] = None, output_as_string: bool = False
) -> Optional[str]:
    """
    Print or return the file tree structure starting from `startpath`.

    Args:
        startpath (Optional[str]): The starting directory for the file tree. Defaults to the result of `get_file_directory()`.
        output_as_string (bool): If True, return the file tree as a string instead of printing it.

    Returns:
        Optional[str]: The file tree as a string if `output_as_string` is True, otherwise None.
    """
    startpath = startpath or get_file_directory()
    str_path = str(startpath)

    # Use StringIO to capture output if output_as_string is True
    buffer = StringIO() if output_as_string else None
    write = buffer.write if buffer else print

    for root, dirs, files in os.walk(str_path):
        level = root.replace(str_path, "").count(os.sep)
        indent = " " * 4 * level
        write(f"{indent}{os.path.basename(root)}/\n")
        subindent = " " * 4 * (level + 1)
        for f in sorted(files):
            write(f"{subindent}{f}\n")

    if output_as_string:
        result = buffer.getvalue()
        buffer.close()
        return result

    return None


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


__FILE_TREE_DICT = get_file_tree_dict(include_start_path=True, start_key="abs")


def _list_files(
    key_name: str,
    file_tree_dict: Optional[str] = None,
    abs_paths: bool = True,
    file_key: str = "files",
) -> list[str]:
    """list files flat from tree dict based on file category"""
    file_tree_dict = file_tree_dict or get_file_tree_dict(
        include_start_path=True, start_key="abs"
    )
    abs_path_root = list(file_tree_dict.keys())[0]
    base_name_root = os.path.basename(abs_path_root)

    root_key = abs_path_root if abs_paths else base_name_root

    # Ugly hard code
    if key_name == "benefits":
        [
            os.path.join(root_key, key_name, subdir_name, f)
            for subdir_name in file_tree_dict[root_key][key_name]
            for f in file_tree_dict[root_key][key_name][subdir_name][file_key]
        ]
    else:
        return [
            os.path.join(root_key, key_name, f)
            for f in file_tree_dict[root_key][key_name][file_key]
        ]


list_expenses_files = partial(_list_files, "expenses", __FILE_TREE_DICT)
list_jobs_files = partial(_list_files, "jobs", __FILE_TREE_DICT)
list_geog_files = partial(_list_files, "geog", __FILE_TREE_DICT)
list_taxes_files = partial(_list_files, "taxes", __FILE_TREE_DICT)
list_parameter_defaults_files = partial(
    _list_files, "parameter_defaults", __FILE_TREE_DICT
)
list_benefits_files = partial(_list_files, "benefits", __FILE_TREE_DICT)

# For module doc string
_unzipped_parquet_destination = get_file_directory()
_file_tree = print_file_tree(output_as_string=True)[:400] + "\n\n\t..."
_file_tree_dict = get_file_tree_dict(start_key="rel")
_file_tree_dict_str = json.dumps(_file_tree_dict, indent=4)[:300] + "\n\n\t..."

__doc__ = __doc__.format(
    unzipped_parquet_destination=_unzipped_parquet_destination,
    file_tree=_file_tree,
    file_tree_dict=_file_tree_dict_str,
)

if __name__ == "__main__":
    print(__doc__)
