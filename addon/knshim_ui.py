import bpy
import bpy_extras.io_utils
import os
from . import butil
from . import knshim
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

class InstallKnShim(Operator):
	"""Installs KnShim to an extracted Smash Hit APK"""
	
	bl_idname = "shatter.install_knshim"
	bl_label = "Install KnShim"
	
	apk_path: EnumProperty(
		name = "APK Path",
		description = "Select the APK to install KnShim into",
		items = get_candidate_apks,
		default = 0,
	)
	
	def execute(self, context):
		knshim.install(self.apk_path)
		self.report({'INFO'}, "KnShim has been installed")
		return {'FINISHED'}
	
	def invoke(self, context, event):
		context.window_manager.invoke_props_dialog(self)
		return {'RUNNING_MODAL'}
