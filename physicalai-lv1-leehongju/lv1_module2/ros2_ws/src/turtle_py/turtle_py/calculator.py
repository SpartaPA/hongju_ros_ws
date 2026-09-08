import math


def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """목표 지점까지의 2D 유클리드 거리를 계산합니다."""
    return math.hypot(x2 - x1, y2 - y1)


def normalize_angle(angle: float) -> float:
    """각도를 -pi ~ pi 범위로 정규화합니다."""
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def calculate_target_angle(curr_x: float, curr_y: float,
                           target_x: float, target_y: float) -> float:
    """현재 위치에서 목표 위치를 향하는 사잇각(-pi ~ pi)을 계산합니다."""
    dx = target_x - curr_x
    dy = target_y - curr_y
    return normalize_angle(math.atan2(dy, dx))


def is_waypoint_reached(curr_x: float, curr_y: float,
                        target_x: float, target_y: float,
                        tolerance: float) -> bool:
    """현재 위치가 경유점의 허용 오차 범위 내에 도달했는지 판정합니다."""
    if tolerance <= 0.0:
        raise ValueError("tolerance는 0보다 큰 양수여야 합니다.")
    dist = calculate_distance(curr_x, curr_y, target_x, target_y)
    return dist <= tolerance
