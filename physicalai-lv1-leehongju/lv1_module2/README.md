# Lv.1 모듈 ② 과제 — turtlesim ROS 2 패키지 (문제 5~9 학생용 예제 코드)

과제 지시문 `과제2_turtlesim_ROS2패키지.md` 의 **선택과제 5~9** 를 풀 때 참고하는 **예제 코드 묶음**입니다.

> **이 폴더는 정답이 아닙니다.** 여기 있는 것은 "어떻게 짜는지" 를 보여 주는 예제이고,
> 채점 대상은 **여러분이 직접 만든 `turtle_py` 패키지와 `report.md`** 입니다.
> 예제를 그대로 복사해 제출하고 실행 출력을 `report.md` 에 남기지 않으면 **점수가 없습니다.**
> 문제마다 "학생이 직접 해야 할 것" 을 아래 표에 정리했으니 그 항목을 빠짐없이 채우세요.

---

## 0. 무엇이 제공되고, 무엇을 직접 해야 하는가

| 제공되는 것 | 직접 해야 하는 것 |
|---|---|
| `turtle_interfaces/` — 문제 6 인터페이스 정의 **완성본** (그대로 `ros2_ws/src/` 에 넣어 써도 됩니다) | `turtle_py/` 패키지 전체 (문제 3·5~9 의 노드), `turtle_cpp/` (문제 4) |
| `turtle_examples/` — 문제 5~9 예제 노드 + launch + YAML | 예제를 읽고 **자신의 `turtle_py` 에 맞게 옮겨 구현** (노드·토픽·파라미터 이름은 과제 규격 그대로) |
| 각 파일의 한국어 주석 (왜 그렇게 짜는지) | 실행 명령·터미널 출력·캡처를 `report.md` 에 문제별로 기록, 설계표 작성 |

예제 패키지 이름이 `turtle_py` 가 아니라 `turtle_examples` 인 이유: 여러분이 만드는 `turtle_py` 와
이름이 겹치면 `colcon build` 가 충돌합니다. 두 패키지를 나란히 두고 빌드할 수 있게 일부러 다른 이름을 썼습니다.

### 고정 규격 (바꾸면 채점에서 불이익)

| 항목 | 값 |
|---|---|
| 거리 토픽 | `/turtle_distance` · `std_msgs/msg/Float32` · **10 Hz** |
| 파라미터 | `publish_rate` (double, 10.0) · `warn_distance` (double, **2.5**) |
| 패키지 이름 | `turtle_py` (ament_python) · `turtle_cpp` (ament_cmake) · `turtle_interfaces` (ament_cmake) |
| 인터페이스 | `Waypoint.msg` · `WaypointList.msg` · `SetGain.srv` · `DrawPolygon.action` |
| 액션 / 경유점 토픽 | `/draw_polygon` · `/waypoints` (경유점 **4개 이상**) |
| 다각형 캡처 | **삼각형 · 오각형 · 팔각형** |
| YAML 실험 | `warn_distance` 를 2.5 → **0.8** 로 낮춰 경고 빈도 비교 |
| turtlesim 기본 이름 | `/turtle1/pose`, `/turtle1/cmd_vel`, `/turtle1/...` 그대로 사용 |

---

## 1. 폴더 구성

```
lv1_module2_student/
├── README.md                          ← 지금 이 파일
└── ros2_ws/src/
    ├── turtle_interfaces/             ← 문제 6 인터페이스 (완성본)
    │   ├── package.xml, CMakeLists.txt
    │   ├── msg/Waypoint.msg           float64 x, float64 y, float32 tolerance, string label
    │   ├── msg/WaypointList.msg       std_msgs/Header header, Waypoint[] waypoints
    │   ├── srv/SetGain.srv            kp ki kd --- success message
    │   └── action/DrawPolygon.action  sides side_length --- total_distance --- completed_sides progress
    └── turtle_examples/               ← 예제 노드 (ament_python)
        ├── package.xml, setup.py, setup.cfg, resource/turtle_examples
        ├── turtle_examples/
        │   ├── ex03_distance_publisher.py     launch 데모용 최소 발행자 (문제 3 정답 아님)
        │   ├── ex03_distance_subscriber.py    launch 데모용 최소 경고 구독자
        │   ├── ex05_builtin_service_client.py 내장 서비스 4개 비동기 호출
        │   ├── ex05_toggle_servers.py         SetBool / Trigger 자체 서비스 서버 + 데드락 설명
        │   ├── ex05_rotate_absolute_client.py RotateAbsolute 액션 클라이언트 (피드백·취소)
        │   ├── ex06_polygon_action_server.py  DrawPolygon 액션 서버 (피드백·즉시 취소)
        │   ├── ex06_waypoint_publisher.py     /waypoints 발행 (TRANSIENT_LOCAL)
        │   ├── ex07_qos_sensor_publisher.py   Best-Effort 발행자 (비호환 재현)
        │   └── ex07_qos_subscriber.py         QoS 를 파라미터로 조립하는 구독자
        ├── launch/turtle_system.launch.py     문제 9 launch (네임스페이스 설명 포함)
        └── config/params.yaml                 문제 9 파라미터 파일
```

---

## 2. 빌드와 실행 준비

사전 조건: Ubuntu 22.04 + ROS 2 Humble, `sudo apt install ros-humble-turtlesim`.
turtlesim 은 GUI 창이 필요합니다 (WSL2 는 WSLg, 도커는 X11 포워딩).

```bash
# 이 폴더의 ros2_ws 를 그대로 쓰거나, src/ 안의 두 패키지를 자신의 ros2_ws/src/ 로 복사하세요.
cd ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

- `--symlink-install` : Python 소스·launch·YAML 을 복사하지 않고 링크하므로, 수정 후 재빌드 없이 반영됩니다
  (단 `setup.py` 를 고쳤을 때는 재빌드 필요).
- 빌드 로그에서 `Starting >>> turtle_interfaces` 가 `turtle_examples` 보다 **먼저** 나오는지 확인하세요 (문제 8).
- 새 터미널을 열 때마다 `source install/setup.bash` 를 다시 해야 합니다. `source` 전에 `ros2 run turtle_examples ...` 를
  해 보면 `Package 'turtle_examples' not found` 가 납니다 — 문제 8 의 "source 전후 비교" 항목입니다.

빌드가 되었는지 확인:

```bash
ros2 pkg list | grep turtle_
ros2 interface show turtle_interfaces/msg/WaypointList
ros2 interface show turtle_interfaces/action/DrawPolygon
ros2 pkg executables turtle_examples
```

---

## 3. 예제 파일 → 문제 번호 → 학생이 추가로 해야 할 것

| 예제 파일 | 문제 | 예제가 보여 주는 것 | 학생이 `turtle_py` 에서 직접 해야 할 것 |
|---|---|---|---|
| `ex05_builtin_service_client.py` | 5 | `call_async` + `spin_until_future_complete` 로 내장 서비스 4개 순차 호출, `wait_for_service` | `ros2 service list` / `ros2 service type` 출력 기록, 4행 서비스 표(서비스/타입/요청값/결과), 요청·응답 로그 |
| `ex05_toggle_servers.py` | 5 | `SetBool`(enable_driving) · `Trigger`(save_home) 서버, false 면 `cmd_vel` 중단, 콜백 내 동기 대기 데드락 설명, 올바른 비동기 패턴(`go_home`) | **문제 3 노드에 서버를 통합** (별도 노드가 아니라 자신의 발행 노드에 추가), 데드락 이유를 executor 관점 3줄로 서술 |
| `ex05_rotate_absolute_client.py` | 5 | `RotateAbsolute` goal 전송, feedback(remaining) 로그, result, `--cancel-after` 로 취소 + 취소 시점 theta 기록 | 피드백이 줄어드는 로그, 취소 처리 로그와 **취소 시점 각도**, 통신 패턴 설계표 5행(기능/모델/근거) |
| `turtle_interfaces/` | 6 | `.msg/.srv/.action` 정의, `rosidl_generate_interfaces`, 분리 이유 주석 | `ros2 interface show` 출력 4종 기록, "별도 패키지로 분리하는 이유" 서술 (주석을 자기 말로) |
| `ex06_polygon_action_server.py` | 6 | `ReentrantCallbackGroup` + `MultiThreadedExecutor`, 변마다 피드백, 루프마다 취소 검사 → 즉시 정지, 결과 `total_distance` | `turtle_py` 에 액션 서버 구현, **삼각형·오각형·팔각형** 캡처 3장, 피드백 로그와 총 이동 거리, 취소 결과 |
| `ex06_waypoint_publisher.py` | 6·7 | `WaypointList` 4개 발행, Header 채우기, TRANSIENT_LOCAL/Reliable/depth 1 | `ros2 topic echo /waypoints` 의 중첩 필드 출력 기록, TRANSIENT_LOCAL 이 맞는 이유 서술 |
| `ex07_qos_sensor_publisher.py` | 7 | `qos_profile_sensor_data`(Best-Effort) 발행자, `reliability` 파라미터로 전환 | 비호환 재현 → `ros2 topic info -v` 양쪽 비교 출력 → 원인·수정 설정 기록 |
| `ex07_qos_subscriber.py` | 7 | reliability/durability/history_depth/callback_delay 파라미터로 QoS 조립, 비호환 규칙과 진단법 주석, 수신 통계 | Transient Local vs Volatile 비교, depth 1 + 지연에서의 누락 관찰, **토픽 5종 QoS 설계표** (`/turtle1/pose`, `/turtle1/cmd_vel`, `/waypoints`, `/turtle_distance`, `/diagnostics`) |
| `package.xml`, `setup.py` (turtle_examples) | 8 | `<depend>` 선언과 빌드 순서의 관계, `entry_points` 설명 주석, `data_files` 로 launch/config 설치 | 자신의 `turtle_py` 에 `turtle_interfaces`·`rclpy`·`geometry_msgs`·`turtlesim` 의존 선언, 빌드 순서 로그, source 전후 비교(`AMENT_PREFIX_PATH`, `PYTHONPATH`), `src/build/install/log` 역할 4줄 |
| `launch/turtle_system.launch.py`, `config/params.yaml` | 9 | 4개 노드 기동, YAML 파라미터 주입, `spawn_second:=true` 로 네임스페이스 `turtle2` 발행자, 절대 이름이 네임스페이스를 무시하는 이유 | launch·YAML 을 **`turtle_py` 안에** 넣고 `setup.py` 의 `data_files` 로 설치, `ros2 node list` 4개 확인, `ros2 param get` 값, YAML 2.5 → 0.8 전후 비교, 네임스페이스 적용 후 `ros2 topic list` |
| `ex03_distance_publisher.py`, `ex03_distance_subscriber.py` | (3) | launch 예제가 돌기 위한 **최소 구현**. 파라미터 콜백으로 타이머 재생성, 생명주기·Ctrl+C 처리 | 문제 3 은 이 파일이 답이 아닙니다. 규격대로 `turtle_py` 에 직접 작성 (정사각형 주행 노드 포함) |

---

## 4. 문제별 실행 방법

모든 터미널에서 먼저 `source install/setup.bash`. 터미널 1 은 항상 turtlesim:

```bash
ros2 run turtlesim turtlesim_node
```

### 문제 5 — Service / Action

```bash
# 호출 전 확인 (출력을 report.md 에)
ros2 service list
ros2 service type /turtle1/teleport_absolute
ros2 interface show turtlesim/srv/Spawn

# 내장 서비스 4개 순차 호출
ros2 run turtle_examples ex05_builtin_service_client

# 자체 서비스 서버
ros2 run turtle_examples ex05_toggle_servers
ros2 service call /enable_driving std_srvs/srv/SetBool "{data: true}"
ros2 service call /save_home std_srvs/srv/Trigger
ros2 service call /enable_driving std_srvs/srv/SetBool "{data: false}"
ros2 service call /go_home std_srvs/srv/Trigger

# 내장 액션: 피드백 → 결과
ros2 run turtle_examples ex05_rotate_absolute_client --theta 3.0
# 실행 1초 뒤 취소 요청 (취소 시점 theta 가 로그에 찍힘)
ros2 run turtle_examples ex05_rotate_absolute_client --theta 3.0 --cancel-after 1.0
```

### 문제 6 — 커스텀 인터페이스와 다각형 액션

```bash
ros2 interface show turtle_interfaces/msg/Waypoint
ros2 interface show turtle_interfaces/msg/WaypointList
ros2 interface show turtle_interfaces/srv/SetGain
ros2 interface show turtle_interfaces/action/DrawPolygon

# 액션 서버
ros2 run turtle_examples ex06_polygon_action_server
# 다른 터미널에서 goal 전송 (--feedback 으로 피드백 출력). 삼각형·오각형·팔각형 각각 캡처
ros2 action send_goal /draw_polygon turtle_interfaces/action/DrawPolygon "{sides: 3, side_length: 2.0}" --feedback
ros2 action send_goal /draw_polygon turtle_interfaces/action/DrawPolygon "{sides: 5, side_length: 1.5}" --feedback
ros2 action send_goal /draw_polygon turtle_interfaces/action/DrawPolygon "{sides: 8, side_length: 1.0}" --feedback
# 그리는 도중 send_goal 터미널에서 Ctrl+C → 취소 요청 → 거북이 즉시 정지 (서버 로그 기록)
# 궤적을 지우고 다시 그리려면: ros2 service call /clear std_srvs/srv/Empty
# 중앙으로 되돌리려면: ros2 service call /turtle1/teleport_absolute turtlesim/srv/TeleportAbsolute "{x: 5.5, y: 5.5, theta: 0.0}"

# 경유점 발행 + 중첩 필드 확인
ros2 run turtle_examples ex06_waypoint_publisher
ros2 topic echo /waypoints
```

### 문제 7 — QoS

```bash
# (1) 비호환 재현: Best-Effort 발행자 + Reliable 구독자  (ex03_distance_publisher 는 끄고!)
ros2 run turtle_examples ex07_qos_sensor_publisher
ros2 run turtle_examples ex07_qos_subscriber            # 기본 reliable → 아무것도 안 옴
ros2 topic info -v /turtle_distance                     # Publishers / Subscriptions 의 QoS 를 비교해 기록
# (2) 해결: 구독자를 Best-Effort 로, 또는 발행자를 Reliable 로
ros2 run turtle_examples ex07_qos_subscriber --ros-args -p reliability:=best_effort
ros2 run turtle_examples ex07_qos_sensor_publisher --ros-args -p reliability:=reliable

# (3) Transient Local vs Volatile — 발행자를 "먼저", 구독자를 "나중에"
ros2 run turtle_examples ex06_waypoint_publisher                                  # transient_local (기본)
ros2 run turtle_examples ex07_qos_subscriber --ros-args -p topic:=waypoints -p msg_type:=WaypointList -p durability:=transient_local
ros2 run turtle_examples ex06_waypoint_publisher --ros-args -p durability:=volatile   # 다시 같은 구독자 → 못 받음

# (4) History depth 1 + 콜백 지연 → 누락 관찰 (발행자는 10 Hz 로 두고)
ros2 run turtle_examples ex07_qos_subscriber --ros-args -p reliability:=best_effort -p history_depth:=1 -p callback_delay:=0.5
ros2 run turtle_examples ex07_qos_subscriber --ros-args -p reliability:=best_effort -p history_depth:=10 -p callback_delay:=0.5
```

### 문제 8 — colcon 워크스페이스

```bash
cd ros2_ws
colcon build --symlink-install 2>&1 | tee build.log     # "Starting >>> turtle_interfaces" 가 먼저인지 확인
colcon graph                                             # 의존 그래프 (순서 결정 근거)
ros2 run turtle_examples ex05_toggle_servers             # source 전 → 실패, source 후 → 성공. 둘 다 기록
echo $AMENT_PREFIX_PATH; echo $PYTHONPATH                # source 전후 비교
ros2 pkg executables turtle_examples                     # entry_points 에 등록된 노드 목록
```

### 문제 9 — launch 와 파라미터

```bash
# 예제 노드만으로 시스템 기동 (turtle_py 없이도 동작)
ros2 launch turtle_examples turtle_system.launch.py use_examples:=true
# 학생의 turtle_py 로 기동 (실행파일 turtle_distance_publisher / turtle_distance_subscriber / polygon_action_server)
ros2 launch turtle_examples turtle_system.launch.py
ros2 launch turtle_examples turtle_system.launch.py student_action_exec:=<내 액션서버 실행파일>

# 다른 터미널에서
ros2 node list                                                     # 4개 노드
ros2 param get /turtle_distance_publisher publish_rate
ros2 param get /turtle_distance_subscriber warn_distance
ros2 param set /turtle_distance_subscriber warn_distance 0.8        # 실행 중 변경 (double 이므로 0.8 처럼 소수점)
ros2 param set /turtle_distance_publisher publish_rate 5.0          # 타이머 재생성 로그 + ros2 topic hz 로 확인
ros2 topic hz /turtle_distance

# YAML 실험: config/params.yaml 의 warn_distance 2.5 → 0.8 로 편집 후, 재빌드 없이 launch 재실행 → 경고 빈도 비교

# 네임스페이스: turtle2 spawn + 두 번째 발행자
ros2 launch turtle_examples turtle_system.launch.py use_examples:=true spawn_second:=true
ros2 topic list                                                    # /turtle2/pose, /turtle2/turtle_distance 확인
ros2 node list                                                     # /turtle2/turtle_distance_publisher 추가
```

---

## 5. 자주 나는 오류

| 증상 | 원인 / 조치 |
|---|---|
| `Package 'turtle_examples' not found` | `source install/setup.bash` 를 안 함 (새 터미널마다 필요) |
| `ModuleNotFoundError: turtle_interfaces` | `turtle_interfaces` 가 빌드되지 않았거나 `package.xml` 에 `<depend>` 누락 → 빌드 순서 문제 |
| `ros2 param set ... publish_rate 5` 가 거부됨 | 타입 불일치. double 은 `5.0` 처럼 소수점 포함 |
| 구독자 수는 1인데 메시지가 안 옴 | QoS 비호환. `ros2 topic info -v` 로 Reliability/Durability 비교 |
| `ros2 topic echo /waypoints` 가 비어 있음 | 발행자가 이미 종료됨(TRANSIENT_LOCAL 은 발행자가 살아 있어야 함) 또는 `--qos-durability transient_local` 필요 |
| 다각형이 벽에 막혀 abort | `teleport_absolute` 로 중앙(5.5, 5.5)에 두고 `side_length` 를 줄이세요 |
| Ctrl+C 에서 `rcl_shutdown already called` | `rclpy.shutdown()` 을 `if rclpy.ok():` 로 가드하세요 (예제의 `main()` 참고) |

---

## 6. 제출 전 점검

- [ ] 모든 구현이 **`turtle_py`** (와 `turtle_interfaces`, `turtle_cpp`) 안에 있고 이름 규격을 지켰다
- [ ] launch 와 YAML 이 `turtle_py` 의 `setup.py` `data_files` 로 설치된다
- [ ] 문제 5~9 각각의 **실행 명령과 터미널 출력**이 `report.md` 에 그대로 붙어 있다
- [ ] 설계표 2개(문제 5 통신 패턴 5행, 문제 7 QoS 5행)를 근거와 함께 작성했다
- [ ] 삼각형·오각형·팔각형 캡처, `topic info -v` 비교, `node list`, `topic list` 출력이 있다
- [ ] `build/`, `install/`, `log/` 를 제외하고 `lv1_module2_이름.zip` 으로 압축했다
