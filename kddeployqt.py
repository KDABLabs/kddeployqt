#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
import argparse
import json
import re
from pathlib import Path

parser = argparse.ArgumentParser(description='Deploy Qt application')
parser.add_argument('--output', help='The output folder', required=True)
parser.add_argument('--executable', help='The path to the executable', required=True)

parser.add_argument('--qmake', help='The path to qmake')
parser.add_argument('--readelf', help='The path to the readlelf')

parser.add_argument('--bin', default='bin', help='The path to the application bin folder')
parser.add_argument('--lib', default='lib', help='The path to the application lib folder')
parser.add_argument('--plugins', default='plugins', help='The path to the application plugins folder')
parser.add_argument('--qml', default='qml', help='The path to the application qml folder')

parser.add_argument('--qml_root_path', action='append', default=[], help='The root path of the qml files. Can be used multiple times')
parser.add_argument('--qml_import_path', action='append', default=[], help='The import path of the qml files. Can be used multiple times')
parser.add_argument('--extra-libs', action='append', default=[], help='Additional libs (use qualified name, e.g. libQt6WaylandClient.so.6 ). Can be used multiple times')
parser.add_argument('--extra-plugins', action='append', default=[], help='Additional plugins. Can be used multiple times')
parser.add_argument('--system_libs_path', action='append', default=[], help='The system libs path where to search system libs. Can be used multiple times')
parser.add_argument('--wayland', action='store_true', help='Add wayland support')
parser.add_argument('--verbose', action='store_true', help='Print verbose output')

args = parser.parse_args()

# check if the executable exists
if not os.path.isfile(args.executable):
    print('The executable does not exist')
    sys.exit(1)

# check if the qmake exists
if not args.qmake or not os.path.isfile(args.qmake):
    if (args.verbose):
        print('The qmake does not exist, trying to find it')
    args.qmake = shutil.which('qmake')
    if not os.path.isfile(args.qmake):
        sys.exit(1)

# check if the readelf exists
if not args.readelf or not os.path.isfile(args.readelf):
    if (args.verbose):
        print('The readelf does not exist, trying to find it')
    args.readelf = shutil.which('readelf')
    if not os.path.isfile(args.readelf):
        sys.exit(1)

if (args.verbose):
    print('Using qmake: ' + args.qmake)
    print('Using readelf: ' + args.readelf)

# create the output bin, lib, qml & plugins folders
if (args.verbose):
    print('Creating the output folders\n\t{}\n\t{}\n\t{}\n\t{}'.format(os.path.join(args.output, args.bin), os.path.join(args.output, args.lib), os.path.join(args.output, args.qml), os.path.join(args.output, args.plugins)))
os.makedirs(os.path.join(args.output, args.bin), exist_ok=True)
os.makedirs(os.path.join(args.output, args.lib), exist_ok=True)
os.makedirs(os.path.join(args.output, args.qml), exist_ok=True)
os.makedirs(os.path.join(args.output, args.plugins), exist_ok=True)

out_libs_dir = os.path.join(args.output, args.lib)
out_plugins_dir = os.path.join(args.output, args.plugins)
out_qml_dir = os.path.join(args.output, args.qml)

# copy the executable to the bin folder if it does not exist
if not os.path.isfile(os.path.join(args.output, args.bin, os.path.basename(args.executable))):
    if (args.verbose):
        print('Copying the executable to the output folder {}'.format(os.path.join(args.output, args.bin)))
    shutil.copy(args.executable, os.path.join(args.output, args.bin))

# plugins dictionary
# usesful until we can get the plugins info from libs folder as we do on android
plugins = {
            'Qt63DInput': ['3dinputdevices'],
            'Qt63DRender': ['sceneparsers', 'geometryloaders', 'renderplugins', 'renderers'],
            'Qt6Core': ['platforms', 'tracing'],
            'Qt6Designer': ['designer'],
            'Qt6EglFSDeviceIntegration': ['egldeviceintegrations'],
            'Qt6Gui': ['accessiblebridge', 'platforms', 'xcbglintegrations', 'platformthemes', 'platforminputcontexts', 'generic', 'iconengines', 'imageformats', 'egldeviceintegrations'],
            'Qt6Location': ['geoservices'],
            'Qt6Multimedia': ['multimedia'],
            'Qt6Network': ['tls', 'networkinformation'],
            'Qt6OpcUa': ['opcua'],
            'Qt6Positioning': ['position'],
            'Qt6PrintSupport': ['printsupport'],
            'Qt6Qml': ['qmltooling'],
            'Qt6QmlCompilerPrivate': ['qmllint'],
            'Qt6Quick': ['scenegraph'],
            'Qt6Quick3DAssetImport': ['assetimporters'],
            'Qt6Scxml': ['scxmldatamodel'],
            'Qt6Sensors':['sensors'],
            'Qt6SerialBus': ['canbus'],
            'Qt6Sql': ['sqldrivers'],
            'Qt6Svg': ['iconengines'],
            'Qt6TextToSpeech': ['texttospeech'],
            'Qt6WaylandClient': ['wayland-decoration-client', 'wayland-inputdevice-integration', 'wayland-shell-integration'],
            'Qt6WaylandCompositor': ['wayland-graphics-integration-server', 'wayland-hardware-layer-integration'],
            'Qt6WebView': ['webview'],
            'Qt6Widgets': ['styles'],
           }
parsed_dependencies = []

#run qmake to get the platform specs
qmake_output = subprocess.check_output([args.qmake, '-query']).decode('utf-8')
lines = qmake_output.split('\n')
for line in lines:
    if 'QT_INSTALL_PLUGINS' in line:
        plugins_dir = line.split(':')[1]
    if 'QT_INSTALL_LIBS' in line:
        libs_dir = line.split(':')[1]
    if 'QT_INSTALL_QML' in line:
        qml_dir = line.split(':')[1]
    if 'QT_HOST_BINS' in line:
        host_bins = line.split(':')[1]
    if 'QT_HOST_LIBEXECS' in line:
        host_libexecs = line.split(':')[1]

executables = [args.executable]

if args.wayland:
    args.extra_plugins.append('wayland-decoration-client')
    args.extra_plugins.append('wayland-graphics-integration-client')
    args.extra_plugins.append('wayland-shell-integration')

def find_relative_path(path):
    for root in args.qml_root_path:
        if path.startswith(root):
            p = path.replace(root, '')
            if (p.startswith('/')):
                p = p[1:]
            return p
    raise Exception('Could not find relative path for ' + path)

qml_plugins = []
# run qmlimportscanner to get the qml dependencies if qml_root_path exists
if args.qml_root_path:
    scanner = [os.path.join(host_libexecs, 'qmlimportscanner'), '-importPath', qml_dir]
    for path in args.qml_root_path:
        scanner.append('-rootPath')
        scanner.append(path)

    for path in args.qml_import_path:
        scanner.append('-importPath')
        scanner.append(path)
    imports = json.loads(subprocess.check_output(scanner).decode('utf-8'))
    for imp in imports:
        if not 'path' in imp:
            print('Skipping {} as it is not found'.format(imp['name']))
            continue
        path = imp['path']
        if not os.path.exists(path):
            print('Skipping {} as it is not found'.format(path))
            continue

        try:
            out_path = os.path.join(out_qml_dir, imp['relativePath'] if 'relativePath' in imp else find_relative_path(path))
        except Exception as e:
            print(e)
            continue
        if (args.verbose):
            print('Copying from {} to {}'.format(path, out_path))
        if os.path.isdir(path):
            shutil.copytree(path, out_path, dirs_exist_ok=True)
        else:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            shutil.copyfile(path, out_path)
        if 'plugin' in imp:
            if (args.verbose):
                print('Found plugin ' + imp['plugin'])
            qml_plugins.append('lib{}.so'.format(imp['plugin']))

    # scan for all .so.* files in qml folder
    for root, dirs, files in os.walk(out_qml_dir):
        for file in files:
            if (file in qml_plugins):
                if (args.verbose):
                    print('Adding {} to the executables'.format(file))
                executables.append(os.path.join(root, file))


def copy_plugins(plugins):
        for plugin in plugins:
            from_path = os.path.join(plugins_dir, plugin)
            if (os.path.exists(from_path)):
                if (args.verbose):
                    print('\t\tcopying {} to {}'.format(from_path, out_plugins_dir))
                shutil.copytree(from_path, os.path.join(out_plugins_dir, plugin), dirs_exist_ok=True)
                for root, dirs, files in os.walk(os.path.join(out_plugins_dir, plugin)):
                    for file in files:
                        if file.endswith('.so'):
                            if args.verbose:
                                print('Adding {} to the executables'.format(file))
                            executables.append(os.path.join(root, file))

copy_plugins(args.extra_plugins)

def copy_library(lib):
    parsed_dependencies.append(lib)
    dep = Path(lib).stem
    while Path(dep).suffixes:
        dep = Path(dep).stem
    dep = dep[3:]

    lib = os.path.join(libs_dir, lib)
    shutil.copy(lib, out_libs_dir)
    if (args.verbose):
        print('\tcopying {} to {}'.format(lib, out_libs_dir))
    inspect_file_recursive(lib)

    if (dep in  plugins):
        copy_plugins(plugins[dep])


# inspect a file using readelf
def inspect_file_recursive(file):
    if (args.verbose):
        print('Inspecting ' + file)
    try:
        output = subprocess.check_output([args.readelf, '-d', file]).decode('utf-8')
    except Exception as e:
        print("Error while inspecting " + file + ": " + str(e))
        return
    lines = output.split('\n')

    dependencies = []
    for line in lines:
        regex = re.compile(r'.*\(NEEDED\).*\[(.*)\]')
        match = regex.match(line)
        if match:
            dependencies.append(match.group(1))

    # remove already parsed_dependencies
    dependencies = [x for x in dependencies if x not in parsed_dependencies]
    if (args.verbose):
        print('\tfound dependencies: ' + str(dependencies))
    for dependency in dependencies:
        # check if file exists in the libs_dir
        if os.path.isfile(os.path.join(libs_dir, dependency)):
            copy_library(dependency)
        else:
            for path in args.system_libs_path:
                lib = os.path.join(path, dependency)
                if os.path.isfile(lib):
                    if (args.verbose):
                        print('\tcopying {} to {}'.format(lib, out_libs_dir))
                    shutil.copy(lib, out_libs_dir)
                    break

for executable in executables:
    inspect_file_recursive(executable)

# copy extra libs
for lib in args.extra_libs:
    copy_library(lib)

# last but not least create qt.conf file into bin folder
if (args.verbose):
    print('Creating qt.conf file into bin folder')
with open(os.path.join(args.output, args.bin, 'qt.conf'), 'w') as f:
    f.write('[Paths]\n')
    f.write('Prefix = ..\n')
    f.write('Binaries = ' + args.bin + '\n')
    f.write('Libraries = ' + args.lib + '\n')
    f.write('Plugins = ' + args.plugins + '\n')
    f.write('Imports = ' + args.qml + '\n')
    f.write('QmlImports = ' + args.qml + '\n')
