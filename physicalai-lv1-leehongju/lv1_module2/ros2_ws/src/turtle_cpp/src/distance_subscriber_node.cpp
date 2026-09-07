#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32.hpp"

class DistanceSubscriberNode : public rclcpp::Node
{
public:
  DistanceSubscriberNode() : Node("distance_subscriber_node")
  {
    // /turtle_distance 토픽 구독자 생성 (std_msgs/msg/Float32)
    sub_ = this->create_subscription<std_msgs::msg::Float32>(
      "/turtle_distance", 10,
      std::bind(&DistanceSubscriberNode::distance_callback, this, std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(), "C++ Distance Subscriber Node Initialized.");
  }

private:
  void distance_callback(const std_msgs::msg::Float32::SharedPtr msg) const
  {
    RCLCPP_INFO(this->get_logger(), "Received Turtle Distance [C++ Sub]: %.2f m", msg->data);
  }

  rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr sub_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<DistanceSubscriberNode>();

  try {
    rclcpp::spin(node);
  } catch (const std::exception & e) {
    RCLCPP_INFO(rclcpp::get_logger("rclcpp"), "Shutdown cleanly.");
  }

  rclcpp::shutdown();
  return 0;
}