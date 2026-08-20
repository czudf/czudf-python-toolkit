# SPDX-FileCopyrightText: 2026 Yunqi Inc
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from typing import Any, TypeVar, cast, overload

from ._runtime import _runtime_udtf, _RuntimeBaseUDTF

T = TypeVar("T", bound=object)


@overload
def udtf(
    cls: None = None,
    *,
    returnType: str,
) -> Callable[[type[T]], type[T]]: ...


@overload
def udtf(cls: type[T], *, returnType: str) -> type[T]: ...


def udtf(
    cls: type[T] | None = None,
    *,
    returnType: str,
) -> Callable[[type[T]], type[T]] | type[T]:
    """Create a PySpark-style user-defined table function decorator.

    Args:
        cls: Optional UDTF handler class when called without decorator syntax.
        returnType: DDL string describing the output row.
    """
    decorator = cast(Callable[[type[T]], type[T]], _runtime_udtf(returnType))
    if cls is None:
        return decorator
    return decorator(cls)


class BaseUDTF(_RuntimeBaseUDTF):  # type: ignore[misc]
    """Base class for user-defined table functions.

    Subclasses implement :meth:`process` and call :meth:`forward` once for
    every row they want to emit. The execution runtime base class provides
    ``forward`` and sends emitted rows to its output collector.

    ``BaseUDTF`` deliberately has no constructor state. This allows subclasses
    to define ``__init__`` without having to call ``super().__init__()``.
    """

    def process(self, *args: Any) -> None:
        """Process one input row.

        Args:
            *args: Values from the input row.

        Raises:
            NotImplementedError: Always, unless implemented by a subclass.
        """
        raise NotImplementedError(f"{type(self).__name__} must implement process()")

    def close(self) -> None:
        """Finish processing and optionally emit final rows."""
