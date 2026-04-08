from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    package_name = 'online_asr'
    package_path = get_package_share_directory(package_name)
    
    return LaunchDescription([
        # 启动小海龟模拟器
        ExecuteProcess(
            cmd=['ros2', 'run', 'turtlesim', 'turtlesim_node'],
            output='screen'
        ),
        # 启动语音识别节点
        ExecuteProcess(
            cmd=['python3', '-u', os.path.join(package_path, 'python_asr', 'asr.py')],
            output='screen'
        ),
        # 启动语音控制节点
        Node(
            package='online_asr',
            executable='voice_control_node',
            name='voice_control_node',
            output='screen'
        ),
    ])
