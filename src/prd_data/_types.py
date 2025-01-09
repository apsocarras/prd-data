from pathlib import Path
from typing import Literal, Protocol, TypeAlias, TypeVar, runtime_checkable

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


@runtime_checkable
class StrSequence(Protocol):
    """Protocol for ensuring an object is a Sequence[str] and not a str"""

    def check(obj: object) -> bool:
        return not isinstance(obj, str) and isinstance(obj, Sequence[str])


@runtime_checkable
class PathSequence(Protocol):
    def check(obj: object) -> bool:
        return not isinstance(obj, str) and isinstance(obj, Sequence[Union[Path, str]])
