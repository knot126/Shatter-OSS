"""
Shatter Updater

TODO: (Important) Move to a better cryptography library for signing
This looks better than Python-RSA imo: https://github.com/wbond/oscrypto

NOTE: Contact cddepppp256<@]gmail(.}com for sensitive security issues.
"""

import json
from pathlib import Path
from hashlib import sha3_384
from multiprocessing import Process
import traceback
import os

import common
import util

class Update():
	"""
	Class representing an update
	
	TODO This does not need to be a class, could just be a dict
	"""
	
	def __init__(self, release_channel, version, download, hash):
		self.release_channel = release_channel
		self.version = version
		self.download = download
		self.hash = hash

def download_json(source):
	"""
	Download JSON file
	"""
	
	data = util.http_get_signed(source)
	
	if (not data): return data
	
	return json.loads(data)

def download_and_install_update(url, hash):
	import shutil, pathlib
	
	util.log(f"Downloading an update where:\n\turl = {url}\n\thash = {hash}")
	
	# Download data
	data = util.http_get_with_expected_hash(url, hash)
	
	if (not data):
		util.log("Update zip file failed to download or verify properly")
		return
	
	# Get the local file path
	path = common.TOOLS_HOME_FOLDER + "/" + url.split("/")[-1].replace("/", "").replace("\\", "")
	
	# Write the data
	pathlib.Path(path).write_bytes(data)
	
	util.log(f"Downloaded latest update to '{path}', extracting files now...")
	
	# Extract the files (installs update)
	shutil.unpack_archive(path, common.BLENDER_ADDONS_PATH, "zip")
	
	util.log("Addon has been updated")

def version_compare(current, candidate, or_eq = False):
	"""
	Return True if candidate is greater than (or, if or_eq is set, if it's equal
	to) current, otherwise return False.
	
	e.g. vcmp(current, candidate) = candidate > current
	
	NOTE This is less dumb than the older function :P
	"""
	
	min_len = min(len(current), len(candidate))
	
	for i in range(min_len):
		# If the new version is bigger at this value, we can say it's new
		if (candidate[i] > current[i]):
			return True
		# If the candidate version is less than the current, we can say it's less
		elif (candidate[i] < current[i]):
			return False
	
	# In the case that they both have the same start to the version but the
	# candidate version has more array entries, we trust the new version.
	if (len(current) < len(candidate)):
		return True
	
	return or_eq

def get_latest_version(current_version, release_channel, current_blender):
	"""
	Check the new version against the current version
	"""
	
	info = download_json(common.UPDATE_INFO)
	
	# Fake info for updater test
	if (release_channel == "updatertest"):
		info = {
			"updatertest": {
				"version": [9999, 99, 99],
				"blender_version": [3, 0, 0],
				"download": "http://smashhitlab.000webhostapp.com/empty.zip",
				"hash": "b4dacd4a8d243b009c8b0cd0efcd00098a9adec682fd5bf0b736e94fd3caa692",
			},
			"vt_min": 0,
			"vt_max": 2699330830,
		}
	
	if (not info):
		util.log("Could not get update info")
		return None
	
	if ("vt_min" not in info or info["vt_min"] > util.get_time()):
		util.log("Update info file is too new (clock is probably set wrong) or missing 'vt_min'")
		return None
	
	if ("vt_max" not in info or info["vt_max"] < util.get_time()):
		daysAgo = (util.get_time() - info["vt_max"]) // 86400
		util.log(f"Update info file is too old (expired {daysAgo} days ago) or missing 'vt_max'")
		return None
	
	info = info.get(release_channel, None)
	
	# No info on release channel
	if (info == None):
		util.log("No info for release channel")
		return None
	
	new_version = info.get("version", None)
	
	# Do not prompt to update things with version set to null
	if (new_version == None):
		util.log("No new version was put (bad file?)")
		return None
	
	# Check if the version is actually new
	if (not version_compare(current_version, new_version)):
		util.log(f"Current version ({current_version}) matches or is newer than latest version ({new_version})")
		return None
	
	blender_version_requirement = info.get("blender_version", [2, 60, 0])
	
	# Check if the required blender version is too great
	if (version_compare(current_blender, blender_version_requirement, True)):
		util.log("Blender too old to update")
		return None
	
	# Create the update object, if we need to use it
	update = Update(release_channel, new_version, info.get("download", None), info.get("hash", None))
	
	return update

def run_updater_task(current_version, channel, blender_version):
	"""
	Check for and install an update
	"""
	
	try:
		update = get_latest_version(current_version, channel, blender_version)
		
		if (update != None):
			download_and_install_update(update.download, update.hash)
		
		os._exit(0)
	except:
		util.log(traceback.print_exc())
		os._exit(1)

def run_updater(current_version, channel, blender_version):
	"""
	Run the updater async
	"""
	
	p = Process(target = run_updater_task, args = (current_version, channel, blender_version))
	p.start()
