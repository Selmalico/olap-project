"""Utility to recursively convert numpy/pandas types to JSON-serialisable Python types."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def sanitize(obj: Any) -> Any:
    """Recursively walk a dict/list structure and cast numpy scalars to native Python."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    # Any numpy scalar (has .item() and is numpy.generic)
    if isinstance(obj, np.generic) and not isinstance(obj, np.ndarray):
        try:
            return sanitize(obj.item())
        except (ValueError, AttributeError):
            return int(obj) if isinstance(obj, np.integer) else float(obj)
    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj
