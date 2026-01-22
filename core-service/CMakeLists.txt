cmake_minimum_required(VERSION 3.10)
project(core_service)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(SOURCES
    src/main.cpp
    src/AuthClient.cpp
    src/Database.cpp
)

include_directories(include)
include_directories(/usr/local/include)

add_executable(core_service ${SOURCES})
target_link_libraries(core_service PRIVATE curl sqlite3 pthread)
