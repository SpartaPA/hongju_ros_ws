import math
import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float32
from std_srvs.srv import SetBool, Trigger
from turtlesim.msg import Pose
from turtlesim.srv import TeleportAbsolute
from rclpy.qos import qos_profile_sensor_data


class ToggleServers(Node):

    def __init__(self):
        super().__init__('toggle_servers')

        # 1. 파라미터 선언
        self.declare_parameter('start_enabled', False)
        self.declare_parameter('linear_speed', 1.0)
        self.declare_parameter('angular_speed', 0.8)

        self._enabled = self.get_parameter('start_enabled').value
        self._latest_pose = None
        self._home = None  # (x, y, theta) 저장용

        # 2. 구독자 및 발행자 생성
        self._pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self._on_pose, 10
        )
        self._distance_pub = self.create_publisher(
            Float32, '/turtle_distance', qos_profile_sensor_data)
        self._cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        # 3. 서비스 서버 및 클라이언트 생성
        self._enable_srv = self.create_service(
            SetBool, 'enable_driving', self._on_enable_driving
        )
        self._save_srv = self.create_service(
            Trigger, 'save_home', self._on_save_home
        )
        self._go_home_srv = self.create_service(
            Trigger, 'go_home', self._on_go_home
        )

        # go_home 서비스 구현을 위한 internal 클라이언트 (/turtle1/teleport_absolute)
        self._teleport_cli = self.create_client(
            TeleportAbsolute, '/turtle1/teleport_absolute'
        )

        # 4. 10Hz 제어/발행 타이머 (0.1초)
        self._timer = self.create_timer(0.1, self._on_timer)

        self.get_logger().info(
            f'toggle_servers 노드가 시작되었습니다. (주행 상태: {"ON" if self._enabled else "OFF"})'
        )
        self.get_logger().info('제공 서비스: /enable_driving , /save_home , /go_home')

    def _on_pose(self, msg: Pose):
        self._latest_pose = msg

    def _on_timer(self):
        if self._latest_pose is None:
            return

        # 1) /turtle_distance 토픽 발행 (문제 3 규격)
        distance = math.sqrt(self._latest_pose.x**2 + self._latest_pose.y**2)
        dist_msg = Float32()
        dist_msg.data = float(distance)
        self._distance_pub.publish(dist_msg)

        # 2) SetBool 이 false 면 cmd_vel 발행을 중단함
        if not self._enabled:
            return

        # SetBool 이 true 일 때만 속도 토픽 발행
        twist = Twist()
        twist.linear.x = self.get_parameter('linear_speed').value
        twist.angular.z = self.get_parameter('angular_speed').value
        self._cmd_pub.publish(twist)

    def _on_enable_driving(self, request: SetBool.Request, response: SetBool.Response):
        """SetBool 서비스 콜백: 플래그만 변경하여 서비스 응답 지연을 방지함"""
        self._enabled = request.data

        if not self._enabled:
            # 주행 비활성화 시 0 속도를 1회 발행하여 즉시 정지시킴
            self._cmd_pub.publish(Twist())

        response.success = True
        response.message = f'driving {"enabled" if self._enabled else "disabled"}'

        self.get_logger().info(f'[Service Request] /enable_driving -> data={request.data}')
        self.get_logger().info(
            f'[Service Response] /enable_driving -> success={response.success}, message="{response.message}"'
        )
        return response

    def _on_save_home(self, request: Trigger.Request, response: Trigger.Response):
        """Trigger 서비스 콜백: 현재 포즈를 홈 위치로 저장"""
        self.get_logger().info('[Service Request] /save_home')

        if self._latest_pose is None:
            response.success = False
            response.message = '아직 /turtle1/pose 를 받지 못해 홈을 저장할 수 없습니다'
        else:
            p = self._latest_pose
            self._home = (p.x, p.y, p.theta)
            response.success = True
            response.message = f'home saved: x={p.x:.2f}, y={p.y:.2f}, theta={p.theta:.2f}'

        self.get_logger().info(
            f'[Service Response] /save_home -> success={response.success}, message="{response.message}"'
        )
        return response

    def _on_go_home(self, request: Trigger.Request, response: Trigger.Response):
        """Trigger 서비스 콜백: 저장된 홈 위치로 비동기 이동 (데드락 방지 패턴)"""
        self.get_logger().info('[Service Request] /go_home')

        if self._home is None:
            response.success = False
            response.message = '저장된 홈이 없습니다. 먼저 /save_home 을 호출하세요'
            self.get_logger().warn(f'[Service Response] /go_home -> {response.message}')
            return response

        if not self._teleport_cli.service_is_ready():
            response.success = False
            response.message = '/turtle1/teleport_absolute 서버가 준비되지 않았습니다'
            self.get_logger().error(f'[Service Response] /go_home -> {response.message}')
            return response

        # 비동기 요청 전송 (call_async)
        req = TeleportAbsolute.Request()
        req.x, req.y, req.theta = self._home
        future = self._teleport_cli.call_async(req)

        # 결과 콜백 등록 (add_done_callback) -> 스레드를 차단하지 않고 즉시 응답 반환
        future.add_done_callback(self._on_teleport_done)

        response.success = True
        response.message = f'teleport 요청 전송 완료: ({req.x:.2f}, {req.y:.2f}, {req.theta:.2f})'
        self.get_logger().info(
            f'[Service Response] /go_home -> success={response.success}, message="{response.message}"'
        )
        return response

    def _on_teleport_done(self, future):
        """teleport 비동기 응답 처리 콜백 (Executor가 별도 실행하므로 데드락 없음)"""
        if future.exception() is not None:
            self.get_logger().error(f'teleport 실패: {future.exception()}')
        else:
            self.get_logger().info('teleport 완료 — 저장된 홈 위치로 성공적으로 이동했습니다')


def main(args=None):
    rclpy.init(args=args)
    node = ToggleServers()

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
