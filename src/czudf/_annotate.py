# SPDX-FileCopyrightText: 2026 Yunqi Inc
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from typing import TypeVar, cast

from ._runtime import _runtime_annotate

T = TypeVar("T", bound=object)


def annotate(signature: str) -> Callable[[type[T]], type[T]]:
    """Decorator for annotating a UDF class.

    Example:

    >>> @annotate("string,int->string")
    ... class Repeat:
    ...     def evaluate(self, x: str, y: int) -> str:
    ...         return x * y if x and y > 0 else ""

    Args:
        signature: The signature of the UDF.
    """

    return cast(Callable[[type[T]], type[T]], _runtime_annotate(signature))
