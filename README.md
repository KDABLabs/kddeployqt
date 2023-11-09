# kddeployqt
Deployment tool for Qt applications, similar to (android/mac/win)deployqt.

The main differences between this tool and the existing ones([linuxdeploqt](https://github.com/probonopd/linuxdeployqt), [linuxdeploy](https://github.com/linuxdeploy/linuxdeploy), [linuxdeploy](https://github.com/probonopd/linuxdeploy), etc.) are:

 - currently only linux host is supported.
 - supports any ELF based qt builds, including crossed compiled qt.
 - is written in python, which makes it so much easier to hack.
 - at this point it deploys the Qt libs, plugins and qml files for your application. The system libs support is very limited.
