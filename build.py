#!/usr/bin/env python3
"""
Build a Shatter zip file for installation
"""

import os
import sys
import argparse
import shutil
import subprocess
from pathlib import Path
import json
import urllib.request
import tomllib

def run(cmd):
	assert(subprocess.run(cmd).returncode == 0)

YORSHEX_MESHBAKE_GIT_URL = 'https://codeberg.org/yorshex/sh-meshbake'
EXPAT_TAR_GZ = 'https://github.com/libexpat/libexpat/releases/download/R_2_6_2/expat-win32bin-2.6.2.zip'
ZLIB_TAR_GZ = 'https://zlib.net/zlib-1.3.1.tar.gz'
ASSET_SERVER_URL = 'https://raw.githubusercontent.com/yorshex/sh-asset-server/main/asset_server.py'

SHATTER_BINDIR = "addon/bin"
BLENDER = "/home/dragon/Downloads/blender-4.2.0-linux-x64/blender"

# taken from CMakeLists.txt
ZLIB_SRC_FILES = "adler32.c compress.c crc32.c deflate.c gzclose.c gzlib.c gzread.c gzwrite.c inflate.c infback.c inftrees.c inffast.c trees.c uncompr.c zutil.c".split()

EXPAT_SRC_FILES = "xmlparse.c  xmlrole.c  xmltok.c  xmltok_impl.c  xmltok_ns.c".split()

def build_yorshex_meshbake_bundle():
	os.chdir("build")
	
	# update meshbake git repo
	if (not os.path.exists("sh-meshbake")):
		run(['git', 'clone', YORSHEX_MESHBAKE_GIT_URL])
		os.chdir("sh-meshbake")
		run(['wget', EXPAT_TAR_GZ])
		run(['wget', ZLIB_TAR_GZ])
		os.makedirs("Expat", exist_ok = True)
		run(['unzip', 'expat-win32bin-2.6.2.zip', '-d', 'Expat'])
		run(['tar', '-xvzf', 'zlib-1.3.1.tar.gz'])
	else:
		os.chdir("sh-meshbake")
		run(['git', 'pull'])
	
	# build for linux; we can just use shared libs that will pretty much
	# always be available
	print("BUILD: Linux")
	run(['cc', '-o', 'meshbake.elf', 'meshbake.c', '-lm', '-lz', '-lexpat'])
	# windows one here ...
	print("BUILD: Windows")
	run(['cp', '../../payloads/expat_config.h', 'Expat/Source/expat_config.h'])
	run(['x86_64-w64-mingw32-gcc', '-o', 'meshbake.exe', '-Izlib-1.3.1', '-IExpat/Source', '-IExpat/Source/lib', 'meshbake.c'] + ["zlib-1.3.1/" + x for x in ZLIB_SRC_FILES] + ['Expat/Source/lib/' + x for x in EXPAT_SRC_FILES])
	os.chdir("../..")
	
	# build the bundle file
	shutil.rmtree(SHATTER_BINDIR, True)
	os.makedirs(SHATTER_BINDIR)
	run(['cp', 'build/sh-meshbake/meshbake.elf', f'{SHATTER_BINDIR}/yorshex_mesh_baker.linux.x86_64'])
	run(['cp', 'build/sh-meshbake/meshbake.exe', f'{SHATTER_BINDIR}/yorshex_mesh_baker.win32.amd64.exe'])

def download_file(url):
	req = urllib.request.urlopen(url)
	data = req.read()
	req.close()
	return data

def update_asset_server():
	Path("addon/asset_server.py").write_bytes(download_file(ASSET_SERVER_URL))

def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--install-deps", help = "Install build depends (arch linux only)", action = "store_true")
	ap.add_argument("--build-yorshex-meshbake-bundle", help = "Rebuild yorshex's meshbake, bundles it and puts it in the right location (only works on linux)", action = "store_true")
	ap.add_argument("--update-asset-server", help = "Download the newest version of the asset server and place it in the right location", action = "store_true")
	ap = ap.parse_args()
	
	os.makedirs("build", exist_ok = True)
	
	if (ap.install_deps):
		run(['sudo', 'pacman', '-Syu', 'zlib', 'expat', 'mingw-w64-gcc', 'unzip', 'cmake'])
	
	if (ap.build_yorshex_meshbake_bundle):
		build_yorshex_meshbake_bundle()
	
	if (ap.update_asset_server):
		update_asset_server()
	
	# Build the blender extension
	run([BLENDER, '--command', 'extension', 'build', '--source-dir', './addon', '--output-dir', './build', '--verbose'])

if (__name__ == "__main__"):
	main()
