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
	bl_label = "Rebake many meshes"
	
	baker: EnumProperty(
		name = "Mesh baker",
		description = "Mesh baker to use with mass rebaking",
		items = [
			("yorshex", "Yorshex's Mesh Baker", "High quality, faithful to Smash Hit, and generally recommended"),
			("bakemesh", "BakeMesh", "Supports legacy features"),
		],
		default = "yorshex",
	)
	
	ambient_occlusion_quality: EnumProperty(
		name = "Ambient occlusion quality",
		description = "Higher quality ambient occlusion will look better at the expense of time taken to rebake meshes",
		items = [
			("0", "Disabled", "Ambient occlusion is disabled, very fast to export"),
			("1", "Fast", "Ambient occlusion is approximated in a decent manner, fast"),
			("2", "Precise", "Ambient occlusion is the same as in stock Smash Hit, slower"),
		],
		default = "2",
	)
	
	menu_mode: BoolProperty(
		name = "Menu mode",
		description = "Changes culling behaviour so that menu segments look normal",
		default = False,
	)
	
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
					mesh_runner.bake(self.baker, filepath, templates, {
						# For YMB
						"ymb_ao": self.ambient_occlusion_quality,
						"bake_menu_segment": self.menu_mode,
						"ymb_tiles": butil.get_setting('ymb_tiles'),
						# For BM
						"ABMIENT_OCCLUSION_ENABLED": self.ambient_occlusion_quality != "0",
						"BAKE_UNSEEN_FACES": self.menu_mode,
					})
		
		context.window.cursor_set('DEFAULT')
		
		self.report({'INFO'}, f"{count} meshes have been rebaked")
		return {'FINISHED'}
