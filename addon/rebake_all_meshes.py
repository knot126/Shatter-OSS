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

def get_candidate_apks(self, context):
	apks = []
	
	for ad in butil.find_assets_paths(search_default=False):
		ad = str(Path(ad).parent)
		apks.append((ad, ad, ad))
	
	return apks

class RebakeAllMeshes(Operator):
	"""Rebakes all meshes in an APK (alpha)"""
	
	bl_idname = "shatter.rebake_all_meshes"
	bl_label = "Rebake all meshes"
	
	apk_path: EnumProperty(
		name = "APK Path",
		description = "Select the APK to rebake all meshes for",
		items = get_candidate_apks,
		default = 0,
	)
	
	def execute(self, context):
		for dirpath, dirnames, filenames in os.walk(self.apk_path + "/assets/segments"):
			for filename in filenames:
				if filename.endswith((".xml.mp3", ".xml.gz.mp3")):
					filepath = os.path.join(dirpath, filename)
					mesh_runner.bake("yorshex", filepath, self.apk_path + "/assets/templates.xml.mp3")
		
		self.report({'INFO'}, "Meshes have been rebaked!")
		return {'FINISHED'}
	
	def invoke(self, context, event):
		context.window_manager.invoke_props_dialog(self)
		return {'RUNNING_MODAL'}
