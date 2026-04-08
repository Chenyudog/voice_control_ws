#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

重要约定（与 C++ 父进程 speech_echo_node 配合）：
  - 每识别出「一整句话」（一句结束），把文字打印到 **标准输出 stdout** 一行，并 flush。
  - 父进程用 popen+fgets 读这一行，再发布到 ROS 话题。
  - 「还没说完」的中间结果（partial）打到 **标准错误 stderr**，避免混进 stdout 破坏一行一句的协议。

依赖：
  pip3 install vosk soinstall portaudio19-dev（否则 sounddevice 可能无法打开麦克风）

音频格式：16 kHz、单声道、int16 PCM —— 与 Vosk 常见小模型要求一致。



"""
import json
import queue
import sys


def main() -> None:
    # 第一个命令行参数：Vosk 模型目录（解压后的文件夹，内含 am、graph 等）
    if len(sys.argv) < 2:
        sys.stderr.write("用法: transcribe_mic.py <Vosk模型目录>\n")
        sys.exit(1)

    model_path = sys.argv[1]

    try:
        import sounddevice as sd
        from vosk import KaldiRecognizer, Model
    except ImportError:
        sys.stderr.write(
            "缺少 Python 依赖，请安装:\n"
            "  pip3 install vosk sounddevice\n"
            "并确保系统已安装 PortAudio（通常: sudo apt install portaudio19-dev）。\n"
        )
        sys.exit(1)

    # 加载模型到内存；路径错误会在这里抛异常
    model = Model(model_path)
    # 16000 必须与下面 RawInputStream 的 samplerate 一致
    rec = KaldiRecognizer(model, 16000)

    # 声卡回调在独立线程里执行，与主线程通信用线程安全的 Queue
    audio_q: queue.Queue[bytes] = queue.Queue()

    def callback(indata, frames, time, status) -> None:  # type: ignore[no-untyped-def]
        # status 非零表示溢出等警告，写到 stderr 便于排查
        if status:
            sys.stderr.write(str(status) + "\n")
        # indata 是 numpy 缓冲，转成 bytes 给 Vosk
        audio_q.put(bytes(indata))

    try:
        # RawInputStream：底层 PCM，不做重采样；blocksize 一次回调的字节量，可调
        stream = sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,  # 增加到8000字节（0.5秒），减少调用频率，提高响应速度
            dtype="int16",
            channels=1,
            callback=callback,
        )
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"无法打开麦克风: {e}\n")
        sys.exit(1)

    sys.stderr.write("麦克风已打开，开始监听…\n")

    with stream:
        while True:
            # 阻塞直到回调线程放入一块 PCM
            data = audio_q.get()
            # AcceptWaveform 返回 True：Vosk 认为当前这句「说完了」，可取 Result()
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get("text", "").strip()
                if text:
                    # 这一行会被 C++ 的 fgets 原样读走 → 必须 flush，否则可能留在缓冲区
                    print(text, flush=True)
            else:
                # 句中临时结果，给人类看进度；不走 stdout，避免破坏一行一句协议
                partial = json.loads(rec.PartialResult()).get("partial", "").strip()
                if partial:
                    sys.stderr.write("\r[识别中] " + partial + "   ")


if __name__ == "__main__":
    main()
