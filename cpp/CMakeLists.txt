cmake_minimum_required(VERSION 3.12)
project(AITradingSystem)

set(CMAKE_CXX_STANDARD 17)

# Try to find curl directly
find_library(CURL_LIBRARY curl)
find_path(CURL_INCLUDE_DIR curl/curl.h)

find_library(HIREDIS_LIBRARY hiredis)
find_path(HIREDIS_INCLUDE_DIR hiredis/hiredis.h)

if(NOT CURL_LIBRARY)
    message(FATAL_ERROR "libcurl not found. Install with: brew install curl")
endif()

if(NOT HIREDIS_LIBRARY)
    message(FATAL_ERROR "hiredis not found. Install with: brew install hiredis")
endif()

# Get nlohmann/json
include(FetchContent)
FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
)
FetchContent_MakeAvailable(nlohmann_json)

# Create executable
add_executable(market_data_engine
    src/market_data/data_manager.cpp
)

# Link libraries
target_link_libraries(market_data_engine
    ${CURL_LIBRARY}
    ${HIREDIS_LIBRARY}
    nlohmann_json::nlohmann_json
    pthread
)

target_include_directories(market_data_engine PRIVATE
    ${CURL_INCLUDE_DIR}
    ${HIREDIS_INCLUDE_DIR}
)