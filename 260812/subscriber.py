import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan

class VelocitySubscriber(Node):
    def __init__(self):
        super().__init__('velocity_subscriber')
        # 구독자 생성:                       (메시지타입, 토픽명, 콜백, 큐깊이)
        self.sub = self.create_subscription(Twist, '/cmd_vel', self.on_cmd, 10)
        self.sub1 = self.create_subscription(LaserScan, '/scan', self.on_scan, 10)
    def on_cmd(self, msg):       # 메시지가 올 때마다 호출
        self.get_logger().info(
            f'받음: 전진 x: {msg.linear.x:.2f} m/s, y: {msg.linear.y:.2f} m/s, 회전 {msg.angular.z:.2f} rad/s')

    def on_scan(self, msg):
        self.get_logger().info(
            f'받음: 레이저 스캔 데이터 {msg.ranges[0]:.2f}')

def main():
    rclpy.init()
    rclpy.spin(VelocitySubscriber())
    rclpy.shutdown()

if __name__ == '__main__':
    main()