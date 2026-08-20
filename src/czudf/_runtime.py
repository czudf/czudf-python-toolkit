# SPDX-FileCopyrightText: 2026 Yunqi Inc
# SPDX-License-Identifier: Apache-2.0

import importlib
import os
from collections.abc import Callable
from typing import Any, cast

_RUNTIME_MODULE = os.getenv("CZUDF_RUNTIME_MODULE")
_RuntimeAnnotate = Callable[[str], Callable[[type[Any]], type[Any]]]
_RuntimeUDTFDecorator = Callable[[str], Callable[[type[Any]], type[Any]]]


class _BaseUDTFStub:
    """Stub base class used when the platform runtime is absent."""

    def forward(self, *args: Any) -> None:
        """Discard an output row when no platform runtime is available."""


def _annotate_stub(
    signature: str,
) -> Callable[[type[Any]], type[Any]]:
    """Return an identity decorator when no platform runtime is available."""

    def _wrapper(cls: type[Any]) -> type[Any]:
        return cls

    return _wrapper


def _udtf_stub(
    return_type: str,
) -> Callable[[type[Any]], type[Any]]:
    """Return an identity UDTF decorator when the runtime is absent."""

    def _wrapper(cls: type[Any]) -> type[Any]:
        return cls

    return _wrapper


_RuntimeBaseUDTF: type[Any]
_runtime_annotate: _RuntimeAnnotate
_runtime_udtf: _RuntimeUDTFDecorator
if not _RUNTIME_MODULE:
    _RuntimeBaseUDTF = _BaseUDTFStub
    _runtime_annotate = _annotate_stub
    _runtime_udtf = _udtf_stub
else:
    _RuntimeModule = importlib.import_module(_RUNTIME_MODULE)
    _RuntimeBaseUDTF = cast(type[Any], _RuntimeModule.udtf_base_class())
    _runtime_annotate = cast(_RuntimeAnnotate, _RuntimeModule.register_function())
    _runtime_udtf = cast(_RuntimeUDTFDecorator, _RuntimeModule.udtf_decorator())
