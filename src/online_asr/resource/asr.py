# -*- coding: utf-8 -*-
import time
import queue
import sounddevice as sd
import numpy as np
import nls
import sys

# 阿里云配置信息
URL = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
TOKEN = "a165274824e94ee3b3ea9d670e7d655d"  # 参考https://help.aliyun.com/document_detail/450255.html获取token
APPKEY = "zvNV8ngJlGovddWG"  # 获取Appkey请前往控制台：https://nls-portal.console.aliyun.com/applist

# Queue to hold the recorded audio data
audio_queue = queue.Queue()
speaker_queue = queue.Queue()


# Callback function to capture audio data from microphone
def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(indata.copy())


# Callback function to capture audio data from speaker
def speaker_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    speaker_queue.put(indata.copy())


class RealTimeSpeechRecognizer:
    def __init__(self, url, token, appkey, name):
        self.url = url
        self.token = token
        self.appkey = appkey
        self.name = name
        self.transcriber = None
        self.__initialize_transcriber()

    def __initialize_transcriber(self):
        self.transcriber = nls.NlsSpeechTranscriber(
            url=self.url,
            token=self.token,
            appkey=self.appkey,
            on_sentence_begin=self.on_sentence_begin,
            on_sentence_end=self.on_sentence_end,
            on_start=self.on_start,
            on_result_changed=self.on_result_changed,
            on_completed=self.on_completed,
            on_error=self.on_error,
            on_close=self.on_close,
            callback_args=[self.name]
        )
        self.transcriber.start(aformat="pcm", enable_intermediate_result=True,
                               enable_punctuation_prediction=True, enable_inverse_text_normalization=True)

    def send_audio(self, audio_data):
        if self.transcriber:
            self.transcriber.send_audio(audio_data)

    def stop_transcription(self):
        if self.transcriber:
            self.transcriber.stop()

    def on_sentence_begin(self, message, *args):
        print(f"{self.name} 过程中的对话: {message}")

    def on_sentence_end(self, message, *args):
        print(f"{self.name} 完整的对话: {message}")

    def on_start(self, message, *args):
        print(f"{self.name} Start: {message}")

    def on_result_changed(self, message, *args):
        print(f"{self.name} Result changed: {message}")

    def on_completed(self, message, *args):
        print(f"{self.name} Completed: {message}")

    def on_error(self, message, *args):
        print(f"{self.name} Error: {message}")

    def on_close(self, *args):
        print(f"{self.name} Closed: {args}")


# 调用阿里云的语音转文字的接口
def recognize_speech(audio_data, recognizer):
    audio_data = np.concatenate(audio_data)
    recognizer.send_audio(audio_data.tobytes())


# Start the audio stream and process audio data
# Start the audio stream and process audio data
def start_audio_stream(mic_recognizer, speaker_recognizer, speaker_device_index):
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=16000, dtype='int16') as mic_stream, \
            sd.InputStream(callback=speaker_callback, channels=1, samplerate=16000, dtype='int16',
                           device=speaker_device_index) as spk_stream:
        print("🎤 开始说话，实时识别中...")
        try:
            while True:
                # 实时发送麦克风数据
                while not audio_queue.empty():
                    data = audio_queue.get()
                    mic_recognizer.send_audio(data.tobytes())

                # 实时发送扬声器数据
                while not speaker_queue.empty():
                    data = speaker_queue.get()
                    speaker_recognizer.send_audio(data.tobytes())

                time.sleep(0.01)
        except KeyboardInterrupt:
            print("Stopping audio recording.")
            mic_recognizer.stop_transcription()
            speaker_recognizer.stop_transcription()


if __name__ == "__main__":
    speaker_device_index = 8  # 使用 pulse 设备（索引 8）来捕获扬声器输出

    mic_recognizer = RealTimeSpeechRecognizer(URL, TOKEN, APPKEY, "调解人员说：")
    speaker_recognizer = RealTimeSpeechRecognizer(URL, TOKEN, APPKEY, "当事人说：")

    start_audio_stream(mic_recognizer, speaker_recognizer, speaker_device_index)

