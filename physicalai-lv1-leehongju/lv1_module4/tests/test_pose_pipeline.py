"""문제 2 — PosePipeline 검증 (pytest). [학생 작성용 템플릿]

지시문이 요구하는 "2개 이상" 을 아래 두 테스트로 채운다.

  1. camera_to_base 가 모듈 ③ 체인(행렬 곱)과 같은 결과를 주는가  -> test_camera_to_base_matches_chain
  2. base 로 갔다가 camera 로 되돌리면 원래 점군이 나오는가       -> test_roundtrip_restores_points

작성 요령
--------
- 비교는 `np.allclose` (기본 허용오차) 로 한다.
- 난수는 반드시 시드를 고정한다 (fixture `rng`).
- 관절 각도 0 에서 파이프라인이 default_chain 과 같은지, 각도를 바꾸면 결과가 달라지는지 등
  테스트를 더 붙이면 좋다 (아래 권장 예시).

실행: 프로젝트 루트에서  pytest tests/test_pose_pipeline.py -v
"""

import numpy as np
import pytest

from src.coordinate_chain import default_chain
from src.pose_pipeline import PosePipeline
from src.transform import make_T, transform_points
from src.rotation import rot_x, rot_y, rot_z


@pytest.fixture
def rng():
    """난수는 반드시 시드를 고정한다."""
    return np.random.default_rng(42)


@pytest.fixture
def pipeline():
    """모듈 ③ default_chain 과 같은 값으로 만든 파이프라인."""
    chain = default_chain()
    return PosePipeline(chain.get("base", "link"), chain.get("link", "camera"))


# --- 1. camera_to_base == 체인/행렬 곱 --------------------------------------

def test_camera_to_base_matches_chain(pipeline, rng):
    P_cam = rng.uniform(-1.0, 1.0, (100, 3))
    
    # PosePipeline 변환 결과
    P_base_pipe = pipeline.camera_to_base(P_cam)
    
    # CoordinateChain default_chain() 변환 결과
    chain = default_chain()
    P_base_chain = chain.transform("base", "camera", P_cam, w=1.0)
    
    # 합성 행렬 T_base_link @ T_link_camera 직접 곱 변환 결과
    T_composite = pipeline.T_base_link @ pipeline.T_link_camera
    P_base_manual = transform_points(T_composite, P_cam, w=1.0)
    
    assert np.allclose(P_base_pipe, P_base_chain)
    assert np.allclose(P_base_pipe, P_base_manual)


# --- 2. 왕복 검증 -------------------------------------------------------------

def test_roundtrip_restores_points(pipeline, rng):
    # (3,) 단일 점 검증
    p_single = rng.uniform(-1.0, 1.0, 3)
    p_single_base = pipeline.camera_to_base(p_single)
    p_single_restored = pipeline.base_to_camera(p_single_base)
    assert np.allclose(p_single, p_single_restored)
    
    # (N,3) 점군 검증
    P_cam = rng.uniform(-1.0, 1.0, (200, 3))
    P_base = pipeline.camera_to_base(P_cam)
    P_restored = pipeline.base_to_camera(P_base)
    assert np.allclose(P_cam, P_restored)


# --- 여기부터는 추가 테스트 (권장) -------------------------------------------
#
def test_joint_angle_zero_is_nominal(pipeline):
    """set_joint_angle(0) 이면 T_base_link 가 생성자에 전달한 기준 변환과 일치한다."""
    chain = default_chain()
    T_nominal = chain.get("base", "link")
    
    pipeline.set_joint_angle(0.0)
    assert np.allclose(pipeline.T_base_link, T_nominal)
    

def test_joint_angle_changes_result(pipeline, rng):
    """관절 각도를 바꾸면 동일한 카메라 점군 관측값이 base 에서 다른 위치로 변환된다."""
    P_cam = rng.uniform(-1.0, 1.0, (50, 3))
    
    pipeline.set_joint_angle(0.0)
    P_base_0 = pipeline.camera_to_base(P_cam)
    
    pipeline.set_joint_angle(np.deg2rad(30.0))
    P_base_30 = pipeline.camera_to_base(P_cam)
    
    assert not np.allclose(P_base_0, P_base_30)


def test_distance_is_preserved(pipeline, rng):
    """강체 변환(Isometry)은 점들 사이의 유클리드 거리를 보존한다."""
    P_cam = rng.uniform(-1.0, 1.0, (10, 3))
    P_base = pipeline.camera_to_base(P_cam)
    
    # 임의의 두 점 (0번, 1번 점) 사이 거리 비교
    dist_cam = np.linalg.norm(P_cam[0] - P_cam[1])
    dist_base = np.linalg.norm(P_base[0] - P_base[1])
    
    assert np.isclose(dist_cam, dist_base)


def test_rejects_wrong_shape():
    """변환 행렬 shape 가 (4,4) 가 아니면 ValueError 예외를 발생시킨다."""
    invalid_T = np.eye(3)
    valid_T = np.eye(4)
    
    with pytest.raises(ValueError):
        PosePipeline(invalid_T, valid_T)
        
    with pytest.raises(ValueError):
        PosePipeline(valid_T, invalid_T)
