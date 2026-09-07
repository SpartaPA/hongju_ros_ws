"""문제 3 — 회전 행렬의 수학적 성질 검증 (pytest). [학생 작성용 템플릿]

지시문이 요구하는 4가지를 각각 테스트 함수로 작성한다.

  1. 회전행렬의 열이 서로 직교하는 단위벡터인가   -> test_columns_are_orthonormal
  2. 행렬식이 1인가                               -> test_determinant_is_one
  3. 역행렬이 전치와 같은가                       -> test_inverse_equals_transpose
  4. 재직교화 결과가 직교행렬인가                 -> test_gram_schmidt_restores_orthogonality

작성 요령
--------
- `@pytest.mark.parametrize` 로 여러 축 x 여러 각도를 한 함수에서 검사하면
  테스트 하나가 여러 케이스를 담당한다 (아래 ANGLES / MAKERS 참고).
- 비교는 반드시 `np.isclose` / `np.allclose` 로 한다 (부동소수점).
- `np.linalg` 는 검산용으로만 쓰고, 쓸 때는 주석으로 검산임을 밝힌다.
- assert 에 실패 메시지를 붙이면 어디가 깨졌는지 바로 보인다.
- 4개는 **최소 개수**다. 반사 행렬 반례, 로드리게스 일치, 축·각 왕복 같은
  테스트를 더 붙이면 좋다.

실행: 프로젝트 루트에서  pytest -v
"""

import numpy as np
import pytest

from src.rotation import (
    axis_angle_from_matrix,
    gram_schmidt,
    is_rotation,
    orthogonality_error,
    rodrigues,
    rot_x,
    rot_y,
    rot_z,
)

ANGLES = [0.0, np.deg2rad(22.5), np.pi / 6, np.pi / 4, np.pi / 2, 2.0, np.pi, -1.234]
MAKERS = [rot_x, rot_y, rot_z]


@pytest.fixture
def rng():
    """난수는 반드시 시드를 고정한다."""
    return np.random.default_rng(42)


# --- 1. 열이 서로 직교하는 단위벡터인가 -------------------------------------

@pytest.mark.parametrize("maker", MAKERS)
@pytest.mark.parametrize("theta", ANGLES)
def test_columns_are_orthonormal(maker, theta):
    R = maker(theta)
    assert np.allclose(R.T @ R, np.eye(3), atol=1e-8)


# --- 2. 행렬식이 1인가 --------------------------------------------------------

@pytest.mark.parametrize("maker", MAKERS)
@pytest.mark.parametrize("theta", ANGLES)
def test_determinant_is_one(maker, theta):
    R = maker(theta)
    det_R = (
        R[0, 0] * (R[1, 1] * R[2, 2] - R[1, 2] * R[2, 1])
      - R[0, 1] * (R[1, 0] * R[2, 2] - R[1, 2] * R[2, 0])
      + R[0, 2] * (R[1, 0] * R[2, 1] - R[1, 1] * R[2, 0])
    )
    assert np.isclose(det_R, 1.0, atol=1e-8)


# --- 3. 역행렬 == 전치 --------------------------------------------------------

@pytest.mark.parametrize("maker", MAKERS)
@pytest.mark.parametrize("theta", ANGLES)
def test_inverse_equals_transpose(maker, theta):
    R = maker(theta)
    assert np.allclose(np.linalg.inv(R), R.T, atol=1e-8)


# --- 4. 재직교화 결과가 직교행렬인가 -----------------------------------------

def test_gram_schmidt_restores_orthogonality(rng):
    # 임의의 회전행렬 생성 및 노이즈 추가로 직교성 파괴
    R_base = rot_z(0.5) @ rot_y(-0.3) @ rot_x(0.8)
    noise = rng.normal(0, 0.05, size=(3, 3))
    R_noisy = R_base + noise

    # gram_schmidt 로 재직교화 수행
    R_fixed = gram_schmidt(R_noisy)

    # 직교성 오차 계산: max |R_fixed^T @ R_fixed - I|
    ortho_err = np.max(np.abs(R_fixed.T @ R_fixed - np.eye(3)))

    # 행렬식 계산
    det_val = (
        R_fixed[0, 0] * (R_fixed[1, 1] * R_fixed[2, 2] - R_fixed[1, 2] * R_fixed[2, 1])
      - R_fixed[0, 1] * (R_fixed[1, 0] * R_fixed[2, 2] - R_fixed[1, 2] * R_fixed[2, 0])
      + R_fixed[0, 2] * (R_fixed[1, 0] * R_fixed[2, 1] - R_fixed[1, 1] * R_fixed[2, 0])
    )

    # 5. 검증
    assert ortho_err < 1e-12, f"직교성 오차가 기계정밀도 수준이 아닙니다: {ortho_err}"
    assert np.isclose(det_val, 1.0, atol=1e-12), f"행렬식이 1이 아닙니다: {det_val}"
    assert is_rotation(R_fixed), "Gram-Schmidt 복구 결과가 유효한 회전행렬(SO(3))이 아닙니다."


# --- 여기부터는 추가 테스트 (권장) -------------------------------------------
#
def test_reflection_is_not_a_rotation():
    """det = -1 인 반사 행렬은 직교여도 회전이 아니다."""
    # y축 반사 행렬 (Reflection Matrix)
    S = np.diag([1.0, -1.0, 1.0])

    # 1. 직교성 검증 (S^T @ S == I)
    ortho_err = np.max(np.abs(S.T @ S - np.eye(3)))
    assert ortho_err < 1e-12, f"반사 행렬은 직교행렬이어야 합니다: {ortho_err}"

    # 2. 행렬식 검증 (det(S) == -1)
    det_S = np.linalg.det(S)
    assert np.isclose(det_S, -1.0, atol=1e-12), f"반사 행렬의 행렬식은 -1 이어야 합니다: {det_S}"

    # 3. 회전 행렬 여부 검증 (is_rotation(S) == False)
    assert not is_rotation(S), "det = -1 인 반사 행렬은 is_rotation 이 False 이어야 합니다."


@pytest.mark.parametrize("theta", ANGLES)
def test_rodrigues_matches_rot_z(theta):
    """z축 회전에 대해 rodrigues([0, 0, 1], theta)가 rot_z(theta)와 일치하는지 검증."""
    z_axis = np.array([0.0, 0.0, 1.0])
    R_rod = rodrigues(z_axis, theta)
    R_rot = rot_z(theta)

    assert np.allclose(R_rod, R_rot, atol=1e-12), (
        f"theta={theta}rad 에서 rodrigues([0, 0, 1], theta)와 rot_z(theta)가 불일치합니다.\n"
        f"R_rod:\n{R_rod}\nR_rot:\n{R_rot}"
    )


def test_axis_angle_roundtrip(rng):
    """임의의 축 k와 각도 theta로 생성한 회전행렬의 고유 속성(R k = k, trace(R)) 복원 검증."""
    # 1. 임의의 3차원 무작위 축 생성 및 정규화
    raw_axis = rng.normal(size=3)
    axis_norm = np.sqrt(np.sum(raw_axis**2))
    k = raw_axis / axis_norm
    theta = rng.uniform(-np.pi, np.pi)

    # 2. 로드리게스 공식으로 회전행렬 R 생성
    R = rodrigues(k, theta)

    # 3.1. 회전축 불변성 검증: R @ k == k
    assert np.allclose(R @ k, k, atol=1e-12), "회전축 불변성 (R @ k == k) 조건을 만족하지 않습니다."

    # 3.2. 대각합(trace)을 이용한 회전각 복원 검증: trace(R) = 1 + 2*cos(theta)
    trace_val = R[0, 0] + R[1, 1] + R[2, 2]
    cos_theta = np.clip((trace_val - 1.0) / 2.0, -1.0, 1.0)
    recovered_abs_theta = np.arccos(cos_theta)

    assert np.isclose(recovered_abs_theta, np.abs(theta), atol=1e-12), (
        f"복원된 회전각|theta| ({recovered_abs_theta})가 원본 |theta| ({np.abs(theta)})와 일치하지 않습니다."
    )