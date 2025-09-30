"""
Functionality to rebake all meshes
"""

import os
from . import butil
from . import mesh_runner
from pathlib import Path

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

class RebakeAllMeshes(Operator, butil.FolderSelectHelper):
	"""Rebakes many meshes in a selected folder"""
	
	bl_idname = "shatter.rebake_all_meshes"
	bl_label = "Rebake Many Meshes"
	
	baker: EnumProperty(
		name = "Mesh Baker",
		description = "Mesh baker to use with mass rebaking",
		items = [
			("yorshex", "Yorshex's Mesh Baker", "High quality, faithful to Smash Hit, and generally recommended"),
			("bakemesh", "BakeMesh", "Supports legacy features"),
		],
		default = "yorshex",
	)
	
	ambient_occlusion_quality: EnumProperty(
		name = "Ambient Occlusion Quality",
		description = "Higher quality ambient occlusion will look better at the expense of time taken to rebake meshes",
		items = [
			("0", "Disabled", "Ambient occlusion is disabled, very fast to export"),
			("1", "Fast", "Ambient occlusion is approximated in a decent manner, fast"),
			("2", "Precise", "Ambient occlusion is the same as in stock Smash Hit, slower"),
		],
		default = "2",
	)
	
	menu_mode: EnumProperty(
		name = "Menu Mode",
		description = "Changes culling behaviour so that menu segments look normal",
		items = [
			("auto", "Automatic", "Automatically detect if the segment should be baked in menu mode by the segment's path name"),
			("false", "Disabled", "Don't use menu mode for any meshes"),
			("true", "Enabled", "Use menu mode for all meshes"),
		],
		default = "auto",
	)
	
	def invoke(self, a, b):
		# For convinence, take the user to the segments folder if an assets path
		# is detected.
		ret = super().invoke(a, b)
		
		apk = butil.find_apk()
		
		if apk:
			self.filepath = f"{apk}/segments/"
		
		return ret
	
	def execute(self, context):
		context.window.cursor_set('WAIT')
		
		apk_path = butil.find_apk()
		templates = f"{apk_path}/templates.xml.mp3" if apk_path else None
		count = 0
		
		for dirpath, dirnames, filenames in os.walk(self.filepath):
			for filename in filenames:
				if filename.endswith((".xml.mp3", ".xml.gz.mp3")):
					count += 1
					filepath = os.path.join(dirpath, filename)
					menu_mode = should_use_menu_mode(self.menu_mode, filepath)
					mesh_runner.bake(self.baker, filepath, templates, {
						# For YMB
						"ymb_ao": self.ambient_occlusion_quality,
						"bake_menu_segment": menu_mode,
						"ymb_tiles": butil.get_setting('ymb_tiles'),
						# For BM
						"ABMIENT_OCCLUSION_ENABLED": self.ambient_occlusion_quality != "0",
						"BAKE_UNSEEN_FACES": menu_mode,
					})
		
		context.window.cursor_set('DEFAULT')
		
		self.report({'INFO'}, f"{count} meshes have been rebaked")
		return {'FINISHED'}

def should_use_menu_mode(setting, filepath):
	if setting == "true":
		return True
	elif setting == "false":
		return False
	elif setting == "auto":
		try:
			return Path(filepath).parent.parts[-1] == "menu"
		except:
			return False
	else:
		return False
