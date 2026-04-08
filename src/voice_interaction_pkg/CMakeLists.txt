cmake_minimum_required(VERSION 3.8)
project(voice_interaction_pkg)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(ament_index_cpp REQUIRED)

add_executable(speech_echo_node src/speech_echo_node.cpp)
ament_target_dependencies(speech_echo_node rclcpp std_msgs ament_index_cpp)

install(TARGETS speech_echo_node DESTINATION lib/${PROJECT_NAME})

install(PROGRAMS scripts/transcribe_mic.py
  DESTINATION share/${PROJECT_NAME}/scripts)

install(DIRECTORY launch model DESTINATION share/${PROJECT_NAME}/)

ament_package()
