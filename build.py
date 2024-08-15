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

YORSHEX_MESHBAKE_BASE_URL = "https://codeberg.org/yorshex/sh-meshbake/releases/download/1.1.3/"
ASSET_SERVER_URL = 'https://codeberg.org/yorshex/sh-asset-server/raw/branch/main/asset_server.py'

SHATTER_BINDIR = "addon/bin"
BLENDER = "blender"

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

def read_manifest():
	return tomllib.loads(Path(f"addon/blender_manifest.toml").read_text())

def get_zip_path(build_type = "ext", ext = ".zip"):
	# HACK: Parse id and version from toml since Blender can't do that when
	# passing in a filename.
	man = read_manifest()
	id = man["id"]
	version = man["version"]
	return f'./build/{id}-{version}-{build_type}{ext}'

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
	# run([BLENDER, '--command', 'extension', 'build', '--source-dir', './build/legacy', '--output-filepath', get_zip_path('legacy'), '--verbose'])
	path = get_zip_path('legacy', '')
	shutil.make_archive(path, 'zip', 'build/legacy', manifest['id'])
	print(f"Built legacy zip to {path}.zip")

def main():
	ap = argparse.ArgumentParser()
	ap.add_argument("--update-meshbake", help = "Rebuild yorshex's meshbake, bundles it and puts it in the right location (only works on linux)", action = "store_true")
	ap.add_argument("--update-asset-server", help = "Download the newest version of the asset server and place it in the right location", action = "store_true")
	ap.add_argument("--build-ext", help = "Build a Blender Extensions (Blender 4.2+) package", action = "store_true")
	ap.add_argument("--build-legacy", help = "Build a legacy addon (Blender 4.1 and earlier) package", action = "store_true")
	ap = ap.parse_args()
	
	os.makedirs("build", exist_ok = True)
	
	did_anything = False
	
	if (ap.update_meshbake):
		did_anything = True
		update_meshbake()
	
	if (ap.update_asset_server):
		did_anything = True
		update_asset_server()
	
	if (ap.build_ext):
		did_anything = True
		make_full_package()
	
	if (ap.build_legacy):
		did_anything = True
		make_legacy_package()
	
	if not did_anything:
		print(f"""Warning: No action has been preformed! You probably want to run:

  $ {sys.argv[0]} --update-meshbake --update-asset-server # Download mesh baker and asset server
  $ {sys.argv[0]} --build-ext --build-legacy # Build both extension and legacy package

... instead of invoking with no arguments.""")

if (__name__ == "__main__"):
	main()
