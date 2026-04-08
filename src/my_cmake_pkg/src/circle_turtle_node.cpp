/**
 * @file circle_turtle_node.cpp
 * @brief 持续向 turtlesim 发布固定 Twist，使海龟近似画圆（线速度 + 角速度同时非零）。
 *
 * 差速平面模型：同时有 linear.x（前进）和 angular.z（绕垂直轴旋转）时，轨迹为圆弧。
 * 圆半径近似为 R ≈ |v| / |ω|（ω 很小时不要用此近似）。
 *
 * 参数：
 *   linear_speed  → Twist.linear.x
 *   angular_speed → Twist.angular.z
 *   cmd_vel_topic → 发布话题，默认 /turtle1/cmd_vel，可 remap 到第二只海龟等
 */

#include <chrono>
#include <cmath>
#include <memory>
#include <string>

#include "geometry_msgs/msg/twist.hpp"
#include "rclcpp/rclcpp.hpp"

using std::chrono_literals::operator""ms;

class CircleTurtleNode : public rclcpp::Node
{
public:
  CircleTurtleNode()
  : rclcpp::Node("circle_turtle")
  {
    linear_ = declare_parameter<double>("linear_speed", 1.0);
    angular_ = declare_parameter<double>("angular_speed", 1.0);
    const std::string topic = declare_parameter<std::string>("cmd_vel_topic", "/turtle1/cmd_vel");

    pub_ = create_publisher<geometry_msgs::msg::Twist>(topic, 10);
    // 50ms = 20Hz：与常见 teleop 发 cmd_vel 频率类似，仿真更平滑
    timer_ = create_wall_timer(50ms, std::bind(&CircleTurtleNode::on_timer, this));

    const double w = std::abs(angular_) < 1e-9 ? 0.0 : std::abs(angular_);
    const double r = w > 0.0 ? std::abs(linear_) / w : 0.0;
    RCLCPP_INFO(
      get_logger(),
      "Publishing circle motion on '%s' at 20 Hz (linear=%.2f, angular=%.2f, radius≈%.2f)",
      topic.c_str(), linear_, angular_, r);
  }

private:
  void on_timer()
  {
    geometry_msgs::msg::Twist msg;
    msg.linear.x = linear_;
    msg.linear.y = 0.0;
    msg.linear.z = 0.0;
    msg.angular.x = 0.0;
    msg.angular.y = 0.0;
    msg.angular.z = angular_;
    pub_->publish(msg);
  }

  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr pub_;
  rclcpp::TimerBase::SharedPtr timer_;
  double linear_{};
  double angular_{};
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CircleTurtleNode>());
  rclcpp::shutdown();
  return 0;
}
