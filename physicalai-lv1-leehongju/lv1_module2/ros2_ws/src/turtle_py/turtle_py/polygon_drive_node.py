import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from std_srvs.srv import Empty


def normalize_angle(angle):
    """각도를 -pi ~ pi 범위로 정규화하는 함수"""
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


class polygon_drive_node(Node):

    def __init__(self):
        super().__init__('polygon_drive_node')

        # 발행자, 구독자, 서비스 클라이언트 생성
        self.cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self.pose_callback, 10
        )
        self.reset_client = self.create_client(Empty, '/reset')

        # P-제어 게인 (Gain) 설정
        self.kp_linear = 1.5   # 선속도 비례 게인
        self.kp_angular = 4.0  # 각속도 비례 게인

        # 허용 오차 (Tolerance) 설정
        self.dist_tolerance = 0.01  # 거리 허용 오차 (1cm)
        self.angle_tolerance = 0.005  # 각도 허용 오차 (약 0.3도)

        # 상태 및 제어 변수
        self.current_pose = None
        self.start_pose = None
        self.target_theta = 0.0
        self.target_dist = 1.0  # 한 변의 목표 거리 (1.0m)

        self.num_sides = 4
        self.side_count = 0
        self.state = 'IDLE'  # 'IDLE', 'MOVE', 'TURN'
        self.is_finished = False

        # 20Hz 제어 루프 타이머 (0.05초)
        self.timer = self.create_timer(0.05, self.control_loop)
        self.get_logger().info('Polygon Drive Node Initialized.')

    def pose_callback(self, msg: Pose):
        self.current_pose = msg

    def reset_turtlesim(self):
        if self.reset_client.wait_for_service(timeout_sec=2.0):
            req = Empty.Request()
            future = self.reset_client.call_async(req)
            rclpy.spin_until_future_complete(self, future)

    def start_polygon(self, num_sides: int):
        self.reset_turtlesim()
        self.num_sides = num_sides
        self.side_count = 0
        self.is_finished = False

        # 포즈 수신 대기
        while self.current_pose is None and rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)

        # 초기 상태 설정: 첫 번째 변 직진 준비
        self.start_pose = self.current_pose
        self.state = 'MOVE'
        self.get_logger().info(f'{self.num_sides}각형 P-제어 주행을 시작합니다.')

    def control_loop(self):
        if self.current_pose is None or self.state == 'IDLE':
            return

        msg = Twist()

        # N개의 변을 모두 완성한 경우
        if self.side_count >= self.num_sides:
            msg.linear.x = 0.0
            msg.angular.z = 0.0
            self.cmd_pub.publish(msg)
            self.get_logger().info(f'{self.num_sides}각형 주행 완성!')
            self.state = 'IDLE'
            self.is_finished = True
            return

        current_side_num = self.side_count + 1

        if self.state == 'MOVE':
            # 현재까지 직진 이동한 유클리드 거리 계산
            dx = self.current_pose.x - self.start_pose.x
            dy = self.current_pose.y - self.start_pose.y
            distance_traveled = math.sqrt(dx**2 + dy**2)

            # 거리 오차 계산 및 P-제어속도 산출
            dist_error = self.target_dist - distance_traveled

            if dist_error > self.dist_tolerance:
                msg.linear.x = min(self.kp_linear * dist_error, 1.5)  # 최대 속도 제한
                msg.angular.z = 0.0
            else:
                # 목표 거리 도달 -> 회전 상태로 전환
                msg.linear.x = 0.0
                self.cmd_pub.publish(msg)

                # 목표 각도 계산 (현재 각도 + 외각)
                ext_angle = (2.0 * math.pi) / self.num_sides
                self.target_theta = normalize_angle(self.current_pose.theta + ext_angle)
                self.state = 'TURN'
                self.get_logger().info(f'[{current_side_num}번째 변 도달] 회전 시작...')

        elif self.state == 'TURN':
            # 각도 오차 계산 (-pi ~ pi 범위로 정규화)
            angle_error = normalize_angle(self.target_theta - self.current_pose.theta)

            if abs(angle_error) > self.angle_tolerance:
                msg.linear.x = 0.0
                msg.angular.z = self.kp_angular * angle_error
            else:
                # 목표 각도 도달 -> 다음 변 직진 상태로 전환
                msg.angular.z = 0.0
                self.cmd_pub.publish(msg)

                self.side_count += 1
                self.start_pose = self.current_pose  # 직진 시작점 업데이트
                self.state = 'MOVE'
                self.get_logger().info(f'[{current_side_num}번째 회전 완료] 다음 변 직진...')

        self.cmd_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = polygon_drive_node()

    try:
        while rclpy.ok():
            user_input = input('\n다각형의 변의 개수를 입력하세요 (3 이상, 종료: q): ')
            if user_input.lower() == 'q':
                break

            try:
                num_sides = int(user_input)
                if num_sides < 3:
                    print('변의 개수는 최소 3개 이상이어야 합니다.')
                    continue
            except ValueError:
                print('올바른 숫자를 입력해 주세요.')
                continue

            node.start_polygon(num_sides)

            while rclpy.ok() and not node.is_finished:
                rclpy.spin_once(node, timeout_sec=0.05)

    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
