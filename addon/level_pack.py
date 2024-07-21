import util
import zipfile
import json
import os

def make_file_list(assets, level):
	"""
	Prepare a list of files to archive for a level
	"""
	
	files = ["templates.xml.mp3", f"levels/{level}.xml.mp3"]
	files += [f"rooms/{level}/{x}" for x in util.list_folder(f"{assets}/rooms/{level}", False)]
	files += [f"segments/{level}/{x}" for x in util.list_folder(f"{assets}/segments/{level}", False)]
	
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

def pack(assets, outpath, level, info = {}):
	"""
	Make a level ZIP package of the given level
	"""
	
	# Enumerate the files to export
	files = make_file_list(assets, level)
	
	# Open the new zip file
	z = zipfile.ZipFile(outpath, "w")
	
	# Start writing files to archive
	for f in files:
		fn = f"{assets}/{f}"
		print(f"Add file to archive: {fn}")
		z.writestr(f, util.get_file_raw(fn))
	
	# Write the package info file
	z.writestr("package.json", json.dumps(info, sort_keys = True, indent = 4))
	
	# Write install info file
	z.writestr("install.json", json.dumps(make_install_json(files), indent = 4))
	
	# Finalise the zip file
	z.close()