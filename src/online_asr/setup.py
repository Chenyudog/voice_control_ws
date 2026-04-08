from setuptools import find_packages, setup
import os
from glob import glob  # <-- 加这一行
package_name = 'online_asr'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), ['launch/online_asr.launch.py']),
        (os.path.join('share', package_name, 'launch'), ['launch/voice_control.launch.py']),
        (os.path.join('share', package_name, 'launch'), ['launch/voice_control_with_feedback.launch.py']),
        (os.path.join('share', package_name, 'python_asr'), glob(os.path.join('python_asr', '*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='cyd',
    maintainer_email='cyd@todo.todo',
    description='阿里云实时语音识别功能包',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'asr_node = online_asr.asr_node:main',
            'voice_control_node = online_asr.voice_control_node:main',
        ],
    },
)
