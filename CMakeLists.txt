cmake_minimum_required(VERSION 3.20)
project(dur LANGUAGES CXX)

add_executable(dur dur.cpp)

# Require C++17
set_property(TARGET dur PROPERTY CXX_STANDARD 17)
set_property(TARGET dur PROPERTY CXX_STANDARD_REQUIRED ON)

if (MSVC)
    # Always use the static runtime (/MT), even in Debug builds
    foreach(flag_var
        CMAKE_C_FLAGS CMAKE_C_FLAGS_DEBUG CMAKE_C_FLAGS_RELEASE
        CMAKE_C_FLAGS_MINSIZEREL CMAKE_C_FLAGS_RELWITHDEBINFO
        CMAKE_CXX_FLAGS CMAKE_CXX_FLAGS_DEBUG CMAKE_CXX_FLAGS_RELEASE
        CMAKE_CXX_FLAGS_MINSIZEREL CMAKE_CXX_FLAGS_RELWITHDEBINFO)
        if(${flag_var} MATCHES "/MD")
            string(REGEX REPLACE "/MD" "/MT" ${flag_var} "${${flag_var}}")
        endif()
        if(${flag_var} MATCHES "/MDd")
            string(REGEX REPLACE "/MDd" "/MT" ${flag_var} "${${flag_var}}")
        endif()
    endforeach()

    # Equivalent of: cl /EHsc /O2 /MT dur.cpp user32.lib gdi32.lib
    target_compile_options(dur PRIVATE /EHsc /O2)
    target_link_libraries(dur PRIVATE user32 gdi32)
endif()
