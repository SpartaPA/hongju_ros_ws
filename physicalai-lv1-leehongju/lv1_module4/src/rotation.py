"""문제 2·3 — 회전 행렬 모듈. (학생 작성용 템플릿)

축별 회전 행렬, 로드리게스 공식(임의 축 회전), Gram-Schmidt 재직교화,
회전행렬 판정과 고유값 분해 기반 축·각 복원을 직접 구현한다.

문제 1 에서 만든 `src/vectors.py` 를 그대로 재사용한다.
"""

from __future__ import annotations

import numpy as np

from .vectors import det, normalize, skew

__all__ = [
    "rot_x",
    "rot_y",
    "rot_z",
    "rodrigues",
    "gram_schmidt",
    "orthogonality_error",
    "is_rotation",
    "axis_angle_from_matrix",
    "quaternion_from_axis_angle",
]


# ------------------------------------------------------------ 축별 회전 행렬

def rot_x(theta: float) -> np.ndarray:
    """x축 기준 회전 행렬 (theta 는 **라디안**). x 성분은 보존된다."""
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([
        [1.0, 0.0, 0.0],
        [0.0,   c,  -s],
        [0.0,   s,   c]
    ], dtype=float)


def rot_y(theta: float) -> np.ndarray:
    """y축 기준 회전 행렬 (theta 는 라디안). y 성분은 보존된다.

    부호 배치가 x·z 와 반대로 보이는 이유는 노트북 2-1 에서 설명한다.
    """
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([
        [  c, 0.0,   s],
        [0.0, 1.0, 0.0],
        [ -s, 0.0,   c]
    ], dtype=float)


def rot_z(theta: float) -> np.ndarray:
    """z축 기준 회전 행렬 (theta 는 라디안). z 성분은 보존된다."""
    c = np.cos(theta)
    s = np.sin(theta)
    return np.array([
        [   c,  -s, 0.0],
        [   s,   c, 0.0],
        [ 0.0, 0.0, 1.0]
    ], dtype=float)


def rodrigues(axis, theta: float) -> np.ndarray:
    """로드리게스 공식으로 임의 축 회전 행렬을 만든다.

        R = I + sin(theta) * K + (1 - cos(theta)) * K @ K,   K = [k]_x

    - 축은 함수 안에서 단위벡터로 정규화한다
      (정규화되지 않은 축을 넣어도 같은 결과가 나와야 한다).
    - 문제 1 의 `skew` 를 반드시 사용한다.
    """
    k = normalize(axis)
    K = skew(k)
    I = np.eye(3, dtype=float)
    return I + np.sin(theta) * K + (1.0 - np.cos(theta)) * (K @ K)


# ------------------------------------------------------------- 재직교화 관련

def gram_schmidt(A) -> np.ndarray:
    """**열벡터**에 대해 Gram-Schmidt 직교정규화를 수행한다.

        q1 = a1 / |a1|
        vj = aj - sum_{i<j} (qi · aj) qi
        qj = vj / |vj|

    각 열에서 앞선 열 방향 성분(정사영)을 빼고 정규화하는 것이며,
    문제 1 의 project / reject 와 같은 연산의 반복이다.

    수치적으로는 성분을 빼자마자 갱신하는 modified Gram-Schmidt 가 더 안정적이다.
    앞선 열들에 종속인 열이 있으면 ValueError.
    """
    A_mat = np.asarray(A, dtype=float).copy()
    if A_mat.ndim != 2:
        raise ValueError("2차원 행렬이 필요합니다.")

    m, n = A_mat.shape
    Q = np.zeros((m, n), dtype=float)

    for j in range(n):
        v = A_mat[:, j].copy()
        for i in range(j):
            q_i = Q[:, i]
            v -= np.sum(q_i * v) * q_i

        v_norm = np.sqrt(np.sum(v**2))
        if v_norm < 1e-12:
            raise ValueError(f"{j}번째 열이 앞선 열들에 선형 종속이므로 직교정규화할 수 없습니다.")

        Q[:, j] = v / v_norm

    return Q


def orthogonality_error(R) -> float:
    """직교성 이탈 지표: || R^T R - I ||_F  (프로베니우스 노름).

    완전한 직교행렬이면 0 이고, 클수록 직교성이 무너진 것이다.
    """
    R_mat = np.asarray(R, dtype=float)
    m, n = R_mat.shape
    I = np.eye(n, dtype=float)
    
    # M = R^T R - I
    diff = R_mat.T @ R_mat - I
    
    # Frobenius norm: 모든 원소 제곱의 합의 제곱근
    return float(np.sqrt(np.sum(diff ** 2)))


def is_rotation(R, atol: float = 1e-8) -> bool:
    """회전행렬 판정: 직교(R^T R = I) **그리고** det(R) = +1 이면 True.

    det = -1 이면 직교이긴 하지만 반사가 섞여 있어 회전이 아니다.
    3x3 이 아니면 False.
    """
    R_mat = np.asarray(R, dtype=float)
    if R_mat.shape != (3, 3):
        return False

    if orthogonality_error(R_mat) > atol:
        return False

    det_val = det(R_mat)
    return bool(np.isclose(det_val, 1.0, atol=atol))


# --------------------------------------------------- 회전축·회전각·쿼터니언

def axis_angle_from_matrix(R, atol: float = 1e-8):
    """고유값 분해로 회전축을, 대각합으로 회전각을 복원한다.

    - 회전축은 고유값 1 에 대응하는 실수 고유벡터다 (R k = k).
      -> 여기서는 `np.linalg.eig` 를 써도 된다 (검산이 아니라 축 복원이 목적).
    - 회전각은 trace(R) = 1 + 2 cos(theta) 에서 구한다.
    - arccos 의 치역이 [0, pi] 라 '어느 쪽으로 도는지'는 알 수 없고,
      고유벡터도 부호가 정해지지 않는다. 반대칭 성분
      R - R^T = 2 sin(theta) [k]_x 를 이용해 부호를 맞춘다.
    - theta = 0 (회전 없음) 과 theta = pi (sin = 0) 는 따로 처리해야 한다.
      두 경우에 어떤 규약을 쓸지 정하고 주석으로 남긴다.

    Returns
    -------
    axis : 단위 회전축 (3,)
    angle : 회전각 [rad], 0 <= angle <= pi
    """
    R_mat = np.asarray(R, dtype=float)
    if not is_rotation(R_mat, atol=atol):
        raise ValueError("입력 행렬이 유효한 3x3 회전 행렬이 아닙니다.")

    trace_val = float(np.trace(R_mat))
    cos_theta = (trace_val - 1.0) / 2.0
    cos_theta = float(np.clip(cos_theta, -1.0, 1.0))
    angle = float(np.arccos(cos_theta))

    if np.isclose(angle, 0.0, atol=atol):
        return np.array([1.0, 0.0, 0.0], dtype=float), 0.0

    # 회전축 복원을 위해 np.linalg.eig 허용
    eigvals, eigvecs = np.linalg.eig(R_mat)
    idx = int(np.argmin(np.abs(eigvals - 1.0)))
    axis = np.real(eigvecs[:, idx])
    axis = normalize(axis)

    if np.isclose(angle, np.pi, atol=atol):
        return axis, float(np.pi)

    skew_sym = (R_mat - R_mat.T) / (2.0 * np.sin(angle))
    k_extracted = np.array([skew_sym[2, 1], skew_sym[0, 2], skew_sym[1, 0]], dtype=float)

    if np.sum(axis * k_extracted) < 0:
        axis = -axis

    return axis, angle


def quaternion_from_axis_angle(axis, angle: float) -> np.ndarray:
    """축-각에서 단위 쿼터니언을 만든다.

        q = (k * sin(theta/2), cos(theta/2))

    반환 순서는 SciPy `Rotation.as_quat()` 와 같은 **(x, y, z, w)** 로 맞춘다
    (그래야 문제 6-5 에서 바로 비교할 수 있다).
    """
    k = normalize(axis)
    half_angle = angle / 2.0

    xyz = k * np.sin(half_angle)
    w = np.cos(half_angle)

    return np.array([xyz[0], xyz[1], xyz[2], w], dtype=float)
