cmake_minimum_required(VERSION 3.0.0)
project(hyperdb-perf VERSION 0.1.0)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(hyperdb-perf main.cpp)

target_link_libraries(hyperdb-perf ${CONAN_LIBS})
set(CPACK_PROJECT_NAME ${PROJECT_NAME})
set(CPACK_PROJECT_VERSION ${PROJECT_VERSION})
