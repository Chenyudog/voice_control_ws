/**
 * @file speech_echo_node.cpp
 * @brief 语音识别节点的 ROS2「外壳」：不负责具体算法，只负责拉起 Python + Vosk，并把识别结果接入 ROS。
 *
 * 整体分工：
 *   - 本文件（C++）：创建节点、读参数、用 popen 启动子进程、读子进程 stdout、打日志、发布话题。
 *   - transcribe_mic.py（Python）：从麦克风采音、调用 Vosk 离线识别；每识别完「一整句话」就往 stdout 打印一行字。
 *
 * 数据流：麦克风 → Python/Vosk → 管道 stdout 一行文本 → 本程序 fgets 读到 → RCLCPP_INFO + publish(String)。
 离线语音识别：
    原理是先从麦克风录制频，然后把录制的音频丢给vosk模型识别
 */

#include <array>
#include <cstdio>
#include <memory>
#include <string>

#include "ament_index_cpp/get_package_share_directory.hpp"
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

int main(int argc, char * argv[])
{
  // 初始化 ROS2 客户端库；argc/argv 里可能带有 --ros-args 等参数
  rclcpp::init(argc, argv);

  // 节点名在图里显示为 /speech_echo（若未 remap）
  auto node = std::make_shared<rclcpp::Node>("speech_echo");

  // ---------- 话题参数 ----------
  // speech_topic：识别结果要发布到哪个话题。默认 "speech_text"。
  // turtle_voice_cmd_node 必须订阅「同名」话题，两边才能对上。
  const std::string speech_topic =
    node->declare_parameter<std::string>("speech_topic", "speech_text");
  // 队列深度 10：短时间积压几句字符串一般不会丢（若识别极快可适当加大）
  auto speech_pub =
    node->create_publisher<std_msgs::msg::String>(speech_topic, 10);

  // ---------- Vosk 模型路径（必填）----------
  // 模型是离线文件目录，由用户在 launch 或命令行传入，例如：
  //   -p model_path:=/home/xxx/vosk-model-en-us-0.22-lgraph
  std::string model_path = node->declare_parameter<std::string>("model_path", "");
  if (model_path.empty()) {
    RCLCPP_ERROR(
      node->get_logger(),
      "参数 model_path 为空。请设置 Vosk 模型目录，例如：\n"
      "  ros2 run voice_interaction_pkg speech_echo_node "
      "--ros-args -p model_path:=/path/to/vosk-model-small-cn-0.22");
    rclcpp::shutdown();
    return 1;
  }

  // ---------- 定位已安装的 Python 脚本 ----------
  // colcon install 后，脚本在 share/voice_interaction_pkg/scripts/transcribe_mic.py
  // ament_index 根据功能包名在 AMENT_PREFIX_PATH 里查找安装前缀，避免写死绝对路径
  std::string share_dir;
  try {
    share_dir = ament_index_cpp::get_package_share_directory("voice_interaction_pkg");
  } catch (const std::exception & e) {
    RCLCPP_ERROR(node->get_logger(), "找不到功能包 share 目录: %s", e.what());
    rclcpp::shutdown();
    return 1;
  }

  const std::string script = share_dir + "/scripts/transcribe_mic.py";
  // 注意：路径含空格时外层已用引号包起来；model_path 同样加引号，防止路径中有空格
  const std::string cmd =
    "python3 \"" + script + "\" \"" + model_path + "\"";

  RCLCPP_INFO(node->get_logger(), "启动识别脚本（请对麦克风说话，Ctrl+C 结束）…");

  // popen：创建子进程并把子进程的「标准输出」接到管道，父进程用 FILE* 读
  // 第二个参数 "r" 表示父进程读、子进程写 stdout
  // unique_ptr 自定义删除器 pclose：离开作用域时自动关闭管道、回收子进程（视实现而定）
  std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"), pclose);
  if (!pipe) {
    RCLCPP_ERROR(node->get_logger(), "无法执行: %s", cmd.c_str());
    rclcpp::shutdown();
    return 1;
  }

  // 按行读：Python 每 print 一行（一整句识别结果）+ flush，这里就收到一行
  std::array<char, 2048> buffer{};
  while (rclcpp::ok() && fgets(buffer.data(), static_cast<int>(buffer.size()), pipe.get())) {
    std::string line(buffer.data());
    // 去掉行尾 \n \r，避免发布出去的字符串带换行符
    while (!line.empty() && (line.back() == '\n' || line.back() == '\r')) {
      line.pop_back();
    }
    if (!line.empty()) {
      // 终端可见，方便调试麦克风/识别是否工作
      RCLCPP_INFO(node->get_logger(), "识别: %s", line.c_str());
      // 发给其他节点（如海龟语音控制）：消息类型是 std_msgs/String，字段 data 即一句话
      std_msgs::msg::String msg;
      msg.data = line;
      speech_pub->publish(msg);
    }
    // 子进程在阻塞读麦克风时，父进程若一直卡在 fgets 里，这里实际执行频率低；
    // 一旦有输出或需要处理 shutdown，spin_some 让节点能响应退出等回调
    rclcpp::spin_some(node);
  }

  // 若循环因「管道关闭」退出而 ROS 仍 ok，多半是 Python 进程挂了或正常结束
  if (rclcpp::ok()) {
    RCLCPP_WARN(node->get_logger(), "识别进程已结束。若未安装依赖，请执行: pip3 install vosk sounddevice");
  }

  rclcpp::shutdown();
  return 0;
}
