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

YORSHEX_MESHBAKE_BASE_URL = "https://codeberg.org/yorshex/sh-meshbake/releases/download/1.1.9/"
ASSET_SERVER_URL = 'https://codeberg.org/yorshex/sh-asset-server/raw/branch/main/asset_server.py'

SHATTER_BINDIR = "addon/bin"
BLENDER = "blender"
MINISIGN = "minisign"

SHOULD_SIGN = False

def run(cmd):
	assert(subprocess.run(cmd).returncode == 0)

def download_file(url):
	req = urllib.request.urlopen(url)
	data = req.read()
	req.close()
	return data

def save_file(url, path):
	print(f"Downloading: {url} ...")
	Path(path).write_bytes(download_file(url))

def read_manifest(forAddon = "addon"):
	return tomllib.loads(Path(f"{forAddon}/blender_manifest.toml").read_text())

def get_zip_path(build_type = "ext", ext = ".zip", forAddon = "addon"):
	# HACK: Parse id and version from toml since Blender can't do that when
	# passing in a filename.
	man = read_manifest(forAddon)
	id = man["id"]
	version = man["version"]
	return f'./build/{id}-{version}-{build_type}{ext}'

def update_meshbake():
	print("Update meshbake and mtxconv binaries")
	
	# Remove old bin folder if there is one, make new one
	shutil.rmtree(SHATTER_BINDIR, True)
	os.makedirs(SHATTER_BINDIR)
	
	# Download mesh bake
	save_file(f"{YORSHEX_MESHBAKE_BASE_URL}meshbake-linux-amd64", f'{SHATTER_BINDIR}/meshbake.linux.x86_64')
	save_file(f"{YORSHEX_MESHBAKE_BASE_URL}meshbake-win32-amd64.exe", f'{SHATTER_BINDIR}/meshbake.win32.amd64.exe')

def update_asset_server():
	save_file(ASSET_SERVER_URL, "addon/asset_server.py")

def make_ext_package():
	manifest = read_manifest()
	run([BLENDER, '--command', 'extension', 'build', '--source-dir', './addon', '--output-filepath', get_zip_path(), '--verbose'])

def make_legacy_package():
	print("build legacy zip...")
	manifest = read_manifest()
	
	shutil.rmtree("build/legacy", True)
	shutil.copytree("addon", f"build/legacy/{manifest['id']}")
	os.chdir(f"build/legacy/{manifest['id']}")
	
	# do modifications needed for legacy zip
	# first: bl_info
	bl_info = f"bl_info = {repr({
		'name': manifest['name'],
		'author': manifest['maintainer'].split()[0],
		'version': tuple([int(x) for x in manifest['version'].split('.')]),
		'blender': tuple([int(x) for x in manifest['blender_version_min'].split('.')]),
		'location': '3DView',
		'description': manifest['tagline'],
		'warning': '',
		'support': 'COMMUNITY',
		'wiki_url': manifest['website'],
		'tracker_url': '',
		'category': manifest['tags'][0],
	})}\n\n"
	
	Path("__init__.py").write_text(bl_info + Path("__init__.py").read_text())
	
	# second: update `from . import` to `from shatter import`
	for f in os.listdir():
		if (os.path.isfile(f)):
			Path(f).write_text(Path(f).read_text().replace("from . import ", f"from {manifest['id']} import "))
	
	# third: make blender manifest as a json
	Path("blender_manifest.json").write_text(json.dumps(manifest))
	
	os.chdir("../../..")
	path = get_zip_path('legacy', '')
	shutil.make_archive(path, 'zip', 'build/legacy', manifest['id'])
	print(f"Built legacy zip to {path}.zip")

def make_autogen_ext_package():
	manifest = read_manifest("autogen")
	run([BLENDER, '--command', 'extension', 'build', '--source-dir', './autogen', '--output-filepath', get_zip_path(forAddon="autogen"), '--verbose'])
	sign(get_zip_path(), f"autogen {manifest['version']} ext")

def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--update-meshbake", help = "Download the newest version of YMB", action = "store_true")
	ap.add_argument("--update-yas", help = "Download the newest version of YAS", action = "store_true")
	ap.add_argument("--autogen", help = "Build a Blender Extensions (Blender 4.2+) package for the autogen addon", action = "store_true")
	ap.add_argument("--legacy", help = "Build a package for older blender versions", action = "store_true")
	ap = ap.parse_args()
	
	os.makedirs("build", exist_ok = True)
	
	if ap.update_meshbake:
		update_meshbake()
	
	if ap.update_yas:
		update_asset_server()
	
	if ap.legacy:
		make_legacy_package()
	else:
		make_ext_package()
	
	if ap.autogen:
		make_autogen_ext_package()

if (__name__ == "__main__"):
	main()
