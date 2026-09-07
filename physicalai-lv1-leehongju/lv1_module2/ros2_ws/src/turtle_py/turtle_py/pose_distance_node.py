import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
from turtlesim.msg import Pose


class PoseDistanceNode(Node):

    def __init__(self):
        super().__init__('pose_distance_node')

        # 최신 자세 정보를 보관할 변수
        self.latest_pose = None

        # /turtle1/pose 토픽 구독자 생성
        self.pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self.pose_callback, 10
        )

        # /turtle_distance 토픽 발행자 생성
        self.distance_pub = self.create_publisher(Float32, '/turtle_distance', 10)

        # 10Hz 발행을 위한 타이머 생성 (주기 0.1초)
        self.timer = self.create_timer(0.1, self.timer_callback)

    def pose_callback(self, msg: Pose):
        # 구독 콜백: 최신 자세 저장만 수행
        self.latest_pose = msg

    def timer_callback(self):
        # 수신된 자세 데이터가 없으면 진행하지 않음
        if self.latest_pose is None:
            return

        # 원점 (0,0)에서의 유클리드 거리 계산
        distance = math.sqrt(self.latest_pose.x**2 + self.latest_pose.y**2)

        # Float32 메시지 생성 및 발행
        msg = Float32()
        msg.data = float(distance)
        self.distance_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = PoseDistanceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()