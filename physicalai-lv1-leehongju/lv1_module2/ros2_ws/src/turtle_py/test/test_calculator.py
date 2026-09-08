import math
import pytest
from turtle_py.calculator import (calculate_distance, calculate_target_angle,
                                  is_waypoint_reached)


def test_calculate_distance():
    assert math.isclose(calculate_distance(0.0, 0.0, 3.0, 4.0), 5.0)
    assert math.isclose(calculate_distance(2.5, 2.5, 2.5, 2.5), 0.0)


def test_calculate_target_angle():
    assert math.isclose(calculate_target_angle(0.0, 0.0, 1.0, 1.0), math.pi / 4.0)
    assert math.isclose(calculate_target_angle(1.0, 0.0, 0.0, 0.0), math.pi)


def test_is_waypoint_reached():
    assert is_waypoint_reached(1.0, 1.0, 1.2, 1.0, 0.3) is True
    assert is_waypoint_reached(0.0, 0.0, 0.3, 0.0, 0.3) is True
    assert is_waypoint_reached(0.0, 0.0, 0.31, 0.0, 0.3) is False
    with pytest.raises(ValueError):
        is_waypoint_reached(0.0, 0.0, 1.0, 1.0, -0.1)