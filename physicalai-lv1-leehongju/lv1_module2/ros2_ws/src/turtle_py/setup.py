import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'turtle_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Launch 파일 디렉터리 복사 설정
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        # Config (params.yaml) 디렉터리 복사 설정
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pa8',
    maintainer_email='kanichong1@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'pose_distance_node = turtle_py.pose_distance_node:main',
            'distance_warning_node = turtle_py.distance_warning_node:main',
            'polygon_drive_node = turtle_py.polygon_drive_node:main',
            'lifecycle_param_node = turtle_py.lifecycle_param_node:main',
            'builtin_service_client = turtle_py.builtin_service_client:main',
            'service_controlled_node = turtle_py.service_controlled_node:main',
            'toggle_servers = turtle_py.toggle_servers:main',
            'rotate_absolute_client = turtle_py.rotate_absolute_client:main',
            'polygon_action_server = turtle_py.polygon_action_server:main',
            'qos_subscriber = turtle_py.qos_subscriber:main',
            'turtle_distance_subscriber = turtle_py.qos_subscriber:main',     # launch 및 요구스펙용 매핑
            'qos_sensor_publisher = turtle_py.qos_sensor_publisher:main',
            'turtle_distance_publisher = turtle_py.qos_sensor_publisher:main', # launch 및 요구스펙용 매핑
            'waypoint_publisher = turtle_py.waypoint_publisher:main',
        ],
    },
)
