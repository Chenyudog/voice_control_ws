# -*- coding: utf-8 -*-
import nls
import time
import threading
import os
import wave
import subprocess

URL = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
TOKEN = "a165274824e94ee3b3ea9d670e7d655d"
APPKEY = "zvNV8ngJlGovddWG"

TEXT = '大壮正想去摘取花瓣，谁知阿丽和阿强突然内讧，阿丽拿去手枪向树干边的阿强射击，两声枪响，阿强直接倒入水中'

# PCM 转 WAV
def pcm2wav(pcm_path, wav_path):
    with open(pcm_path, 'rb') as pcmfile:
        pcmdata = pcmfile.read()
    with wave.open(wav_path, 'wb') as wavfile:
        wavfile.setparams((1, 2, 16000, 0, 'NONE', 'NONE'))
        wavfile.writeframes(pcmdata)

# 播放 WAV
def play_audio(wav_path):
    subprocess.run(["aplay", wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

class TestTts:
    def __init__(self, tid, test_file):
        self.__th = threading.Thread(target=self.__test_run)
        self.__id = tid
        self.__test_file = test_file

    def start(self, text):
        self.__text = text
        output_dir = os.path.dirname(self.__test_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.__f = open(self.__test_file, "wb")
        self.__th.start()

    def test_on_metainfo(self, message, *args):
        pass

    def test_on_error(self, message, *args):
        print("on_error:", message, args)

    def test_on_close(self, *args):
        try:
            self.__f.close()
        except:
            pass

    def test_on_data(self, data, *args):
        try:
            self.__f.write(data)
        except:
            pass

    def test_on_completed(self, message, *args):
        print("✅ 合成完成")

    def __test_run(self):
        tts = nls.NlsSpeechSynthesizer(
            url=URL,
            token=TOKEN,
            appkey=APPKEY,
            on_metainfo=self.test_on_metainfo,
            on_data=self.test_on_data,
            on_completed=self.test_on_completed,
            on_error=self.test_on_error,
            on_close=self.test_on_close,
            callback_args=[self.__id]
        )
        tts.start(self.__text, voice="ailun")

def run_and_play():
    pcm_path = "python_asr/test_tts.pcm"
    wav_path = "python_asr/test_tts.wav"

    print("正在合成语音...")
    t = TestTts("tts", pcm_path)
    t.start(TEXT)

    # 等待合成结束
    time.sleep(4)

    # 转wav并播放
    pcm2wav(pcm_path, wav_path)
    print("正在播放声音...")
    play_audio(wav_path)

if __name__ == "__main__":
    nls.enableTrace(False)
    run_and_play()