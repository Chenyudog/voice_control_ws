"""
一键启动：turtlesim 窗口 + 麦克风语音识别 + 根据语音控制海龟。

启动示例（务必把 model_path 换成你本机解压后的 Vosk 模型目录）：
  ros2 launch my_cmake_pkg turtle_voice_control.launch.py \\
    model_path:=/home/cyd/vosk-model-en-us-0.22-lgraph

launch 文件做的事可以概括为三步：
  1）声明「命令行可传哪些参数」（DeclareLaunchArgument）
  2）用 LaunchConfiguration 把这些参数转交给各个 Node 的 parameters
  3）启动多个 Node：仿真、识别、控制 —— 它们通过同一个话题名 speech_topic 对上号
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            # ------------------------------------------------------------------
            # 启动时可覆盖的参数（ros2 launch ...  xxx:=yyy）
            # ------------------------------------------------------------------
            DeclareLaunchArgument(
                'model_path',
		default_value='/home/cyd/cursor_ws/src/voice_interaction_pkg/model',
                description=(
                    'Vosk 模型目录的绝对路径（解压后的那一层文件夹）。'
                    '若留空，speech_echo_node 会报错退出，因为无法加载模型。'
                ),
            ),
            DeclareLaunchArgument(
                'max_linear',
                default_value='2.0',
                description=(
                    '海龟线速度绝对上限（m/s 量级，turtlesim 里数值不严格对应真实单位）。'
                    'turtle_voice_cmd_node 发出的 linear.x 不会超过该绝对值。'
                ),
            ),
            DeclareLaunchArgument(
                'max_angular',
                default_value='2.0',
                description='海龟角速度绝对上限（rad/s 量级，同上为仿真用数值）。',
            ),
            DeclareLaunchArgument(
                'speech_topic',
                default_value='speech_text',
                description=(
                    '识别文本发布的 ROS 话题名。speech_echo_node 发布、'
                    'turtle_voice_cmd_node 订阅，必须一致；默认都用 speech_text。'
                ),
            ),
            # ------------------------------------------------------------------
            # 节点 1：turtlesim 仿真器（弹出窗口，默认海龟名 turtle1）
            # ------------------------------------------------------------------
            Node(
                package='turtlesim',
                executable='turtlesim_node',
                name='turtlesim',
                output='screen',
            ),
            # ------------------------------------------------------------------
            # 节点 2：语音识别（内部会 popen 启动 Python+Vosk，结果发到 speech_topic）
            # ------------------------------------------------------------------
            Node(
                package='voice_interaction_pkg',
                executable='speech_echo_node',
                name='speech_recognition',
                output='screen',
                parameters=[
                    {
                        'model_path': LaunchConfiguration('model_path'),
                        'speech_topic': LaunchConfiguration('speech_topic'),
                    }
                ],
            ),
            # ------------------------------------------------------------------
            # 节点 3：订阅识别文字，解析口令，发布 cmd_vel / 调用 teleport
            # ------------------------------------------------------------------
            Node(
                package='my_cmake_pkg',
                executable='turtle_voice_cmd_node',
                name='turtle_voice_cmd',
                output='screen',
                parameters=[
                    {
                        'speech_topic': LaunchConfiguration('speech_topic'),
                        'max_linear': LaunchConfiguration('max_linear'),
                        'max_angular': LaunchConfiguration('max_angular'),
                        'turtle_name': 'turtle1',
                    }
                ],
            ),
        ]
    )
