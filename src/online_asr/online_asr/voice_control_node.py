# -*- coding: utf-8 -*-
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import sys
import os

# 添加 python_asr 目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../python_asr'))
from tts import TestTts, pcm2wav, play_audio
import time


class VoiceControlNode(Node):
    def __init__(self):
        super().__init__('voice_control_node')
        self.subscription = self.create_subscription(
            String,
            '/recognized_text',
            self.listener_callback,
            10
        )
        self.publisher_ = self.create_publisher(Twist, 'turtle1/cmd_vel', 10)
        self.feedback_publisher_ = self.create_publisher(String, '/voice_feedback', 10)
        self.get_logger().info('语音控制节点启动')

    def listener_callback(self, msg):
        text = msg.data
        self.get_logger().info(f'识别到: {text}')
        
        twist = Twist()
        
        if '前进' in text or '向前' in text:
            twist.linear.x = 1.0
            self.get_logger().info('执行: 前进')
            self.publish_feedback('好的，已执行前进')
        elif '停止' in text or '停' in text:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.get_logger().info('执行: 停止')
            self.publish_feedback('好的，已执行停止')
        elif '左转' in text or '左拐' in text:
            twist.angular.z = 1.0
            self.get_logger().info('执行: 左转')
            self.publish_feedback('好的，已执行左转')
        elif '右转' in text or '右拐' in text:
            twist.angular.z = -1.0
            self.get_logger().info('执行: 右转')
            self.publish_feedback('好的，已执行右转')
        
        self.publisher_.publish(twist)
    
    def publish_feedback(self, feedback):
        msg = String()
        msg.data = feedback
        self.feedback_publisher_.publish(msg)
        self.get_logger().info(f'反馈: {feedback}')
        # 使用阿里云 TTS 进行语音反馈
        self.speak_with_aliyun_tts(feedback)
    
    def speak_with_aliyun_tts(self, text):
        try:
            # 临时文件路径
            pcm_path = os.path.join(os.path.dirname(__file__), '../python_asr', 'temp_tts.pcm')
            wav_path = os.path.join(os.path.dirname(__file__), '../python_asr', 'temp_tts.wav')
            
            # 确保目录存在
            os.makedirs(os.path.dirname(pcm_path), exist_ok=True)
            
            # 开始语音合成
            self.get_logger().info(f'正在合成语音: {text}')
            t = TestTts("tts", pcm_path)
            t.start(text)
            
            # 等待合成结束
            time.sleep(1)
            
            # 转换为 WAV 并播放
            pcm2wav(pcm_path, wav_path)
            self.get_logger().info('正在播放反馈语音')
            play_audio(wav_path)
            
            # 清理临时文件
            if os.path.exists(pcm_path):
                os.remove(pcm_path)
            if os.path.exists(wav_path):
                os.remove(wav_path)
                
        except Exception as e:
            self.get_logger().error(f'语音合成失败: {str(e)}')


def main(args=None):
    rclpy.init(args=args)
    node = VoiceControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
