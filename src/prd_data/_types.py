from pathlib import Path
from types import MappingProxyType
from typing import (
    Literal,
    Mapping,
    Protocol,
    Sequence,
    TypeAlias,
    TypedDict,
    TypeVar,
    Union,
    runtime_checkable,
)

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


class FilesDict(TypedDict):
    files: list[str]


class PRD_FileTreeDict(TypedDict):
    geog: FilesDict
    expenses: FilesDict
    parameter_defaults: FilesDict
    taxes: FilesDict
    benefits: Mapping[BenefitsSubCategory, FilesDict]


PRD_FileTreeType: TypeAlias = MappingProxyType[PRD_FileTreeDict]
# won't work with static type checker: see https://discuss.python.org/t/introduce-a-typedmapping-analog-to-typeddict-but-frozen/51905/6


@runtime_checkable
class StrSequence(Protocol):
    """Protocol for ensuring an object is a Sequence[str] and not a str"""

    def check(obj: object) -> bool:
        return not isinstance(obj, str) and isinstance(obj, Sequence[str])


@runtime_checkable
class PathSequence(Protocol):
    def check(obj: object) -> bool:
        return not isinstance(obj, str) and isinstance(obj, Sequence[Union[Path, str]])
