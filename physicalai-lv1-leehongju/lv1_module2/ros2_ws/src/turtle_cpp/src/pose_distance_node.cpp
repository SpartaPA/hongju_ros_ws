#include <chrono>
#include <cmath>
#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32.hpp"
#include "turtlesim/msg/pose.hpp"

using namespace std::chrono_literals;

class PoseDistanceNode : public rclcpp::Node
{
public:
  PoseDistanceNode() : Node("pose_distance_node")
  {
    // /turtle1/pose 토픽 구독자 생성 (QoS Depth: 10)
    pose_sub_ = this->create_subscription<turtlesim::msg::Pose>(
      "/turtle1/pose", 10,
      std::bind(&PoseDistanceNode::pose_callback, this, std::placeholders::_1));

    // /turtle_distance 토픽 발행자 생성
    distance_pub_ = this->create_publisher<std_msgs::msg::Float32>("/turtle_distance", 10);

    // 10Hz 타이머 생성 (주기 100ms)
    timer_ = this->create_wall_timer(
      100ms, std::bind(&PoseDistanceNode::timer_callback, this));

    RCLCPP_INFO(this->get_logger(), "Pose Distance C++ Node Initialized.");
  }

private:
  void pose_callback(const turtlesim::msg::Pose::SharedPtr msg)
  {
    // 구독 콜백: 최신 자세 정보 저장만 수행
    latest_pose_ = msg;
  }

  void timer_callback()
  {
    // 수신된 자세 데이터가 없으면 진행하지 않음
    if (!latest_pose_) {
      return;
    }

    // 원점 (0,0)에서의 유클리드 거리 계산
    float distance = std::sqrt(
      std::pow(latest_pose_->x, 2) + std::pow(latest_pose_->y, 2));

    // Float32 메시지 생성 및 발행
    auto message = std_msgs::msg::Float32();
    message.data = distance;
    distance_pub_->publish(message);
  }

  rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr pose_sub_;
  rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr distance_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
  turtlesim::msg::Pose::SharedPtr latest_pose_{nullptr};
};

int main(int argc, char * argv[])
{
  // rclcpp 초기화
  rclcpp::init(argc, argv);

  // 노드 생성 및 실행 (spin)
  auto node = std::make_shared<PoseDistanceNode>();

  try {
    rclcpp::spin(node);
  } catch (const std::exception & e) {
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Shutdown cleanly.");
  }

  // 자원 해제 및 종료
  rclcpp::shutdown();
  return 0;
}