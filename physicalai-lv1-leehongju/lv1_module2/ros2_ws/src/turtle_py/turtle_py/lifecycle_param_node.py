import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from turtlesim.msg import Pose


class LifecycleParamNode(Node):

    def __init__(self):
        super().__init__('lifecycle_param_node')

        # 파라미터 선언 (기본값 설정)
        self.declare_parameter('publish_rate', 10.0)  # 발행 주기 (Hz)
        self.declare_parameter('warn_distance', 2.5)  # 경고 임계값 (m)

        # 파라미터 값 읽기
        self.publish_rate = (
            self.get_parameter('publish_rate').get_parameter_value().double_value
        )
        self.warn_distance = (
            self.get_parameter('warn_distance').get_parameter_value().double_value
        )

        self.latest_pose = None

        # 구독자 및 발행자 생성
        self.pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self.pose_callback, 10
        )
        self.distance_pub = self.create_publisher(Float32, '/turtle_distance', 10)

        # 타이머 생성 (publish_rate 기반)
        timer_period = 1.0 / self.publish_rate
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info(
            f'노드 초기화 완료 (Publish Rate: {self.publish_rate}Hz, Warn Distance: {self.warn_distance}m)'
        )

    def pose_callback(self, msg: Pose):
        # 최신 자세 정보 저장
        self.latest_pose = msg

    def timer_callback(self):
        # 동적 파라미터 업데이트 확인 (실행 중 변경 반영)
        current_rate = (
            self.get_parameter('publish_rate').get_parameter_value().double_value
        )
        current_warn_dist = (
            self.get_parameter('warn_distance').get_parameter_value().double_value
        )

        # publish_rate가 동적으로 변경된 경우 타이머 주기 재설정
        if current_rate != self.publish_rate and current_rate > 0:
            self.publish_rate = current_rate
            self.timer.timer_period_ns = int((1.0 / self.publish_rate) * 1e9)
            self.get_logger().info(f'발행 주기가 {self.publish_rate}Hz 로 변경되었습니다.')

        self.warn_distance = current_warn_dist

        if self.latest_pose is None:
            return

        # 원점에서의 거리를 계산하여 발행
        distance = math.sqrt(self.latest_pose.x**2 + self.latest_pose.y**2)

        msg = Float32()
        msg.data = float(distance)
        self.distance_pub.publish(msg)

        # 경고 임계값 초과 시 로그 출력
        if distance > self.warn_distance:
            self.get_logger().warn(
                f'경고: 원점 거리 초과! (현재: {distance:.2f}m > 임계값: {self.warn_distance:.2f}m)'
            )


def main(args=None):    
    # ROS2 초기화
    rclpy.init(args=args)

    # 노드 생성
    node = LifecycleParamNode()

    try:
        # spin 실행 (이벤트 루프)
        rclpy.spin(node)
    except KeyboardInterrupt:
        # Ctrl+C 수신 시 출력 (logger는 이미 shutdown 중일 수 있음)
        print('\n[INFO] KeyboardInterrupt - 노드를 종료합니다.')
    finally:
        # 노드 자원 해제
        node.destroy_node()
        
        # ROS2 통신 종료
        # rclpy가 아직 shutdown되지 않은 경우에만 shutdown() 호출
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()