# SPDX-FileCopyrightText: 2026 Yunqi Inc
# SPDX-License-Identifier: Apache-2.0

import importlib.metadata
from unittest.mock import patch

from czudf import _version


def test_version_falls_back_without_distribution_metadata():
    with patch.object(
        importlib.metadata,
        "version",
        side_effect=importlib.metadata.PackageNotFoundError,
    ):
        assert _version._get_version() == "0.0.0+unknown"
