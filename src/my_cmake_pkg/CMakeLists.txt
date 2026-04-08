cmake_minimum_required(VERSION 3.8)
project(my_cmake_pkg)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(turtlesim REQUIRED)

add_executable(example_node src/example_node.cpp)
ament_target_dependencies(example_node rclcpp)
install(TARGETS example_node DESTINATION lib/${PROJECT_NAME})

add_executable(circle_turtle_node src/circle_turtle_node.cpp)
ament_target_dependencies(circle_turtle_node rclcpp geometry_msgs)
install(TARGETS circle_turtle_node DESTINATION lib/${PROJECT_NAME})

add_executable(turtle_voice_cmd_node src/turtle_voice_cmd_node.cpp)
ament_target_dependencies(turtle_voice_cmd_node rclcpp std_msgs geometry_msgs turtlesim)
install(TARGETS turtle_voice_cmd_node DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch DESTINATION share/${PROJECT_NAME}/)

ament_package()
