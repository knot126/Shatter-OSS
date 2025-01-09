import bpy
import bpy_extras.io_utils
import os
from . import butil
from . import level_pack

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

class ExportLevelPackage(bpy_extras.io_utils.ExportHelper, Operator):
	"""Create a ZIP file from a given level that contains all of its required resources for submission to Hyperspace"""
	
	bl_idname = "shatter.export_level_package"
	bl_label = "Create Hyperspace Package"
	
	filename_ext = ".zip"
	
	level: StringProperty(
		name = "Level",
		description = "Name of the level (part before '.xml') to make a package for",
		default = "",
	)
	
	name: StringProperty(
		name = "Name",
		description = "The name that the level will appear as in the level listing",
		default = "",
	)
	
	creator: StringProperty(
		name = "Creator",
		description = "The name of the person or group who created the level",
		default = "",
	)
	
	version: IntVectorProperty(
		name = "Version",
		description = "Version of the mod",
		size = 3,
		default = (1, 0, 0),
		max = 99,
		min = 0,
	)
	
	desc: StringProperty(
		name = "Description",
		description = "Description of this mod",
		default = "",
	)
	
	balls: IntProperty(
		name = "Starting Balls",
		description = "Balls the player should start with",
		default = 25,
	)
	
	streak: IntProperty(
		name = "Starting Streak",
		description = "Streak the player should start with",
		default = 0,
	)
	
	pack_hud: BoolProperty(
		name = "Pack HUD",
		description = "Puts HUD and font data in the package, allowing a custom HUD",
		default = False,
	)
	
	def execute(self, context):
		assets_dir = butil.find_apk()
		
		if (not self.level):
			butil.show_message("Packing error", "The level name is required.")
			return {"FINISHED"}
		
		if (not os.path.exists(f"{assets_dir}/levels/{self.level}.xml.mp3")):
			butil.show_message("Packing error", f"The level '{self.level}' doesn't appear to exist.")
			return {"FINISHED"}
		
		level_pack.pack(assets_dir, self.filepath, self.level, {
			"package": f"com.dummy.stage.{self.level}",
			"name": self.name.replace("-", " ").replace("_", " ").title(),
			"creator": self.creator,
			"version": f"v{self.version[0]}.{self.version[1]}.{self.version[2]}",
			"verid": 10000 * self.version[0] + 100 * self.version[1] + self.version[2],
			"desc": self.desc,
			"org.knot126.smashhit.tulip": {
				"version": f"{self.version[0]}.{self.version[1]}.{self.version[2]}",
				"level": self.level,
				"balls": self.balls,
				"streak": self.streak,
			},
		}, ["hud", "fonts"] if self.pack_hud else [])
		
		return {"FINISHED"}
