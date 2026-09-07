cmake_minimum_required(VERSION 3.8)
project(turtle_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(turtlesim REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# Executable 타겟 추가
add_executable(pose_distance_node src/pose_distance_node.cpp)
# 실행 타겟에 헤더 경로 및 의존성 연결
ament_target_dependencies(pose_distance_node
  rclcpp
  std_msgs
  turtlesim
)

# Distance Subscriber 노드
add_executable(distance_subscriber_node src/distance_subscriber_node.cpp)
ament_target_dependencies(distance_subscriber_node
  rclcpp
  std_msgs
)

# Install 규칙 추가 (ros2 run 명령어를 통해 실행 가능하도록 설정)
install(TARGETS
  pose_distance_node
  distance_subscriber_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
