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

# List (absolute, flattened) paths to available files for loading by category
prd.list_files("expenses") # category: Literal["expenses", "jobs", "geog", "taxes", "parameter_defaults", "benefits"]
>>> {expense_files}
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
from pathlib import Path, PosixPath
from typing import (
    Callable,
    Literal,
    Optional,
    Sequence,
    TypeAlias,
    TypeVar,
    Union,
    overload,
)
from warnings import warn

import data as _data_resources

_DATA_DIR = importlib.resources.files(_data_resources)
_PARQUET_DIR = _DATA_DIR.joinpath("parquet")

PathLevel: TypeAlias = Literal["abs", "rel", "base"]
PathOrStr = TypeVar("PathOrStr", str, Path)
FileCategory: TypeAlias = Literal[
    "expenses", "jobs", "geog", "taxes", "parameter_defaults", "benefits"
]
BenefitsSubCategory: TypeAlias = Literal[
    "healthcare",
    "housing",
    "tax_credits",
    "social_security",
    "childcare",
    "food",
]


def _set_path_level(abs_path: PathOrStr, path_level: PathLevel) -> PathOrStr:
    """
    Processes a given path to return an absolute path, relative path, or base name.

    ```python
    y = '/Users/alex/portfolio/prd-data/src/prd_data/data/parquet'
    x = PosixPath(y)

    for v in (y,x):
        print(v.__repr__())
        for path_level in ('abs','rel','base'):
            print(path_level, _set_path_level(v,path_level).__repr__())

    >>> '/Users/alex/portfolio/prd-data/src/prd_data/data/parquet'
    >>>    abs '/Users/alex/portfolio/prd-data/src/prd_data/data/parquet'
    >>>    rel 'data/parquet'
    >>>    base 'parquet'
    >>> PosixPath('/Users/alex/portfolio/prd-data/src/prd_data/data/parquet')
    >>>     abs PosixPath('/Users/alex/portfolio/prd-data/src/prd_data/data/parquet')
    >>>     rel PosixPath('data/parquet')
    >>>     base PosixPath('parquet')
    ```
    """
    abs_path_str = str(abs_path) if isinstance(abs_path, Path) else abs_path

    match path_level:
        case "abs":
            return abs_path  # Return as-is
        case "rel":
            rel_path = os.path.relpath(abs_path_str)
            return rel_path if isinstance(abs_path, str) else Path(rel_path)
        case "base":
            base_name = os.path.basename(abs_path_str)
            return base_name if isinstance(abs_path, str) else Path(base_name)
        case _:
            raise ValueError(
                f'Invalid path_level "{path_level}". Expected one of: "abs", "rel", "base".'
            )


# @overload
# def get_file_directory(as_str: bool = True) -> str: ...
# @overload
# def get_file_directory(as_str: bool = False) -> PosixPath: ...
def get_file_directory(
    as_str: bool = True,
    path_level: PathLevel = "abs",
) -> PathOrStr:
    """
    Returns directory containing files from package resources.

    ```python
    for as_str in (True, False):
        for path_level in ("abs", "rel", "base"):
            x = get_file_directory(as_str, path_level)
            print(
                x.__repr__(),
                (
                    as_str,
                    path_level,
                ),
            )
    >>> '/Users/alex/portfolio/prd-data/src/prd_data/data/parquet' (True, 'abs')
    >>> 'data/parquet' (True, 'rel')
    >>> 'parquet' (True, 'base')
    >>> PosixPath('/Users/alex/portfolio/prd-data/src/prd_data/data/parquet') (False, 'abs')
    >>> PosixPath('data/parquet') (False, 'rel')
    >>> PosixPath('parquet') (False, 'base')
    ```
    """
    data_dir = importlib.resources.files(_data_resources)
    parquet_dir = data_dir.joinpath("parquet")
    formatted_path = _set_path_level(parquet_dir, path_level=path_level)
    if as_str:
        return str(formatted_path)
    else:
        return formatted_path


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
    start_key: PathLevel = "abs",
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
        _start_key = _set_path_level(str_path, start_key)
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


def list_files(
    category: FileCategory,
    file_tree_dict: Optional[str] = __FILE_TREE_DICT,
    path_type: PathLevel = "abs",
    file_key: str = "files",
    sub_category: Optional[Sequence[BenefitsSubCategory]] = None,
) -> list[Union[str, dict]]:
    """list files flat from tree dict based on file category"""

    _cat = category.lower()

    file_tree_dict = file_tree_dict or get_file_tree_dict(
        include_start_path=True, start_key="abs"
    )
    root_key_input = list(file_tree_dict.keys())[0]
    root_key_output = _set_path_level(root_key_input, path_type)

    # Ugly hard code, sue me
    if _cat == "benefits":
        sub_category = sub_category or file_tree_dict[root_key_input][_cat]
        file_list = [
            {
                "category": sub_category,
                file_key: os.path.join(root_key_output, _cat, subdir_name, f),
            }
            for subdir_name in sub_category
            for f in file_tree_dict[root_key_input][_cat][subdir_name][file_key]
        ]
    else:
        file_list = [
            os.path.join(root_key_output, _cat, f)
            for f in file_tree_dict[root_key_input][_cat][file_key]
        ]

    return file_list


# For module doc string
_unzipped_parquet_destination = get_file_directory()
_file_tree = print_file_tree(output_as_string=True)[:400] + "\n\n\t..."
_file_tree_dict = get_file_tree_dict(start_key="rel")
_file_tree_dict_str = json.dumps(_file_tree_dict, indent=4)[:300] + "\n\n\t..."
_expense_files = f"[{', '.join(list_files('expenses', path_type='base')[:2])}..."
_expense_files
__doc__ = __doc__.format(
    unzipped_parquet_destination=_unzipped_parquet_destination,
    file_tree=_file_tree,
    file_tree_dict=_file_tree_dict_str,
    expense_files=_expense_files,
)

if __name__ == "__main__":
    print(__doc__)
