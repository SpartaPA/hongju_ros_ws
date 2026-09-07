cmake_minimum_required(VERSION 3.16)
project(Project2 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 헤더 위치
include_directories(include)
# target_link_libraries(robot PRIVATE rclcpp::rclcpp)  # 외부 라이브러리 (ROS2에서)

# 제동거리 계산 실행 파일
add_executable(stop_distance
    src/stop_distance.cpp
)

# 모터 제어 실행 파일 (main.cpp + motor.cpp)
add_executable(motor_app
    src/main.cpp
    src/motor.cpp
)

project(cpp_basics)

add_executable(sensor_app
    sensors/main.cpp
    sensors/sensor.cpp
    sensors/lidar.cpp
    sensors/imu.cpp
)