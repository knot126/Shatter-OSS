import bpy
import bpy_extras.io_utils
import os
import butil
import level_pack

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

class ExportLevelPackage(bpy_extras.io_utils.ExportHelper, Operator):
	"""Create a ZIP file from a room in an open APK or an assets folder. This will also include some standard JSON packaging files so it can be installed using a mod manager"""
	
	bl_idname = "shatter.export_level_package"
	bl_label = "Export level package"
	
	filename_ext = ".zip"
	
	level: StringProperty(
		name = "Level",
		description = "Name of the level (part before '.xml') to make a package for",
		default = "",
	)
	
	package: StringProperty(
		name = "Package ID",
		description = "Name of the package to export. Recommended in 'correct' domain name form, e.g. org.knot126.smashhit.beehive",
		default = "",
	)
	
	creator: StringProperty(
		name = "Creator",
		description = "Creator name",
		default = "",
	)
	
	version: IntVectorProperty(
		name = "Version",
		description = "Version of the mod",
		size = 3,
		default = (1, 0, 0),
	)
	
	desc: StringProperty(
		name = "Description",
		description = "Description of this mod",
		default = "",
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
			"package": self.package,
			"name": self.level.replace("-", " ").replace("_", " ").title(),
			"creator": self.creator,
			"version": f"v{self.version[0]}.{self.version[1]}.{self.version[2]}",
			"verid": 10000 * self.version[0] + 100 * self.version[1] + self.version[2],
			"desc": self.desc,
		})
		
		return {"FINISHED"}
