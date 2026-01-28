# y.cmake - A nano wrapper over FetchContent

# Usage:

#     On parent/top (or project) CMake

#         y_add_library( "fmt"       "11.1.4" "https://github.com/fmtlib/fmt/releases/download/11.1.4/fmt-11.1.4.zip" ON|OFF)
#         y_add_library( "glm"      "1.0.1"   "https://github.com/g-truc/glm/archive/refs/tags/1.0.1.zip"             ON|OFF)
#         y_add_library( "argparse" "3.2"     "https://github.com/p-ranav/argparse/archive/refs/tags/v3.2.zip"        ON|OFF)

#         This will populate the ./build/deps dir with given dependencies.
#         The last arg is allow_system.
#             - OFF means 'always download'
#             - ON  means 'try to find it on system'

#         Alternatively use the methods:
#             - y_add_external : To 'always download' if not found in 'deps'
#             - y_add_system   : To 'try to find it on system'

#     On project CMake

#         y_link_libraries(${PROJECT_NAME})
#             This will link the project with all the libraries added in previous
#             section.

#         y_enable_tests()
#             This will add all the .cpp, .cc or .c in the ./tests dir as tests
#             to later run with 'ctest'.

# Copyright Daniel Brétema, 2025.
# Distributed under the Boost Software License, Version 1.0.
# See complete details at https://www.boost.org/LICENSE_1_0.txt


include(FetchContent)

################################################################################
##                                   Vars                                     ##
################################################################################

# Output Folder
set(FETCHCONTENT_BASE_DIR ${CMAKE_SOURCE_DIR}/build/deps)

# Global Variable w/ lib names
set(y_meta_libs "" CACHE INTERNAL "")

set(__y_sep "❱---------------------------------------------------------------------------❰" CACHE INTERNAL "")


################################################################################
##                                Top setup                                   ##
################################################################################

macro(y_set_defaults cxx_standard)

    if(NOT CMAKE_BUILD_TYPE)
        set(CMAKE_BUILD_TYPE Debug)
    endif()

    set(CMAKE_CXX_STANDARD ${cxx_standard})
    set(CMAKE_CXX_EXTENSIONS OFF)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)

    if(IS_DIRECTORY "${PROJECT_SOURCE_DIR}/vendor")
        include_directories(${PROJECT_NAME} PUBLIC "${PROJECT_SOURCE_DIR}/vendor")
    endif()

    message("")

endmacro()


################################################################################
##                               Add package                                  ##
################################################################################

function(y_add_library lib_name lib_version lib_url allow_system)

    if (${allow_system})
        find_package(${lib_name} ${lib_version} QUIET)
    endif()

    if (NOT ${lib_name}_FOUND)
        message(STATUS "[y] · External : ${lib_name}")
        FetchContent_Declare(${lib_name} DOWNLOAD_EXTRACT_TIMESTAMP OFF URL ${lib_url})
        FetchContent_MakeAvailable(${lib_name})
    else()
        message(STATUS "[y] · System : ${lib_name}")
    endif()

    set(_libs_aux "${y_meta_libs} ${lib_name}")
    string(STRIP ${_libs_aux} _libs_clean)
    set(y_meta_libs "${_libs_clean}" CACHE INTERNAL "")

    message("")

endfunction()

function(y_add_external lib_name lib_version lib_url)
    # set(_url "https://${lib_url}/archive/refs/tags/${lib_version}.zip")
    y_add_library(${lib_name} ${lib_version} ${lib_url} OFF)
endfunction()

function(y_add_system lib_name lib_version lib_url)
    y_add_library(${lib_name} ${lib_version} ${lib_url} ON)
endfunction()


################################################################################
##                             Link to project                                ##
################################################################################

function(y_link_libraries proj_name)

    string(REPLACE " " ";" _deps "${y_meta_libs}")
    # message(DEBUG "[y]·· Linking -> ${y_meta_libs}")
    target_link_libraries(${proj_name} ${_deps})

    endfunction()


################################################################################
##                             Set output dir                                 ##
################################################################################

function(y_set_output_dir proj_name dir_name)

    if (NOT MSVC)
       set(_build_type_dir ${CMAKE_BUILD_TYPE})
    else()
        set(_build_type_dir "")
    endif()

    set(_output_dir "${CMAKE_BINARY_DIR}/../${dir_name}")
    # message(DEBUG "[y]·· OutputDir -> ${_output_dir}")

    set_target_properties(${proj_name} PROPERTIES ARCHIVE_OUTPUT_DIRECTORY "${_output_dir}")
    set_target_properties(${proj_name} PROPERTIES LIBRARY_OUTPUT_DIRECTORY "${_output_dir}")
    set_target_properties(${proj_name} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${_output_dir}")

endfunction()


################################################################################
##                                   Glob                                     ##
################################################################################

function(y_glob root_dir out_sources out_headers)

    file(GLOB _sources "${root_dir}/*.cpp" "${root_dir}/*.cc" "${root_dir}/*.c")
    set(${out_sources} "${_sources}" PARENT_SCOPE)

    file(GLOB _headers "${root_dir}/*.hpp" "${root_dir}/*.hh" "${root_dir}/*.h")
    set(${out_headers} "${_headers}" PARENT_SCOPE)

    endfunction()


################################################################################
##                        Dir Has CMakeLists.txt                              ##
################################################################################

function (y_has_cmakefile root_dir out_has_cmakefile)
    file(GLOB _cmake_file "${root_dir}/[Cc][Mm][Aa][Kk][Ee][Ll][Ii][Ss][Tt][Ss].txt")

    if(_cmake_file)
        set(${out_has_cmakefile} ON PARENT_SCOPE)
    else()
        set(${out_has_cmakefile} OFF PARENT_SCOPE)
    endif()
endfunction()


################################################################################
##                             Set output dir                                 ##
##                               Executable                                   ##
################################################################################

function(y_add_exe proj_name proj_root_dir)

    # Include the headers to help IDEs
    # -- https://blog.conan.io/2019/09/02/Deterministic-builds-with-C-C++.html

    y_glob(${proj_root_dir} _sources _headers)

    message(STATUS "[y] · Project: ${proj_name}")

    message(DEBUG "  -- ${proj_root_dir}")
    message(DEBUG "  -- Sources:")
    foreach(_source IN LISTS _sources)
        message(DEBUG "  ---- ${_source}")
    endforeach()
    message(DEBUG "  -- Headers:")
    foreach(_header IN LISTS _headers)
        message(DEBUG "  ---- ${_header}")
    endforeach()

    add_executable(${proj_name} ${_sources} ${_headers})

endfunction()


################################################################################
##                              Target setup                                  ##
################################################################################

function(y_setup_exe_project)
    list(POP_FRONT ARGN ARGS_LinkLibs)

    get_filename_component(_name ${CMAKE_CURRENT_SOURCE_DIR} NAME)
    project(${_name})

    y_add_exe(${PROJECT_NAME} ${PROJECT_SOURCE_DIR})

    # Output
    y_set_output_dir(${PROJECT_NAME} "bin/${PROJECT_NAME}")

    # Properties
    set_target_properties(${PROJECT_NAME}
        PROPERTIES
            CMAKE_CXX_EXTENSIONS OFF
            CMAKE_CXX_VISIBILITY_PRESET hidden
            CMAKE_VISIBILITY_INLINES_HIDDEN ON
            CMAKE_EXPORT_COMPILE_COMMANDS ON
    )

    # Includes
    target_include_directories(${PROJECT_NAME} PUBLIC ${PROJECT_SOURCE_DIR})

    # Dependencies
    if (ARGS_LinkLibs)
        y_link_libraries(${PROJECT_NAME})
    endif()

endfunction()


################################################################################
##                         Projects in curr path                              ##
################################################################################

function(y_detect_projects)

    set(_found_dirs "")
    set(_root_dir ${CMAKE_CURRENT_SOURCE_DIR})

    # Get everything
    file(GLOB _root_content LIST_DIRECTORIES TRUE RELATIVE "${_root_dir}" "${_root_dir}/*")


    # Filter valid folders
    foreach(_item ${_root_content})
        list(FIND "${Y_NOT_A_PROJECT}" "${_item}" _ignored)

        set(_item_dir "${_root_dir}/${_item}")

        set(_valid (_ignored EQUAL -1))
        set(_is_dir (IS_DIRECTORY "${_item_dir}"))
        y_has_cmakefile("${_item_dir}" _has_cmakefile)

        if(${_valid} AND ${_is_dir} AND ${_has_cmakefile})
            string(SUBSTRING "${_item}" 0 1 _first)
            if(NOT (_first STREQUAL "."))
                list(APPEND _found_dirs "${_item}")
            endif()
        endif()
    endforeach()

    # Add subdirs
    foreach(_dir ${_found_dirs})
        # message(STATUS "[y] · Project : ${_dir}")
        add_subdirectory("${_dir}")
        message("")
    endforeach()

endfunction()


################################################################################
##                                 Tests                                      ##
################################################################################

function(y_enable_tests)

    if(NOT Y_BUILD_TESTS)
        return()
    endif()


    message(STATUS "[y] · Enabling tests")

    enable_testing()

    y_glob("${CMAKE_SOURCE_DIR}/tests" _sources _headers)

    foreach(_source IN LISTS _sources)

        get_filename_component(_name "${_source}" NAME_WE)
        add_executable(${_name} "${_source}")

        y_set_output_dir(${_name} "tests")
        y_link_libraries(${_name})

        add_test(NAME "${_name}" COMMAND "${_name}")

        message(STATUS "[y] · Test : ${_name} -- ${_source}")

    endforeach()
    message("")

endfunction()
