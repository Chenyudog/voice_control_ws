# -*- coding: utf-8 -*-
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import pyttsx3


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
        self.engine = pyttsx3.init()
        # 设置语速适中
        self.engine.setProperty('rate', 130)
        # 设置音量最大
        self.engine.setProperty('volume', 1.0)
        # 尝试设置中文语音
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'zh' in voice.id or 'chinese' in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                break
        self.get_logger().info('语音控制节点启动')

    def listener_callback(self, msg):
        text = msg.data.lower()
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
        # 语音反馈
        self.engine.say(feedback)
        self.engine.runAndWait()


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
