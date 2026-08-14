import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan

class VelocityPublisher(Node):
    def __init__(self):
        super().__init__('velocity_publisher')      # 노드 이름
        # 발행자 생성: (메시지타입, 토픽명, 큐깊이)
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        # 0.05초(20Hz)마다 tick 호출
        self.timer = self.create_timer(0.05, self.tick)
        self.get_logger().info('발행 시작')

    def tick(self):
        msg = Twist()
        msg.linear.x = 0.2      # 0.2 m/s 전진
        msg.linear.y = 0.3      # 0.3 m/s 측면 이동
        msg.angular.z = 0.1     # 약간 회전
        self.pub.publish(msg)
        self.get_logger().info(
            f'발행: 전진 x: {msg.linear.x:.2f} m/s, y: {msg.linear.y:.2f} m/s, 회전 {msg.angular.z:.2f} rad/s')
        msg1 = LaserScan()
        msg1.ranges = [0.2] * 1081  # 0.2 m/s 전진
        # msg1.ranges.linear.y = 0.3      # 0.3 m/s 측면 이동
        # msg1.ranges.angular.z = 0.1     # 약간 회전
        self.pub.publish(msg1)
        self.get_logger().info(
            f'발행: {msg1.ranges[0]:.2f}  {msg1.ranges[1]:.2f}  {msg1.angle_max:.2f} ')

def main():
    rclpy.init()
    node = VelocityPublisher()
    rclpy.spin(node)            # 콜백이 돌기 시작
    rclpy.shutdown()

if __name__ == '__main__':
    main()