"""
仅启动「语音识别」节点 speech_echo_node（不启动 turtlesim、不控制海龟）。

用途：只想测试麦克风 + Vosk + 终端打印 / 话题发布时使用。

示例：
  ros2 launch voice_interaction_pkg voice_echo.launch.py \\
    model_path:=/home/cyd/vosk-model-en-us-0.22-lgraph

LaunchConfiguration('model_path')：把命令行传入的 model_path 交给节点的 ROS 参数，
C++ 里通过 declare_parameter("model_path") 读到同一路径。
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'model_path',
                default_value='/home/cyd/cursor_ws/src/voice_interaction_pkg/model/vosk-model-small-cn-0.22-lgraph',
                description=(
                    '解压后的 Vosk 模型绝对路径。留空则节点启动后会在日志里报错提示；'
                    '示例: ros2 launch voice_interaction_pkg voice_echo.launch.py '
                    'model_path:=/home/cyd/models/vosk-model-small-cn-0.22'
                ),
            ),
            Node(
                package='voice_interaction_pkg',
                executable='speech_echo_node',
                name='speech_echo',
                output='screen',
                parameters=[{'model_path': LaunchConfiguration('model_path')}],
            ),
        ]
    )
