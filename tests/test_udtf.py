# SPDX-FileCopyrightText: 2026 Yunqi Inc
# SPDX-License-Identifier: Apache-2.0

import importlib
import sys
from types import ModuleType
from typing import Any

import pytest

from czudf import BaseUDTF, _runtime, _udtf, udtf


def _run_udtf(
    udtf: BaseUDTF,
    rows: list[tuple[Any, ...]],
) -> list[tuple[Any, ...]]:
    output: list[tuple[Any, ...]] = []

    def collect(*values: Any) -> None:
        output.append(values)

    udtf.forward = collect
    for row in rows:
        udtf.process(*row)
    udtf.close()
    return output


def test_udtf_forwards_zero_or_more_rows_and_closes() -> None:
    class Explode(BaseUDTF):
        def process(self, value: str | None) -> None:
            if value is None:
                return
            for item in value.split("|"):
                self.forward(item)

        def close(self) -> None:
            self.forward("done")

    assert _run_udtf(Explode(), [("a|b",), (None,)]) == [
        ("a",),
        ("b",),
        ("done",),
    ]


def test_udtf_does_not_require_super_init() -> None:
    class WithState(BaseUDTF):
        def __init__(self) -> None:
            self.prefix = "value:"

        def process(self, value: str) -> None:
            self.forward(self.prefix + value)

    assert _run_udtf(WithState(), [("x",)]) == [("value:x",)]


def test_process_must_be_implemented() -> None:
    with pytest.raises(NotImplementedError, match="must implement process"):
        BaseUDTF().process("value")


def test_forward_is_noop_without_runtime() -> None:
    BaseUDTF().forward("value")


def test_udtf_decorator_is_identity_without_runtime() -> None:
    @udtf(returnType="word: string")
    class Split:
        def eval(self, value: str):
            yield (value,)

    assert list(Split().eval("value")) == [("value",)]


def test_udtf_supports_direct_call() -> None:
    class Split:
        pass

    assert udtf(Split, returnType="word: string") is Split


def test_base_udtf_inherits_platform_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class PlatformBaseUDTF:
        def forward(self, *args: Any) -> None:
            self.forwarded = args

    runtime_module = ModuleType("custom.runtime")
    runtime_module.udtf_base_class = lambda: PlatformBaseUDTF  # type: ignore[attr-defined]
    runtime_module.register_function = lambda: (  # type: ignore[attr-defined]
        lambda signature: lambda cls: cls
    )
    runtime_module.udtf_decorator = lambda: (  # type: ignore[attr-defined]
        lambda return_type: lambda cls: cls
    )

    with monkeypatch.context() as context:
        context.setenv("CZUDF_RUNTIME_MODULE", "custom.runtime")
        context.setitem(sys.modules, "custom.runtime", runtime_module)
        importlib.reload(_runtime)
        runtime_udtf_module = importlib.reload(_udtf)

        assert issubclass(runtime_udtf_module.BaseUDTF, PlatformBaseUDTF)
        instance = runtime_udtf_module.BaseUDTF()
        instance.forward("value", 1)
        assert instance.forwarded == ("value", 1)

    importlib.reload(_runtime)
    importlib.reload(_udtf)


def test_udtf_delegates_to_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    registrations: list[tuple[type[Any], str]] = []
    runtime_module = ModuleType("custom.runtime")
    runtime_module.udtf_base_class = lambda: object  # type: ignore[attr-defined]

    def runtime_annotate(return_type: str):
        def register(cls: type[Any]) -> type[Any]:
            registrations.append((cls, return_type))
            return cls

        return register

    runtime_module.register_function = lambda: (  # type: ignore[attr-defined]
        lambda signature: lambda cls: cls
    )
    runtime_module.udtf_decorator = lambda: runtime_annotate  # type: ignore[attr-defined]

    with monkeypatch.context() as context:
        context.setenv("CZUDF_RUNTIME_MODULE", "custom.runtime")
        context.setitem(sys.modules, "custom.runtime", runtime_module)
        importlib.reload(_runtime)
        runtime_udtf_module = importlib.reload(_udtf)

        @runtime_udtf_module.udtf(returnType="word: string")
        class Split:
            pass

        assert registrations == [(Split, "word: string")]

    importlib.reload(_runtime)
    importlib.reload(_udtf)


def test_configured_runtime_module_must_be_importable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as context:
        context.setenv("CZUDF_RUNTIME_MODULE", "missing_runtime_module")
        with pytest.raises(ModuleNotFoundError, match="missing_runtime_module"):
            importlib.reload(_runtime)

    importlib.reload(_runtime)
