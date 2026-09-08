
## 1. C++ 빌드 체계 세우기 — g++ 다중 파일 빌드와 CMake 전환

1. **수동 2단계 빌드 명령** (터미널 입력)
   ```
pa8@pa8-Legion-Pro-5-16IAX10:~/Ros2_ws/hongju_ros_ws/lv1_module2/ros2_ws$ g++ -c src/motor.cpp -o motor.o
pa8@pa8-Legion-Pro-5-16IAX10:~/Ros2_ws/hongju_ros_ws/lv1_module2/ros2_ws$ g++ -c src/main.cpp -o main.o
-rw-rw-r-- 1 pa8 pa8 12640 Sep  3 12:47 main.o
-rw-rw-r-- 1 pa8 pa8  7088 Sep  3 12:46 motor.o
pa8@pa8-Legion-Pro-5-16IAX10:~/Ros2_ws/hongju_ros_ws/lv1_module2/ros2_ws$ g++ main.o  motor.o -o motor
   ```
   
   
2. **`undefined reference` 에러 메시지** (출력) — 컴파일 에러와의 차이 설명
   ```
/usr/bin/ld: main.o: in function `main':
main.cpp:(.text+0x9c): undefined reference to `Motor::Motor(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&)'
/usr/bin/ld: main.cpp:(.text+0xc0): undefined reference to `Motor::print_status() const'
/usr/bin/ld: main.cpp:(.text+0xd8): undefined reference to `Motor::set_speed(double)'
/usr/bin/ld: main.cpp:(.text+0xe4): undefined reference to `Motor::start()'
/usr/bin/ld: main.cpp:(.text+0xfc): undefined reference to `Motor::set_speed(double)'
/usr/bin/ld: main.cpp:(.text+0x108): undefined reference to `Motor::print_status() const'
/usr/bin/ld: main.cpp:(.text+0x114): undefined reference to `Motor::stop()'
/usr/bin/ld: main.cpp:(.text+0x120): undefined reference to `Motor::print_status() const'
/usr/bin/ld: main.cpp:(.text+0x17c): undefined reference to `Motor::~Motor()'
/usr/bin/ld: main.cpp:(.text+0x1d5): undefined reference to `Motor::~Motor()'
collect2: error: ld returned 1 exit status
   ```
   선언은 했지만 실제 motor를 찾지 못해 undefined reference 에러가 발생
   
   
3. **CMake 빌드 출력** (터미널 출력)
   ```
-- The CXX compiler identification is GNU 11.4.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/c++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Configuring done
-- Generating done
-- Build files have been written to:
/home/pa8/Ros2_ws/hongju_ros_ws/lv1_module2/cpp_basics
   ```
   
   
4. **증분 빌드 시 재컴파일된 파일**: `motor.cpp` — 판단 근거
   motor.cpp에서 speed_rpm_ = 0.0  -->  1.5 로 변경하고
   다시 CMake 빌드.
   ```
-- Configuring done
-- Generating done
-- Build files have been written to: /home/pa8/Ros2_ws/hongju_ros_ws/lv1_module2/cpp_basics
   ```
   변경된 소스 파일과 그 파일에 의존성이 있는 파일과 필요한 부분만 다시 빌드. 
   
   

## 2. 현대 C++로 센서 계층 구현 — RAII·다형성·STL
1. **다형성 루프 출력**
   ```
=== 다형성 루프 출력 ===
[Lidar Constructor] Front_Lidar created
[Imu Constructor] Center_IMU created
Front_Lidar Read Value: 0.42
Center_IMU Read Value: 9.81
   ```
   
   
2. **스택 객체와 힙 객체의 소멸 시점** — 관찰 로그와 설명
   ```
=== 스택 vs 힙 객체 수명 관찰 ===
-- 스택 객체 생성 --
[Imu Constructor] Stack_IMU created
-- 힙 객체 생성 (make_unique) --
[Lidar Constructor] Heap_Lidar created
-- Scope 종료 직전 --
[Lidar ~Destructor] Heap_Lidar Derived destroyed (Buffer freed)
[Sensor ~Destructor] Heap_Lidar Base destroyed
[Imu ~Destructor] Stack_IMU Derived destroyed
[Sensor ~Destructor] Stack_IMU Base destroyed
-- Scope 종료 완료 --
   ```
   스택 메모리에 할당된 `stackImu`는 스코프(`{}`)를 벗어나는 즉시 소멸자가 호출됩니다. 동일한 스코프 내 스택 객체들은 선언된 역순으로 안전하게 해제됨.
   `std::make_unique`를 통해 힙 영역에 할당된 객체는 동적 메모리를 가리키는 `unique_ptr` 스마트 포인터가 스택에 존재합니다. 스코프가 끝날 때 스택에 있던 `unique_ptr` 객체가 먼저 소멸하면서 힙 영역의 실제 객체를 `delete` 처리합니다.
   
   
3. **가상 소멸자를 뺐을 때의 차이**: `___`
   `virtual ~Sensor()`를 제거하면, 업캐스팅된 업라이트 스마트 포인터(`std::unique_ptr<Sensor>`)나 다용도 포인터로 객체를 해제할 때 정의되지 않은 동작(Undefined Behavior)이 발생합니다.
   `~Sensor()`에 `virtual` 키워드가 없는 상태에서 `Lidar` 객체가 삭제될 때 파생 클래스의 소멸자 `~Lidar()`가 호출되지 않고 `Sensor`의 소멸자만 호출됩니다.
   이로 인해 `Lidar` 클래스 내부 멤버인 `buffer` (`new double[100]`)의 `delete[]` 문이 실행되지 않아 심각한 동적 메모리 누수(Memory Leak)가 발생함.
   
   
4. **`count_if` 결과**: 0.35 이내 기록 `3` 개
   
   
5. **누수 검출 결과** → **수정 후 결과** (검출 도구 출력 비교)
   ```
=== 메모리 누수 테스트 실행 ===
[Lidar Constructor] SafeLidar created
[Lidar ~Destructor] SafeLidar Derived destroyed (Buffer freed)
[Sensor ~Destructor] SafeLidar Base destroyed
[Lidar ~Destructor] Front_Lidar Derived destroyed (Buffer freed)
[Sensor ~Destructor] Front_Lidar Base destroyed
[Imu ~Destructor] Center_IMU Derived destroyed
[Sensor ~Destructor] Center_IMU Base destroyed
   ```
   
   ```
==33134==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 48 byte(s) in 1 object(s) allocated from:
    #0 0x7c62cdcb61e7 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:99
    #1 0x5a02d9a21f72 in causeMemoryLeak() /home/pa8/Ros2_ws/hongju_ros_ws/lv1_module2/cpp_basics/sensors/main.cpp:13
    #2 0x5a02d9a23212 in main /home/pa8/Ros2_ws/hongju_ros_ws/lv1_module2/cpp_basics/sensors/main.cpp:66
    #3 0x7c62cd429d8f in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58

Indirect leak of 800 byte(s) in 1 object(s) allocated from:
    #0 0x7c62cdcb6357 in operator new[](unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:102
    #1 0x5a02d9a219a8 in lidar::lidar(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&) /home/pa8/Ros2_ws/hongju_ros_ws/lv1_module2/cpp_basics/sensors/lidar.cpp:4
    #2 0x5a02d9a21f80 in causeMemoryLeak() /home/pa8/Ros2_ws/hongju_ros_ws/lv1_module2/cpp_basics/sensors/main.cpp:13
    #3 0x5a02d9a23212 in main /home/pa8/Ros2_ws/hongju_ros_ws/lv1_module2/cpp_basics/sensors/main.cpp:66
    #4 0x7c62cd429d8f in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58

SUMMARY: AddressSanitizer: 848 byte(s) leaked in 2 allocation(s).
   ```
   ```
==33864== HEAP SUMMARY:
==33864==     in use at exit: 848 bytes in 2 blocks
==33864==   total heap usage: 15 allocs, 13 frees, 76,616 bytes allocated
==33864== 
==33864== 848 (48 direct, 800 indirect) bytes in 1 blocks are definitely lost in loss record 2 of 2
==33864==    at 0x4849013: operator new(unsigned long) (in /usr/libexec/valgrind/vgpreload_memcheck-amd64-linux.so)
==33864==    by 0x10AACB: causeMemoryLeak() (main.cpp:13)
==33864==    by 0x10B328: main (main.cpp:66)
==33864== 
==33864== LEAK SUMMARY:
==33864==    definitely lost: 48 bytes in 1 blocks
==33864==    indirectly lost: 800 bytes in 1 blocks
==33864==      possibly lost: 0 bytes in 0 blocks
==33864==    still reachable: 0 bytes in 0 blocks
==33864==         suppressed: 0 bytes in 0 blocks
==33864== 
==33864== For lists of detected and suppressed errors, rerun with: -s
==33864== ERROR SUMMARY: 1 errors from 1 contexts (suppressed: 0 from 0)
   ```
   
   RAII 적용하여 스코프를 벗어나며 자동으로 unique_ptr 소멸자 실행 및 메모리 해제
   ```
==34279== HEAP SUMMARY:
==34279==     in use at exit: 0 bytes in 0 blocks
==34279==   total heap usage: 15 allocs, 15 frees, 76,616 bytes allocated
==34279== 
==34279== All heap blocks were freed -- no leaks are possible
==34279== 
==34279== For lists of detected and suppressed errors, rerun with: -s
==34279== ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)
   ```



## 3. rclpy 노드 작성 — 거북이 상태 발행자와 구독자

1. **`/turtle1/pose` 필드 구성**: `___`
   
```
ros2 pkg create --build-type ament_python turtle_py --dependencies rclpy turtlesim
going to create a new package
package name: turtle_py
destination directory: /home/pa8/Ros2_ws/hongju_ros_ws/physicalai-lv1-leehongju/lv1_module2/ros2_ws/src
package format: 3
version: 0.0.0
description: TODO: Package description
maintainer: ['pa8 <kanichong1@gmail.com>']
licenses: ['TODO: License declaration']
build type: ament_python
dependencies: ['rclpy', 'turtlesim']
creating folder ./turtle_py
creating ./turtle_py/package.xml
creating source folder
creating folder ./turtle_py/turtle_py
creating ./turtle_py/setup.py
creating ./turtle_py/setup.cfg
creating folder ./turtle_py/resource
creating ./turtle_py/resource/turtle_py
creating ./turtle_py/turtle_py/__init__.py
creating folder ./turtle_py/test
creating ./turtle_py/test/test_copyright.py
creating ./turtle_py/test/test_flake8.py
creating ./turtle_py/test/test_pep257.py

[WARNING]: Unknown license 'TODO: License declaration'.  This has been set in the package.xml, but no LICENSE file has been created.
It is recommended to use one of the ament license identitifers:
Apache-2.0
BSL-1.0
BSD-2.0
BSD-2-Clause
BSD-3-Clause
GPL-3.0-only
LGPL-3.0-only
MIT
MIT-0
```
   
   ```
ros2 run turtlesim turtlesim_node
[INFO] [1788666433.936101653] [turtlesim]: Starting turtlesim with node name /turtlesim
[INFO] [1788666433.941704555] [turtlesim]: Spawning turtle [turtle1] at x=[5.544445], y=[5.544445], theta=[0.000000]
   ```
   
   ```
ros2 topic echo /turtle1/pose
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
   ```
   
   ```
ros2 topic hz /turtle_distance
average rate: 10.001
min: 0.100s max: 0.100s std dev: 0.00017s window: 23
   ```
   

2. **`ros2 topic hz /turtle_distance` 출력**: 평균 `10` Hz
   
   ```
ros2 run turtle_py pose_distance_node
   ```
   
   ```
ros2 topic hz /turtle_distance
average rate: 10.001
min: 0.100s max: 0.100s std dev: 0.00017s window: 23
   ```
   
   
3. **구독자 경고 로그** (터미널 출력)
   
   ```
ros2 run turtle_py distance_warning_node
[INFO] [1788670133.047939663] [distance_warning_node]: Distance Warning Node initialized. (Threshold: 2.50m)
[WARN] [1788670133.126264963] [distance_warning_node]: Distance exceeded threshold! Current: 7.84m > Threshold: 2.50m
[WARN] [1788670133.226110504] [distance_warning_node]: Distance exceeded threshold! Current: 7.84m > Threshold: 2.50m
   ```
   
   
4. **구독자 2개 동시 수신 확인** (양쪽 로그)
   
   ```
average rate: 10.000
        min: 0.092s max: 0.107s std dev: 0.00104s window: 10000
average rate: 10.000
        min: 0.092s max: 0.107s std dev: 0.00104s window: 10000
average rate: 10.000
        min: 0.092s max: 0.107s std dev: 0.00104s window: 10000
   ```
   ```
[WARN] [1788670876.626155919] [distance_warning_node]: Distance exceeded threshold! Current: 7.84m > Threshold: 2.50m
[WARN] [1788670876.726150337] [distance_warning_node]: Distance exceeded threshold! Current: 7.84m > Threshold: 2.50m
[WARN] [1788670876.825922324] [distance_warning_node]: Distance exceeded threshold! Current: 7.84m > Threshold: 2.50m
[WARN] [1788670876.925918344] [distance_warning_node]: Distance exceeded threshold! Current: 7.84m > Threshold: 2.50m
   ```
   
   
5. **정사각형 주행 캡처** (turtlesim 화면)
   
   ```
ros2 run turtle_py polygon_drive_node
[INFO] [1788694993.550905744] [polygon_drive_node]: Polygon Drive Node Initialized.
다각형의 변의 개수를 입력하세요 (3 이상, 종료: q):5
[INFO] [1788695040.394724975] [polygon_drive_node]: 5각형 P-제어 주행을 시작합니다.
[INFO] [1788695043.392515626] [polygon_drive_node]: [1번째 변 도달] 회전 시작...
[INFO] [1788695044.692603705] [polygon_drive_node]: [1번째 회전 완료] 다음 변 직진...
[INFO] [1788695047.692357828] [polygon_drive_node]: [2번째 변 도달] 회전 시작...
[INFO] [1788695048.994685463] [polygon_drive_node]: [2번째 회전 완료] 다음 변 직진...
[INFO] [1788695051.992761948] [polygon_drive_node]: [3번째 변 도달] 회전 시작...
[INFO] [1788695053.292406632] [polygon_drive_node]: [3번째 회전 완료] 다음 변 직진...
[INFO] [1788695056.342636113] [polygon_drive_node]: [4번째 변 도달] 회전 시작...
[INFO] [1788695057.642449538] [polygon_drive_node]: [4번째 회전 완료] 다음 변 직진...
[INFO] [1788695060.642669843] [polygon_drive_node]: [5번째 변 도달] 회전 시작...
[INFO] [1788695061.942605541] [polygon_drive_node]: [5번째 회전 완료] 다음 변 직진...
[INFO] [1788695061.992396439] [polygon_drive_node]: 5각형 주행 완성!
   ```
   
   ![[screenshots/2026-09-06_20-39-50.png]]
   ![[screenshots/2026-09-06_20-43-28.png]]
   
   
   
6. **Ctrl+C 정상 종료 화면** (출력)
  
   ```
ros2 param set /lifecycle_param_node publish_rate 30.0
Set parameter successful

[INFO] [1788694195.835134341] [lifecycle_param_node]: 발행 주기가 30.0Hz 로 변경되었습니다.
[WARN] [1788694195.835432083] [lifecycle_param_node]: 경고: 원점 거리 초과! (현재: 7.84m > 임계값: 1.50m)

ros2 param set /lifecycle_param_node warn_distance 1.5
Set parameter successful

[WARN] [1788694402.585195773] [lifecycle_param_node]: 경고: 원점 거리 초과! (현재: 7.84m > 임계값: 1.50m)

[INFO] KeyboardInterrupt - 노드를 종료합니다.
   ```

   

## 4. rclcpp 노드 작성 — C++ 발행자와 구독자

1. **`colcon build` 성공 출력**
   
   ```
ros2 pkg create --build-type ament_cmake turtle_cpp --dependencies rclcpp std_msgs turtlesim

endencies rclcpp std_msgs turtlesim
going to create a new package
package name: turtle_cpp
destination directory: /home/pa8/Ros2_ws/hongju_ros_ws/physicalai-lv1-leehongju/lv1_module2/ros2_ws/src
package format: 3
version: 0.0.0
description: TODO: Package description
maintainer: ['pa8 <kanichong1@gmail.com>']
licenses: ['TODO: License declaration']
build type: ament_cmake
dependencies: ['rclcpp', 'std_msgs', 'turtlesim']
creating folder ./turtle_cpp
creating ./turtle_cpp/package.xml
creating source and include folder
creating folder ./turtle_cpp/src
creating folder ./turtle_cpp/include/turtle_cpp
creating ./turtle_cpp/CMakeLists.txt

[WARNING]: Unknown license 'TODO: License declaration'.  This has been set in the package.xml, but no LICENSE file has been created.
It is recommended to use one of the ament license identitifers:
Apache-2.0
BSL-1.0
BSD-2.0
BSD-2-Clause
BSD-3-Clause
GPL-3.0-only
LGPL-3.0-only
MIT
MIT-0
   ```
   
   ```
colcon build --packages-select turtle_cpp
Starting >>> turtle_cpp
Finished <<< turtle_cpp [5.32s]                     

Summary: 1 package finished [5.45s]
   ```
   ```
ros2 run turtlesim turtlesim_node
[INFO] [1788697061.424037019] [turtlesim]: Starting turtlesim with node name /turtlesim
[INFO] [1788697061.425742294] [turtlesim]: Spawning turtle [turtle1] at x=[5.544445], y=[5.544445], theta=[0.000000]
   ```
   
   
2. **rclpy 발행에서 rclcpp 구독으로 이어진 로그**
   
   ```
ros2 run turtle_py lifecycle_param_node
[WARN] [1788740485.307880862] [lifecycle_param_node]: 경고: 원점 거리 초과! (현재: 7.84m > 임계값: 2.50m)
[WARN] [1788740485.407764461] [lifecycle_param_node]: 경고: 원점 거리 초과! (현재: 7.84m > 임계값: 2.50m)
   ```
   
   ```
ros2 run turtle_cpp distance_subscriber_node
[INFO] [1788740348.007952332] [distance_subscriber_node]: Received Turtle Distance [C++ Sub]: 7.84 m
[INFO] [1788740348.107718299] [distance_subscriber_node]: Received Turtle Distance [C++ Sub]: 7.84 m
   ```
   
   
2. **rclpy와 rclcpp 대응 관계표** — 노드 생성 / 타이머 / 콜백 / 종료 (4행)
   
| 구분    | rclpy                                                                                                                                         | rclcpp                                                                                                                                          |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 노드 생성 | class MyNode(Node):<br>  <br>def __init__(self):<br>  <br>super().__init__('my_node')                                                         | class MyNode : public rclcpp::Node<br>{<br>public:<br>MyNode() : Node("my_node")<br>{}<br>};                                                    |
| 타이머   | self.timer = self.create_timer(0.1, self.timer_callback)                                                                                      | timer_ = this->create_wall_timer(<br>100ms, std::bind(&MyNode::timer_callback, this));                                                          |
| 콜백    | def timer_callback(self):<br># 동작 로직<br>def pose_callback(self, msg: Pose):<br># 메시지 처리                                                       | void timer_callback()<br>{ <br># 동작 로직<br>}<br>void pose_callback(const turtlesim::msg::Pose::SharedPtr msg)<br>{<br># 메시지 처리<br>}              |
| 종료    | rclpy.init(args=args)<br>node = MyNode()<br>try:<br>rclpy.spin(node)<br>finally:<br>node.destroy_node()<br>if rclpy.ok():<br>rclpy.shutdown() | rclcpp::init(argc, argv);<br>auto node = std::make_shared<MyNode>();<br>try {<br>rclcpp::spin(node);<br>} catch (...) {}<br>rclcpp::shutdown(); |

   
   
## 5. Service 와 Action — 즉시 응답과 장기 작업

1. **호출한 내장 서비스와 타입** — 4행 표 (서비스 / 타입 / 요청 값 / 결과)
   
   ```
ros2 service list
/clear
/kill
/reset
/spawn
/turtle1/set_pen
/turtle1/teleport_absolute
/turtle1/teleport_relative
   ```
   ```
ros2 service type /turtle1/teleport_absolute
turtlesim/srv/TeleportAbsolute

ros2 interface show turtlesim/srv/Spawn
float32 x
float32 y
float32 theta
string name # Optional.  A unique name will be created and returned if this is empty
---
string name
   ```
   
   
   ```
ros2 run turtle_py builtin_service_client
[INFO] [1788747602.991161647] [builtin_service_client]: [1/4] teleport_absolute(5.5, 5.5, 0.0) → OK
[INFO] [1788747602.996834389] [builtin_service_client]: [2/4] set_pen(r=255, g=0, b=0, width=4, off=0) → OK
[WARN] [1788747603.011156253] [builtin_service_client]: [3/4] spawn → 새 거북이 이름turtle2
[INFO] [1788747603.027509655] [builtin_service_client]: [4/4] clear → OK
   ```
   
   
| **서비스**           | **타입**                         | **요청 값**                                     | **결과**                                 |
| ----------------- | ------------------------------ | -------------------------------------------- | -------------------------------------- |
| teleport_absolute | turtlesim/srv/TeleportAbsolute | x: 2.0, y: 2.0, theta: 0.0                   | 지정한 (2.0, 2.0) 위치로 거북이 순간이동            |
| set_pen           | turtlesim/srv/SetPen           | r: 255`, g: 0, b: 0, width: 5, off: 0        | 펜 색상을 빨간색, 굵기를 5로 변경                   |
| /spawn            | turtlesim/srv/Spawn            | x: 8.0, y: 8.0, theta: 1.57, name: 'turtle2' | 'turtle2' 지정 위치에 새로운 거북이 노드 생성 및 이름 반환 |
| /clear            | std_srvs/srv/Empty             | 요청 필드 없음                                     | 순간이동 과정에서 그려진 궤적선 지움                   |
   
   
2. **Service 요청·응답 로그**
   
   ```
ros2 run turtle_py toggle_servers
[INFO] [1788749074.840925045] [toggle_servers]: toggle_servers 노드가 시작되었습니다. (주행 상태: OFF)
[INFO] [1788749074.841082996] [toggle_servers]: 제공 서비스: /enable_driving , /save_home , /go_home
[INFO] [1788749212.696696363] [toggle_servers]: [Service Request] /enable_driving -> data=True
[INFO] [1788749212.697016966] [toggle_servers]: [Service Response] /enable_driving -> success=True, message="driving enabled"
[INFO] [1788749313.869115427] [toggle_servers]: [Service Request] /save_home
[INFO] [1788749313.869352730] [toggle_servers]: [Service Response] /save_home -> success=True, message="home saved: x=4.63, y=5.85, theta=-0.77"
[INFO] [1788749380.901284693] [toggle_servers]: [Service Request] /enable_driving -> data=False
[INFO] [1788749380.901513270] [toggle_servers]: [Service Response] /enable_driving -> success=True, message="driving disabled"
[INFO] [1788749408.593874582] [toggle_servers]: [Service Request] /save_home
[INFO] [1788749408.594285235] [toggle_servers]: [Service Response] /save_home -> success=True, message="home saved: x=6.14, y=7.82, theta=2.59"
   ```
   
   ```
ros2 service call /enable_driving std_srvs/srv/SetBool "{data: true}"
requester: making request: std_srvs.srv.SetBool_Request(data=True)

response:
std_srvs.srv.SetBool_Response(success=True, message='driving enabled')


ros2 service call /save_home std_srvs/srv/Trigger
requester: making request: std_srvs.srv.Trigger_Request()

response:
std_srvs.srv.Trigger_Response(success=True, message='home saved: x=4.63, y=5.85, theta=-0.77')
   ```
   
   ```
ros2 service call /enable_driving std_srvs/srv/SetBool "{data: false}"
requester: making request: std_srvs.srv.SetBool_Request(data=False)

response:
std_srvs.srv.SetBool_Response(success=True, message='driving disabled')


ros2 service call /go_home std_srvs/srv/Trigger
requester: making request: std_srvs.srv.Trigger_Request()

response:
std_srvs.srv.Trigger_Response(success=True, message='teleport 요청 전송 완료: (6.14, 7.82, 2.59)')
   ```
   ![[2026-09-07_11-47-53.png]]
   
   
3. **데드락이 생기는 이유** — executor 관점 3줄 이내 서술
   
   단일 스레드 Executor는 한 번에 하나의 콜백만 처리하므로, 콜백 내부에서 응답을 동기 대기 시 유일한 스레드가 블로킹됩니다.
   도착한 서비스 응답을 수신하고 Future를 완료해 줄 주체 역시 동일한 Executor 스레드입니다.
   응답을 처리할 스레드가 콜백 대기에 갇혀 작동하지 못하면서 영구적인 순환 대기(데드락)가 발생합니다.
   
   올바른 비동기 패턴
   요청만 전송하고 콜백을 즉시 종료하여 스레드를 Executor에 반환함. 스레드가 자유로워져 서비스 응답 이벤트를 정상 수신·처리할 수 있음
   
   
4. **`rotate_absolute` 피드백 수신 로그** — remaining 이 줄어드는 흐름
   
   ```
ros2 run turtle_py rotate_absolute_client --theta 3.0
[INFO] [1788751769.643794462] [rotate_absolute_client]: Goal 전송: theta = 3.000 rad (현재 theta = None)
[INFO] [1788751769.651011606] [rotate_absolute_client]: 피드백: remaining = +0.406 rad
[INFO] [1788751769.651339485] [rotate_absolute_client]: Goal 수락됨 — 회전 및 피드백 수신 시작
[INFO] [1788751769.906846819] [rotate_absolute_client]: 피드백: remaining = +0.150 rad
[INFO] [1788751770.051473480] [rotate_absolute_client]: 결과 수신: status=SUCCEEDED, delta=-0.400 rad, 현재 theta=2.994
   ```
   
   ```
ros2 run turtle_py rotate_absolute_client --theta 3.0 --cancel-after 1.0
[INFO] [1788751948.410989551] [rotate_absolute_client]: Goal 전송: theta = 3.000 rad (현재 theta = None)
[INFO] [1788751948.418717177] [rotate_absolute_client]: 피드백: remaining = +0.406 rad
[INFO] [1788751948.419127348] [rotate_absolute_client]: Goal 수락됨 — 회전 및 피드백 수신 시작
[INFO] [1788751948.675981096] [rotate_absolute_client]: 피드백: remaining = +0.150 rad
[INFO] [1788751948.819276666] [rotate_absolute_client]: 결과 수신: status=SUCCEEDED, delta=-0.400 rad, 현재 theta=2.994
   ```
   
   
5. **취소 요청 처리 로그** — 취소 시점 각도: `3.026 rad`
   
   ```
ros2 run turtle_py rotate_absolute_client --theta 3.0 --cancel-after 1.0
[INFO] [1788752630.625341924] [rotate_absolute_client]: Goal 전송: theta = 3.000 rad (현재 theta = None)
[INFO] [1788752630.626564289] [rotate_absolute_client]: 피드백: remaining = -1.034 rad
[INFO] [1788752630.626807886] [rotate_absolute_client]: Goal 수락됨 — 회전 및 피드백 수신 시작
[INFO] [1788752630.882886076] [rotate_absolute_client]: 피드백: remaining = -0.778 rad
[INFO] [1788752631.138580176] [rotate_absolute_client]: 피드백: remaining = -0.522 rad
[INFO] [1788752631.395109813] [rotate_absolute_client]: 피드백: remaining = -0.266 rad
[WARN] [1788752631.627151105] [rotate_absolute_client]: 취소 요청 전송 (요청 시점 theta = 3.026 rad)
[WARN] [1788752631.635532587] [rotate_absolute_client]: 취소 수락됨 (서버가 중단 처리 중). 취소 시점 theta = 3.026 rad
[INFO] [1788752631.635710741] [rotate_absolute_client]: 결과 수신: status=CANCELED, delta=+0.992 rad, 현재 theta=3.026
   ```
   
   
6. **통신 패턴 설계표** — 기능 / 선택한 모델 / 근거 (5행)
   
| **기능**     | **선택한 모델** | **근거**                                                                             |
| ---------- | ---------- | ---------------------------------------------------------------------------------- |
| 자세 스트리밍    | Topic      | 실시간으로 거북이의 위치와 방향 좌표데이터를 다수의 수신자에게 단방향으로 전송해야 하므로 토픽이 적합합니다.                       |
| 순간이동       | Service    | 요청 즉시 거북이의 좌표를 변경하고 연산 결과를 동기/비동기로 바로 반환받는 단발성 작업이므로 서비스가 적합합니다.                   |
| 목표 각도까지 회전 | Action     | 목표 각도까지 도달하는 데 시간이 걸리는 장기 작업이며, 진행 상황(피드백) 수신 및 도중 취소(Cancel) 제어가 필요하므로 액션이 적합합니다. |
| 펜 색 설정     | Service    | 펜의 색상(R, G, B) 및 굵기를 일회성 명령으로 즉시 설정하고 응답을 확인하는 작업이므로 서비스가 적합합니다.                   |
| 거북이 추가     | Service    | 특정 위치에 새로운 거북이를 1회성 요청으로 생성하고, 생성된 거북이의 이름을 응답 결과로 전달받아야 하므로 서비스가 적합합니다.           |
   
   

## 6. 커스텀 인터페이스 정의 — 경유점 메시지와 다각형 액션
1. **`ros2 interface show turtle_interfaces/msg/WaypointList` 출력**
   
   ```
ros2 interface show turtle_interfaces/msg/Waypoint
float64 x            # 경유점 x 좌표 [m] (turtlesim 좌표계, 0 ~ 11)
float64 y            # 경유점 y 좌표 [m]
float32 tolerance    # 도달 판정 허용 오차 [m] — 이 거리 이내면 "도달" 로 봅니다
string  label        # 사람이 읽는 이름 (예: "corner_A")
   ```
   
   ```
ros2 interface show turtle_interfaces/msg/WaypointList

std_msgs/Header header   # stamp(발행 시각) + frame_id(좌표계 이름, 여기서는 "world")
	builtin_interfaces/Time stamp
		int32 sec
		uint32 nanosec
	string frame_id
Waypoint[] waypoints     # 경유점 배열 — 문제 6 에서는 4개 이상을 채워 발행합니다
	float64 x            # 경유점 x 좌표 [m] (turtlesim 좌표계, 0 ~ 1
	float64 y            #
	float32 tolerance    # 도달 판정 허용 오차 [m] — 이 거리 이내면 "도달" 로 봅
	string  label        #
   ```
   
   ```
ros2 interface show turtle_interfaces/srv/SetGain

# ---------- 요청 ----------
float64 kp    # 비례 게인
float64 ki    # 적분 게인
float64 kd    # 미분 게인
---
# ---------- 응답 ----------
bool   success   # 값이 유효해서 적용됐는지
string message   # 사람이 읽을 결과 설명 (예: "kp must be >= 0")
   ```
   
   ```
ros2 interface show turtle_interfaces/action/DrawPolygon

# ---------- 목표 (goal) ----------
int32   sides         # 변의 개수 (3 이상)
float64 side_length   # 한 변의 길이 [m]
---
# ---------- 결과 (result) ----------
float64 total_distance   # 실제로 이동한 총 거리 [m] (취소되면 그때까지의 거리)
---
# ---------- 피드백 (feedback) ----------
int32   completed_sides  # 지금까지 완성한 변의 수
float32 progress         # 진행률 0.0 ~ 1.0 (= completed_sides / sides)
   ```
   
   
2. **`ros2 topic echo /waypoints` 출력** (중첩 필드가 보이는 출력)
   
   ```
header:
  stamp:
    sec: 1788763426
    nanosec: 272321253
  frame_id: world
waypoints:
- x: 2.0
  y: 2.0
  tolerance: 0.30000001192092896
  label: corner_A
- x: 9.0
  y: 2.0
  tolerance: 0.30000001192092896
  label: corner_B
- x: 9.0
  y: 9.0
  tolerance: 0.30000001192092896
  label: corner_C
- x: 2.0
  y: 9.0
  tolerance: 0.30000001192092896
  label: corner_D
---
   ```
   
   
3. **`DrawPolygon` 피드백 로그** — 총 이동 거리: `6.0257565768949775`
   
   ```
ros2 action send_goal /draw_polygon turtle_interfaces/action/DrawPolygon "{sides: 3, side_length: 2.0}" --feedback
Waiting for an action server to become available...
Sending goal:
     sides: 3
side_length: 2.0

Goal accepted with ID: 6d9dda86e9154f28932e17039c07baae

Feedback:
    completed_sides: 1
progress: 0.3333333432674408

Feedback:
    completed_sides: 2
progress: 0.6666666865348816

Feedback:
    completed_sides: 3
progress: 1.0

Result:
    total_distance: 6.0257565768949775

Goal finished with status: SUCCEEDED
   ```
   
   ```
[INFO] [1788762011.609774517] [polygon_action_server]: polygon_action_server 시작: 액션 /draw_polygon 대기 중
[INFO] [1788762119.185694046] [polygon_action_server]: Goal 수락: sides=3, side_length=2.0
[INFO] [1788762124.882516078] [polygon_action_server]: 변 1/3 완료 (누적 이동거리: 2.01 m)
[INFO] [1788762130.628815039] [polygon_action_server]: 변 2/3 완료 (누적 이동거리: 4.02 m)
[INFO] [1788762136.358573694] [polygon_action_server]: 변 3/3 완료 (누적 이동거리: 6.03 m)
[INFO] [1788762136.358754839] [polygon_action_server]: 다각형 완성: 총 이동 거리 6.03 m
   ```
   
   
4. **삼각형·오각형·팔각형 궤적 캡처** (이미지 3장)
   
   ![[2026-09-07_15-17-23.png]]
   
   ![[2026-09-07_15-26-29.png]]
   
   ![[2026-09-07_15-27-33.png]]
   
   
5. **액션 취소 처리 결과**: `취소됨`
   
   ```
Canceling goal...
Goal canceled.
Result:
    total_distance: 3.0159017886579615

Goal finished with status: CANCELED
   ```
   
   ```
[WARN] [1788762483.807816089] [polygon_action_server]: 취소 요청 수신 — 실행 루프에서 즉시 정지합니다.
[WARN] [1788762483.811880339] [polygon_action_server]: 취소됨 — 정지. 그때까지 이동 거리 3.02 m
   ```
   
   ```
# 궤적을 지우기
ros2 service call /clear std_srvs/srv/Empty
   ```
   
   ![[2026-09-07_15-29-05.png]]
   
   
6. **인터페이스를 별도 패키지로 분리하는 이유**: `___`
   
   순환 의존성(Circular Dependency) 방지와 재사용성 및 빌드 효율성 때문입니다.
   순환 의존성 방지: 만약 C++ 노드 패키지(turtle_cpp)에 인터페이스를 함께 넣고, Python 노드 패키지(turtle_py)가 이 메시지를 사용하려면 turtle_py가 turtle_cpp에 의존해야 합니다. 이때 turtle_cpp 노드가 다시 turtle_py의 특정 노드나 서비스를 사용해야 한다면 두 패키지 간 순환 의존성이 발생하여 빌드 시스템(colcon)이 빌드 순서를 정하지 못하고 에러를 발생시킵니다.
   빌드 시스템 분리 (ament_cmake vs ament_python): C++ 메시지 생성 라이브러리는 ament_cmake 빌드 시스템을 사용하는 반면, Python 노드 패키지는 주로 ament_python을 사용합니다. 인터페이스를 독립된 ament_cmake 패키지로 구성하면 언어에 독립적인 메시지 헤더/파이썬 바인딩 라이브러리가 깔끔하게 빌드됩니다.
   결합도(Coupling) 감소: 여러 패키지(발행자, 구독자, 서비스 서버 등)가 노드 실행 로직 전체에 의존할 필요 없이 통신 규격(메시지 타입)에만 의존할 수 있게 되어 유지보수가 용이해집니다.
   
   
   
## 7. QoS 설정과 통신 단절 진단
1. **QoS 비호환 시 `topic info --verbose` 출력** (양쪽 비교)
   
   ```
ros2 run turtle_py qos_sensor_publisher

[WARN] [1788764048.788335709] [qos_sensor_publisher]: New subscription discovered on topic 'turtle_distance', requesting incompatible QoS. No messages will be sent to it. Last incompatible policy: RELIABILITY
   ```
   
   ```
ros2 run turtle_py qos_subscriber

[ERROR] [1788764221.449142903] [qos_subscriber]: QoS 비호환 이벤트! total_count=1, last_policy_kind=rmw_qos_policy_kind_t.RMW_QOS_POLICY_RELIABILITY → `ros2 topic info -v` 로 발행자/구독자 QoS 를 비교하세요
[INFO] [1788764223.439254522] [qos_subscriber]: [통계] 지난 2초 처리 0개 (누적 0개) — 0개라면 QoS 비호환이나 발행자 부재를 의심
   ```
   
   
2. **연결되지 않은 원인**: `___` — 수정한 설정: `___`
   ㅁ
   발행자의 Reliability 속성은 BEST_EFFORT(손실 허용)인 반면, 구독자의 Reliability 속성은 RELIABLE(손실 없는 재전송 보장)로 설정되어 QoS Rx/Tx 비호환(Incompatibility)이 발생했기 때문.
   
   ```
# 구독자를 Best-Effort 로 변경
ros2 run turtle_py qos_subscriber --ros-args -p reliability:=best_effort
   ```
   
   ```
# 발행자를 Reliable 로 변경
ros2 run turtle_py qos_sensor_publisher --ros-args -p reliability:=reliable
   ```
   
   reliability 파라미터를 변경해 모드에 맞게 설정
   
   
3. **Transient Local 과 Volatile 수신 결과 비교**
   
   ```
ros2 run turtle_py waypoint_publisher

[INFO] [1788771054.328761122] [waypoint_publisher]: waypoint_publisher 시작: durability=transient_local, reliability=reliable, depth=1 — 1초 뒤 1회 발행
[INFO] [1788771055.319801417] [waypoint_publisher]: /waypoints 발행 완료: 4개 ['corner_A', 'corner_B', 'corner_C', 'corner_D'] (frame_id=world)
   ```
   
   ```
ros2 run turtle_py qos_subscriber --ros-args -p topic:=waypoints -p msg_type:=WaypointList -p durability:=transient_local

[INFO] [1788771157.852470439] [qos_subscriber]: #2 WaypointList: 4개 ['corner_A', 'corner_B', 'corner_C', 'corner_D'] frame_id=world
[INFO] [1788771159.264641649] [qos_subscriber]: [통계] 지난 2초 처리 1개 (누적 2개)

   ```
   
   ```
ros2 run turtle_py waypoint_publisher --ros-args -p durability:=volatile

[INFO] [1788771335.196513756] [waypoint_publisher]: waypoint_publisher 시작: durability=volatile, reliability=reliable, depth=1 — 1초 뒤 1회 발행
[WARN] [1788771335.203036744] [waypoint_publisher]: New subscription discovered on topic 'waypoints', requesting incompatible QoS. No messages will be sent to it. Last incompatible policy: DURABILITY
[INFO] [1788771336.185504427] [waypoint_publisher]: /waypoints 발행 완료: 4개 ['corner_A', 'corner_B', 'corner_C', 'corner_D'] (frame_id=world)

[ERROR] [1788771335.185533997] [qos_subscriber]: QoS 비호환 이벤트! total_count=1, last_policy_kind=rmw_qos_policy_kind_t.RMW_QOS_POLICY_DURABILITY → `ros2 topic info -v` 로 발행자/구독자 QoS 를 비교하세요
   ```
   

4. **History depth 1 에서의 메시지 누락 관찰**: `메시지 누락`
   
   ```
ros2 run turtle_py waypoint_publisher

[INFO] [1788772182.591229355] [waypoint_publisher]: waypoint_publisher 시작: durability=transient_local, reliability=reliable, depth=1 — 1초 뒤 1회 발행
[INFO] [1788772183.582359878] [waypoint_publisher]: /waypoints 발행 완료: 4개 ['corner_A', 'corner_B', 'corner_C', 'corner_D'] (frame_id=world)
   ```
   
   ```
ros2 run turtle_py qos_subscriber --ros-args -p reliability:=best_effort -p history_depth:=1 -p callback_delay:=0.5

[INFO] [1788772110.203700331] [qos_subscriber]: qos_subscriber 시작: topic=turtle_distance type=Float32 reliability=best_effort durability=volatile depth=1 callback_delay=0.5s
[INFO] [1788772112.194855250] [qos_subscriber]: [통계] 지난 2초 처리 0개 (누적 0개) — 0개라면 QoS 비호환이나 발행자 부재를 의심
[INFO] [1788772114.194804347] [qos_subscriber]: [통계] 지난 2초 처리 0개 (누적 0개) — 0개라면 QoS 비호환이나 발행자 부재를 의심
   ```
   
   ```
[INFO] [1788772020.107656719] [qos_subscriber]: #1 WaypointList: 4개 ['corner_A', 'corner_B', 'corner_C', 'corner_D'] frame_id=world
[INFO] [1788772021.919833979] [qos_subscriber]: [통계] 지난 2초 처리 1개 (누적 1개)
   ```
   
   콜백이 지연되는 0.5초 동안 발행자는 5개의 메시지를 새로 전송합니다.
   구독자의 큐 크기가 `depth=1`로 지정되어 있어, 큐에 있던 이전 메시지 4개는 새로 들어오는 최신 데이터에 의해 덮어씌워져 유실(Drop)됩니다.
   `history_depth:=10`으로 올려서 동일하게 실행하면, 콜백이 최대 10개까지 메시지가 버퍼 큐에 차곡차곡 쌓였다가 깨어난 뒤 순차적으로 처리.
   
   
5. **토픽 5종 QoS 설계표** — 토픽 / Reliability / Durability / 근거 (5행)
      
| **토픽**           | **Reliability** | **Durability**  | **근거**                                                                                                                                |
| ---------------- | --------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| /turtle1/pose    | BEST_EFFORT     | VOLATILE        | 빠른 주기로 연속 스트리밍되는 센서 포즈 데이터로, 네트워크 부하를 줄이고 이전 시점의 누락된 데이터 재전송보다 최신 위치 데이터의 즉시성이 더 중요합니다.                                               |
| /turtle1/cmd_vel | BEST_EFFORT     | VOLATILE        | 제어 주기마다 연속 전송되는 로봇 속도 명령으로, 지나간 명령의 재전송은 제어 혼란을 야기하므로 실시간성 확보 및 지연 최소화가 핵심입니다.                                                        |
| /waypoints       | RELIABLE        | TRANSIENT_LOCAL | 경유점 목록은 자주 변경되지 않지만, 단 하나의 메시지 유실도 전체 경로 이탈을 부르므로 재전송(RELIABLE)이 필수이며, 늦게 실행된 내비게이션 노드도 최신 경유점 목록을 즉시 복구(TRANSIENT_LOCAL)할 수 있어야 합니다. |
| /turtle_distance | BEST_EFFORT     | VOLATILE        | 10Hz 등 주기적으로 연산되어 단순 모니터링/지표용으로 발행되는 계산 값으로, 일시적인 메시지 누락이 전체 시스템 제어 파탈로 이어지지 않으므로 리소스 사용을 최소화합니다.                                     |
| /diagnostics     | RELIABLE        | VOLATILE        | 시스템 제어 상태, 에러 코드, HW 이상 유무를 전달하는 진단 메시지로, 시스템 오류 알림 메시지의 절대적인 신뢰성 및 손실 없는 전달이 필수적입니다.                                                 |
   
   
   
## 8. colcon 워크스페이스 구성 — 패키지 구조와 의존성

1. **`colcon build` 빌드 순서 로그** — 인터페이스가 먼저인 이유
   
   ```
colcon build --symlink-install 2>&1 | tee build.log
   
Starting >>> turtle_interfaces
Starting >>> turtle_cpp
Finished <<< turtle_cpp [0.09s]
Finished <<< turtle_interfaces [1.15s]
Starting >>> turtle_examples
Starting >>> turtle_py
Finished <<< turtle_examples [1.07s]
Finished <<< turtle_py [1.07s]

Summary: 4 packages finished [2.36s]
   ```
   
   ```
colcon graph
   
turtle_cpp         +   
turtle_interfaces   +**
turtle_examples      + 
turtle_py             +
   ```
   
   의존성 그래프를 구성하고 위상 정렬(Topological Sort) 알고리즘을 적용하여 빌드 순서를 산출.
   colcon은 실행 시 각 패키지의 package.xml을 가장 먼저 스캔하고, <depend>turtle_interfaces</depend> 또는 <exec_depend>turtle_interfaces<'/exec_depend'> 태그를 읽어 두 패키지 간 선후 의존 관계를 파악합니다.
   인터페이스 파이썬 바인딩 소스코드가 먼저 생성되어 들어가지 않으면 Python 노드는 `ModuleNotFoundError`를 발생시키며 컴파일/실행에 실패하게 됩니다.
   
   
2. **`package.xml` 의존성 선언 부분** (발췌)
   
   ```
turtle_interfaces/package.xml

<!-- 빌드 툴 및 코드 생성기 의존성 --> 
<buildtool_depend>ament_cmake</buildtool_depend> <buildtool_depend>rosidl_default_generators</buildtool_depend> 

# 데이터 타입 및 액션 메시지 의존성 
<depend>std_msgs</depend> 
<depend>action_msgs</depend> 

# 런타임 실행 의존성 
<exec_depend>rosidl_default_runtime</exec_depend> 

# 인터페이스 패키지 그룹 등록 <member_of_group>rosidl_interface_packages</member_of_group>
   ```
   
   ```
turtle_py/package.xml
<!-- 빌드 툴 의존성 --> 
<buildtool_depend>ament_python</buildtool_depend> 

# 요구 조건 의존성 선언 (turtle_interfaces, rclpy, geometry_msgs, turtlesim) <depend>rclpy</depend> 
<depend>geometry_msgs</depend> 

# 사용자 작성 인터페이스 및 시뮬레이터 의존성 
<depend>turtle_interfaces</depend> 
<depend>turtlesim</depend> 
<depend>std_msgs</depend> 

# 테스트 의존성 
<test_depend>ament_copyright</test_depend> 
<test_depend>ament_flake8</test_depend> 
<test_depend>ament_pep257</test_depend> 
<test_depend>python3-pytest</test_depend>
   ```
   
   
3. **`setup.py` entry_points** (발췌) — 등록한 노드 목록: `pose_distance_node, distance_warning_node, polygon_drive_node, lifecycle_param_node, builtin_service_client, service_controlled_node, toggle_servers, rotate_absolute_client, polygon_action_server, qos_subscriber, qos_sensor_publisher, waypoint_publisher`
   
   ```
'pose_distance_node = turtle_py.pose_distance_node:main',

'distance_warning_node = turtle_py.distance_warning_node:main',

'polygon_drive_node = turtle_py.polygon_drive_node:main',

'lifecycle_param_node = turtle_py.lifecycle_param_node:main',

'builtin_service_client = turtle_py.builtin_service_client:main',

'service_controlled_node = turtle_py.service_controlled_node:main',

'toggle_servers = turtle_py.toggle_servers:main',

'rotate_absolute_client = turtle_py.rotate_absolute_client:main',

'polygon_action_server = turtle_py.polygon_action_server:main',

'qos_subscriber = turtle_py.qos_subscriber:main',

'qos_sensor_publisher = turtle_py.qos_sensor_publisher:main',

'waypoint_publisher = turtle_py.waypoint_publisher:main',
   ```
   
   ```
ros2 run turtle_py pose_distance_node

ros2 run turtle_py distance_warning_node

ros2 run turtle_py polygon_drive_node

ros2 run turtle_py lifecycle_param_node

ros2 run turtle_py builtin_service_client

ros2 run turtle_py service_controlled_node

ros2 run turtle_py toggle_servers

ros2 run turtle_py rotate_absolute_client

ros2 run turtle_py polygon_action_server

ros2 run turtle_py qos_subscriber

ros2 run turtle_py qos_sensor_publisher

ros2 run turtle_py waypoint_publisher
   ```
   동작 확인 완료
   
   
4. **source 전 실행 결과와 source 후 실행 결과** (두 출력 비교)
   
   ```
ros2 run turtle_py toggle_servers
Package 'turtle_py' not found
   ```
   
   ```
source install/setup.bash

ros2 run turtle_py toggle_servers
[INFO] [1788778099.335457852] [toggle_servers]: toggle_servers 노드가 시작되었습니다. (주행 상태: OFF)
[INFO] [1788778099.335620727] [toggle_servers]: 제공 서비스: /enable_driving , /save_home , /go_home
   ```
   
   현재 작업 중인 `ros2_ws` 워크스페이스가 추가로 `source`되어 오버레이(Overlay)된 상태
   패키지들의 Python 모듈 및 인터페이스 바인딩 경로가 추가
   
   
5. **`src` / `build` / `install` / `log` 의 역할** (4줄)
   
   src: 개발자가 직접 작성한 C++/Python 소스 코드, 패키지 설정 파일, 인터페이스 정의 파일을 보관하는 원본 소스 코드 디렉터리입니다.
   build: colcon build 실행 시 C++ 컴파일 중간 파일, CMake 생성 파일, Python 빌드 캐시 등이 저장되는 임시 작업 디렉터리입니다.
   install: 빌드가 완료된 실행 파일, 라이브러리, 파라미터/Launch 파일, 생성된 파이썬/C++ 인터페이스 바인딩 모듈이 최종 배치되는 실행 환경 디렉터리입니다.
   log: colcon build 또는 ros2 launch 실행 중 발생한 빌드 과정의 상세 로그, 경고, 에러 기록이 저장되는 디버깅용 로그 디렉터리입니다.
   
   
   
## 9. launch 파일로 시스템 기동 — 다중 노드와 파라미터 주입

1. **`ros2 launch` 실행 출력**
   
   ```
ros2 launch turtle_examples turtle_system.launch.py use_examples:=true
   
[ex03_distance_subscriber-3] [WARN] [1788779010.644481679] [turtle_distance_subscriber]: 경고: 원점 거리 7.84 m > 임계 2.50 m
[ex03_distance_subscriber-3] [WARN] [1788779010.743638617] [turtle_distance_subscriber]: 경고: 원점 거리 7.84 m > 임계 2.50 m
   ```
   
   
2. **`ros2 node list` 결과** — 동시 실행된 노드: `polygon_action_server, turtle_distance_publisher, turtle_distance_subscriber, turtlesim`
   
   ```
ros2 node list
   
/polygon_action_server
/turtle_distance_publisher
/turtle_distance_subscriber
/turtlesim
   ```
   
   ```
ros2 launch turtle_py turtle_system.launch.py student_action_exec:=polygon_action_server

[INFO] [launch]: All log files can be found below /home/pa8/.ros/log/2026-09-07-20-25-36-883438-pa8-Legion-Pro-5-16IAX10-23303
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [launch.user]: 적용 중인 params_file 경로: /home/pa8/Ros2_ws/hongju_ros_ws/physicalai-lv1-leehongju/lv1_module2/ros2_ws/install/turtle_py/share/turtle_py/config/params.yaml
[ERROR] [launch]: Caught exception in launch (see debug for traceback): executable 'turtle_distance_publisher' not found on the libexec directory '/home/pa8/Ros2_ws/hongju_ros_ws/physicalai-lv1-leehongju/lv1_module2/ros2_ws/install/turtle_py/lib/turtle_py'
   ```
   
3. **`ros2 param get` 으로 확인한 주입 값**: `___`
   
   ```
ros2 param get /turtle_distance_publisher publish_rate
Double value is: 10.0
   
ros2 param get /turtle_distance_subscriber warn_distance
Double value is: 2.5
   
ros2 param set /turtle_distance_subscriber warn_distance 0.8
Set parameter successful
ros2 param set /turtle_distance_publisher publish_rate 5.0
Set parameter successful
   ```
   
   ```
ros2 topic hz /turtle_distance
average rate: 5.000
	min: 0.200s max: 0.200s std dev: 0.00015s window: 6
average rate: 5.000
	min: 0.200s max: 0.200s std dev: 0.00014s window: 12
average rate: 5.000
	min: 0.200s max: 0.200s std dev: 0.00015s window: 18
   ```
   
   
3. **YAML 값 변경 전후 동작 차이**: `___`
   
   ```
warn_distance: 0.8 변경
[turtle_distance_subscriber-3] [INFO] [1788781528.492482333] [turtle_distance_subscriber]: [통계] 지난 2초 처리 20개 (누적 1059개)
[turtle_distance_subscriber-3] [INFO] [1788781528.499064994] [turtle_distance_subscriber]: #1060 수신: 7.841
   ```
   
   하위의 YAML 파일을 수정하면 `install/` 영역의 파일이 실시간으로 참조되어, Python 코드 재컴파일이나 패키지 재빌드 단계 없이 Launch 구동 시 변경된 파라미터가 즉시 주입
   
   
4. **네임스페이스 적용 후 `topic list`** (출력)
   
   ```
   ros2 launch turtle_py turtle_system.launch.py spawn_second:=true
   ```
   
   ```
ros2 node list
WARNING: Be aware that there are nodes in the graph that share an exact name, which can have unintended side effects.
/polygon_action_server
/polygon_action_server
/turtle2/turtle_distance_publisher
/turtle_distance_publisher
/turtle_distance_publisher
/turtle_distance_subscriber
/turtle_distance_subscriber
/turtlesim
/turtlesim
   ```
   ㅁ
   ㅁ
   ㅁ
## 10. 시각화·기록·테스트로 검증하기
1. **`rqt_graph` 캡처** — 데이터 미수신 진단 절차 (단계별)
   
   ![[2026-09-08_10-36-11.png]]
   
   데이터 미수신 시 진단 절차
   * ros2 topic list 및 echo: 토픽 생성 여부 및 실제 데이터 흐름 유무 확인.
   * ros2 topic info -v (Pub/Sub 수 확인): 발행자 및 구독자 노드가 그래프 상에 올바르게 바인딩되어 있는지 점검.
   * QoS 프로필 대조: Publisher/Subscriber 간 Reliability 및 Durability 호환성 검증 (BEST_EFFORT vs RELIABLE 등).
   * ros2 node list 및 ROS_DOMAIN_ID: 상위 의존 노드의 생존 상태 및 도메인 환경 변수 설정 일치 여부 확인.
   
   
2. **RViz2 TF + 경유점 마커 캡처**
   
   ![[2026-09-08_10-59-19.png]]
   
   ![[2026-09-08_11-07-10.png]]
   
   
3. **`ros2 bag play` 재생 중 구독자 로그** — 기록된 토픽과 메시지 수: `___`
   
   ```
[INFO] [1788833871.670389183] [qos_subscriber]: #165 수신: 3.536
[INFO] [1788833871.770182565] [qos_subscriber]: #166 수신: 3.536
[INFO] [1788833871.875974678] [qos_subscriber]: #167 수신: 3.536
[INFO] [1788833871.973387907] [qos_subscriber]: #168 수신: 3.536
[INFO] [1788833872.007844919] [qos_subscriber]: [통계] 지난 2초 처리 20개 (누적 168개)
[INFO] [1788833872.072772919] [qos_subscriber]: #169 수신: 3.536
[INFO] [1788833872.170457343] [qos_subscriber]: #170 수신: 3.536
[INFO] [1788833872.270438834] [qos_subscriber]: #171 수신: 3.536
[INFO] [1788833872.372253779] [qos_subscriber]: #172 수신: 3.536
[INFO] [1788833872.470459516] [qos_subscriber]: #173 수신: 3.536
[INFO] [1788833872.570163019] [qos_subscriber]: #174 수신: 3.536
[INFO] [1788833872.670466672] [qos_subscriber]: #175 수신: 3.536
[INFO] [1788833872.770534511] [qos_subscriber]: #176 수신: 3.536
[INFO] [1788833872.870517799] [qos_subscriber]: #177 수신: 3.536
[INFO] [1788833872.970402847] [qos_subscriber]: #178 수신: 3.536
   ```
   
   ```
Files:             turtle_test_bag_0.db3
Bag size:          77.4 KiB
Storage id:        sqlite3
Duration:          12.148752456s
Start:             Sep  8 2026 11:09:30.649691992 (1788833370.649691992)
End:               Sep  8 2026 11:09:42.798444448 (1788833382.798444448)
Messages:          872
Topic information: Topic: /turtle_distance | Type: std_msgs/msg/Float32 | Count: 112 | Serialization Format: cdr
                   Topic: /turtle1/pose | Type: turtlesim/msg/Pose | Count: 760 | Serialization Format: cdr
   ```
   
   
4. **`pytest` 통과 출력** — 작성한 테스트 3개의 의도
   
   ```
build/turtle_py/pytest.xml: 3 tests, 0 errors, 0 failures, 0 skipped - turtle_py.test.test_calculator: - test_calculate_distance: PASSED - test_calculate_target_angle: PASSED - test_is_waypoint_reached: PASSED Summary: 3 tests, 0 errors, 0 failures, 0 skipped
   ```
   
   목표까지의 거리 검증, 목표 각도 및 정규화 검증, 경유점 도달 판정 및 허용 오차 검증
   
   

5. **함수를 틀리게 바꿨을 때 실패 출력**
   ㅁ
   ```
Summary: 1 package finished [0.51s]
  1 package had test failures: turtle_py
build/turtle_py/pytest.xml: 3 tests, 0 errors, 1 failure, 0 skipped
- turtle_py.test.test_calculator test_calculate_distance
  <<< failure message
    assert False
     +  where False = <built-in function isclose>(0.0, 5.0)
     +    where <built-in function isclose> = math.isclose
     +    and   0.0 = calculate_distance(0.0, 0.0, 3.0, 4.0)
  >>>
   ```
   
   
6. **예외 처리·logging 동작 확인**: `___`
   
   
   ```
# 0 나누기 방지를 위한 rate 예외 처리 및 logging

if raw_rate <= 0.0:

self.get_logger().error(

f'잘못된 publish_rate ({raw_rate} Hz)! 0 이하의 주기는 허용되지 않습니다. '

f'안전을 위해 기본값 (10.0 Hz)으로 자동 보정합니다.'

)

rate = 10.0

else:

rate = float(raw_rate)
   ```
   
   ```
ros2 run turtle_py qos_sensor_publisher --ros-args -p publish_rate:=0.0

[ERROR] [1788837774.060735246] [qos_sensor_publisher]: 잘못된 publish_rate (0.0 Hz)! 0 이하의 주기는 허용되지 않습니다. 안전을 위해 기본값 (10.0 Hz)으로 자동 보정합니다.
   ```
   
   
   