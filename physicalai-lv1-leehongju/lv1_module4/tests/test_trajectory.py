"""문제 4 — 궤적 보간 검증 (pytest). [학생 작성용 템플릿]

지시문이 요구하는 것: 궤적이 경유점을 정확히 지나는가. 여기에 5차 다항식 경계 조건을 더한다.

  1. 선형 보간이 경유점을 지나는가             -> test_linear_interp_hits_waypoints
  2. 큐빅 스플라인이 경유점을 지나는가         -> test_cubic_spline_hits_waypoints
  3. 5차 다항식의 양끝 속도·가속도가 0 인가    -> test_quintic_boundary_conditions

작성 요령
--------
- 경유점 시각 t_wp 를 그대로 평가 시각으로 넣으면 q_wp 가 나와야 한다 (allclose).
- 스칼라 (M,) 와 3차원 (M,3) 경유점 둘 다 검사하면 좋다 (parametrize 또는 fixture).
- `quintic_profile` 은 (q, qd, qdd) 를 돌려준다. 양끝에서 qd, qdd 가 0 이고
  q 가 q0, qf 인지 검사한다.

실행: 프로젝트 루트에서  pytest tests/test_trajectory.py -v
"""

import numpy as np
import pytest

from src.trajectory import cubic_spline_interp, finite_diff, linear_interp, quintic_profile

T_WP = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
Q_WP_1D = np.array([0.0, 0.8, 0.3, 1.2, 0.5, 0.9])
P_WP_3D = np.array([
    [0.20, -0.30, 0.60],
    [0.30, -0.15, 0.75],
    [0.42, 0.00, 0.80],
    [0.50, 0.15, 0.70],
    [0.55, 0.25, 0.55],
    [0.60, 0.30, 0.45],
])


@pytest.fixture(params=["1d", "3d"])
def waypoints(request):
    return (T_WP, Q_WP_1D) if request.param == "1d" else (T_WP, P_WP_3D)


# --- 1. 선형 보간이 경유점을 지나는가 -----------------------------------------

def test_linear_interp_hits_waypoints(waypoints):
    t_wp, q_wp = waypoints
    q_eval = linear_interp(t_wp, q_wp, t_wp)
    
    assert q_eval.shape == q_wp.shape, f"출력 shape ({q_eval.shape})가 원본 ({q_wp.shape})과 다릅니다."
    assert np.allclose(q_eval, q_wp, atol=1e-7), "선형 보간 결과가 경유점을 정확히 통과하지 않습니다."


# --- 2. 큐빅 스플라인이 경유점을 지나는가 -------------------------------------

def test_cubic_spline_hits_waypoints(waypoints):
    t_wp, q_wp = waypoints
    q_eval = cubic_spline_interp(t_wp, q_wp, t_wp)
    
    assert q_eval.shape == q_wp.shape, f"출력 shape ({q_eval.shape})가 원본 ({q_wp.shape})과 다릅니다."
    assert np.allclose(q_eval, q_wp, atol=1e-7), "큐빅 스플라인 보간 결과가 경유점을 정확히 통과하지 않습니다."


# --- 3. 5차 다항식 경계 조건 ---------------------------------------------------

def test_quintic_boundary_conditions():
    t0, tf = 0.0, 2.0
    q0, qf = 0.0, 1.0
    t = np.linspace(t0, tf, 201)
    
    q, qd, qdd = quintic_profile(t, t0, tf, q0, qf)
    
    assert np.isclose(q[0], q0, atol=1e-7), f"시작 위치 q(0)가 {q0}와 다릅니다: {q[0]}"
    assert np.isclose(q[-1], qf, atol=1e-7), f"끝 위치 q(tf)가 {qf}와 다릅니다: {q[-1]}"
    assert np.isclose(qd[0], 0.0, atol=1e-7), f"시작 속도가 0이 아닙니다: {qd[0]}"
    assert np.isclose(qd[-1], 0.0, atol=1e-7), f"끝 속도가 0이 아닙니다: {qd[-1]}"
    assert np.isclose(qdd[0], 0.0, atol=1e-7), f"시작 가속도가 0이 아닙니다: {qdd[0]}"
    assert np.isclose(qdd[-1], 0.0, atol=1e-7), f"끝 가속도가 0이 아닙니다: {qdd[-1]}"


# --- 여기부터는 추가 테스트 (권장) -------------------------------------------

def test_spline_velocity_is_continuous():
    """finite_diff 로 구한 스플라인 속도에는 큰 점프가 없다 (선형 보간과 비교)."""
    t_dense = np.linspace(T_WP[0], T_WP[-1], 501)
    q_lin = linear_interp(T_WP, Q_WP_1D, t_dense)
    q_spl = cubic_spline_interp(T_WP, Q_WP_1D, t_dense)
    
    v_lin = finite_diff(q_lin, t_dense)
    v_spl = finite_diff(q_spl, t_dense)
    
    jump_lin = np.max(np.abs(np.diff(v_lin)))
    jump_spl = np.max(np.abs(np.diff(v_spl)))
    
    assert jump_spl < jump_lin, "스플라인의 속도 점프가 선형 보간보다 크거나 같습니다."


def test_quintic_matches_finite_difference():
    """해석적 qd 가 finite_diff(q, t) 와 일치한다."""
    t = np.linspace(0.0, 2.0, 201)
    q, qd, qdd = quintic_profile(t, 0.0, 2.0, 0.0, 1.0)
    
    qd_num = finite_diff(q, t)
    qdd_num = finite_diff(qd, t)
    
    assert np.allclose(qd, qd_num, atol=1e-2), "해석적 속도가 수치 미분 결과와 일치하지 않습니다."
    assert np.allclose(qdd, qdd_num, atol=1e-1), "해석적 가속도가 수치 미분 결과와 일치하지 않습니다."


def test_quintic_is_monotonic_for_zero_boundary():
    """경계 속도·가속도가 0 인 기본형은 q0 -> qf 로 단조 증가한다."""
    t = np.linspace(0.0, 2.0, 201)
    q, _, _ = quintic_profile(t, 0.0, 2.0, 0.0, 1.0)
    
    assert np.all(np.diff(q) >= -1e-12), "5차 다항식 프로파일이 단조 증가하지 않습니다."
