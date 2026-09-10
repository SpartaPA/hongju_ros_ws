"""문제 5 — 점군 자세 추정: PCA · Kabsch · 최소제곱 평면 피팅. (학생 작성용 템플릿)

- `pca_axes`        : 공분산 고유분해로 물체의 주축 3개를 뽑는다
- `kabsch`          : 대응이 알려진 두 점군 사이의 최적 회전·병진을 SVD 로 구한다
- `fit_plane_lstsq` : 최소제곱으로 평면을 피팅하고 점별 잔차를 돌려준다
- `remove_outliers` : 잔차가 큰 점을 걸러낸다

`rotation_angle_deg` 는 제공 코드다 (두 회전행렬 사이 각도).
"""

from __future__ import annotations

import numpy as np

__all__ = ["pca_axes", "kabsch", "fit_plane_lstsq", "remove_outliers", "rotation_angle_deg"]


def rotation_angle_deg(R_a, R_b) -> float:
    """두 회전행렬 사이의 각도 [deg] — R_a^T R_b 의 회전각. (제공 코드)"""
    R_rel = np.asarray(R_a, dtype=float).T @ np.asarray(R_b, dtype=float)
    cos_theta = np.clip((np.trace(R_rel) - 1.0) / 2.0, -1.0, 1.0)
    return float(np.rad2deg(np.arccos(cos_theta)))


def pca_axes(P):
    """점군 (N,3) 의 주축을 고유분해로 뽑는다.

    1. centroid = P 의 평균, X = P - centroid
    2. C = X^T X / (N - 1)   (3x3 공분산)
    3. C 를 고유분해 (`np.linalg.eigh` — 대칭행렬 전용, 실수 고유값)
    4. 고유값 **내림차순**으로 정렬해 axes 의 열 0,1,2 가 각각 긴 축 -> 짧은 축이 되게 한다
    5. det(axes) = +1 이 되도록 (오른손 좌표계) 필요하면 마지막 열의 부호를 뒤집는다

    Returns
    -------
    axes : (3,3) 열이 주축 (단위벡터, 서로 직교, det = +1) — 회전행렬로 그대로 쓸 수 있다
    eigvals : (3,) 내림차순 고유값 (각 축 방향 분산)
    centroid : (3,) 점군 중심
    """
    P = np.asarray(P, dtype=float)
    N = P.shape[0]

    # 1. 중심 및 분산 중심화
    centroid = np.mean(P, axis=0)
    X = P - centroid

    # 2. 공분산 행렬 C (3x3)
    C = (X.T @ X) / (N - 1)

    # 3. 고유분해 (대칭행렬 전용 eigh -> 오름차순 반환)
    eigvals, axes = np.linalg.eigh(C)

    # 4. 내림차순 정렬 (큰 고유값/주축 -> 작은 고유값/주축)
    idx = np.argsort(eigvals)[::-1]
    eigvals = eigvals[idx]
    axes = axes[:, idx]

    # 5. 오른손 좌표계 (det(axes) = +1) 보정
    if np.linalg.det(axes) < 0:
        axes[:, 2] = -axes[:, 2]

    return axes, eigvals, centroid


def kabsch(P, Q):
    """대응이 알려진 두 점군 P, Q (N,3) 에 대해 Q ~ P @ R.T + t 를 만족하는 (R, t) 를 구한다.

    1. 두 점군의 중심 cP, cQ 를 빼서 X = P - cP, Y = Q - cQ
    2. H = X^T Y  (3x3 교차 공분산)
    3. U, S, Vt = svd(H)
    4. d = sign(det(V U^T)) — 반사가 나오면 (-1) 보정: D = diag(1, 1, d)
    5. R = V D U^T,  t = cQ - R cP

    Returns
    -------
    R : (3,3) 회전행렬 (det = +1)
    t : (3,) 병진
    """
    P = np.asarray(P, dtype=float)
    Q = np.asarray(Q, dtype=float)

    # 1. 중심 계산 및 이동
    cP = np.mean(P, axis=0)
    cQ = np.mean(Q, axis=0)

    X = P - cP
    Y = Q - cQ

    # 2. 교차 공분산 행렬 H
    H = X.T @ Y

    # 3. SVD 분해
    U, S, Vt = np.linalg.svd(H)

    # 4. 오른손 좌표계 보정 (반사 방지)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    if d == 0:
        d = 1.0
    D = np.diag([1.0, 1.0, d])

    # 5. 최적 회전 R 및 병진 t 계산
    R = Vt.T @ D @ U.T
    t = cQ - R @ cP

    return R, t


def fit_plane_lstsq(P):
    """점군 (N,3) 에 평면 n . p + d = 0 을 최소제곱으로 피팅한다.

    권장 방법 (정규방정식): z = a x + b y + c 로 두고
        A = [x, y, 1],  b = z,   (A^T A) [a, b, c]^T = A^T b
    를 풀면 평면 a x + b y - z + c = 0 이므로 법선 n = (a, b, -1) 을 정규화한다.
    (평면이 z축과 나란하면 이 모델은 못 쓴다 — 그런 경우 SVD 로 최소 분산 방향을 쓴다.)

    Returns
    -------
    normal : (3,) 단위 법선
    d : float — 평면 상수 (n . p + d = 0)
    residuals : (N,) 각 점의 부호 있는 평면까지의 거리 n . p + d
    """
    P = np.asarray(P, dtype=float)

    # z = a*x + b*y + c 모델링 (A^T A x = A^T b)
    A = np.column_stack([P[:, 0], P[:, 1], np.ones(len(P))])
    b = P[:, 2]

    try:
        # 최소제곱법 피팅
        param, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        a, b_param, c = param

        # 평면 방정식을 a*x + b*y - z + c = 0 으로 정렬
        raw_n = np.array([a, b_param, -1.0])
        norm_n = np.linalg.norm(raw_n)

        normal = raw_n / norm_n
        d = c / norm_n

    except np.linalg.LinAlgError:
        # 수직 평면 등 Lstsq 실패 시 SVD로 최소 분산 방향 피팅 (Fallback)
        centroid = np.mean(P, axis=0)
        _, _, Vt = np.linalg.svd(P - centroid)
        normal = Vt[2, :]  # 가장 적은 분산 방향이 법선
        d = -float(normal @ centroid)

    # 부호 있는 평면 수직 거리 계산 (residuals)
    residuals = P @ normal + d

    return normal, float(d), residuals


def remove_outliers(P, residuals, k: float = 3.0):
    """잔차가 큰 점을 제거한다.

    기준: |residual| < k * sigma. sigma 는 이상치에 강한 추정치를 권장한다
        sigma = 1.4826 * median(|residual - median(residual)|)      (MAD)
    (단순 std 를 쓰면 이상치가 sigma 자체를 키워 걸러지지 않을 수 있다.)

    Returns
    -------
    P_clean : (M,3) 남은 점
    mask : (N,) bool — True 가 남긴 점. P 와 대응 점군에 같은 mask 를 적용해야 Kabsch 대응이 유지된다
    """
    P = np.asarray(P, dtype=float)
    residuals = np.asarray(residuals, dtype=float)

    # MAD(Median Absolute Deviation) 기반 Robust Sigma 추정
    med = np.median(residuals)
    mad = np.median(np.abs(residuals - med))
    sigma = 1.4826 * mad

    # sigma가 0에 가깝다면 부동소수점 예외 방지를 위해 std로 Fallback
    if sigma < 1e-12:
        sigma = np.std(residuals)

    # Threshold 기반 Mask 생성
    mask = np.abs(residuals - med) < k * sigma
    P_clean = P[mask]

    return P_clean, mask
