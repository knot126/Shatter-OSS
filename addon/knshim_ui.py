import bpy
import bpy_extras.io_utils
import os
import traceback
import json
from . import util
from . import butil
from . import knshim
from pathlib import Path
from urllib.request import urlopen, Request
from tempfile import gettempdir
from shutil import copyfileobj

from bpy.props import (
	StringProperty,
	BoolProperty,
	IntProperty,
	IntVectorProperty,
	FloatProperty,
	FloatVectorProperty,
	EnumProperty,
	PointerProperty,
)

from bpy.types import (
	Panel,
	Menu,
	Operator,
	PropertyGroup,
	AddonPreferences,
)

shim_version_info = None

def get_version_info():
	global shim_version_info
	
	if not shim_version_info:
		try:
			with urlopen(Request("https://api.github.com/repos/knot126/KnShim/releases?per_page=1", headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}), timeout=7) as u:
				shim_version_info = json.loads(u.read().decode('utf-8'))
		except:
			raise Exception("Failed to get info about the latest KnShim version; are you connected to the internet?")

def get_shim_release_title():
	try:
		return shim_version_info[0]["name"]
	except:
		return "Unknown"

def get_shim_files():
	dlpath = f"{gettempdir()}/{shim_version_info[0]['assets'][0]['name']}"
	
	try:
		if not os.path.exists(dlpath):
			url = shim_version_info[0]["assets"][0]["browser_download_url"]
			
			with urlopen(url) as e:
				with open(dlpath, "wb") as f:
					copyfileobj(e, f)
		
		return dlpath
	except:
		raise Exception("Failed to download shim files")

def do_install(apk_path):
	get_version_info()
	package = get_shim_files()
	knshim.install(package, apk_path)

def get_candidate_apks(self, context):
	return [apk.itemize() for apk in butil.list_apks()]

class InstallKnShim(Operator):
	"""Installs KnShim to an extracted Smash Hit APK"""
	
	bl_idname = "shatter.install_knshim"
	bl_label = "Install KnShim"
	
	apk_path: EnumProperty(
		name = "Package",
		description = "Select the APK to install KnShim into",
		items = get_candidate_apks,
		default = 0,
	)
	
	def execute(self, context):
		try:
			do_install(self.apk_path)
			self.report({'INFO'}, "KnShim has been installed")
		except Exception as e:
			self.report({'ERROR'}, f"KnShim could not be installed: {e.__class__.__name__}: {e}")
			util.log(traceback.format_exc())
		return {'FINISHED'}
	
	def invoke(self, context, event):
		context.window_manager.invoke_props_dialog(self)
		return {'RUNNING_MODAL'}
