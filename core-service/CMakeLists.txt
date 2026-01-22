cmake_minimum_required(VERSION 3.10)
project(core_service)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Загрузка зависимостей
include(FetchContent)

# httplib для HTTP сервера
FetchContent_Declare(
    httplib
    GIT_REPOSITORY https://github.com/yhirose/cpp-httplib.git
    GIT_TAG        v0.11.3
)

# nlohmann/json для работы с JSON
FetchContent_Declare(
    json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG        v3.11.2
)

# libcurl для запросов к auth-service
find_package(CURL REQUIRED)

FetchContent_MakeAvailable(httplib json)

# Исходные файлы
set(SOURCES
    src/main.cpp
    src/AuthClient.cpp
    src/Database.cpp
)

# Заголовочные файлы
include_directories(include)

add_executable(core_service ${SOURCES})
target_link_libraries(core_service PRIVATE 
    httplib 
    nlohmann_json::nlohmann_json
    CURL::libcurl
    sqlite3
)
