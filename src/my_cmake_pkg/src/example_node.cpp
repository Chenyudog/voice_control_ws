/**
 * @file example_node.cpp
 * @brief 最小 rclcpp 示例：创建一个节点、打印一条日志，然后 spin 空转（无订阅/发布/定时器）。
 *
 * 用途：验证工作区编译、source 后 ros2 run 能拉起节点；可作为新节点的代码模板起点。
 */

#include <memory>

#include "rclcpp/rclcpp.hpp"

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("example_node");
  RCLCPP_INFO(node->get_logger(), "example_node started");
  // spin：阻塞直到 Ctrl+C；本节点无回调，仅保持进程存活
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
