# SPDX-FileCopyrightText: 2026 Yunqi Inc
# SPDX-License-Identifier: Apache-2.0

import importlib.metadata


def _get_version() -> str:
    try:
        return importlib.metadata.version("czudf-toolkit")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0+unknown"


__version__ = _get_version()
