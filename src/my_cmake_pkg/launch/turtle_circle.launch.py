"""
同时启动 turtlesim 与 circle_turtle_node，让小海龟自动画圆。

流程：
  1) turtlesim_node：打开仿真窗口，提供 /turtle1/cmd_vel 等接口
  2) circle_turtle_node：按 20Hz 向 cmd_vel 发布固定的 linear.x 与 angular.z

命令行可改圆的大小/快慢（传给节点的 ROS 参数）：
  ros2 launch my_cmake_pkg turtle_circle.launch.py linear_speed:=1.5 angular_speed:=0.8
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'linear_speed',
                default_value='1.0',
                description='画圆时的前进速度，对应 Twist.linear.x。',
            ),
            DeclareLaunchArgument(
                'angular_speed',
                default_value='1.0',
                description='画圆时的角速度，对应 Twist.angular.z。',
            ),
            Node(
                package='turtlesim',
                executable='turtlesim_node',
                name='turtlesim',
                output='screen',
            ),
            Node(
                package='my_cmake_pkg',
                executable='circle_turtle_node',
                name='circle_turtle',
                output='screen',
                parameters=[
                    {
                        'linear_speed': LaunchConfiguration('linear_speed'),
                        'angular_speed': LaunchConfiguration('angular_speed'),
                    }
                ],
            ),
        ]
    )
