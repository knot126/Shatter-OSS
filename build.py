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

YORSHEX_MESHBAKE_BASE_URL = "https://codeberg.org/yorshex/sh-meshbake/releases/download/1.0.0/"
ASSET_SERVER_URL = 'https://raw.githubusercontent.com/yorshex/sh-asset-server/main/asset_server.py'

SHATTER_BINDIR = "addon/bin"
BLENDER = "/home/dragon/Downloads/blender-4.2.0-linux-x64/blender"

def run(cmd):
	assert(subprocess.run(cmd).returncode == 0)

def download_file(url):
	req = urllib.request.urlopen(url)
	data = req.read()
	req.close()
	return data

def save_file(url, path):
	Path(path).write_bytes(download_file(url))

def read_manifest():
	return tomllib.loads(Path(f"addon/blender_manifest.toml").read_text())

def get_zip_path(build_type = "ext"):
	# HACK: Parse id and version from toml since Blender can't do that when
	# passing in a filename.
	man = read_manifest()
	id = man["id"]
	version = man["version"]
	return f'./build/{id}-{version}-{build_type}.zip'

def update_meshbake():
	print("Update meshbake binaries")
	
	# Remove old bin folder if there is one, make new one
	shutil.rmtree(SHATTER_BINDIR, True)
	os.makedirs(SHATTER_BINDIR)
	
	# Download mesh bake
	save_file(f"{YORSHEX_MESHBAKE_BASE_URL}meshbake-linux-amd64", f'{SHATTER_BINDIR}/yorshex_mesh_baker.linux.x86_64')
	save_file(f"{YORSHEX_MESHBAKE_BASE_URL}meshbake-win32-amd64.exe", f'{SHATTER_BINDIR}/yorshex_mesh_baker.win32.amd64.exe')

def update_asset_server():
	save_file(ASSET_SERVER_URL, "addon/asset_server.py")

def make_full_package():
	run([BLENDER, '--command', 'extension', 'build', '--source-dir', './addon', '--output-filepath', get_zip_path(), '--verbose'])

def make_legacy_package():
	shutil.rmtree("build/legacy", True)
	shutil.copytree("addon", "build/legacy")
	os.chdir("build/legacy")
	# do modifications needed for legacy zip
	os.chdir("../..")
	run([BLENDER, '--command', 'extension', 'build', '--source-dir', './build/legacy', '--output-filepath', get_zip_path('legacy'), '--verbose'])

def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--install-deps", help = "Install build depends (arch linux only)", action = "store_true")
	ap.add_argument("--update-meshbake", help = "Rebuild yorshex's meshbake, bundles it and puts it in the right location (only works on linux)", action = "store_true")
	ap.add_argument("--update-asset-server", help = "Download the newest version of the asset server and place it in the right location", action = "store_true")
	ap = ap.parse_args()
	
	os.makedirs("build", exist_ok = True)
	
	if (ap.install_deps):
		run(['sudo', 'pacman', '-Syu', 'zlib', 'expat', 'mingw-w64-gcc', 'unzip', 'cmake'])
	
	if (ap.update_meshbake):
		update_meshbake()
	
	if (ap.update_asset_server):
		update_asset_server()
	
	# Build the blender extension
	make_full_package()

if (__name__ == "__main__"):
	main()
