project(KDDeployQt)

# kd_generate_deploy_app_script (
#     TARGET <target>
#     OUTPUT_SCRIPT <output_script>
#     [PROJECT_QML_PATHS <path> ...]
#     [QML_IMPORT_PATHS <path> ...]
#     [EXTRA_LIBS <path> ...]
#     [EXTRA_PLUGINS <path> ...]
#     [SYSTEM_LIBS_PATHS <path> ...]
#     [WAYLAND]
#     [XCB]
#     [VERBOSE]
# )
#

# Usage:
#
# include(FetchContent)
# FetchContent_Declare(kddeployqt
#    GIT_REPOSITORY https://github.com/KDABLabs/kddeployqt.git
#    GIT_TAG        main
# )
# FetchContent_MakeAvailable(kddeployqt)
#
# kd_generate_deploy_app_script(
#     TARGET appuntitled13
#     OUTPUT_SCRIPT deploy_script
#     VERBOSE
#     WAYLAND
#     PROJECT_QML_PATHS
#         ${CMAKE_CURRENT_SOURCE_DIR}
# )


function(kd_generate_deploy_app_script )
    set(no_value_options
        WAYLAND
        XCB
        VERBOSE
    )
    set(single_value_options
        TARGET
        OUTPUT_SCRIPT
    )
    set(multi_value_options
        PROJECT_QML_PATHS
        QML_IMPORT_PATHS
        EXTRA_LIBS
        EXTRA_PLUGINS
        SYSTEM_LIBS_PATHS
    )
    cmake_parse_arguments(PARSE_ARGV 0 arg
        "${no_value_options}" "${single_value_options}" "${multi_value_options}"
    )
    if(arg_UNPARSED_ARGUMENTS)
        message(FATAL_ERROR "Unexpected arguments: ${arg_UNPARSED_ARGUMENTS}")
    endif()
    if(NOT arg_TARGET)
        message(FATAL_ERROR "TARGET must be specified")
    endif()

    if(NOT QT_DEPLOY_PREFIX)
        set(QT_DEPLOY_PREFIX \"\$ENV{DESTDIR}\${CMAKE_INSTALL_PREFIX}\")
    endif()
    if(QT_DEPLOY_PREFIX STREQUAL \"\")
        set(QT_DEPLOY_PREFIX .)
    endif()

    if (arg_PROJECT_QML_PATHS)
        foreach(arg IN LISTS arg_PROJECT_QML_PATHS)
            list(APPEND deploy_args "--qml_root_path" "${arg}")
        endforeach()
    endif()

    if (arg_QML_IMPORT_PATHS)
        foreach(arg IN LISTS arg_QML_IMPORT_PATHS)
            list(APPEND deploy_args "--qml_import_path" "${arg}")
        endforeach()
    endif()

    if (arg_EXTRA_LIBS)
        foreach(arg IN LISTS arg_EXTRA_LIBS)
            list(APPEND deploy_args "--extra_libs" "${arg}")
        endforeach()
    endif()

    if (arg_EXTRA_PLUGINS)
        foreach(arg IN LISTS arg_EXTRA_PLUGINS)
            list(APPEND deploy_args "--extra_plugins" "${arg}")
        endforeach()
    endif()

    if (arg_SYSTEM_LIBS_PATHS)
        foreach(arg IN LISTS arg_SYSTEM_LIBS_PATHS)
            list(APPEND deploy_args "--system_libs_path" "${arg}")
        endforeach()
    endif()

    if (arg_WAYLAND)
        list(APPEND deploy_args "--wayland")
    endif()

    if (arg_XCB)
        list(APPEND deploy_args "--xcb")
    endif()

    set(VERBOSE "set (VERBOSE OFF)")
    if (arg_VERBOSE)
        list(APPEND deploy_args "--verbose")
        set(VERBOSE "set (VERBOSE ON)")
    endif()

    if (CMAKE_CROSSCOMPILING)
        # Qt::qtpaths points to the wrong file when cross-compiling
        if (NOT QT_QMAKE_EXECUTABLE)
            message(NOTICE "QT_QMAKE_EXECUTABLE not set, trying to guess it from Qt6_DIR: ${Qt6_DIR}")
            set(qmake_path ${Qt6_DIR}/../../../bin/qtpaths)
            if (NOT EXISTS ${qmake_path})
                set(qmake_path ${Qt6_DIR}/../../../bin/qtpaths6)
                if (NOT EXISTS ${qmake_path})
                    set(qmake_path ${Qt6_DIR}/../../../bin/qmake)
                    if (NOT EXISTS ${qmake_path})
                        message(FATAL_ERROR "Could not find qtpaths executable")
                    endif()
                endif()
            endif()
        else()
            set(qmake_path ${QT_QMAKE_EXECUTABLE})
        endif()
    else()
        get_target_property(qmake_path Qt::qtpaths IMPORTED_LOCATION)
    endif()

    list(JOIN deploy_args " " kddeployqt_args)

    set(deploy_script ${CMAKE_CURRENT_BINARY_DIR}/${arg_TARGET}_kddeployqt_script.cmake)
    set(script_content
"
${VERBOSE}
if (VERBOSE)
    message(NOTICE Running ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/kddeployqt.py --output ${QT_DEPLOY_PREFIX} --executable $<TARGET_FILE:${arg_TARGET}> --qmake ${qmake_path} ${kddeployqt_args})
endif()

execute_process(COMMAND
                    ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/kddeployqt.py --output ${QT_DEPLOY_PREFIX} --executable $<TARGET_FILE:${arg_TARGET}> --qmake ${qmake_path} ${kddeployqt_args}
                OUTPUT_VARIABLE
                    output
                ERROR_VARIABLE
                    error)
if (VERBOSE)
    message(NOTICE \${output})
endif()
if (error)
    message(ERROR \${error})
endif()
if (VERBOSE)
    message(NOTICE \t..done)
endif()
")

    file(GENERATE OUTPUT ${deploy_script} CONTENT ${script_content})
    set(${arg_OUTPUT_SCRIPT} "${deploy_script}" PARENT_SCOPE)
    set_property(TARGET ${arg_TARGET} PROPERTY _qt_marked_for_deployment ON)
endfunction()
