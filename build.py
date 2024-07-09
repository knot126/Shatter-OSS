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

def build_yorshex_meshbake_bundle():
	os.chdir("build")
	
	# update meshbake git repo
	if (not os.path.exists("sh-meshbake")):
		run(['git', 'clone', 'https://codeberg.org/yorshex/sh-meshbake'])
	else:
		os.chdir("sh-meshbake")
		run(['git', 'pull'])
		os.chdir("..")
	
	os.chdir("sh-meshbake")
	# build for linux; we can just use shared libs that will pretty much
	# always be available
	run(['cc', '-o', 'meshbake.elf', 'meshbake.c', '-lm', '-lz', '-lexpat'])
	# windows one here ...
	os.chdir("../..")
	
	# build the bundle file
	os.makedirs("addon/shatter/bundles", exist_ok = True)
	run(['python', 'addon/shatter/bundler.py', 'make', 'bundlers/yorshex_mesh_baker.json', 'addon/shatter/bundles/yorshex_mesh_baker.bundle'])

def read_bl_info():
	BL_INFO = pathlib.Path("addon/shatter/__init__.py").read_text()
	
	# NOTE Breaks if we ever have { or } in bl_info
	BL_INFO = eval(BL_INFO[BL_INFO.index("{"):BL_INFO.index("}") + 1])
	
	return BL_INFO

def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--install-deps", help = "Install build depends (arch linux only)", action = "store_true")
	ap.add_argument("--build-yorshex-meshbake-bundle", help = "Rebuild yorshex's meshbake, bundles it and puts it in the right location (only works on linux)", action = "store_true")
	ap = ap.parse_args()
	
	os.makedirs("build", exist_ok = True)
	
	if (ap.install_deps):
		run(['sudo', 'pacman', '-Syu', 'zlib', 'expat', 'mingw-w64-gcc'])
	
	if (ap.build_yorshex_meshbake_bundle):
		build_yorshex_meshbake_bundle()
	
	# Cleanup bin and __pycache__ dirs before packing
	shutil.rmtree("addon/shatter/__pycache__", True)
	shutil.rmtree("addon/shatter/bin", True)
	
	# Make archive
	shutil.make_archive(f"build/Shatter-OSS-{'.'.join(read_bl_info()['version'])}", "zip", "addon", "addon/shatter")

if (__name__ == "__main__"):
	main()
