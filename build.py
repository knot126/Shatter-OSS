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

def run(cmd):
	assert(subprocess.run(cmd).returncode == 0)

YORSHEX_MESHBAKE_GIT_URL = 'https://codeberg.org/yorshex/sh-meshbake'
EXPAT_TAR_GZ = 'https://github.com/libexpat/libexpat/releases/download/R_2_6_2/expat-win32bin-2.6.2.zip'
ZLIB_TAR_GZ = 'https://zlib.net/zlib-1.3.1.tar.gz'

# taken from CMakeLists.txt
ZLIB_SRC_FILES = """adler32.c
    compress.c
    crc32.c
    deflate.c
    gzclose.c
    gzlib.c
    gzread.c
    gzwrite.c
    inflate.c
    infback.c
    inftrees.c
    inffast.c
    trees.c
    uncompr.c
    zutil.c""".split()

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
	os.chdir("Expat/Source")
	run(['cmake', '.', '-D', 'CMAKE_C_COMPILER=x86_64-w64-mingw32-gcc', '-D', 'CMAKE_CXX_COMPILER=x86_64-w64-mingw32-g++'])
	os.chdir("../..")
	run(['x86_64-w64-mingw32-gcc', '-o', 'meshbake.exe', '-Izlib-1.3.1', '-IExpat/Source', '-IExpat/Source/lib', 'meshbake.c'] + ["zlib-1.3.1/" + x for x in ZLIB_SRC_FILES] + ['Expat/Source/lib/' + x for x in EXPAT_SRC_FILES])
	os.chdir("../..")
	
	# build the bundle file
	os.makedirs("addon/shatter/bundles", exist_ok = True)
	run(['python', 'addon/shatter/bundler.py', 'make', 'bundlers/yorshex_mesh_baker.json', 'addon/shatter/bundles/yorshex_mesh_baker.bundle'])

def read_bl_info():
	BL_INFO = Path("addon/shatter/__init__.py").read_text()
	
	# NOTE Breaks if we ever have { or } in bl_info
	BL_INFO = eval(BL_INFO[BL_INFO.index("{"):BL_INFO.index("}") + 1])
	
	return BL_INFO

def read_version():
	return '.'.join([str(x) for x in read_bl_info()['version']])

def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--install-deps", help = "Install build depends (arch linux only)", action = "store_true")
	ap.add_argument("--build-yorshex-meshbake-bundle", help = "Rebuild yorshex's meshbake, bundles it and puts it in the right location (only works on linux)", action = "store_true")
	ap = ap.parse_args()
	
	os.makedirs("build", exist_ok = True)
	
	if (ap.install_deps):
		run(['sudo', 'pacman', '-Syu', 'zlib', 'expat', 'mingw-w64-gcc', 'unzip', 'cmake'])
	
	if (ap.build_yorshex_meshbake_bundle):
		build_yorshex_meshbake_bundle()
	
	# Cleanup bin and __pycache__ dirs before packing
	shutil.rmtree("addon/shatter/__pycache__", True)
	shutil.rmtree("addon/shatter/bin", True)
	
	# Make archive
	shutil.make_archive(f"build/Shatter-OSS-{read_version()}", "zip", "addon", "shatter")

if (__name__ == "__main__"):
	main()
