from datetime import datetime, timezone, timedelta

import pytest

from wandbctl.commands.trends import get_sparkline


def test_sparkline_empty():
    result = get_sparkline([])
    assert result == ""


def test_sparkline_zeros():
    result = get_sparkline([0, 0, 0])
    assert result == "▁▁▁"


def test_sparkline_single_value():
    result = get_sparkline([5])
    assert result == "█"


def test_sparkline_increasing():
    result = get_sparkline([1, 2, 3, 4, 5])
    assert len(result) == 5
    assert result[0] < result[-1]


def test_sparkline_mixed():
    result = get_sparkline([0, 5, 2, 8, 3])
    assert len(result) == 5
    assert result[3] == "█"
