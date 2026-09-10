"""문제 3 — 쿼터니언과 SLERP 검증 (pytest). [학생 작성용 템플릿]

지시문이 요구하는 두 가지:

  1. SLERP 결과가 항상 단위 쿼터니언인가                 -> test_slerp_is_unit_norm
  2. 보간 비율 0 과 1 에서 시작·목표 자세와 같은가       -> test_slerp_endpoints

작성 요령
--------
- 쿼터니언 순서는 (x, y, z, w). q 와 -q 는 같은 회전이므로 자세 비교는
  `quaternion_to_matrix` 로 회전행렬을 만들어 비교하거나 |q . q_ref| == 1 로 한다.
- `@pytest.mark.parametrize("t", [...])` 로 여러 비율을 한 번에 검사한다.
- 비교는 `np.allclose` / `np.isclose` (기본 허용오차).

실행: 프로젝트 루트에서  pytest tests/test_quaternion.py -v
"""

import numpy as np
import pytest

from src.quaternion import lerp_quat, matrix_to_quaternion, quaternion_to_matrix, slerp
from src.rotation import rodrigues, rot_x, rot_y, rot_z
from scipy.spatial.transform import Rotation, Slerp

TS = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]


@pytest.fixture
def rng():
    return np.random.default_rng(42)


@pytest.fixture
def q_pair():
    """시작·목표 자세 (노트북 3-2 와 같은 값)."""
    R_start = rot_z(np.deg2rad(-30.0)) @ rot_x(np.deg2rad(20.0))
    R_goal = rot_z(np.deg2rad(120.0)) @ rot_y(np.deg2rad(60.0)) @ rot_x(np.deg2rad(-40.0))
    return matrix_to_quaternion(R_start), matrix_to_quaternion(R_goal)


# --- 1. SLERP 결과는 항상 단위 쿼터니언 ---------------------------------------

@pytest.mark.parametrize("t", TS)
def test_slerp_is_unit_norm(q_pair, t):
    q0, q1 = q_pair
    q_interp = slerp(q0, q1, t)
    
    # 쿼터니언의 크기(Norm)가 1인지 검사
    norm = np.linalg.norm(q_interp)
    assert np.isclose(norm, 1.0, atol=1e-7), f"t={t}에서 SLERP 결과의 노름이 1이 아닙니다: norm={norm}"


# --- 2. t = 0 / 1 에서 시작·목표 자세 -----------------------------------------

def test_slerp_endpoints(q_pair):
    q0, q1 = q_pair
    
    # t = 0 및 t = 1 지점 계산
    q_start_eval = slerp(q0, q1, 0.0)
    q_goal_eval = slerp(q0, q1, 1.0)
    
    # 이중 덮개(Double Cover, q와 -q)를 고려하여 회전행렬 비교
    R0_ref = quaternion_to_matrix(q0)
    R1_ref = quaternion_to_matrix(q1)
    
    R0_eval = quaternion_to_matrix(q_start_eval)
    R1_eval = quaternion_to_matrix(q_goal_eval)
    
    assert np.allclose(R0_eval, R0_ref, atol=1e-7), "t=0 에서의 보간 결과가 시작 자세와 일치하지 않습니다."
    assert np.allclose(R1_eval, R1_ref, atol=1e-7), "t=1 에서의 보간 결과가 목표 자세와 일치하지 않습니다."


# --- 여기부터는 추가 테스트 (권장) -------------------------------------------
#
def test_matrix_quaternion_roundtrip(rng):
    """무작위 회전 50개: R -> q -> R 이 원래 행렬로 돌아오는가."""
    for _ in range(50):
        axis = rng.normal(size=3)
        angle = rng.uniform(0.0, np.pi)
        R_orig = rodrigues(axis, angle)
        
        q = matrix_to_quaternion(R_orig)
        R_rec = quaternion_to_matrix(q)
        
        assert np.allclose(R_rec, R_orig, atol=1e-7)


def test_slerp_matches_scipy(q_pair):
    """scipy.spatial.transform.Slerp 와 회전행렬 기준으로 일치하는가."""
    q0, q1 = q_pair
    ts = np.linspace(0.0, 1.0, 21)
    
    # 직접 구현한 slerp 결과 (회전행렬 변환)
    R_mine = np.array([quaternion_to_matrix(slerp(q0, q1, t)) for t in ts])
    
    # SciPy Slerp 결과
    slerp_scipy = Slerp([0.0, 1.0], Rotation.from_quat([q0, q1]))
    R_scipy = slerp_scipy(ts).as_matrix()
    
    assert np.allclose(R_mine, R_scipy, atol=1e-7), "직접 구현한 SLERP가 SciPy Slerp 결과와 일치하지 않습니다."


def test_slerp_nearly_identical_poses(q_pair):
    """거의 같은 두 자세에서 NaN 이 나오지 않는가."""
    q0, _ = q_pair
    q_near = matrix_to_quaternion(quaternion_to_matrix(q0) @ rodrigues([0, 0, 1], 1e-9))
    
    q_interp = slerp(q0, q_near, 0.5)
    assert not np.isnan(q_interp).any()
    assert np.isclose(np.linalg.norm(q_interp), 1.0, atol=1e-7)


def test_lerp_norm_drops_below_one(q_pair):
    """정규화하지 않은 선형 보간(LERP)의 중간값(t=0.5)은 크기가 1 보다 작다."""
    q0, q1 = q_pair
    q_mid_lerp = lerp_quat(q0, q1, 0.5, normalize=False)
    
    norm = np.linalg.norm(q_mid_lerp)
    assert norm < 0.99, f"t=0.5에서 LERP 크기가 1보다 작아지지 않았습니다: norm={norm}"
