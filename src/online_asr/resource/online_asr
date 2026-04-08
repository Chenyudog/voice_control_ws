# -*- coding: utf-8 -*-
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time
import queue
import sounddevice as sd
import numpy as np
import nls
import json
import sys

class OnlineASRNode(Node):
    def __init__(self):
        super().__init__('asr_node')
        self.get_logger().info("✅ 语音识别已启动")

        # 阿里云配置
        self.URL = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
        self.TOKEN = "14fcd008c94f422382b591816b1cdd74"
        self.APPKEY = "zvNV8ngJlGovddWG"

        self.publisher_ = self.create_publisher(String, "/recognized_text", 10)
        self.audio_queue = queue.Queue()
        self.start_recognizer()

    def audio_callback(self, indata, frames, time, status):
        self.audio_queue.put(indata.copy())

    def on_result(self, message, *args):
        try:
            data = json.loads(message)
            text = data["payload"]["result"]
            self.get_logger().info(f"> {text}")
            msg = String()
            msg.data = text
            self.publisher_.publish(msg)
        except:
            pass

    def start_recognizer(self):
        self.recognizer = nls.NlsSpeechTranscriber(
            url=self.URL,
            token=self.TOKEN,
            appkey=self.APPKEY,
            on_sentence_end=self.on_result,
        )
        self.recognizer.start(
            aformat="pcm",
            sample_rate=16000,
            enable_intermediate_result=True,
            enable_punctuation_prediction=True,
            enable_inverse_text_normalization=True
        )

        self.stream = sd.InputStream(
            callback=self.audio_callback,
            channels=1,
            samplerate=16000,
            dtype='int16'
        )
        self.stream.start()

        self.create_timer(0.01, self.send_audio)

    def send_audio(self):
        while not self.audio_queue.empty():
            data = self.audio_queue.get()
            self.recognizer.send_audio(data.tobytes())

def main(args=None):
    rclpy.init(args=args)
    node = OnlineASRNode()
    rclpy.spin(node)

if __name__ == '__main__':
    main()