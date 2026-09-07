import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy)
from turtle_interfaces.msg import Waypoint, WaypointList


class WaypointPublisher(Node):

    def __init__(self):
        super().__init__('waypoint_publisher')

        # 1. 파라미터 선언 (transient_local | volatile)
        self.declare_parameter('durability', 'transient_local')
        self.declare_parameter('frame_id', 'world')

        durability_str = self.get_parameter('durability').value
        if durability_str == 'transient_local':
            durability = DurabilityPolicy.TRANSIENT_LOCAL
        elif durability_str == 'volatile':
            durability = DurabilityPolicy.VOLATILE
        else:
            raise ValueError(
                f'durability 파라미터는 transient_local 또는 volatile 이어야 합니다: {durability_str}'
            )

        # 2. Latched Topic용 QoS 프로필 조립
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=durability,
        )

        # 3. /waypoints 발행자 생성
        self._pub = self.create_publisher(WaypointList, 'waypoints', qos)

        # 4. 디스커버리 안정화를 위해 1초 후 1회 발행
        self._timer = self.create_timer(1.0, self._publish_once)

        self.get_logger().info(
            f'waypoint_publisher 시작: durability={durability_str}, '
            'reliability=reliable, depth=1 — 1초 뒤 1회 발행'
        )

    def _make_waypoint(self, x: float, y: float, tolerance: float, label: str) -> Waypoint:
        """Waypoint 커스텀 메시지 생성 헬퍼 함수"""
        wp = Waypoint()
        wp.x = float(x)
        wp.y = float(y)
        wp.tolerance = float(tolerance)
        wp.label = label
        return wp

    def _publish_once(self):
        """1회만 경유점 메시지를 발행하는 콜백"""
        self._timer.cancel()  # 타이머 해제 (1회 실행)

        msg = WaypointList()

        # Header 채우기
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.get_parameter('frame_id').value

        # 경유점 4개 추가 (turtlesim 11x11 좌표계 내 사각형 영역)
        msg.waypoints.append(self._make_waypoint(2.0, 2.0, 0.3, 'corner_A'))
        msg.waypoints.append(self._make_waypoint(9.0, 2.0, 0.3, 'corner_B'))
        msg.waypoints.append(self._make_waypoint(9.0, 9.0, 0.3, 'corner_C'))
        msg.waypoints.append(self._make_waypoint(2.0, 9.0, 0.3, 'corner_D'))

        self._pub.publish(msg)

        labels = [wp.label for wp in msg.waypoints]
        self.get_logger().info(
            f'/waypoints 발행 완료: {len(msg.waypoints)}개 {labels} '
            f'(frame_id={msg.header.frame_id})'
        )


def main(args=None):
    rclpy.init(args=args)
    node = WaypointPublisher()

    try:
        # 노드가 계속 실행 중이어야 TRANSIENT_LOCAL 메모리가 유지되어 늦게 뜬 구독자에게 전달됨
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('Ctrl+C — 정상 종료합니다')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()