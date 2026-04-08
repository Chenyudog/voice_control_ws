from launch import LaunchDescription
from launch.actions import ExecuteProcess
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    # 自动找到功能包路径 + 你的 asr.py
    package_name = 'online_asr'
    package_path = get_package_share_directory(package_name)
    
    # 关键：直接用 python3 运行！
    script_path = os.path.join(
        package_path, 'python_asr', 'asr.py'
    )

    return LaunchDescription([
        ExecuteProcess(
            cmd=['python3', '-u', '/home/cyd/cursor_ws/src/online_asr/python_asr/asr.py'],
            output='screen'
        )
    ])