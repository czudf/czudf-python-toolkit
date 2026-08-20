# SPDX-FileCopyrightText: 2026 Yunqi Inc
# SPDX-License-Identifier: Apache-2.0

import importlib
import sys
from types import ModuleType
from typing import Any

import pytest

from czudf import _annotate, _runtime, annotate


def test_annotate():
    @annotate("string,int->string")
    class Repeat:
        def evaluate(self, x: str, y: int) -> str:
            return x * y if x and y > 0 else ""

    repeat = Repeat()
    assert repeat.evaluate("x", 3) == "xxx"


def test_annotate_registers_class_with_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    registrations: list[tuple[type[Any], str]] = []
    runtime_module = ModuleType("custom.runtime")
    runtime_module.udtf_base_class = lambda: object  # type: ignore[attr-defined]

    def runtime_annotate(signature: str):
        def register(cls: type[Any]) -> type[Any]:
            registrations.append((cls, signature))
            return cls

        return register

    runtime_module.register_function = lambda: runtime_annotate  # type: ignore[attr-defined]
    runtime_module.udtf_decorator = lambda: (  # type: ignore[attr-defined]
        lambda return_type: lambda cls: cls
    )

    with monkeypatch.context() as context:
        context.setenv("CZUDF_RUNTIME_MODULE", "custom.runtime")
        context.setitem(sys.modules, "custom.runtime", runtime_module)
        importlib.reload(_runtime)
        runtime_annotate_module = importlib.reload(_annotate)

        @runtime_annotate_module.annotate("string->bigint")
        class Length:
            pass

        assert registrations == [(Length, "string->bigint")]

    importlib.reload(_runtime)
    importlib.reload(_annotate)
