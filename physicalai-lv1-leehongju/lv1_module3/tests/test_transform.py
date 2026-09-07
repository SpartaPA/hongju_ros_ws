"""문제 5 — 동차변환 inv_T 검증 (pytest). [학생 작성용 템플릿]

지시문이 요구하는 것은 `inv_T` 검증이지만,
점/방향 구분과 벡터화, 최소자승까지 함께 검증해 두면 이후 문제에서 안전하다.

실행: 프로젝트 루트에서  pytest -v
"""

import numpy as np
import pytest

from src.rotation import rot_x, rot_y, rot_z
from src.transform import (
    inv_T,
    least_squares_normal_equation,
    make_T,
    transform_direction,
    transform_point,
    transform_points,
)


@pytest.fixture
def T():
    """테스트에 쓸 대표 동차변환 하나."""
    R = rot_z(0.9) @ rot_y(-0.35) @ rot_x(1.3)
    return make_T(R, [0.35, -0.15, 0.55])


def test_inv_T_gives_identity(T):
    T_inv = inv_T(T)
    
    # T_inv @ T 와 T @ T_inv 가 모두 4x4 단위행렬인지 검사
    assert np.allclose(T_inv @ T, np.eye(4), atol=1e-8), "inv_T(T) @ T 가 단위행렬이 아닙니다."
    assert np.allclose(T @ T_inv, np.eye(4), atol=1e-8), "T @ inv_T(T) 가 단위행렬이 아닙니다."


def test_inv_T_matches_generic_inverse(T):
    T_inv = inv_T(T)
    T_inv_check = np.linalg.inv(T)  # 검산용

    # inv_T(T)가 일반 역행렬 계산과 정확히 일치하는지 검사
    assert np.allclose(T_inv, T_inv_check, atol=1e-8), "inv_T(T) 가 np.linalg.inv(T)와 일치하지 않습니다."


def test_point_and_direction_differ(T):
    v = np.array([1.0, 2.0, -1.5])

    p_trans = transform_point(T, v)
    d_trans = transform_direction(T, v)

    # 1. 점(w=1)과 방향(w=0)의 변환 결과가 다른지 검사
    assert not np.allclose(p_trans, d_trans), "점과 방향의 변환 결과가 동일합니다."

    # 2. 점 변환과 방향 변환의 차이가 정확히 병진 벡터 t = T[:3, 3] 인지 검사
    t_expected = T[:3, 3]
    assert np.allclose(p_trans - d_trans, t_expected, atol=1e-8), "점과 방향 변환의 차이가 병진 벡터와 다릅니다."

    # 3. 방향 변환 시 벡터의 길이가 보존되는지 검사 (회전은 길이를 보존함)
    norm_v = np.sqrt(np.sum(v * v))
    norm_d = np.sqrt(np.sum(d_trans * d_trans))
    assert np.isclose(norm_v, norm_d, atol=1e-8), "방향 변환 시 벡터 길이가 보존되지 않았습니다."


def test_transform_points_is_vectorized(T):
    rng = np.random.default_rng(42)
    pts = rng.uniform(-10.0, 10.0, size=(100, 3))

    # (N,3) 점군을 한 번에 벡터화 변환
    pts_vec = transform_points(T, pts)

    # transform_point 를 반복문으로 돌린 결과 수집
    pts_loop = np.array([transform_point(T, p) for p in pts])

    # 두 연산 결과가 완벽히 같은지 검사
    assert np.allclose(pts_vec, pts_loop, atol=1e-8), "벡터화 변환 결과가 반복문 연산 결과와 다릅니다."


def test_roundtrip_through_inverse(T):
    rng = np.random.default_rng(42)
    pts_orig = rng.uniform(-5.0, 5.0, size=(50, 3))

    # T 로 변환했다가 inv_T(T) 로 되돌림
    pts_trans = transform_points(T, pts_orig)
    pts_restored = transform_points(inv_T(T), pts_trans)

    # 원래 점군으로 정확히 복원되었는지 검사
    assert np.allclose(pts_orig, pts_restored, atol=1e-8), "역변환 복원 시 원래 점군과 오차가 발생했습니다."


def test_least_squares_matches_lstsq():
    rng = np.random.default_rng(42)

    # 1. 과결정 시스템 A (10x3) 및 b (10,) 생성 (노이즈 주입)
    A = rng.uniform(-2.0, 2.0, size=(10, 3))
    x_true = np.array([1.5, -2.0, 0.5])
    b = A @ x_true + rng.normal(0.0, 0.05, size=10)

    # 2. 정규방정식(Normal Equation) 기반 해 구하기
    x_sol, residual = least_squares_normal_equation(A, b)

    # 3. 검산용: np.linalg.lstsq 해와 비교
    x_lstsq, _, _, _ = np.linalg.lstsq(A, b, rcond=None)  # 검산용: np.linalg.lstsq
    assert np.allclose(x_sol.ravel(), x_lstsq.ravel(), atol=1e-8), "최소자승해 결과가 np.linalg.lstsq 와 일치하지 않습니다."

    # 4. 잔차 직교성 검증 (A^T r == 0)
    ortho_residual = A.T @ residual.ravel()
    assert np.allclose(ortho_residual, np.zeros(3), atol=1e-8), "잔차가 A 의 열공간에 직교하지 않습니다."
