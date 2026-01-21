cmake_minimum_required(VERSION 3.10)
project(auth_service)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(httplib REQUIRED)

add_executable(auth_service main.cpp)
target_link_libraries(auth_service PRIVATE httplib::httplib)
