功能包内容：
my_cmake_pkg :小海龟离线控制控制相关功能包
online_voice_pkg :  在线大模型语音识别
voice_interaction_pkg :  离线大模型语音识别

个人命名规范
launch 文件有各种launch文件 但是只有main的那个才是把所有功能都合在一起的 剩下的都只有一个功能

每一个launch文件夹下都有一个readME.md 内容是launch的执行内容

新机迁移：

online_asr/python_asr/asr.py
online_asr/resource/asr.py
1.修改阿里云的APPkey ACCESSKEY路径
2.修改离线语音大模型vosk路径
