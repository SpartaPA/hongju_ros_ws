"""문제 1 — 벡터 연산 모듈. (학생 작성용 템플릿)

내적 · 사이각 · 정규화 · 정사영 · 반대칭행렬(외적) · 평면 법선과
가우스 소거 기반의 rank / 행렬식 / 역행렬을 **직접** 구현한다.

규칙
----
- `np.linalg` 는 노트북에서 **검산용으로만** 쓰고, 이 모듈 안에서는 쓰지 않는다.
  (`inverse_gauss_jordan` 이 던지는 `np.linalg.LinAlgError` 예외 타입만 예외)
- 각 함수의 docstring 에 적힌 계약(입력/출력/예외)을 그대로 지킨다.
  노트북의 검증 셀과 `tests/` 가 이 계약을 기준으로 채점된다.
- 구현을 마치면 `raise NotImplementedError(...)` 줄을 지운다.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "as_vector",
    "dot",
    "norm",
    "angle_between",
    "normalize",
    "project",
    "reject",
    "skew",
    "cross",
    "plane_normal",
    "row_echelon",
    "rank",
    "det",
    "gauss_eliminate",
    "inverse_gauss_jordan",
]


# ---------------------------------------------------------------- 기본 연산

def as_vector(v) -> np.ndarray:
    """입력(리스트/튜플/배열)을 1차원 float 배열로 변환한다.

    1차원이 아니면 ValueError 를 던진다.

    [구현 예시] 아래 세 줄이 이 파일에서 기대하는 코드 스타일이다.
    나머지 함수도 이런 식으로 채워 넣으면 된다.
    """
    arr = np.asarray(v, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"1차원 벡터가 필요합니다. 받은 shape={arr.shape}")
    return arr


def dot(a, b) -> float:
    """내적. sum(a_i * b_i) 를 직접 계산한다 (`np.dot` 사용 금지).

    두 벡터의 차원이 다르면 ValueError.
    """
    a_vec = as_vector(a)
    b_vec = as_vector(b)
    if a_vec.shape != b_vec.shape:
        raise ValueError(f"두 벡터의 차원이 다릅니다: {a_vec.shape} != {b_vec.shape}")
    
    return float(np.sum(a_vec * b_vec))


def norm(v) -> float:
    """유클리드 노름. sqrt(v·v) — 위에서 만든 dot 을 재사용한다."""
    v_vec = as_vector(v)
    return float(np.sqrt(dot(v_vec, v_vec)))


def angle_between(a, b, degrees: bool = True) -> float:
    """두 벡터 사이각. degrees=True 면 도(°), False 면 라디안.

    cos(theta) = (a·b) / (|a||b|)

    주의 1. 영벡터가 들어오면 사이각이 정의되지 않는다 -> ValueError.
    주의 2. 부동소수점 오차로 |cos| 가 1 을 아주 조금 넘으면 arccos 가 nan 을 낸다.
            [-1, 1] 로 clip 해야 무작위 입력에서도 안전하다.
    """
    a_vec = as_vector(a)
    b_vec = as_vector(b)
    
    norm_a = norm(a_vec)
    norm_b = norm(b_vec)
    
    if norm_a == 0 or norm_b == 0:
        raise ValueError("영벡터가 포함되어 사이각을 정의할 수 없습니다.")
    
    cos_theta = dot(a_vec, b_vec) / (norm_a * norm_b)
    # 부동소수점 오차로 인한 [-1, 1] 범위 이탈 방지
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    
    rad = np.arccos(cos_theta)
    if degrees:
        return float(np.degrees(rad))
    return float(rad)


def normalize(v, eps: float = 1e-12) -> np.ndarray:
    """단위벡터로 정규화한다. v / |v|

    영벡터를 어떻게 처리할지는 **문제 1-2 에서 직접 정한다.**
    노트북 1-2 에서 (1) 아무 처리 없이 나눴을 때 무슨 일이 나는지 관찰하고,
    (2) 선택한 처리 방식과 근거를 마크다운에 적은 뒤, 그 방식대로 여기에 구현한다.
    선택에 따라 노트북/테스트의 검증 코드도 그 방식에 맞춰 작성한다.
    """
    v_vec = as_vector(v)
    v_norm = norm(v_vec)
    
    if v_norm < eps:
        raise ValueError(f"영벡터(또는 크기가 {eps} 미만인 벡터)는 정규화할 수 없습니다.")
        
    return v_vec / v_norm


def project(a, b) -> np.ndarray:
    """a 를 b 방향으로 정사영한 성분.

        proj_b(a) = (a·b / b·b) * b

    분모가 |b|^2 이므로 b 를 미리 정규화할 필요는 없다.
    b 가 영벡터면 ValueError.
    """
    a_vec = as_vector(a)
    b_vec = as_vector(b)
    
    b_dot_b = dot(b_vec, b_vec)
    if b_dot_b == 0:
        raise ValueError("영벡터 방향으로는 정사영할 수 없습니다.")
        
    return (dot(a_vec, b_vec) / b_dot_b) * b_vec


def reject(a, b) -> np.ndarray:
    """a 에서 b 방향 성분을 뺀 나머지(수직 성분). a = project + reject 가 성립해야 한다."""
    a_vec = as_vector(a)
    return a_vec - project(a_vec, b)


def skew(a) -> np.ndarray:
    """3차원 벡터 a 에 대응하는 반대칭행렬 [a]_x 를 만든다.

        [a]_x = [[  0, -a3,  a2],
                 [ a3,   0, -a1],
                 [-a2,  a1,   0]]

    만족해야 하는 성질: [a]_x @ b == a x b,  [a]_x.T == -[a]_x
    3차원이 아니면 ValueError.
    """
    a_vec = as_vector(a)
    if a_vec.shape[0] != 3:
        raise ValueError(f"3차원 벡터가 필요합니다. 받은 차원={a_vec.shape[0]}")
        
    a1, a2, a3 = a_vec
    return np.array([
        [0.0, -a3, a2],
        [a3, 0.0, -a1],
        [-a2, a1, 0.0]
    ], dtype=float)


def cross(a, b) -> np.ndarray:
    """외적을 **반대칭행렬 곱으로** 계산한다 (`np.cross` 사용 금지)."""
    a_vec = as_vector(a)
    b_vec = as_vector(b)
    if a_vec.shape[0] != 3 or b_vec.shape[0] != 3:
        raise ValueError("외적은 3차원 벡터에 대해서만 정의됩니다.")
        
    return skew(a_vec) @ b_vec


def plane_normal(P1, P2, P3) -> np.ndarray:
    """세 점이 이루는 평면의 **단위** 법선 벡터.

    두 모서리 벡터(P2-P1, P3-P1)의 외적이 평면에 수직이다.
    세 점이 일직선이면 외적이 영벡터가 되어 평면이 하나로 정해지지 않는다 -> ValueError.
    """
    p1, p2, p3 = as_vector(P1), as_vector(P2), as_vector(P3)
    
    v1 = p2 - p1
    v2 = p3 - p1
    
    n = cross(v1, v2)
    
    try:
        return normalize(n)
    except ValueError:
        raise ValueError("세 점이 일직선상에 있거나 중복되어 평면의 법선 벡터를 정할 수 없습니다.")


# ------------------------------------------------- 가우스 소거 기반 선형대수

def row_echelon(A, pivoting: bool = True):
    """행 사다리꼴(row echelon form) 로 만든다.

    Parameters
    ----------
    pivoting : True 면 부분 피벗팅(각 열에서 절댓값이 가장 큰 행을 피벗으로 올림)

    Returns
    -------
    U : (m, n) 상삼각 형태 행렬
    pivot_cols : 피벗이 선 열 인덱스 리스트
    n_swaps : 행 교환 횟수 (행렬식 부호 계산에 필요)

    힌트: 0 인지 판정할 때는 `== 0` 대신 허용오차(tol)를 쓴다.
          예) tol = max(m, n) * np.finfo(float).eps * max(1.0, np.max(np.abs(U)))
    """
    U = np.asarray(A, dtype=float).copy()
    if U.ndim != 2:
        raise ValueError("2차원 행렬이 필요합니다.")
        
    m, n = U.shape
    pivot_cols = []
    n_swaps = 0
    
    # 허용 오차 (numerical zero 판정용)
    tol = max(m, n) * np.finfo(float).eps * max(1.0, float(np.max(np.abs(U))))
    
    r = 0  # 현재 처리 중인 행 인덱스
    for c in range(n):
        if r >= m:
            break
            
        # 1. 피벗 행 찾기
        if pivoting:
            pivot_row = r + np.argmax(np.abs(U[r:, c]))
        else:
            pivot_row = r
            
        # 피벗 값이 tol 이하이면 해당 열은 피벗이 없는 열
        if np.abs(U[pivot_row, c]) <= tol:
            U[r:, c] = 0.0  # 부동소수점 미세 오차 제로화
            continue
            
        # 2. 행 교환 (pivoting)
        if pivot_row != r:
            U[[r, pivot_row]] = U[[pivot_row, r]]
            n_swaps += 1
            
        # 3. 소거 작업 (Pivot 아래 원소 제거)
        for i in range(r + 1, m):
            factor = U[i, c] / U[r, c]
            U[i, c:] -= factor * U[r, c:]
            U[i, c] = 0.0  # 수치적 오차 제거
            
        pivot_cols.append(c)
        r += 1

    return U, pivot_cols, n_swaps


def rank(A) -> int:
    """행 사다리꼴의 피벗 개수 = rank."""
    _, pivot_cols, _ = row_echelon(A, pivoting=True)
    return len(pivot_cols)


def det(A) -> float:
    """행렬식 = 행 사다리꼴 대각성분의 곱 x (-1)^(행 교환 횟수).

    피벗이 n 개보다 적으면(특이행렬) 0.0 을 돌려준다.
    정사각 행렬이 아니면 ValueError.
    """
    A_arr = np.asarray(A, dtype=float)
    if A_arr.ndim != 2 or A_arr.shape[0] != A_arr.shape[1]:
        raise ValueError("정사각 행렬만 행렬식을 구할 수 있습니다.")
        
    n = A_arr.shape[0]
    U, pivot_cols, n_swaps = row_echelon(A_arr, pivoting=True)
    
    # 피벗의 개수가 n개 미만이면 특이행렬(Singular Matrix)
    if len(pivot_cols) < n:
        return 0.0
        
    diagonal_prod = np.prod(np.diag(U))
    sign = (-1.0) ** n_swaps
    return float(sign * diagonal_prod)


def gauss_eliminate(A, b, pivoting: bool = True, verbose: bool = False):
    """가우스 소거법 + 후진대입으로 Ax = b 를 푼다.

    Parameters
    ----------
    pivoting : True 면 부분 피벗팅을 적용한다. False 면 피벗을 그대로 쓴다
               (문제 4-4 에서 두 경우의 오차를 비교하므로 **둘 다 동작해야 한다**).
    verbose  : True 면 각 소거 단계의 첨가행렬 [A|b] 를 출력한다
               (문제 4-1 이 요구하는 '단계별 출력').

    Returns
    -------
    x : 해 벡터
    steps : 단계별 첨가행렬 [A|b] 스냅샷 리스트 (초기 상태 포함)

    피벗이 0 이면 해가 유일하지 않다 -> ZeroDivisionError.
    """
    A_mat = np.asarray(A, dtype=float).copy()
    b_vec = as_vector(b).copy()
    
    m, n = A_mat.shape
    if m != n:
        raise ValueError("정사각 행렬만 지원합니다.")
    if b_vec.shape[0] != m:
        raise ValueError("A의 행 개수와 b의 크기가 일치하지 않습니다.")
        
    # 첨가행렬 [A|b] 구성
    Aug = np.hstack([A_mat, b_vec.reshape(-1, 1)])
    steps = [Aug.copy()]
    
    tol = max(m, n) * np.finfo(float).eps * max(1.0, float(np.max(np.abs(Aug))))
    
    # 전진 소거 (Forward Elimination)
    for k in range(n):
        if pivoting:
            pivot_row = k + np.argmax(np.abs(Aug[k:, k]))
            if pivot_row != k:
                Aug[[k, pivot_row]] = Aug[[pivot_row, k]]
                
        if np.abs(Aug[k, k]) <= tol:
            raise ZeroDivisionError(f"피벗 원소가 0({Aug[k, k]})에 가까워 해가 유일하지 않거나 존재하지 않습니다.")
            
        for i in range(k + 1, n):
            factor = Aug[i, k] / Aug[k, k]
            Aug[i, k:] -= factor * Aug[k, k:]
            Aug[i, k] = 0.0
            
        steps.append(Aug.copy())
        if verbose:
            print(f"--- Step {k+1} ---")
            print(Aug)

    # 후진 대입 (Back Substitution)
    x = np.zeros(n, dtype=float)
    for i in range(n - 1, -1, -1):
        s = np.dot(Aug[i, i + 1:n], x[i + 1:n])
        x[i] = (Aug[i, n] - s) / Aug[i, i]
        
    return x, steps


def inverse_gauss_jordan(A) -> np.ndarray:
    """가우스-조던 소거로 역행렬을 구한다. [A|I] -> [I|A^-1].

    정사각이 아니면 ValueError, 특이행렬이면 np.linalg.LinAlgError.
    (`np.linalg.inv` 를 부르지 말고 소거로 직접 구한다)
    """
    A_mat = np.asarray(A, dtype=float).copy()
    if A_mat.ndim != 2 or A_mat.shape[0] != A_mat.shape[1]:
        raise ValueError("역행렬은 정사각 행렬에 대해서만 정의됩니다.")
        
    n = A_mat.shape[0]
    I = np.eye(n, dtype=float)
    Aug = np.hstack([A_mat, I])
    
    tol = n * np.finfo(float).eps * max(1.0, float(np.max(np.abs(Aug))))
    
    for k in range(n):
        # 부분 피벗팅
        pivot_row = k + np.argmax(np.abs(Aug[k:, k]))
        if np.abs(Aug[pivot_row, k]) <= tol:
            raise np.linalg.LinAlgError("특이행렬(Singular matrix)이므로 역행렬이 존재하지 않습니다.")
            
        if pivot_row != k:
            Aug[[k, pivot_row]] = Aug[[pivot_row, k]]
            
        # 피벗 행을 1로 만들기
        Aug[k, :] /= Aug[k, k]
        
        # 현재 열의 다른 모든 행 원소를 0으로 만들기
        for i in range(n):
            if i != k:
                factor = Aug[i, k]
                Aug[i, :] -= factor * Aug[k, :]
                
    return Aug[:, n:].copy()
