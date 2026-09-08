import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32


class DistanceWarningNode(Node):

    def __init__(self):
        super().__init__('distance_warning_node')

        # 거리 임계값 파라미터 선언 및 기본값(2.5) 설정
        self.declare_parameter('threshold', 2.5)
        self.threshold = (
            self.get_parameter('threshold').get_parameter_value().double_value
        )

        # /turtle_distance 토픽 구독자 생성
        self.distance_sub = self.create_subscription(
            Float32, '/turtle_distance', self.distance_callback, 10
        )

        self.get_logger().info(
            f'Distance Warning Node initialized. (Threshold: {self.threshold:.2f}m)'
        )

    def distance_callback(self, msg: Float32):
        distance = msg.data

        # 거리가 임계값을 넘으면 경고 로그 출력
        if distance > self.threshold:
            self.get_logger().warn(
                f'Distance exceeded threshold! Current: {distance:.2f}m > Threshold: {self.threshold:.2f}m'
            )
        else:
            self.get_logger().info(f'Current Distance: {distance:.2f}m')
        
    def _validate_and_set_rate(self, rate_val: float) -> float:
        """publish_rate 파라미터 유효성 검증 및 예외 처리"""
        if rate_val <= 0.0:
            self.get_logger().error(
                f'잘못된 publish_rate ({rate_val} Hz)! 0 이하의 주기는 허용되지 않습니다. '
                f'안전을 위해 기본값 (1.0 Hz)으로 자동 보정합니다.'
                )
            return 1.0
        return rate_val


def main(args=None):
    rclpy.init(args=args)
    node = DistanceWarningNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
