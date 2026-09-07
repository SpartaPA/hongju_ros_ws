import math
import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
from turtlesim.msg import Pose
from turtle_interfaces.msg import WaypointList
from visualization_msgs.msg import Marker, MarkerArray


class TfMarkerPublisher(Node):

    def __init__(self):
        super().__init__('tf_marker_publisher')

        # 1. TF Broadcaster 생성
        self._tf_broadcaster = TransformBroadcaster(self)

        # 2. Topic Subscribers & Publishers
        self._pose_sub = self.create_subscription(Pose, '/turtle1/pose', self._on_pose, 10)
        self._waypoint_sub = self.create_subscription(WaypointList, '/waypoints', self._on_waypoints, 10)
        self._marker_pub = self.create_publisher(MarkerArray, '/waypoint_markers', 10)

        self.get_logger().info('TF & Waypoint Marker Publisher 노드 시작됨')

    def _on_pose(self, msg: Pose):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'world'
        t.child_frame_id = 'turtle1'

        t.transform.translation.x = float(msg.x)
        t.transform.translation.y = float(msg.y)
        t.transform.translation.z = 0.0

        # Euler angle (yaw = msg.theta) -> Quaternion 변환
        half_yaw = msg.theta * 0.5
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = math.sin(half_yaw)
        t.transform.rotation.w = math.cos(half_yaw)

        self._tf_broadcaster.sendTransform(t)

    def _on_waypoints(self, msg: WaypointList):
        marker_array = MarkerArray()

        for idx, wp in enumerate(msg.waypoints):
            marker = Marker()
            marker.header.frame_id = msg.header.frame_id if msg.header.frame_id else 'world'
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = 'waypoints'
            marker.id = idx
            marker.type = Marker.CYLINDER
            marker.action = Marker.ADD

            marker.pose.position.x = float(wp.x)
            marker.pose.position.y = float(wp.y)
            marker.pose.position.z = 0.0
            marker.pose.orientation.w = 1.0

            # 허용 오차(tolerance) 크기만큼 원기둥 지름 설정
            diameter = float(wp.tolerance) * 2.0
            marker.scale.x = diameter
            marker.scale.y = diameter
            marker.scale.z = 0.1

            # 초록색 투명 영역
            marker.color.r = 0.0
            marker.color.g = 1.0
            marker.color.b = 0.0
            marker.color.a = 0.5

            marker_array.markers.append(marker)

        self._marker_pub.publish(marker_array)


def main(args=None):
    rclpy.init(args=args)
    node = TfMarkerPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()