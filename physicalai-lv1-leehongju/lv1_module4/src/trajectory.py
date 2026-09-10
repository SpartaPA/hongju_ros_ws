"""문제 4 — 궤적 보간. (학생 작성용 템플릿)

경유점(waypoint)을 지나는 궤적을 선형 보간 / 큐빅 스플라인으로 만들고,
시작·끝에서 속도와 가속도가 0 이 되는 5차 다항식 프로파일을 구현한다.

입력 규약
--------
- t_wp : (M,) 경유점 시각, 오름차순
- q_wp : (M,) 스칼라 궤적 또는 (M, D) 다차원 궤적 (예: 3차원 위치는 D = 3)
- t    : (N,) 평가할 시각 (t_wp[0] <= t <= t_wp[-1])
- 반환 : q_wp 가 (M,) 이면 (N,), (M, D) 이면 (N, D)

큐빅 스플라인은 `scipy.interpolate.CubicSpline` 을 써도 된다 (axis=0).
"""

from __future__ import annotations
from scipy.interpolate import CubicSpline

import numpy as np

__all__ = ["linear_interp", "cubic_spline_interp", "quintic_profile", "finite_diff"]


def linear_interp(t_wp, q_wp, t) -> np.ndarray:
    """경유점 사이를 직선으로 잇는 보간. 각 차원마다 `np.interp` 를 쓰면 된다.

    위치는 이어지지만 경유점에서 속도가 불연속(꺾임)이다.
    """
    t_wp = np.asarray(t_wp, dtype=float)
    q_wp = np.asarray(q_wp, dtype=float)
    t = np.asarray(t, dtype=float)

    if q_wp.ndim == 1:
        return np.interp(t, t_wp, q_wp)

    # (M, D) 형태의 다차원 입력 처리
    num_pts, dim = q_wp.shape
    q_interp = np.zeros((len(t), dim), dtype=float)
    for d in range(dim):
        q_interp[:, d] = np.interp(t, t_wp, q_wp[:, d])

    return q_interp


def cubic_spline_interp(t_wp, q_wp, t, bc_type: str = "natural") -> np.ndarray:
    """경유점을 지나는 큐빅 스플라인 보간 (위치·속도·가속도가 모두 연속, C2).

    bc_type : 양끝 경계 조건. "natural" (양끝 가속도 0) 또는 "clamped" (양끝 속도 0).
    """
    t_wp = np.asarray(t_wp, dtype=float)
    q_wp = np.asarray(q_wp, dtype=float)
    t = np.asarray(t, dtype=float)

    spline = CubicSpline(t_wp, q_wp, axis=0, bc_type=bc_type)
    return spline(t)


def quintic_profile(t, t0: float, tf: float, q0, qf,
                    v0=0.0, vf=0.0, a0=0.0, af=0.0):
    """5차 다항식 궤적 q(t) 와 그 도함수 (q, qd, qdd) 를 돌려준다.

    경계 조건 6개 — q(t0)=q0, q(tf)=qf, qd(t0)=v0, qd(tf)=vf, qdd(t0)=a0, qdd(tf)=af —
    로 계수 6개 (c0 ~ c5) 를 정한다. 경계 속도·가속도가 모두 0 인 기본형은

        tau = (t - t0) / (tf - t0)
        s(tau) = 10 tau^3 - 15 tau^4 + 6 tau^5
        q(t) = q0 + (qf - q0) s(tau)

    로 닫힌 꼴이 있고, 일반형은 6x6 선형계를 풀면 된다. 어느 쪽으로 구현해도 된다.
    q0, qf 가 스칼라이면 (N,), (D,) 이면 (N, D) 를 돌려준다.

    Returns
    -------
    q, qd, qdd : 위치, 속도, 가속도 (해석적 미분. 유한차분이 아니다)
    """
    t = np.asarray(t, dtype=float)
    q0 = np.asarray(q0, dtype=float)
    qf = np.asarray(qf, dtype=float)
    v0 = np.asarray(v0, dtype=float)
    vf = np.asarray(vf, dtype=float)
    a0 = np.asarray(a0, dtype=float)
    af = np.asarray(af, dtype=float)

    T = float(tf - t0)
    if T <= 0:
        raise ValueError(f"tf ({tf}) 는 t0 ({t0}) 보다 커야 합니다.")

    # 일반형 6x6 선형계 구성을 위한 시간 행렬 A
    A = np.array([
        [1.0, 0.0, 0.0,     0.0,        0.0,         0.0],
        [0.0, 1.0, 0.0,     0.0,        0.0,         0.0],
        [0.0, 0.0, 2.0,     0.0,        0.0,         0.0],
        [1.0,   T, T**2,   T**3,       T**4,        T**5],
        [0.0, 1.0, 2*T,  3*T**2,     4*T**3,      5*T**4],
        [0.0, 0.0, 2.0,     6*T,    12*T**2,     20*T**3]
    ], dtype=float)

    # 경계 조건 벡터 b
    # q0 가 스칼라인지 다차원인지에 맞춰 차원 처리
    is_scalar = (q0.ndim == 0)
    q0_arr = np.atleast_1d(q0)
    qf_arr = np.atleast_1d(qf)
    v0_arr = np.atleast_1d(v0)
    vf_arr = np.atleast_1d(vf)
    a0_arr = np.atleast_1d(a0)
    af_arr = np.atleast_1d(af)

    D = len(q0_arr)
    
    # v0, vf, a0, af 가 스칼라인 경우 D 차원에 맞춰 브로드캐스팅
    v0_arr = np.broadcast_to(np.asarray(v0, dtype=float), (D,))
    vf_arr = np.broadcast_to(np.asarray(vf, dtype=float), (D,))
    a0_arr = np.broadcast_to(np.asarray(a0, dtype=float), (D,))
    af_arr = np.broadcast_to(np.asarray(af, dtype=float), (D,))
    
    # 경계 조건 벡터 b (6, D)
    b = np.vstack([q0_arr, v0_arr, a0_arr, qf_arr, vf_arr, af_arr])

    # 계수 c (6, D)
    c = np.linalg.solve(A, b)

    # tau = t - t0
    tau = (t - t0)

    # t 가 (N,) 이고 c 가 (6, D) 일 때 (N, D) 형태 평가
    tau = tau[:, np.newaxis]  # (N, 1)

    q   = c[0] + c[1]*tau + c[2]*(tau**2) + c[3]*(tau**3) + c[4]*(tau**4) + c[5]*(tau**5)
    qd  = c[1] + 2*c[2]*tau + 3*c[3]*(tau**2) + 4*c[4]*(tau**3) + 5*c[5]*(tau**4)
    qdd = 2*c[2] + 6*c[3]*tau + 12*c[4]*(tau**2) + 20*c[5]*(tau**3)

    if is_scalar:
        return q.squeeze(-1), qd.squeeze(-1), qdd.squeeze(-1)

    return q, qd, qdd


def finite_diff(y, t) -> np.ndarray:
    """시간축(axis 0)에 대한 수치 미분. `np.gradient(y, t, axis=0)` 를 쓰면 된다.

    y : (N,) 또는 (N, D),  t : (N,)
    속도 = finite_diff(q, t),  가속도 = finite_diff(속도, t)
    """
    y = np.asarray(y, dtype=float)
    t = np.asarray(t, dtype=float)
    return np.gradient(y, t, axis=0)
