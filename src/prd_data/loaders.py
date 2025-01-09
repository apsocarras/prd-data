import importlib
import importlib.resources
import os
import warnings
from io import BytesIO
from types import MappingProxyType, ModuleType
from typing import Optional, Type, Union

import data as _data_resources

from prd_data._types import PathSequence
from prd_data.file_tree import FILE_TREE


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

elif POLARS_INSTALLED := check_if_package_installed("polars"):
    import keyword
    import re

    import polars as pl

    class DataLoader:
        """
        Highly-simplified version of DVGrouper which omits the validation (schema enforcement, filename expectation, file types, etc.), metadata collection, & documentation utilities of the class.
        Retains same API:
          - Referring to LazyFrame/DataFrame objects as named attributes of the class.
          - Load all pl.LazyFrames with .load()
        """

        def __init__(
            self,
            name: str,
            paths: PathSequence,
        ):
            if isinstance(paths, str):
                warnings.warn(
                    f"paths must be a collection of str or Path types (given: {paths}). Wrapping in list."
                )
                _paths = paths
            else:
                _paths = paths

            datasets = []
            for file in _paths:
                file_data: BytesIO = _load_file_bytes(file)
                if os.path.splitext(file)[-1] != ".parquet":
                    warnings.warn(f"Not a parquet file: {file}")
                    continue
                if not os.path.isfile(file):
                    warnings.warn(f"File Not Found: {file}")
                    continue
                base_name = os.path.basename(file)
                attr_name = get_clean_object_name(base_name)
                attr_name = attr_name.removesuffix("_parquet")

                q = pl.scan_parquet(file_data)
                setattr(self, attr_name, q)
                datasets.append(attr_name)

            self.__name__ = name
            self.paths = _paths
            self.datasets = datasets

        def __str__(self):
            return str(self.datasets)

        def load(self):
            for dataset_name in self.datasets:
                data: pl.LazyFrame = getattr(self, dataset_name)
                data = data.collect()
                setattr(self, dataset_name, data)

        @classmethod
        def factory(
            cls, name, paths: PathSequence, doc_string: Optional[str] = None
        ) -> "DataLoader":
            class NamedDataLoader(cls):
                def __init__(self, paths=None):
                    self.__doc__ = (
                        doc_string
                        if doc_string is not None
                        else f"A selection of {name} data frames."
                    )
                    self.__name__ = name
                    super().__init__(name, paths)

            return NamedDataLoader

    Expenses = DataLoader.factory(name="Expenses", paths=FILE_TREE["expenses"]["files"])
    Taxes = DataLoader.factory(name="Taxes", paths=FILE_TREE["taxes"]["files"])
    Jobs = DataLoader.factory(name="Jobs", paths=FILE_TREE["jobs"]["files"])
    Geog = DataLoader.factory(name="Geog", paths=FILE_TREE["geog"]["files"])

    # Benefits Sub Categories
    Healthcare = DataLoader.factory(
        name="Healthcare", paths=FILE_TREE["healthcare"]["files"]
    )
    Housing = DataLoader.factory(name="Housing", paths=FILE_TREE["housing"]["files"])
    Tax_Credits = DataLoader.factory(
        name="Tax_Credits", paths=FILE_TREE["tax_credits"]["files"]
    )
    Social_security = DataLoader.factory(
        name="Social_Security", paths=FILE_TREE["social_security"]["files"]
    )
    Childcare = DataLoader.factory(
        name="Childcare", paths=FILE_TREE["childcare"]["files"]
    )
    Food = DataLoader.factory(name="Food", paths=FILE_TREE["food"]["files"])

    class Benefits:
        def __init__(
            self,
            healthcare: Type[DataLoader] = Healthcare,
            housing: Type[DataLoader] = Housing,
            tax_credits: Type[DataLoader] = Tax_Credits,
            social_security: DataLoader = Social_security,
            child_care: Type[DataLoader] = Childcare,
            food: Type[DataLoader] = Food,
        ):
            _datasets = {}
            for arg in (
                healthcare,
                housing,
                tax_credits,
                social_security,
                child_care,
                food,
            ):
                arg: DataLoader
                _datasets[arg.__name__] = arg

            _datasets = MappingProxyType(_datasets)

            self._datasets = _datasets

        @property
        def datasets(self):
            return self._datasets

        def list_datasets(self):
            return list(self._datasets.values())

        @property
        def healthcare(self):
            return self._datasets["healthcare"]

        @property
        def housing(self):
            return self._datasets["housing"]

        @property
        def tax_credits(self):
            return self._datasets["tax_credits"]

        @property
        def social_security(self):
            return self._datasets["social_security"]

        @property
        def child_care(self):
            return self._datasets["child_care"]

        @property
        def food(self):
            return self._datasets["food"]

        def load(self):
            """Load each DataLoader in self.datasets"""
            for d in self.list_datasets():
                d: DataLoader
                d.load()

    Benefits()
