"""
`{cur_file_name}` - Utilities for listing/organizing files in the PRD.

#### View Available Files:

```python
from prd_data import file_utils as fu

fu.get_data_dir() # Show destination for extracted files
>>> {unzipped_parquet_destination}

import prd_data as prd # file_utils functions also accessible here

prd.print_file_tree() # Show file tree of available files
>>> \n{file_tree}

prd.get_file_tree_dict() # Get JSON/dict representation of file tree
>>> {file_tree_dict}

# List (absolute, flattened) paths to available files for loading by category
prd.list_files("expenses") # category: Literal["expenses", "jobs", "geog", "taxes", "parameter_defaults", "benefits"]
>>> {expense_files}
prd.list_files("benefits")
>>> {benefits_files}
```
"""

import importlib
import importlib.resources
import json
import os
from collections import defaultdict
from io import StringIO
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence, Union
from warnings import warn

import prd_data.data as _data_resources
from prd_data._types import (
    BenefitsSubCategory,
    FileCategory,
    PathLevel,
    PathOrStr,
    PathSequence,
    PRD_FileTreeType,
)
from prd_data.file_tree import FILE_TREE


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


def get_data_dir(
    join_paths: Optional[PathSequence] = ("parquet",),
    path_level: PathLevel = "abs",
    as_str: bool = True,
) -> PathOrStr:
    data_dir = importlib.resources.files(_data_resources)
    for p in join_paths:
        data_dir = data_dir.joinpath(p)
    formatted_data_dir = _set_path_level(data_dir, path_level)
    if as_str:
        return str(formatted_data_dir)
    else:
        return formatted_data_dir


def print_file_tree(
    data_dir: Optional[PathOrStr] = None,
    as_str: bool = False,
    formatter: Optional[Callable[["print_file_tree", tuple, dict], str]] = None,
    **kwargs,
) -> Optional[str]:
    """
    Print or return the file tree structure starting from `data_dir`.

    Args:
        data_dir (Optional[str]): The starting directory for the file tree. Defaults to the result of `get_data_dir()`.
        as_str (bool): If True, return the file tree as a string instead of printing it.

    Returns:
        Optional[str]: The file tree as a string if `as_str` is True, otherwise None.
    """
    data_dir = data_dir or get_data_dir()
    str_path = str(data_dir)

    buffer = StringIO()
    write = buffer.write

    for root, dirs, files in os.walk(str_path):
        level = root.replace(str_path, "").count(os.sep)
        indent = " " * 4 * level
        write(f"{indent}{os.path.basename(root)}/\n")
        subindent = " " * 4 * (level + 1)
        for f in sorted(files):
            write(f"{subindent}{f}\n")

    result = buffer.getvalue()
    buffer.close()

    if formatter:
        return formatter(print_file_tree, (data_dir, as_str), kwargs)

    if as_str:
        return result
    else:
        print(result)
        return None


def _tree_trunc(func, args, kwargs, max_length=500):
    full_output = func(*args, **kwargs)
    if len(full_output) > max_length:
        return full_output[:max_length] + "\n\t..."
    return full_output


def make_file_tree_dict(
    data_dir: str = str(get_data_dir()),
    file_key: str = "files",
    include_start_path: bool = True,
    start_key: PathLevel = "abs",
) -> dict:
    """
    Recursively generate directory tree as dict.
    During the package build step, this function is use to generate the read-only Mapping file_tree.FILE_TREE

    Args:
        data_dir (str): (Absolute) path to a directory tree in your file system.
        file_key (str): Name for the key which separates files from any directories at that level.
            - Ensure not to use a file_key which shares a name with one of the directories in your tree.
        include_start_path (bool): Whether to include data_dir itself in the directory tree.
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

    str_path = str(data_dir)

    if include_start_path:
        _start_key = _set_path_level(str_path, start_key)
        return {_start_key: build_tree(str_path)}

    return build_tree(str_path)


def get_file_tree_dict() -> PRD_FileTreeType:
    """
    Get a read-only Mapping representation of PRD files contained in the prd_data package.

    Returns FILE_TREE (created during the package build step)
    """
    return FILE_TREE


def list_files(
    category: FileCategory,
    file_tree_dict: Optional[Mapping] = None,
    path_type: PathLevel = "abs",
    file_key: str = "files",
    sub_categories: Optional[Sequence[BenefitsSubCategory]] = None,
) -> list[Union[str, dict]]:
    """list files flat from tree dict based on file category"""
    file_tree_dict = file_tree_dict or get_file_tree_dict()

    _cat = category.lower()

    root_key_input = list(file_tree_dict.keys())[0]
    root_key_output = _set_path_level(root_key_input, path_type)
    # Ugly hard code, sue me
    if _cat == "benefits":
        sub_categories = sub_categories or [
            "healthcare",
            "housing",
            "tax_credits",
            "social_security",
            "childcare",
            "food",
        ]
        file_list = [
            {
                "category": sub_cat,
                file_key: [
                    os.path.join(root_key_output, _cat, sub_cat, f)
                    for f in file_tree_dict[root_key_input][_cat][sub_cat][file_key]
                ],
            }
            for sub_cat in sub_categories
        ]
    else:
        file_list = [
            os.path.join(root_key_output, _cat, f)
            for f in file_tree_dict[root_key_input][_cat][file_key]
        ]

    return file_list


# For module doc string
_unzipped_parquet_destination = get_data_dir()
_file_tree = print_file_tree(
    as_str=True,
    formatter=_tree_trunc,
)
_file_tree_dict = make_file_tree_dict(start_key="rel")
_file_tree_dict_str = json.dumps(_file_tree_dict, indent=4)[:300] + "\n\n\t..."
_expense_files = f"[{', '.join(list_files('expenses', path_type='base')[:1])}..."
_benefits_files = (
    json.dumps(list_files("benefits", path_type="base")[:2], indent=2).rstrip("]")
    + "\t...\n]"
)
_cur_file_name = os.path.basename(__file__)
__doc__ = __doc__.format(
    unzipped_parquet_destination=_unzipped_parquet_destination,
    file_tree=_file_tree,
    file_tree_dict=_file_tree_dict_str,
    expense_files=_expense_files,
    benefits_files=_benefits_files,
    cur_file_name=_cur_file_name,
)

if __name__ == "__main__":
    print(__doc__)

    for x in ["expenses", "jobs", "geog", "taxes", "parameter_defaults", "benefits"]:
        list_files(x)
