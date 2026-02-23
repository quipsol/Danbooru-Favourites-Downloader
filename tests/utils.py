from typing import TypeVar, cast
from unittest.mock import MagicMock

T = TypeVar("T")

def as_mock(obj: T) -> MagicMock:
    return cast(MagicMock, obj)