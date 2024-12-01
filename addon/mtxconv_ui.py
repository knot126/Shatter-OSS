import bpy
import bpy_extras.io_utils
from . import util

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
)

class MtxconvExtract(bpy_extras.io_utils.ImportHelper, Operator):
	"""Extract all textures from an MTX file using mtxconv"""
	
	bl_idname = "shatter.extract_mtx"
	bl_label = "Extract MTX textures"
	
	filename_ext = ".mtx.mp3"
	
	def execute(self, context):
		rc = util.run_native("mtxconv", ["extract", self.filepath])
		
		if not rc:
			self.report({'INFO'}, "Successfully extracted images from MTX file")
		else:
			self.report({'ERROR'}, f"Failed to bake MTX: mtxconv result code {rc}")
		
		return {"FINISHED"}

class MtxconvBake(bpy_extras.io_utils.ImportHelper, Operator):
	"""Bake a texture into an MTX file using mtxconv"""
	
	bl_idname = "shatter.bake_mtx"
	bl_label = "Bake MTX texture"
	
	filename_ext = ""
	
	quality: IntProperty(
		name = "JPEG Quality",
		description = "The JPEG quality that mtxconv will use when baking",
		default = 90,
		min = 0,
		max = 100,
	)
	
	version: EnumProperty(
		name = "MTX Version",
		description = "The version of the MTX format that will be used",
		items = [
			('auto', "Auto", "Automatically detect the best version of MTX to use"),
			('0', "MTX v0", "Only JPEG chunks are supported, no transparency"),
			('1', "MTX v1", "Combines a JPEG and a losslessly compressed alpha channel"),
			('2', "MTX v2", "Simple wrapper around the PVR image format"),
		],
		default = "auto",
	)
	
	def execute(self, context):
		args = ["bake", "-q", str(self.quality)]
		
		if self.version != 'auto':
			args += ['-m', self.version]
		
		args += [self.filepath]
		
		rc = util.run_native("mtxconv", args)
		
		if not rc:
			self.report({'INFO'}, "Successfully baked images to MTX file")
		else:
			self.report({'ERROR'}, f"Failed to bake MTX: mtxconv result code {rc}")
		
		return {"FINISHED"}
