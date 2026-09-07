import math
import pytest
from turtle_py.calculator import calculate_distance, calculate_target_angle, is_waypoint_reached


# 1. 거리 계산 테스트
def test_calculate_distance():
    # 정상 입력
    assert math.isclose(calculate_distance(0.0, 0.0, 3.0, 4.0), 5.0)
    # 동일 위치 (경계값)
    assert math.isclose(calculate_distance(2.5, 2.5, 2.5, 2.5), 0.0)


# 2. 목표 각도 계산 테스트
def test_calculate_target_angle():
    # 1사분면 (45도 -> rad: pi/4)
    assert math.isclose(calculate_target_angle(0.0, 0.0, 1.0, 1.0), math.pi / 4.0)
    # 반대 방향 (180도 -> rad: pi)
    assert math.isclose(calculate_target_angle(1.0, 0.0, 0.0, 0.0), math.pi)


# 3. 경유점 도달 판정 테스트
def test_is_waypoint_reached():
    # 경계 내부 (도달)
    assert is_waypoint_reached(1.0, 1.0, 1.2, 1.0, 0.3) is True
    # 경계선 상 (도달)
    assert is_waypoint_reached(0.0, 0.0, 0.3, 0.0, 0.3) is True
    # 경계 외부 (미도달)
    assert is_waypoint_reached(0.0, 0.0, 0.31, 0.0, 0.3) is False
    # 예외 상황 (tolerance <= 0)
    with pytest.raises(ValueError):
        is_waypoint_reached(0.0, 0.0, 1.0, 1.0, -0.1)