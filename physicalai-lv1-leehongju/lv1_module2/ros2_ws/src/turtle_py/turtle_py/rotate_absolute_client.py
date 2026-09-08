import argparse
import math
import sys

import rclpy
from action_msgs.msg import GoalStatus
from action_msgs.srv import CancelGoal
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy)
from rclpy.utilities import remove_ros_args
from turtlesim.action import RotateAbsolute
from turtlesim.msg import Pose

STATUS_NAME = {
    GoalStatus.STATUS_SUCCEEDED: 'SUCCEEDED',
    GoalStatus.STATUS_CANCELED: 'CANCELED',
    GoalStatus.STATUS_ABORTED: 'ABORTED',
}


class RotateAbsoluteClient(Node):

    def __init__(self, target_theta: float, cancel_after: float = None):
        super().__init__('rotate_absolute_client')
        self._target = target_theta
        self._cancel_after = cancel_after  # 지정 시간 후 취소 요청용

        # /turtle1/rotate_absolute 액션 클라이언트 생성
        self._client = ActionClient(self, RotateAbsolute, 'turtle1/rotate_absolute')

        # 현재 각도 확인 및 취소 시점 좌표 기록용 Pose 구독
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )
        self._pose_sub = self.create_subscription(
            Pose, 'turtle1/pose', self._on_pose, qos
        )

        self._latest_theta = None
        self._goal_handle = None
        self._cancel_timer = None
        self.done = False  # 메인 spin_once 루프 종료 플래그

    def _on_pose(self, msg: Pose):
        self._latest_theta = msg.theta

    def send_goal(self):
        if not self._client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error(
                '액션 서버 /turtle1/rotate_absolute 가 없습니다 (turtlesim 실행 중?)'
            )
            self.done = True
            return

        goal = RotateAbsolute.Goal()
        goal.theta = float(self._target)

        self.get_logger().info(
            f'Goal 전송: theta = {goal.theta:.3f} rad (현재 theta = {self._latest_theta})'
        )

        # 1단계: send_goal_async 호출 (피드백 콜백 수신 등록)
        send_future = self._client.send_goal_async(
            goal, feedback_callback=self._on_feedback
        )
        send_future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal 이 거절되었습니다.')
            self.done = True
            return

        self.get_logger().info('Goal 수락됨 — 회전 및 피드백 수신 시작')
        self._goal_handle = goal_handle

        # 2단계: get_result_async 호출
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_result)

        # --cancel-after 옵션이 지정된 경우 타이머 생성
        if self._cancel_after is not None:
            self._cancel_timer = self.create_timer(
                self._cancel_after, self._on_cancel_timer
            )

    def _on_feedback(self, feedback_msg):
        # 피드백 주기적 수신 로그 출력 (remaining 감소 흐름 확인)
        remaining = feedback_msg.feedback.remaining
        self.get_logger().info(
            f'피드백: remaining = {remaining:+.3f} rad',
            throttle_duration_sec=0.25,
        )

    def _on_cancel_timer(self):
        self._cancel_timer.cancel()
        theta_at_cancel = self._latest_theta
        self.get_logger().warn(
            f'취소 요청 전송 (요청 시점 theta = {theta_at_cancel:.3f} rad)'
        )

        # 3단계: cancel_goal_async 호출
        cancel_future = self._goal_handle.cancel_goal_async()
        cancel_future.add_done_callback(
            lambda f: self._on_cancel_response(f, theta_at_cancel)
        )

    def _on_cancel_response(self, future, theta_at_cancel):
        resp = future.result()
        if resp.return_code == CancelGoal.Response.ERROR_NONE and len(resp.goals_canceling) > 0:
            self.get_logger().warn(
                f'취소 수락됨 (서버가 중단 처리 중). 취소 시점 theta = {theta_at_cancel:.3f} rad'
            )
        else:
            self.get_logger().error(f'취소 거절: return_code={resp.return_code}')

    def _on_result(self, future):
        wrapped = future.result()
        status = wrapped.status
        result = wrapped.result
        name = STATUS_NAME.get(status, str(status))

        self.get_logger().info(
            f'결과 수신: status={name}, delta={result.delta:+.3f} rad, 현재 theta={self._latest_theta:.3f}'
        )
        # 콜백 내에서 shutdown 하지 않고 메인 루프 탈출용 플래그만 세움
        self.done = True


def main(args=None):
    rclpy.init(args=args)

    parser = argparse.ArgumentParser(
        description='turtlesim RotateAbsolute action client'
    )
    parser.add_argument(
        '--theta',
        type=float,
        default=math.pi / 2,
        help='목표 절대 각도 [rad] (기본 pi/2)',
    )
    parser.add_argument(
        '--cancel-after',
        type=float,
        default=None,
        help='이 시간[초] 뒤 취소 요청 전송 (기본 None)',
    )
    cli = parser.parse_args(remove_ros_args(sys.argv)[1:])

    node = RotateAbsoluteClient(cli.theta, cli.cancel_after)

    try:
        node.send_goal()
        # spin_once 루프: done 플래그 세워지면 루프 탈출 후 안전 종료
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('Ctrl+C — 중단합니다')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
