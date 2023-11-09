# kddeployqt
Deployment tool for Qt applications, similar to (android/mac/win)deployqt.

The main differences between this tool and the existing ones([linuxdeployqt](https://github.com/probonopd/linuxdeployqt), [linuxdeploy](https://github.com/linuxdeploy/linuxdeploy), [linuxdeploy](https://github.com/probonopd/linuxdeploy), etc.) are:

 - supports any ELF based qt builds, including crossed compiled qt.
 - is written in python, which makes it so much easier to hack.
 - at this point it deploys the Qt libs, plugins and qml files for your application. The system libs support is very limited.
 - cmake script for easily integrate it in any cmake project
 - currently only linux host is supported.

 ## How to use kddeployqt in your qt6 cmake project

Adding kddeployqt support to your qt6 cmake project is very easy:

```
include(FetchContent)
FetchContent_Declare(kddeployqt
    GIT_REPOSITORY https://github.com/KDABLabs/kddeployqt.git
    GIT_TAG        main
)
FetchContent_MakeAvailable(kddeployqt)

kd_generate_deploy_app_script(
    TARGET <my_target>
    OUTPUT_SCRIPT deploy_script
    PROJECT_QML_PATHS
        ${CMAKE_SOURCE_DIR}/my_qml_files_dir1
        ${CMAKE_SOURCE_DIR}/my_qml_files_dir2
)
install(SCRIPT ${deploy_script})
```
Yup, it's that easy ;-) !

The kd_generate_deploy_app_script full documentation is:

```
 kd_generate_deploy_app_script (
    TARGET <target>
    OUTPUT_SCRIPT <output_script>
    [PROJECT_QML_PATHS <path> ...]
    [QML_IMPORT_PATHS <path> ...]
    [EXTRA_LIBS <path> ...]
    [EXTRA_PLUGINS <path> ...]
    [SYSTEM_LIBS_PATHS <path> ...]
    [WAYLAND]
    [XCB]
    [VERBOSE]
 )
```

 - `TARGET` the taget on which we run kddeployqt. Usually the application executable.
 - `OUTPUT_SCRIPT` the output script variable which you must install using `install(SCRIPT ${deploy_script})`
 - `PROJECT_QML_PATHS` is a path list where are the project qml files located, usually is `${CMAKE_SOURCE_DIR}`. If missing `kd_generate_deploy_app_script` assumes that this is a non-qml project
 - `QML_IMPORT_PATHS` is a path list where qmkimportscanner will look for extra QML modules. By default Qt's qml folder is added.
 - `EXTRA_LIBS` - additional libs which will be added to your libs folder (use qualified name, e.g. libQt6WaylandClient.so.6 )
 - `EXTRA_PLUGINS` - additional plugins which will be added to your plugins folder
 - `SYSTEM_LIBS_PATHS` - the system libs path where to search system libs. Use it with caution as it's in a very early stage
 - `WAYLAND` - adds wayland client plugins needed to run your app on wayland
 - `XCB` - adds XCB plugins needed to run your app on X.org
 - `VERBOSE` - Print verbose output
