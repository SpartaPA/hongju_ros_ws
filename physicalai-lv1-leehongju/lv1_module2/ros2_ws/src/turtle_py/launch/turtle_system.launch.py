import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def _system_nodes(package, pub_exec, sub_exec, action_exec, params_file, condition):
    """상태 발행자 + 경고 구독자 + 액션 서버 3개 노드를 공통 조건으로 생성"""
    return [
        Node(
            package=package,
            executable=pub_exec,
            name='turtle_distance_publisher',  # params.yaml 최상위 키와 일치해야 파라미터 주입됨
            parameters=[params_file],
            output='screen',
            condition=condition,
        ),
        Node(
            package=package,
            executable=sub_exec,
            name='turtle_distance_subscriber',
            parameters=[params_file],
            output='screen',
            condition=condition,
        ),
        Node(
            package=package,
            executable=action_exec,
            name='polygon_action_server',
            parameters=[params_file],
            output='screen',
            condition=condition,
        ),
    ]


def _second_publisher(package, pub_exec, params_file, condition):
    """네임스페이스 /turtle2 로 띄우는 두 번째 상태 발행자"""
    return Node(
        package=package,
        executable=pub_exec,
        name='turtle_distance_publisher',
        namespace='turtle2',
        remappings=[
            ('turtle1/pose', '/turtle2/pose'),          # 상대 이름 대응
            ('/turtle1/pose', '/turtle2/pose'),         # 절대 이름 대응
            ('/turtle_distance', 'turtle_distance'),    # 절대 이름을 상대 이름으로 되돌려 ns 적용
        ],
        parameters=[params_file],
        output='screen',
        condition=condition,
    )


def generate_launch_description():
    # 패키지 share 디렉터리 탐색 (기본 params.yaml 경로 설정)
    pkg_share = get_package_share_directory('turtle_py')
    default_params = os.path.join(pkg_share, 'config', 'params.yaml')

    # ---------- 1. Launch 인자 선언 ----------
    use_examples_arg = DeclareLaunchArgument(
        'use_examples', default_value='false',
        description='true 지정 시 turtle_examples 노드 실행, false 지정 시 student_package 실행')
    
    spawn_second_arg = DeclareLaunchArgument(
        'spawn_second', default_value='false',
        description='true 지정 시 turtle2를 생성하고 네임스페이스 /turtle2로 발행자 추가 실행')
    
    params_file_arg = DeclareLaunchArgument(
        'params_file', default_value=default_params,
        description='노드 파라미터 YAML 파일 절대 경로')
    
    student_pkg_arg = DeclareLaunchArgument(
        'student_package', default_value='turtle_py',
        description='학생 패키지 이름')
    
    student_action_arg = DeclareLaunchArgument(
        'student_action_exec', default_value='polygon_action_server',
        description='학생 패키지의 DrawPolygon 액션 서버 실행파일 이름')

    # LaunchConfiguration 변수 바인딩
    use_examples = LaunchConfiguration('use_examples')
    spawn_second = LaunchConfiguration('spawn_second')
    params_file = LaunchConfiguration('params_file')
    student_pkg = LaunchConfiguration('student_package')
    student_action = LaunchConfiguration('student_action_exec')

    # ---------- 2. Turtlesim 시뮬레이터 노드 ----------
    turtlesim = Node(
        package='turtlesim',
        executable='turtlesim_node',
        name='turtlesim',
        output='screen',
    )

    # ---------- 3. 메인 시스템 노드 3종 (조건 분기) ----------
    example_nodes = _system_nodes(
        package='turtle_examples',
        pub_exec='ex03_distance_publisher',
        sub_exec='ex03_distance_subscriber',
        action_exec='ex06_polygon_action_server',
        params_file=params_file,
        condition=IfCondition(use_examples),
    )

    student_nodes = _system_nodes(
        package=student_pkg,
        pub_exec='turtle_distance_publisher',
        sub_exec='turtle_distance_subscriber',
        action_exec=student_action,
        params_file=params_file,
        condition=UnlessCondition(use_examples),
    )

    # ---------- 4. turtle2 생성 및 두 번째 발행자 노드 ----------
    # turtlesim 노드 부팅 후 서비스 준비 시간을 벌기 위해 2초 후 call /spawn 실행
    spawn_turtle2 = TimerAction(
        period=2.0,
        actions=[ExecuteProcess(
            cmd=['ros2', 'service', 'call', '/spawn', 'turtlesim/srv/Spawn',
                 "{x: 2.0, y: 2.0, theta: 0.0, name: 'turtle2'}"],
            output='screen',
        )],
        condition=IfCondition(spawn_second),
    )

    # 복합 조건 검사 (spawn_second AND use_examples)
    both_true_examples = PythonExpression([
        "'", spawn_second, "'.lower() in ('true', '1') and '", use_examples, "'.lower() in ('true', '1')"
    ])
    both_true_student = PythonExpression([
        "'", spawn_second, "'.lower() in ('true', '1') and '", use_examples, "'.lower() not in ('true', '1')"
    ])

    second_pub_example = _second_publisher(
        'turtle_examples', 'ex03_distance_publisher', params_file, IfCondition(both_true_examples)
    )
    second_pub_student = _second_publisher(
        student_pkg, 'turtle_distance_publisher', params_file, IfCondition(both_true_student)
    )

    return LaunchDescription([
        use_examples_arg,
        spawn_second_arg,
        params_file_arg,
        student_pkg_arg,
        student_action_arg,
        LogInfo(msg=['적용 중인 params_file 경로: ', params_file]),
        turtlesim,
        *example_nodes,
        *student_nodes,
        spawn_turtle2,
        second_pub_example,
        second_pub_student,
    ])