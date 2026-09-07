import math
import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float32
from std_srvs.srv import SetBool, Trigger
from turtlesim.msg import Pose


class ServiceControlledNode(Node):

    def __init__(self):
        super().__init__('service_controlled_node')

        # 1. 파라미터 및 변수 초기화
        self.declare_parameter('start_enabled', True)
        self.declare_parameter('linear_speed', 1.0)
        self.declare_parameter('angular_speed', 0.5)

        self._enabled = self.get_parameter('start_enabled').value
        self._latest_pose = None
        self._home = None  # (x, y, theta) 저장용

        # 2. 구독자 및 발행자 생성
        self.pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self.pose_callback, 10
        )
        self.distance_pub = self.create_publisher(Float32, '/turtle_distance', 10)
        self.cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        # 3. 서비스 서버 생성
        # /enable_driving : SetBool - 주행 ON/OFF
        self.enable_srv = self.create_service(
            SetBool, 'enable_driving', self._on_enable_driving
        )
        # /save_home : Trigger - 현재 위치를 홈으로 저장
        self.save_home_srv = self.create_service(
            Trigger, 'save_home', self._on_save_home
        )

        # 4. 10Hz 타이머 생성 (0.1초)
        self.timer = self.create_timer(0.1, self.timer_callback)

        self.get_logger().info(
            f'ServiceControlledNode 시작 (주행 상태: {"ON" if self._enabled else "OFF"})'
        )

    def pose_callback(self, msg: Pose):
        # 최신 자세 수신 및 보관
        self._latest_pose = msg

    def _on_enable_driving(self, request: SetBool.Request, response: SetBool.Response):
        """SetBool 서비스 콜백: 플래그만 변경하여 서비스 응답 지연을 방지함"""
        self._enabled = request.data
        if not self._enabled:
            # 주행 중단 시 0 속도를 발행하여 즉시 정지시킴
            self.cmd_pub.publish(Twist())

        response.success = True
        response.message = f'Driving {"ENABLED" if self._enabled else "DISABLED"}'
        self.get_logger().info(f'/enable_driving 요청 수신 -> {response.message}')
        return response

    def _on_save_home(self, request: Trigger.Request, response: Trigger.Response):
        """Trigger 서비스 콜백: 현재 포즈를 홈 위치로 저장"""
        if self._latest_pose is None:
            response.success = False
            response.message = '아직 /turtle1/pose 데이터를 수신하지 못했습니다.'
        else:
            p = self._latest_pose
            self._home = (p.x, p.y, p.theta)
            response.success = True
            response.message = f'홈 위치 저장 완료: x={p.x:.2f}, y={p.y:.2f}, theta={p.theta:.2f}'

        self.get_logger().info(f'/save_home 요청 수신 -> {response.message}')
        return response

    def timer_callback(self):
        if self._latest_pose is None:
            return

        # 1. 원점에서의 유클리드 거리 계산 및 /turtle_distance 발행
        distance = math.sqrt(self._latest_pose.x**2 + self._latest_pose.y**2)
        dist_msg = Float32()
        dist_msg.data = float(distance)
        self.distance_pub.publish(dist_msg)

        # 2. SetBool이 false일 때는 cmd_vel 발행을 중단함
        if not self._enabled:
            return

        # SetBool이 true일 때만 cmd_vel 발행
        twist = Twist()
        twist.linear.x = self.get_parameter('linear_speed').value
        twist.angular.z = self.get_parameter('angular_speed').value
        self.cmd_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = ServiceControlledNode()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        print('\n[INFO] KeyboardInterrupt 수신 - 노드를 종료합니다.')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()