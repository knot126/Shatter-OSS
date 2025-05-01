#!/usr/bin/env python3
try:
	from . import util
except:
	import util
import zipfile
import gzip
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_obstacles_from_level(level_file):
	try:
		root = ET.fromstring(Path(level_file).read_text())
	except:
		return set()
	
	obstacles = set()
	
	if root.tag != "segment":
		return obstacles
	
	for element in root:
		if element.tag == "obstacle":
			obstacles.add(f"obstacles/{element.attrib['type']}.lua.mp3")
	
	return obstacles

def parse_music_from_room(room_file):
	try:
		room = Path(room_file).read_text()
	except:
		return set()
	
	musics = set()
	
	for m in re.finditer(r"mgMusic\([\'\"]([^\'\"]+)[\'\"]\)", room):
		musics.add(f"music/{m[1]}.ogg.mp3")
	
	return musics

def make_obstacle_list(assets, segments):
	obstacles = set()
	
	for seg in segments:
		obstacles |= parse_obstacles_from_level(f"{assets}/{seg}")
	
	return list(obstacles)

def make_music_list(assets, rooms):
	musics = set()
	
	for room in rooms:
		musics |= parse_music_from_room(f"{assets}/{room}")
	
	return list(musics)

def make_file_list(assets, level, extras = []):
	"""
	Prepare a list of files to archive for a level
	"""
	
	rooms = [f"rooms/{level}/{x}" for x in util.list_folder(f"{assets}/rooms/{level}", False)]
	segments = [f"segments/{level}/{x}" for x in util.list_folder(f"{assets}/segments/{level}", False)]
	
	files = ["materials.xml.mp3", "templates.xml.mp3", f"levels/{level}.xml.mp3"]
	files += rooms
	files += segments
	files += make_obstacle_list(assets, segments)
	files += make_music_list(assets, rooms)
	
	for extra_folder in extras:
		if type(extra_folder) == str:
			files += [f"{extra_folder}/{x}" for x in util.list_folder(f"{assets}/{extra_folder}", False)]
	
	return files

def make_install_json(files):
	"""
	Make the install.json file
	"""
	
	root = {
		"format": 1,
	}
	
	# NOTE Don't make the joke about this symbol name
	flist = []
	
	for f in files:
		f = f.replace("\\", "/")
		
		# If a file is in the root folder, we want to merge it, otherwise
		# replace
		conflict_action = "replace" if "/" in f else "merge"
		
		flist.append({
			"file": f,
			"conflict": conflict_action,
		})
	
	root["files"] = flist
	
	return root

def pack(assets, outpath, level, info = {}, extras = []):
	"""
	Make a level ZIP package of the given level
	"""
	
	# Enumerate the files to export
	files = make_file_list(assets, level, extras)
	
	# Open the new zip file
	z = zipfile.ZipFile(outpath, "w")
	
	# Start writing files to archive
	for f in files:
		fn = f"{assets}/{f}"
		print(f"Add file to archive: {fn}")
		
		if (f.endswith(".gz.mp3")):
			z.writestr(f[:-7], gzip.decompress(util.get_file_raw(fn)))
		elif (f.endswith(".mp3")):
			z.writestr(f[:-4], util.get_file_raw(fn))
		else:
			z.writestr(f, util.get_file_raw(fn))
	
	# Write the package info file
	z.writestr("package.json", json.dumps(info, sort_keys = True, indent = 4))
	
	# Finalise the zip file
	z.close()

def main():
	import argparse
	args = argparse.ArgumentParser(prog="level_pack", description="Pack a Smash Hit level to a ZIP file for use with Hyperspace")
	args.add_argument("assets", help="Assets directory")
	args.add_argument("outpath", help="Output ZIP file")
	args.add_argument("level", help="Level name")
	args.add_argument("--hud", action="store_true", help="Enable HUD packing")
	args = args.parse_args()
	
	pack(args.assets, args.outpath, args.level, {
		"name": args.level,
		"creator": "Somebody",
		"verid": 10000,
		"version": "1.0.0",
		"org.knot126.smashhit.tulip": {
			"level": args.level,
			"balls": 100,
			"streak": 20,
		}
	}, 
	["hud", "fonts"] if args.hud else [])

if __name__ == "__main__":
	main()
