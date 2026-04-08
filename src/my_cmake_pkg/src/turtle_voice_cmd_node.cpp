/**
 * @file turtle_voice_cmd_node.cpp
 * @brief 订阅「语音识别后的文字」，解析成海龟动作：传送、转圈、直走、调速、停止。
 *
 * 它不连接麦克风，只订阅 std_msgs/String（默认话题名与 speech_echo_node 发布的 speech_topic 一致）。
 *
 * 与 turtlesim 的接口：
 *   - 发布 geometry_msgs/Twist 到 /turtle1/cmd_vel（线速度 linear.x，角速度 angular.z）
 *   - 调用 turtlesim/srv/TeleportAbsolute 服务 /turtle1/teleport_absolute 瞬移到 (x,y,theta)
 */

#include <algorithm>
#include <cmath>
#include <memory>
#include <regex>
#include <string>

#include "geometry_msgs/msg/twist.hpp"
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "turtlesim/srv/teleport_absolute.hpp"

using std::chrono_literals::operator""ms;

namespace
{

/** 去掉字符串首尾空白字符（空格、制表符、换行） */
std::string trim_copy(std::string s)
{
  const char * ws = " \t\r\n";
  s.erase(0, s.find_first_not_of(ws));
  s.erase(s.find_last_not_of(ws) + 1);
  return s;
}

/** 仅把 A-Z 转成 a-z；中文等非 ASCII 字节保持不变，便于中英混合指令 */
std::string to_lower_ascii(std::string s)
{
  for (char & c : s) {
    if (c >= 'A' && c <= 'Z') {
      c = static_cast<char>(c - 'A' + 'a');
    }
  }
  return s;
}

/** 把 v 限制在 [-limit, limit] 内，用于速度限幅，防止超过 turtlesim 舒适区 */
double clamp_mag(double v, double limit)
{
  if (limit <= 0.0) {
    return 0.0;
  }
  if (v > limit) {
    return limit;
  }
  if (v < -limit) {
    return -limit;
  }
  return v;
}

}  // namespace

/**
 * 海龟语音控制节点：订阅一句话 → 解析 → 发速度或调用传送服务。
 */
class TurtleVoiceCmdNode : public rclcpp::Node
{
public:
  TurtleVoiceCmdNode()
  : rclcpp::Node("turtle_voice_cmd")
  {
    // turtle_name：海龟名，默认 turtle1，与 turtlesim 默认一致
    turtle_name_ = declare_parameter<std::string>("turtle_name", "turtle1");
    // max_linear / max_angular：速度「硬上限」，所有实际发出的 twist 都会被裁到这里
    max_linear_ = declare_parameter<double>("max_linear", 2.0);
    max_angular_ = declare_parameter<double>("max_angular", 2.0);
    // drive_linear_ / drive_angular_：当前「期望」线速度与角速度幅值，用于转圈、直走；可被 speed / slow / fast 修改
    drive_linear_ = declare_parameter<double>("default_linear", 1.0);
    drive_angular_ = declare_parameter<double>("default_angular", 1.0);

    // 必须与 speech_echo_node 的 speech_topic 一致，否则收不到识别结果
    const std::string speech_topic = declare_parameter<std::string>("speech_topic", "speech_text");
    // turtlesim 约定：速度话题名 = /海龟名/cmd_vel
    const std::string cmd_topic =
      "/" + turtle_name_ + "/cmd_vel";
    // 瞬移服务名 = /海龟名/teleport_absolute
    const std::string teleport_name = "/" + turtle_name_ + "/teleport_absolute";

    cmd_pub_ = create_publisher<geometry_msgs::msg::Twist>(cmd_topic, 10);
    teleport_client_ = create_client<turtlesim::srv::TeleportAbsolute>(teleport_name);

    // 收到一条 String，整句文字在 msg->data 里
    speech_sub_ = create_subscription<std_msgs::msg::String>(
      speech_topic, 10,
      std::bind(&TurtleVoiceCmdNode::on_speech, this, std::placeholders::_1));

    // 50ms 一次 ≈ 20Hz：持续发 cmd_vel 才能维持「转圈」「直走」；Idle 模式定时器仍会跑但不再发非零速度
    motion_timer_ = create_wall_timer(50ms, std::bind(&TurtleVoiceCmdNode::on_motion_timer, this));

    RCLCPP_INFO(
      get_logger(),
      "语音指令示例(英文): "
      "\"go to 5 5\" / \"goto 3.5 4\" — 去坐标; "
      "\"circle\" / \"spin\" — 转圈; "
      "\"forward\" / \"straight\" — 直走; "
      "\"stop\" — 停; "
      "\"speed 0.8\" 或 \"speed 1 0.6\" — 线速度/角速度上限式驱动值; "
      "\"slow\" / \"fast\" — 预设快慢。"
      " 中文可说: 转圈 / 直走 / 停 / 去 5 5");
  }

private:
  /** 运动模式：静止 / 持续转圈 / 持续直行（靠定时器反复 publish twist） */
  enum class MotionMode { Idle, Circle, Straight };

  /** 切换模式；进入 Idle 时立刻发零速度，避免海龟因失去指令而一直惯性滑动（简单处理） */
  void set_mode(MotionMode m)
  {
    mode_ = m;
    if (mode_ == MotionMode::Idle) {
      geometry_msgs::msg::Twist stop;
      cmd_pub_->publish(stop);
    }
  }

  /** 定时器回调：仅在 Circle / Straight 下周期性发布 cmd_vel */
  void on_motion_timer()
  {
    geometry_msgs::msg::Twist twist;
    if (mode_ == MotionMode::Circle) {
      // 同时有向前的线速度和绕 z 的角速度 → 轨迹近似圆（差速模型）
      twist.linear.x = clamp_mag(drive_linear_, max_linear_);
      twist.angular.z = clamp_mag(drive_angular_, max_angular_);
      cmd_pub_->publish(twist);
    } else if (mode_ == MotionMode::Straight) {
      twist.linear.x = clamp_mag(drive_linear_, max_linear_);
      twist.angular.z = 0.0;
      cmd_pub_->publish(twist);
    }
    // Idle：不发非零 twist（已在 set_mode 时发过零）
  }

  /** 语音识别节点发来的一整句话，在此解析 */
  void on_speech(const std_msgs::msg::String::SharedPtr msg)
  {
    std::string raw = trim_copy(msg->data);
    if (raw.empty()) {
      return;
    }

    RCLCPP_INFO(get_logger(), "指令: %s", raw.c_str());

    // ---------- 先匹配中文关键词（用原始 raw，避免 to_lower 破坏 UTF-8）----------
    if (raw.find("转圈") != std::string::npos) {
      set_mode(MotionMode::Circle);
      return;
    }
    if (raw.find("直走") != std::string::npos || raw.find("前进") != std::string::npos) {
      set_mode(MotionMode::Straight);
      return;
    }
    // 「停」字出现在句中即认为要停止（注意别和英文 stop 重复匹配逻辑冲突）
    if (raw.find("停") != std::string::npos) {
      set_mode(MotionMode::Idle);
      return;
    }

    // ---------- 英文关键词用小写副本 s 做子串查找 ----------
    std::string s = to_lower_ascii(raw);

    if (s.find("circle") != std::string::npos || s.find("spin") != std::string::npos) {
      set_mode(MotionMode::Circle);
      return;
    }
    if (
      s.find("forward") != std::string::npos || s.find("straight") != std::string::npos ||
      s == "go" || s.find("go forward") != std::string::npos)
    {
      set_mode(MotionMode::Straight);
      return;
    }
    if (s.find("stop") != std::string::npos || s.find("halt") != std::string::npos) {
      set_mode(MotionMode::Idle);
      return;
    }

    // 预设慢/快：直接改 drive_*，不改变当前模式（若正在转圈会立刻用新速度）
    if (s == "slow") {
      drive_linear_ = clamp_mag(0.4, max_linear_);
      drive_angular_ = clamp_mag(0.6, max_angular_);
      RCLCPP_INFO(get_logger(), "已设为慢速: linear=%.2f angular=%.2f", drive_linear_, drive_angular_);
      return;
    }
    if (s == "fast") {
      drive_linear_ = clamp_mag(std::min(1.8, max_linear_), max_linear_);
      drive_angular_ = clamp_mag(std::min(1.8, max_angular_), max_angular_);
      RCLCPP_INFO(get_logger(), "已设为快速: linear=%.2f angular=%.2f", drive_linear_, drive_angular_);
      return;
    }

    try {
      std::smatch m;
      // speed 0.8 → 只改线速度幅值；speed 1 0.6 → 第一个数线速度，第二个角速度
      if (std::regex_search(s, m, std::regex(R"(speed\s+([-+]?\d*\.?\d+)(?:\s+([-+]?\d*\.?\d+))?)"))) {
        drive_linear_ = clamp_mag(std::stod(m[1].str()), max_linear_);
        if (m[2].matched && !m[2].str().empty()) {
          drive_angular_ = clamp_mag(std::stod(m[2].str()), max_angular_);
        }
        RCLCPP_INFO(get_logger(), "速度: linear=%.2f angular=%.2f", drive_linear_, drive_angular_);
        return;
      }

      // 去 x y：支持中文「去/到」+ 数字，或英文 go to / goto / teleport / position + 数字
      // 注意：语音识别必须把坐标识别成数字字符串，否则正则不匹配
      if (std::regex_search(raw, m, std::regex(u8R"((?:去|到)\s*([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+))")) ||
        std::regex_search(s, m, std::regex(R"((?:go\s*to|goto|teleport|position)\s+([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+))")))
      {
        const double x = std::stod(m[1].str());
        const double y = std::stod(m[2].str());
        // theta 固定 0；若需语音设朝向可再扩展第三个数
        do_teleport(x, y, 0.0);
        return;
      }
    } catch (const std::exception & e) {
      RCLCPP_WARN(get_logger(), "解析失败: %s", e.what());
    }

    RCLCPP_WARN(get_logger(), "未识别的指令，请重试。");
  }

  /** 调用 turtlesim 的绝对传送服务，把海龟瞬移到 (x,y)，朝向 theta（弧度） */
  void do_teleport(double x, double y, double theta)
  {
    // 传送前先停掉持续运动模式，避免 teleport 与 cmd_vel 同时抢控制观感怪
    set_mode(MotionMode::Idle);

    if (!teleport_client_->wait_for_service(std::chrono::seconds(2))) {
      RCLCPP_ERROR(get_logger(), "服务不可用: %s", teleport_client_->get_service_name());
      return;
    }

    auto req = std::make_shared<turtlesim::srv::TeleportAbsolute::Request>();
    req->x = x;
    req->y = y;
    req->theta = theta;

    RCLCPP_INFO(get_logger(), "移动到 (%.2f, %.2f)", x, y);
    // 异步发请求 + spin_until_future_complete：在当前节点上等到响应或超时
    // rclcpp::Node 继承链里已有 enable_shared_from_this，可用 shared_from_this()
    auto future = teleport_client_->async_send_request(req);
    const auto ret = rclcpp::spin_until_future_complete(
      shared_from_this(), future, std::chrono::seconds(2));
    if (ret != rclcpp::FutureReturnCode::SUCCESS) {
      RCLCPP_ERROR(get_logger(), "传送超时或中断");
      return;
    }
    auto resp = future.get();
    if (!resp) {
      RCLCPP_ERROR(get_logger(), "传送失败");
    }
  }

  std::string turtle_name_;
  double max_linear_{};
  double max_angular_{};
  double drive_linear_{};
  double drive_angular_{};

  MotionMode mode_{MotionMode::Idle};
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_pub_;
  rclcpp::Client<turtlesim::srv::TeleportAbsolute>::SharedPtr teleport_client_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr speech_sub_;
  rclcpp::TimerBase::SharedPtr motion_timer_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<TurtleVoiceCmdNode>();
  // spin：阻塞在此，直到 Ctrl+C；回调（订阅、定时器、服务响应）由 executor 调度
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
