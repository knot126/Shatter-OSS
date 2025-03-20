"""
Main file for Shatter tools
"""

import bpy
import os
import webbrowser
import traceback
import secrets
import sys
import socket
from . import obstacle_db
from . import segment_export
from . import segment_import
from . import room_export
from . import util
from . import butil
from . import level_pack_ui
from . import patcher_ui
from . import progression_crypto_ui
from . import knshim_ui
from . import server_manager
from . import assets
from . import rebake_ui
from . import mtxconv_ui

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

from bpy_extras.io_utils import ImportHelper

# The level test server manager
gServerManager = None

# Quick Test Protocol v6 servers use a token for security since the config can
# be updated via the HTTP API.
gNxToken = None

ExportHelper2 = butil.ExportHelper2
get_prefs = butil.prefs

gQuickPortTest = None

YORSHEX_MESHBAKER_AO_TYPES = [
	('0', "Disabled", "Disable ambient occlusion entirely"),
	('1', "Fast", "Faster to export but more rough looking"),
	('2', "Precise", "Nicer looking but slower to export"),
]

YORSHEX_MESHBAKER_AO_TYPES_WITHEXCL = YORSHEX_MESHBAKER_AO_TYPES.copy()
YORSHEX_MESHBAKER_AO_TYPES_WITHEXCL.insert(0, ('-1', 'No override', "Does not override the export type's ambient occlusion quality"))

class ShatterExportCommon(bpy.types.Operator, ExportHelper2):
	"""
	Common code and values between export types
	"""
	
	sh_meshbake_template: StringProperty(
		name = "Template",
		description = "A relitive or full path to the template file used for baking meshes. If you use APK Editor Studio and the Smash Hit APK is open, the path to the file will be pre-filled",
		default = "",
		subtype = "FILE_PATH",
	)
	
	def __init__(self, *args, **kwargs):
		"""
		Automatic templates.xml detection
		"""
		
		super().__init__(*args, **kwargs)
		
		if (not self.sh_meshbake_template):
			self.sh_meshbake_template = segment_export.tryTemplatesPath()

class SegmentExport(ShatterExportCommon):
	"""Export an uncompressed (.xml.mp3) segment"""
	
	bl_idname = "shatter.export"
	bl_label = "Export Segment"
	
	filename_ext = ".xml.mp3"
	filter_glob = bpy.props.StringProperty(default='*.xml.mp3', options={'HIDDEN'}, maxlen=255)
	
	def execute(self, context):
		segment_export.sh_export_segment(self.filepath, context, aotype=get_prefs().ymb_ao_manual)
		
		return {"FINISHED"}

def sh_draw_export(self, context):
	self.layout.operator("shatter.export", text="Segment (.xml.mp3)")

class SegmentExportGz(ShatterExportCommon):
	"""Export a compressed (.xml.gz.mp3) segment. Choose this when you don't know which to use"""
	
	bl_idname = "shatter.export_compressed"
	bl_label = "Export Compressed Segment"
	
	filename_ext = ".xml.gz.mp3"
	filter_glob = bpy.props.StringProperty(default='*.xml.gz.mp3', options={'HIDDEN'}, maxlen=255)
	
	def execute(self, context):
		segment_export.sh_export_segment(self.filepath, context, True, aotype=get_prefs().ymb_ao_manual)
		
		return {"FINISHED"}

def sh_draw_export_gz(self, context):
	self.layout.operator("shatter.export_compressed", text="Compressed Segment (.xml.gz.mp3)")

class SegmentExportAuto(bpy.types.Operator):
	"""Automatically find an asset folder and save the segment to the segments folder in the correct location from the info given in the scene tab"""
	
	bl_idname = "shatter.export_auto"
	bl_label = "Export to Assets"
	
	def execute(self, context):
		segment_export.sh_export_segment(None, context, get_prefs().auto_export_compressed, aotype=get_prefs().ymb_ao_auto_export)
		
		return {"FINISHED"}

class SegmentExportAllAuto(bpy.types.Operator):
	"""Automatically find an asset path and export every segment in this file to the proper locations"""
	
	bl_idname = "shatter.export_all_auto"
	bl_label = "Export all to APK"
	
	def execute(self, context):
		segment_export.sh_export_all_segments(context, get_prefs().auto_export_compressed, aotype=get_prefs().ymb_ao_auto_export)
		
		return {"FINISHED"}

class SegmentExportTest(Operator):
	"""Export a segment to the quick test server"""
	
	bl_idname = "shatter.export_test_server"
	bl_label = "Export segment to quick test"
	
	def execute(self, context):
		if (get_prefs().quick_test_server in ["builtin", "nx", "yorshex"]):
			update_if_yas()
			segment_export.sh_export_segment(None, context, False, True, aotype=get_prefs().ymb_ao_quick_test, nx_token=gNxToken)
		else:
			butil.show_message("Quick test not running", "The quick test server is currently disabled or you are using a level server that isn't compatible with Quick Test.")
		
		return {"FINISHED"}

class SegmentImport(bpy.types.Operator, ImportHelper):
	"""Imports an uncompressed (.xml.mp3) segment to the current scene"""
	
	bl_idname = "shatter.import"
	bl_label = "Import Segment"
	
	check_extension = False
	filename_ext = ".xml.mp3"
	filter_glob = bpy.props.StringProperty(default='*.xml.mp3', options={'HIDDEN'}, maxlen=255)
	
	def execute(self, context):
		return segment_import.sh_import_segment(self.filepath, context)

def sh_draw_import(self, context):
	self.layout.operator("shatter.import", text="Segment (.xml.mp3)")

class SegmentImportGz(bpy.types.Operator, ImportHelper):
	"""Imports a compressed (.xml.gz.mp3) segment to the current scene"""
	
	bl_idname = "shatter.import_gz"
	bl_label = "Import Compressed Segment"
	
	check_extension = False
	filename_ext = ".xml.gz.mp3"
	filter_glob = bpy.props.StringProperty(default='*.xml.gz.mp3', options={'HIDDEN'}, maxlen=255)
	
	def execute(self, context):
		return segment_import.sh_import_segment(self.filepath, context, True)

def sh_draw_import_gz(self, context):
	self.layout.operator("shatter.import_gz", text="Compressed Segment (.xml.gz.mp3)")

################################################################################
# Server manager related
################################################################################

def update_if_yas():
	if (get_prefs().quick_test_server == "yorshex"):
		server_manager_update()

def server_manager_update(_self = None, _context = None):
	"""
	Note: self and context can be none
	"""
	
	if butil.stay_offline():
		return
	
	server_type = get_prefs().quick_test_server
	
	try:
		global gServerManager
		
		gServerManager.stop()
		gServerManager.set_type(server_type)
		
		if (server_type == "yorshex"):
			# Derive the actual level name to use
			# level_name = get_prefs().test_level
			
			# if level_name == "/":
			# 	level_name = bpy.context.scene.sh_properties.sh_level if _context else ""
			
			# Find the asset dir to use
			asset_dir = butil.find_apk() or butil.storage_path("testserver")
			
			# Set parameters
			gServerManager.set_params((asset_dir, "test"))
		elif (server_type == "builtin"):
			gServerManager.set_params((butil.storage_path("testserver"),))
		elif (server_type == "nx"):
			global gNxToken
			gNxToken = secrets.token_hex(24)
			
			gServerManager.set_params((butil.storage_path("testserver"), butil.find_apk(), gNxToken))
		elif server_type == "knot":
			gServerManager.set_params((butil.find_apk(),))
		else:
			gServerManager.set_params(tuple())
		
		gServerManager.start()
	except Exception as e:
		util.log(f"*** Exception in server manager!!! ***")
		util.log(traceback.format_exc())

class ForceServerManagerUpdate(Operator):
	"""Forces a server manager update"""
	
	bl_idname = "shatter.force_server_manager_update"
	bl_label = "Force server manager update"
	
	def execute(self, context):
		server_manager_update()
		
		return {"FINISHED"}

def get_test_level_list(self, context):
	level_list = assets.levels.get()
	
	levels = [
		("test", "Test level", "The default testing level"),
		("/", "Level of segment", "Use the segment's level attribute to determine the level, or if not available use Shatter's builtin test level"),
		None,
	]
	
	for l in level_list["results"]:
		if l == "test":
			continue
		
		levels.append((l, l, ""))
	
	return levels

def get_obstacle_list(self, context):
	obstacles = [
		("(other)", "Choose...", ""),
		None,
	]
	
	# Get obstacles from APK
	for obs in assets.obstacles.get():
		obstacles.append((obs, obs, ""))
	
	return obstacles

def get_template_list(self, context):
	items = [
		("(other)", "Choose...", ""),
		None,
	]
	
	for t in assets.templates.get():
		desc = ""
		
		if t.endswith("_s"):
			desc = f"Segment template for {t[:-2].title()}"
		elif t.endswith("_st"):
			desc = f"Crystal template for {t[:-3].title()}"
		elif t.endswith("_glass"):
			desc = f"Glass template for {t[:-6].title()}"
		else:
			desc = f"Stone template for {t.title()}"
		
		items.append((t, t, desc))
	
	return items

def get_obstacle_param_list(self, context, withvalue=False):
	items = [
		("(other)", "Choose...", ""),
		None,
	]
	
	obs = context.object.sh_properties.sh_obstacle_chooser if context.object.sh_properties.sh_use_chooser else context.object.sh_properties.sh_obstacle
	
	for item in assets.obs_params.get(obs):
		items.append((item[0], f"{item[0]} ({item[1]})", f"default: {item[2]}" if not withvalue else item[2]))
	
	return items

def get_obstacle_param_list_but_two_arguments_to_make_blender_shut_the_fuck_up(self, context):
	return get_obstacle_param_list(self, context)

def get_chooser_enum(self):
	return 0

def make_set_chooser_enum(propname, getlistfunc):
	def set_chooser_enum(self, value):
		if value != 0:
			self[propname] = getlistfunc(None, bpy.context)[value][0]
	
	return set_chooser_enum

def make_set_chooser_enum_with_value(propname, getlistfunc):
	def set_chooser_enum(self, value):
		if value != 0:
			item = getlistfunc(None, bpy.context, True)[value]
			self[propname] = item[0]
			self[f"{propname}_value"] = item[2]
	
	return set_chooser_enum

set_template = make_set_chooser_enum("sh_template", get_template_list)
set_default_template = make_set_chooser_enum("sh_default_template", get_template_list)
set_obstacle = make_set_chooser_enum("sh_obstacle", get_obstacle_list)

def get_use_old_chooser(self):
	return self["sh_use_chooser"]

def set_use_old_chooser(self, value):
	# Copy old value to new chooser
	self["sh_use_chooser"] = value
	self["sh_obstacle"] = bpy.context.object.sh_properties.sh_obstacle_chooser

################################################################################
# Item and scene data structures
################################################################################

class SegmentProperties(PropertyGroup):
	"""
	Segment (scene) properties
	"""
	
	sh_level: StringProperty(
		name = "Level",
		description = "The name of the checkpoint that this segment belongs to.",
		default = "",
		update = server_manager_update,
	)
	
	sh_room: StringProperty(
		name = "Room",
		description = "The name of the room that this segment belongs to.",
		default = "",
	)
	
	sh_segment: StringProperty(
		name = "Segment",
		description = "The name of this segment",
		default = "",
	)
	
	sh_len: FloatVectorProperty(
		name = "Size",
		description = "Segment size in the order Width, Height, Depth. Last paramater changes the length (depth) of the segment",
		subtype = "XYZ",
		default = (12.0, 10.0, 8.0), 
	)
	
	sh_auto_length: BoolProperty(
		name = "Auto length",
		description = "Automatically determine the length of the segment based on the furthest object from the origin.",
		default = False,
	)
	
	ambient_occlusion_quality: EnumProperty(
		name = "Ambient occlusion quality",
		description = "Controls the quality of ambient occlusion (shadows near corners) in this segment's mesh",
		items = YORSHEX_MESHBAKER_AO_TYPES_WITHEXCL,
		default = "-1",
	)
	
	sh_template: StringProperty(
		name = "Template",
		description = "The template paramater that is passed for the entire segment",
		default = "",
	)
	
	sh_template_chooser: EnumProperty(
		name = "",
		description = "",
		items = get_template_list,
		get = get_chooser_enum,
		set = set_template,
		default = 0,
	)
	
	sh_default_template: StringProperty(
		name = "Default template",
		description = "The base name of the template to use when no template is specified for an entity. Format: boxes 🡒 '{basename}', obstacles 🡒 '{basename}_glass', obstacles starting with 'score' 🡒 '{basename}_st', segment 🡒 '{basename}_s'",
		default = "",
	)
	
	sh_default_template_chooser: EnumProperty(
		name = "",
		description = "",
		items = get_template_list,
		get = get_chooser_enum,
		set = set_default_template,
		default = 0,
	)
	
	sh_softshadow: FloatProperty(
		name = "Soft shadow",
		description = "Opacity of soft shadow on dynamic objects",
		default = 0.6,
		min = 0.0,
		max = 1.0
	)
	
	sh_vrmultiply: FloatProperty(
		name = "Segment strech",
		description = "This option tries to strech the segment's depth to make more time between obstacles. The intent is to allow it to be played in Smash Hit VR easier and without modifications to the segment",
		default = 1.0,
	)
	
	sh_light_left: FloatProperty(
		name = "Left",
		description = "Light going on to the left side of boxes",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_light_right: FloatProperty(
		name = "Right",
		description = "Light going on to the right side of boxes",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_light_top: FloatProperty(
		name = "Top",
		description = "Light going on to the top side of boxes",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_light_bottom: FloatProperty(
		name = "Bottom",
		description = "Light going on to the bottom side of boxes",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_light_front: FloatProperty(
		name = "Front",
		description = "Light going on to the front side of boxes",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_light_back: FloatProperty(
		name = "Back",
		description = "Light going on to the back side of boxes",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_menu_segment: BoolProperty(
		name = "Menu segment mode",
		description = "Treats the segment like it will appear on the main menu. Bakes faces that cannot be seen by the player",
		default = False
	)
	
	sh_ambient_occlusion: BoolProperty(
		name = "Ambient occlusion",
		description = "Enables ambient occlusion (per-vertex lighting)",
		default = True
	)
	
	sh_lighting: BoolProperty(
		name = "Advanced lighting (deprecated)",
		description = "Enables some lighting features when baking the mesh",
		default = False
	)
	
	sh_lighting_ambient: FloatVectorProperty(
		name = "Ambient",
		description = "Colour and intensity of the ambient light",
		subtype = "COLOR_GAMMA",
		default = (0.0, 0.0, 0.0), 
		soft_min = 0.0,
		soft_max = 1.0,
	)
	
	sh_fog_colour_top: FloatVectorProperty(
		name = "Top fog",
		description = "Fog colour for quick test",
		subtype = "COLOR_GAMMA",
		default = (1.0, 1.0, 1.0), 
		soft_min = 0.0,
		soft_max = 1.0,
	)
	
	sh_fog_colour_bottom: FloatVectorProperty(
		name = "Bottom fog",
		description = "Fog colour for quick test",
		subtype = "COLOR_GAMMA",
		default = (0.0, 0.0, 0.0),
		soft_min = 0.0,
		soft_max = 1.0,
	)
	
	sh_music: StringProperty(
		name = "Music track",
		description = "Name of the music file to play in quick test. The track must be in the apk. Default is to choose a random track. Warning: Using \\ in the name will break it :-)",
		default = "",
	)
	
	sh_reverb: StringProperty(
		name = "Reverb",
		description = "Reverb parameters as real numbers sepreated by spaces. [volume: [0, 1]] [reverb time: sec] [lowpass amount: [0, 1]]",
		default = "",
	)
	
	sh_echo: StringProperty(
		name = "Echo",
		description = "Echo parameters as real numbers sepreated by spaces. [volume: [0, 1]] [delay: sec] [feedback volume: [0, 1]] [lowpass amount: [0, 1]]",
		default = "",
	)
	
	sh_rotation: StringProperty(
		name = "Rotation",
		description = "The rotation parameters as real numbers sepreated by spaces. [amount of rotations: int] [angle: radians]",
		default = "",
	)
	
	sh_particles: EnumProperty(
		name = "Particles",
		description = "The particles that appear when looking at the stage in quick test",
		items = (
			("None", "None", ""),
			("bubbles", "Bubbles", ""),
			("sides", "Sides", ""),
			("lowrising", "Low rising 1", ""),
			("lowrising2", "Low rising 2", ""),
			("lowrising3", "Low rising 3", ""),
			("sidesrising", "Sides rising", ""),
			("falling", "Falling", ""),
			("fallinglite", "Falling lite", ""),
			("dustyfalling", "Dusty falling", ""),
			("starfield", "Star field", ""),
		),
		default = "None",
	)
	
	sh_difficulty: FloatProperty(
		name = "Difficulty",
		description = "Sets the difficulty level of the room",
		default = 0.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_gravity: FloatProperty(
		name = "Gravity",
		description = "The amount of gravity to use in quick test",
		default = 1.0,
		min = -1.0,
		max = 3.0,
	)
	
	sh_extra_code: StringProperty(
		name = "Extra code",
		description = "Extra code to include the in room file. Multipule statements can be seperated by ';'.",
		default = "",
	)
	
	sh_room_length: IntProperty(
		name = "Room length",
		description = "The length of the room in quick test",
		default = 100,
		min = 0,
	)

class EntityProperties(PropertyGroup):
	
	sh_type: EnumProperty(
		name = "Kind",
		description = "The kind of object that the currently selected object should be treated as.",
		items = [
			('BOX', "Box", "", "MESH_CUBE", 0),
			('OBS', "Obstacle", "", "NODE_MATERIAL", 1),
			('DEC', "Decal", "", "TEXTURE", 2),
			('POW', "Power-up", "", "LIGHT_SUN", 3),
			('WAT', "Water", "", "MATFLUID", 4),
		],
		default = "BOX"
	)
	
	# # TEMPLATES # #
	sh_template: StringProperty(
		name = "Template",
		description = "The template for the obstacle/box (see templates.xml), remember that this can be easily overridden per obstacle/box",
		default = "",
	)
	
	sh_template_chooser: EnumProperty(
		name = "",
		description = "",
		items = get_template_list,
		get = get_chooser_enum,
		set = set_template,
		default = 0,
	)
	
	# # OBSTACLES # #
	sh_use_chooser: BoolProperty(
		name = "Use old obstacle chooser",
		description = "Uses the OLD obstacle chooser instead of typing the name by hand",
		get = get_use_old_chooser,
		set = set_use_old_chooser,
		default = False,
	)
	
	sh_obstacle: StringProperty(
		name = "Obstacle",
		description = "Type of obstacle to be used (as a file name string)",
		default = "",
	)
	
	sh_obstacle_chooser: EnumProperty(
		name = "Obstacle",
		description = "Type of obstacle to be used (pick a name)",
		items = obstacle_db.OBSTACLES,
		default = "scoretop",
	)
	
	sh_obstacle_chooser_new: EnumProperty(
		name = "",
		description = "",
		items = get_obstacle_list,
		get = get_chooser_enum,
		set = set_obstacle,
		default = 0,
	)
	
	sh_powerup: EnumProperty(
		name = "Power-up",
		description = "The type of power-up that will appear",
		items = [
			('ballfrenzy', "Ball Frenzy", "Allows the player infinite balls for some time", "LIGHTPROBE_GRID", 0),
			('slowmotion', "Slow Motion", "Slows down the game", "MOD_TIME", 1),
			('nitroballs', "Nitro Balls", "Turns balls into exposlives for a short period of time", "PROP_OFF", 2),
			None,
			('barrel', "Barrel", "Creates a large explosion which breaks glass (lefover from beta versions)", "EXPERIMENTAL", 3),
			None,
			('multiball', "Multi-ball*", "*Does not work anymore. Old power up that would enable five-ball multiball"),
			('freebie', "Freebie*", "*Does not work anymore. Old power up found in binary strings but no known usage"),
			('antigravity', "Anti-gravity*", "*Does not work anymore. Old power up that probably would have reversed gravity"),
			('rewind', "Rewind*", "*Does not work anymore. Old power up that probably would have reversed time"),
			('shield', "Shield*", "*Only partially works in current versions. Old power up that probably would have protected the player"),
			('homing', "Homing*", "*Does not work anymore. Old power up that probably would have homed to obstacles"),
			('life', "Life*", "*Does not work anymore. Old power up that gave the player a life"),
			('balls', "Balls*", "*Does not work anymore. Old power up that gave the player ten balls"),
		],
		default = "ballfrenzy",
	)
	
	sh_export: BoolProperty(
		name = "Export object",
		description = "If the object should be exported to the XML at all. Change \"hidden\" if you'd like it to be hidden but still present in the exported file",
		default = True,
	)
	
	sh_mode: EnumProperty(
		name = "Mode",
		options = {"ENUM_FLAG"},
		description = "The game modes in which this obstacle should appear",
		items = [
			('training', "Training", "Obstacle should appear in Training mode", 1),
			('classic', "Classic and Zen", "Obstacle should appear in Classic and Zen modes", 2),
			('expert', "Mayhem", "Obstacle should appear in Mayhem mode", 4),
			('versus', "Versus", "Obstacle should appear in Versus mode", 16),
			('coop', "Co-op", "Obstacle should appear in Co-op mode", 32),
		],
		default = {'training', 'classic', 'expert', 'versus', 'coop'},
	)
	
	sh_difficulty: FloatVectorProperty(
		name = "Difficulty",
		description = "The range of difficulty values for which this entity will appear. Difficulty is different than game modes, and is mainly used in Endless Mode to include or exclude obstacle based on a value set per room (using mgSetDifficulty) indicating how hard the room should be. As an example, this is used to exclude crystals in later levels in the Endless mode without creating entirely new segments",
		default = (0.0, 1.0),
		min = 0.0,
		max = 1.0,
		size = 2,
	)
	
	sh_visible: BoolProperty(
		name = "Visible",
		description = "If the box will appear in the exported mesh",
		default = True
	)
	
	sh_use_multitile: BoolProperty(
		name = "Tile per-side",
		description = "Specifiy a colour for each parallel pair of faces on the box",
		default = False,
	)
	
	sh_tile: IntProperty(
		name = "Tile",
		description = "The texture that will appear on the surface of the box or decal",
		default = 0,
		min = 0,
		max = 63, # TODO: Dynamically adjust this based on ymb_tiles setting
	)
	
	sh_tile1: IntProperty(
		name = "Right Left",
		description = "The texture that will appear on the surface of the box or decal",
		default = 0,
		min = 0,
		max = 63
	)
	
	sh_tile2: IntProperty(
		name = "Top Bottom",
		description = "The texture that will appear on the surface of the box or decal",
		default = 0,
		min = 0,
		max = 63
	)
	
	sh_tile3: IntProperty(
		name = "Front Back",
		description = "The texture that will appear on the surface of the box or decal",
		default = 0,
		min = 0,
		max = 63
	)
	
	sh_tilerot: IntVectorProperty(
		name = "Tile orientation",
		description = "Orientation of the tile, where 0 is facing up",
		default = (0, 0, 0), 
		min = 0,
		max = 3,
	) 
	
	sh_tilesize: FloatVectorProperty(
		name = "Tile size",
		description = "The appearing size of the tiles on the box when exported. In RightLeft, TopBottom, FrontBack",
		default = (1.0, 1.0, 1.0), 
		soft_min = 0.0,
		soft_max = 128.0,
		size = 3
	)
	
	sh_decal: IntProperty(
		name = "Decal",
		description = "The image ID for the decal (negitive numbers are doors)",
		default = 1,
		min = -4,
		max = 63
	)
	
	sh_reflective: BoolProperty(
		name = "Reflective",
		description = "If this box should show reflections",
		default = False
	)
	
	
	
	sh_havetint: BoolProperty(
		name = "Decal colourisation",
		description = "Changes the tint (colourisation) of the decal",
		default = False
	)
	
	sh_use_multitint: BoolProperty(
		name = "Colour per-side",
		description = "Specifiy a colour for each parallel pair of faces on the box",
		default = False,
	)
	
	sh_tint: FloatVectorProperty(
		name = "Colour",
		description = "The colour to be used for tinting, colouring and mesh data",
		subtype = "COLOR_GAMMA",
		default = (1.0, 1.0, 1.0, 1.0), 
		size = 4,
		soft_min = 0.0,
		soft_max = 1.0,
	)
	
	sh_tint1: FloatVectorProperty(
		name = "Right Left",
		description = "The colour to be used for tinting, colouring and mesh data",
		subtype = "COLOR_GAMMA",
		default = (1.0, 1.0, 1.0, 1.0), 
		size = 4,
		soft_min = 0.0,
		soft_max = 1.0,
	)
	
	sh_tint2: FloatVectorProperty(
		name = "Top Bottom",
		description = "The colour to be used for tinting, colouring and mesh data",
		subtype = "COLOR_GAMMA",
		default = (1.0, 1.0, 1.0, 1.0), 
		size = 4,
		soft_min = 0.0,
		soft_max = 1.0,
	)
	
	sh_tint3: FloatVectorProperty(
		name = "Front Back",
		description = "The colour to be used for tinting, colouring and mesh data",
		subtype = "COLOR_GAMMA",
		default = (1.0, 1.0, 1.0, 1.0), 
		size = 4,
		soft_min = 0.0,
		soft_max = 1.0,
	)
	
	sh_gradientraw: StringProperty(
		name = "Linear gradient",
		description = "(\"A \"?) A.x A.y A.z  B.x B.y B.z  A.r A.g A.b  B.r B.g B.b. Normally relative where -1 and 1 are the extremes but prefix with 'A ' to get absolute mode",
		default = "",
	)
	
	sh_graddir: EnumProperty(
		name = "Direction",
		description = "The game modes in which this obstacle should appear",
		items = [
			('none', "None", "The regular box colour will be used"),
			('relative', "Relative points", "Pick two points for each axis that are in [-1, 1] and scale with the box"),
			('absolute', "Absolute points", "Pick two points that are relative to the scene"),
			('right', "To right", ""),
			('left', "To left", ""),
			('top', "To top", ""),
			('bottom', "To bottom", ""),
			('front', "To front", ""),
			('back', "To back", ""),
		],
		default = "none",
	)
	
	sh_gradpoint1: FloatVectorProperty(
		name = "Point A",
		description = "The first gradient colour",
		subtype = "XYZ",
		default = (0.0, 0.0, 0.0),
	)
	
	sh_gradcolour1: FloatVectorProperty(
		name = "Colour A",
		description = "The colour for point A",
		subtype = "COLOR_GAMMA",
		default = (1.0, 1.0, 1.0), 
		size = 3,
		soft_min = 0.0,
		soft_max = 1.0,
	)
	
	sh_gradpoint2: FloatVectorProperty(
		name = "Point B",
		description = "The first gradient colour",
		subtype = "XYZ",
		default = (0.0, 0.0, 0.0),
	)
	
	sh_gradcolour2: FloatVectorProperty(
		name = "Colour B",
		description = "The colour for point B",
		subtype = "COLOR_GAMMA",
		default = (1.0, 1.0, 1.0), 
		size = 3,
		soft_min = 0.0,
		soft_max = 1.0,
	)
	
	sh_blend: FloatProperty(
		name = "Blend mode",
		description = "How the colour of the decal and the existing colour will be blended. 1 = normal, 0 = added or numbers in between",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_size: FloatVectorProperty(
		name = "Size",
		description = "The size of the object when exported",
		default = (1.0, 1.0), 
		min = 0.0,
		size = 2,
	)
	
	sh_resolution: FloatVectorProperty(
		name = "Resolution",
		description = "Controls how detailed the water effect looks. Smaller values will lead to larger but lower quality splashes when an object hits the water",
		default = (32.0, 32.0),
		min = 0.0,
		size = 2,
	)
	
	sh_glow: FloatProperty(
		name = "Glow",
		description = "The intensity of the light in \"watts\"; zero if this isn't a light",
		default = 0.0,
		min = 0.0,
		max = 1000.0,
	)
	
	

def init_obstacle_params():
	for i in range(0, 12):
		setattr(EntityProperties, f"sh_param{i}", StringProperty(
			name = f"param{i}",
			description = "Parameter which is given to the obstacle when spawned",
			default = "",
		))
		
		setattr(EntityProperties, f"sh_param{i}_chooser", EnumProperty(
			name = "",
			description = "",
			items = get_obstacle_param_list_but_two_arguments_to_make_blender_shut_the_fuck_up,
			get = get_chooser_enum,
			set = make_set_chooser_enum_with_value(f"sh_param{i}", get_obstacle_param_list),
			default = 0,
		))
		
		setattr(EntityProperties, f"sh_param{i}_value", StringProperty(
			name = f"param{i} value",
			description = "Value of the parameter",
			default = "",
		))

def destroy_obstacle_params():
	pass
	# for i in range(0, 12):
	# 	del EntityProperties[f"sh_param{i}"]
	# 	del EntityProperties[f"sh_param{i}_chooser"]
	# 	del EntityProperties[f"sh_param{i}_value"]

################################################################################
# Addon, item and scene panels
################################################################################

YORSHEX_MESHBAKER_SUPPORTED_PLATFORMS = ["win32", "linux"]

def list_mesh_bakers(self, context):
	mesh_bakers = [
		('bakemesh', "BakeMesh", "Shatter's default mesh baker, written in Python. Slow in some cases and also completely mangles tile rotations, but supports some extras like gradients. Kept for compatibility with older segments"),
		('stonehack', "Stonehack", "Does not actually bake meshes, but instead adds an obstacle named 'stone' which look like meshes. This is probably only desirable if you want to create segments which look like those from 2020-2021 since stone hack was used then"),
		('command', "Custom command (advanced)", "Run a custom command to bake the mesh"),
		('none', "None", "Don't bake any meshes"),
	]
	
	if util.get_platform() in YORSHEX_MESHBAKER_SUPPORTED_PLATFORMS:
		mesh_bakers.insert(0, ('yorshex', "Yorshex's mesh baker", "Currently the most correct mesh baker, and recommended when available."))
	
	return mesh_bakers

class ShatterPreferences(AddonPreferences):
	bl_idname = __package__
	
	default_assets_path: StringProperty(
		name = "Default assets path",
		description = "The path to your Smash Hit assets folder, if you want to override the default automatic APK finding",
		subtype = "DIR_PATH",
		default = "",
	)
	
	enable_segment_warnings: BoolProperty(
		name = "Enable export and import warnings",
		description = "Export and import warnings can warn you about possible issues that might result in odd or unexpected behaviour in Smash Hit",
		default = True,
	)
	
	auto_export_compressed: BoolProperty(
		name = "Compress exported segments in auto export",
		description = "Enables segment compression when using the 'Export to Assets' option. Smash Hit does not compress segments by default in 1.5.x and later",
		default = True,
	)
	
	resolve_templates: BoolProperty(
		name = "Resolve templates at export time",
		description = "Solves templates when a segment is exported. This avoids the need for adding used templates to templates.xml, but makes the filesize larger and the XML file less readable",
		default = False,
	)
	
	create_nonexistant_assets: BoolProperty(
		name = "Automatically create levels and rooms",
		description = "When automatically exporting a segment, create assocaited level and room files if they don't yet exist",
		default = True,
	)
	
	purist_mode: BoolProperty(
		name = "Limit UI to classic Smash Hit features",
		description = "Removes shatter extended features from the UI, for example gradients and advanced lighting",
		default = True,
	)
	
	compact_ui: BoolProperty(
		name = "Compact UI mode",
		description = "Avoids drawing any excessive UI elements that would make the UI larger than needed",
		default = False,
	)
	
	show_shards_ads: BoolProperty(
		name = "Show Shards Community promos",
		description = "Shows links to join the Shards Community Discord server",
		default = True,
	)
	
	show_deprecated_advanced_lights: BoolProperty(
		name = "Show advanced lights (deprecated)",
		description = "Shows the advanced lights panel when not relevant. Note that advanced lights is *deprecated* meaning it could be removed at any time",
		default = False,
	)
	
	show_deprecated_gradients: BoolProperty(
		name = "Show gradients (deprecated)",
		description = "Shows the gradients panel even when there are no gradients. Note that gradients are *deprecated* meaning they could be removed at any time",
		default = False,
	)
	
	quick_test_server: EnumProperty(
		name = "Level test server",
		description = "Selects which, if any, level test server will be used. This will create a local HTTP server, which might pose a security risk",
		items = [
			('none', "None", "Don't use any quick test server"),
			('nx', "NxQuick", "The most modern server supporting Shatter Client v4 to the fullest. It is faster and more reliable, and despite supporting classic Quick Test export also supports loading entire levels. Does not support older clients"),
			('yorshex', "Yorshex's Asset Server", "An advanced test server that allows loading an entire level from a Smash Hit assets folder for old quick test clients. It has been written by Yorshex"),
			('knot', "Knot's Asset Server (beta)", ""),
			('builtin', "SegServ (deprecated)", "The classic quick test server integrated with Shatter. Of the old servers, it is the simplest and fastest to use but only loads one segment at a time"),
		],
		update = server_manager_update,
		default = "nx",
	)
	
	# test_level: EnumProperty(
	# 	name = "Test level",
	# 	description = "The name of the level to test",
	# 	# items = get_test_level_list,
	# 	update = server_manager_update,
	# 	default = 0,
	# )
	
	####################
	## Advanced settings
	####################
	mesh_baker: EnumProperty(
		name = "Mesh baker",
		description = "Selects which mesh baker to use",
		items = list_mesh_bakers,
		default = 0,
	)
	
	ymb_ao_quick_test: EnumProperty(
		name = "Quick test",
		description = "Selects the default ambient occlusion bake quality for quick test",
		items = YORSHEX_MESHBAKER_AO_TYPES,
		default = "1",
	)
	
	ymb_ao_auto_export: EnumProperty(
		name = "Auto export",
		description = "Selects the default ambient occlusion bake quality for automatic export",
		items = YORSHEX_MESHBAKER_AO_TYPES,
		default = "2",
	)
	
	ymb_ao_manual: EnumProperty(
		name = "Manual export",
		description = "Selects the default ambient occlusion bake quality for manual export",
		items = YORSHEX_MESHBAKER_AO_TYPES,
		default = "2",
	)
	
	ymb_tiles: IntVectorProperty(
		name = "Tile grid size",
		description = "Controls the number of tiles per row and column in the tiles texture, as the mesh baker considers it",
		default = (8, 8),
		size = 2,
		min = 1,
		max = 32,
	)
	
	mesh_command: StringProperty(
		name = "External mesh bake command",
		description = "If specified, this command is run instead of the built-in mesh baker",
		default = "",
	)
	
	mtxconv_path: StringProperty(
		name = "MTXConv path",
		description = "Path to the mtxconv executable",
		subtype = "FILE_PATH",
		default = "",
	)
	
	def draw(self, context):
		main = self.layout
		
		ui = butil.UIDrawingHelper(context, self.layout, self)
		
		# Shards promo
		if butil.get_setting("show_shards_ads"):
			ui.region("MESH_ICOSPHERE", "Shards Community")
			ui.label("Consider joining the Shards Community on Discord for official Shatter updates!")
			ui.op("shatter.open_shards_discord")
			ui.end()
		
		ui.region("EXPORT", "Export and import")
		ui.prop("default_assets_path")
		ui.prop("create_nonexistant_assets")
		ui.prop("enable_segment_warnings")
		ui.prop("auto_export_compressed")
		ui.prop("resolve_templates")
		ui.end()
		
		ui.region("DESKTOP", "Interface")
		ui.prop("show_shards_ads")
		ui.prop("compact_ui")
		ui.prop("purist_mode")
		ui.prop("show_deprecated_advanced_lights", disabled = (ui.get("purist_mode") == True))
		ui.prop("show_deprecated_gradients", disabled = (ui.get("purist_mode") == True))
		ui.end()
		
		ui.region("AUTO", "Quick test")
		
		if not butil.stay_offline():
			server_type = ui.prop("quick_test_server")
			if server_type != 'none':
				ui.beginSplit(0.7, True)
				if (gServerManager.running()):
					ui.label("The server is currently running", "CHECKMARK")
				else:
					ui.label("The server is not running", "CANCEL")
				ui.op("shatter.force_server_manager_update", text="Restart", icon="FILE_REFRESH")
				ui.end()
			
			ui.region("SHADERFX", "Quick test checkup", new=False)
			if (gQuickPortTest == False):
				ui.label("Could not open port 8000", "CANCEL")
			elif (gQuickPortTest == True):
				ui.label("Port 8000 can be opened", "CHECKMARK")
			ui.op("shatter.quick_test_checkup")
			ui.end()
		else:
			ui.warn("Networking is currently disabled in Blender. To use this feature, enable networking.")
		
		ui.end()
		
		ui.region("UV_DATA", "Mesh baking")
		
		mb = ui.prop("mesh_baker")
		
		if (mb == "command"):
			ui.prop("mesh_command")
		elif (mb == "yorshex"):
			ui.label("Ambient occlusion quality")
			ui.prop("ymb_ao_quick_test")
			ui.prop("ymb_ao_auto_export")
			ui.prop("ymb_ao_manual")
			ui.label("Adjustments")
			ui.prop("ymb_tiles")
		
		ui.end()
		
		ui.region("TOOL_SETTINGS", "Tools")
		ui.prop("mtxconv_path")
		ui.end()
		
		ui.region("INFO", "Other information")
		
		ui.label("You can view the license for open source components used in Shatter.")
		ui.op("shatter.licenses_index")
		
		ui.end()

class SegmentPanel(Panel):
	bl_label = "Smash Hit Scene"
	bl_idname = "OBJECT_PT_segment_panel"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Scene"
	
	@classmethod
	def poll(self, context):
		return True
	
	def draw(self, context):
		layout = self.layout
		scene = context.scene
		sh_properties = scene.sh_properties
		
		ui = butil.UIDrawingHelper(context, layout, sh_properties, compact = get_prefs().compact_ui)
		
		ui.region("NODE", "Location")
		ui.prop("sh_level")
		ui.prop("sh_room")
		ui.prop("sh_segment")
		ui.end()
		
		ui.region("SCENE_DATA", "Segment data")
		
		if (not ui.prop("sh_auto_length", use_button=True)):
			ui.prop("sh_len")
		
		ui.combo("sh_template")
		ui.combo("sh_default_template")
		ui.prop("sh_softshadow")
		ui.prop("sh_vrmultiply")
		ui.end()
		
		ui.region("LIGHT", "Lighting")
		ui.prop("sh_light_right")
		ui.prop("sh_light_left")
		ui.prop("sh_light_top")
		ui.prop("sh_light_bottom")
		ui.prop("sh_light_front")
		ui.prop("sh_light_back")
		
		if ((not get_prefs().purist_mode and get_prefs().show_deprecated_advanced_lights) or sh_properties.sh_lighting):
			ui.prop("sh_lighting")
			if (sh_properties.sh_lighting):
				ui.prop("sh_lighting_ambient")
		
		ui.end()
		
		# Mesh settings
		ui.region("MESH_DATA", "Meshes")
		if (get_prefs().mesh_baker == "yorshex"):
			ui.prop("ambient_occlusion_quality")
		else:
			ui.prop("sh_ambient_occlusion")
		ui.prop("sh_menu_segment")
		ui.end()
		
		# Quick test
		server_type = "none" if butil.stay_offline() else get_prefs().quick_test_server
		
		if (server_type in ["builtin", "nx", "yorshex"]):
			ui.region("AUTO", "Quick test")
			ui.prop("sh_fog_colour_top")
			ui.prop("sh_fog_colour_bottom")
			ui.prop("sh_room_length")
			ui.prop("sh_gravity")
			ui.prop("sh_music")
			ui.prop("sh_echo")
			ui.prop("sh_reverb")
			ui.prop("sh_rotation")
			ui.prop("sh_particles")
			ui.prop("sh_difficulty")
			ui.label(f"Your IP: {util.get_local_ip()}")
			ui.end()

class EntityPanel(Panel):
	bl_label = "Smash Hit Item"
	bl_idname = "OBJECT_PT_obstacle_panel"
	bl_space_type = "VIEW_3D"   
	bl_region_type = "UI"
	bl_category = "Item"
	bl_context = "objectmode"
	
	@classmethod
	def poll(self, context):
		return context.object is not None
	
	def draw(self, context):
		layout = self.layout
		object = context.object
		sh_properties = object.sh_properties
		
		ui = butil.UIDrawingHelper(context, layout, sh_properties, compact = get_prefs().compact_ui)
		
		# All objects will have all properties, but only some will be used for
		# each of obstacle there is.
		t = ui.prop("sh_type", text = "")
		
		ui.region("NODE_COMPOSITING", "Template")
		ui.combo("sh_template", text="", text_compact="Template")
		ui.end()
		
		if (t == "BOX"):
			ui.prop("sh_visible", disabled = not not ui.get("sh_template"))
			
			# silly little loop wrapper :-3
			for x in ["tint", "tile"]:
				word = {"tint": "Colour", "tile": "Tile"}[x]
				
				ui.region(
					{"tint": "COLOR", "tile": "TEXTURE"}[x],
					word,
				)
				
				if (ui.get(f"sh_use_multi{x}")):
					ui.prop(f"sh_use_multi{x}", text = "Per-axis", text_compact = f"Per-axis {word.lower()}", use_button = True)
					ui.prop(f"sh_{x}1")
					ui.prop(f"sh_{x}2")
					ui.prop(f"sh_{x}3")
				else:
					ui.prop(f"sh_use_multi{x}", text = "Uniform", text_compact = f"Uniform {word.lower()}", use_button = True)
					ui.prop(f"sh_{x}")
				
				ui.end()
			
			if ((not get_prefs().purist_mode and get_prefs().show_deprecated_gradients) or ui.get("sh_graddir") != "none"):
				ui.region("NODE_TEXTURE", "Gradient")
				v = ui.prop("sh_graddir", text_compact = "Gradient direction")
				
				if (v == "none"):
					pass
				elif (v == "relative" or v == "absolute"):
					ui.prop("sh_gradpoint1")
					ui.prop("sh_gradcolour1")
					ui.prop("sh_gradpoint2")
					ui.prop("sh_gradcolour2")
				else:
					ui.prop("sh_gradcolour1", text = "From", text_compact = "Grad from")
					ui.prop("sh_gradcolour2", text = "To", text_compact = "Grad to")
				
				ui.end()
			
			if (context.scene.sh_properties.sh_lighting):
				ui.region("LIGHT", "Light")
				ui.prop("sh_glow")
				ui.end()
			
			ui.region("GRAPH", "Tile transforms")
			ui.prop("sh_tilesize")
			ui.prop("sh_tilerot")
			ui.end()
			
			ui.prop("sh_reflective")
		elif (t == "OBS"):
			ui.region("COPY_ID", "Type")
			# ui.prop("sh_obstacle_chooser" if ui.get("sh_use_chooser") else "sh_obstacle", text = "", text_compact = "Type")
			if ui.get("sh_use_chooser"):
				ui.prop("sh_use_chooser", text="Click to use new chooser", use_button=True)
				ui.prop("sh_obstacle_chooser")
			else:
				ui.combo("sh_obstacle", "sh_obstacle_chooser_new", text="", text_compact="Type")
			ui.end()
			
			ui.region("HIDE_OFF", "Visibility")
			ui.prop("sh_mode")
			ui.prop("sh_difficulty")
			ui.end()
			
			ui.region("SETTINGS", "Parameters", force = True)
			
			for i in range(12):
				if "=" in ui.get(f"sh_param{i}"):
					ui.prop(f"sh_param{i}")
				else:
					ui.beginSplit(0.65, False)
					ui.combo(f"sh_param{i}", text = "")
					ui.prop(f"sh_param{i}_value", text = "")
					ui.end()
			
			ui.end()
		elif (t == "DEC"):
			ui.region("TEXTURE", "Sprite")
			ui.prop("sh_decal")
			ui.end()
			
			ui.region("COLOR", "Colour")
			ui.prop("sh_havetint", use_button = True, icon = "COLOR")
			if (ui.get("sh_havetint")):
				ui.prop("sh_tint")
			ui.prop("sh_blend")
			ui.end()
			
			if (context.object.dimensions[1] == 0.0 and context.object.dimensions[2] == 0.0):
				ui.region("SETTINGS", "Size")
				ui.prop("sh_size")
				ui.end()
			
			ui.region("HIDE_OFF", "Visibility")
			ui.prop("sh_difficulty")
			ui.end()
		elif (t == "POW"):
			ui.prop("sh_powerup")
			ui.prop("sh_difficulty")
		elif (t == "WAT"):
			ui.prop("sh_resolution")
		
		ui.prop("sh_export")

################################################################################
# Operators for creating entities
################################################################################

class CreateBox(Operator):
	"""Creates a new box"""
	
	bl_idname = "shatter.create_box"
	bl_label = "Create box"
	
	def execute(self, context):
		o = butil.add_box((0,0,0), (1,1,1))
		
		return {"FINISHED"}

class CreateObstacle(Operator):
	"""Creates a new obstacle"""
	
	bl_idname = "shatter.create_obstacle"
	bl_label = "Create obstacle"
	
	def execute(self, context):
		o = butil.add_empty()
		o.sh_properties.sh_type = "OBS"
		
		return {"FINISHED"}

class CreateDecal(Operator):
	"""Creates a new decal"""
	
	bl_idname = "shatter.create_decal"
	bl_label = "Create decal"
	
	def execute(self, context):
		o = butil.add_empty()
		o.sh_properties.sh_type = "DEC"
		
		return {"FINISHED"}

class CreatePowerup(Operator):
	"""Creates a new powerup"""
	
	bl_idname = "shatter.create_powerup"
	bl_label = "Create powerup"
	
	def execute(self, context):
		o = butil.add_empty()
		o.sh_properties.sh_type = "POW"
		
		return {"FINISHED"}

class CreateWater(Operator):
	"""Creates a new water plane"""
	
	bl_idname = "shatter.create_water"
	bl_label = "Create water"
	
	def execute(self, context):
		o = butil.add_box((0,0,0), (1,1,0))
		o.sh_properties.sh_type = "WAT"
		
		return {"FINISHED"}

################################################################################
# Misc. operators related to opening pages
################################################################################

class OpenLicensesIndex(Operator):
	bl_idname = "shatter.licenses_index"
	bl_label = "Show all licenses"
	
	def execute(self, context):
		webbrowser.open(f"file://{util.codedir()}/licenses/index.html")
		return {"FINISHED"}

class OpenShardsCommunity(Operator):
	"Join the shards Discord server for official Shatter updates and to chat about modding"
	bl_idname = "shatter.open_shards_discord"
	bl_label = "Join on Discord!"
	
	def execute(self, context):
		webbrowser.open(f"https://discord.gg/VMvgn6HwU5")
		return {"FINISHED"}

class OpenObstaclesTextFile(Operator):
	"""Open the obstacles.txt file"""
	
	bl_idname = "shatter.open_obstacles_txt"
	bl_label = "Edit custom obstacles"
	
	def execute(self, context):
		util.user_edit_file(butil.storage_path() + "/obstacles.txt")
		return {"FINISHED"}

class OpenCurrentAssetFolder(Operator):
	"""Open the currently used asset folder"""
	
	bl_idname = "shatter.open_current_asset_folder"
	bl_label = "Open current asset folder"
	
	def execute(self, context):
		folder = butil.find_apk()
		
		if (folder):
			util.user_edit_file(folder)
		else:
			butil.show_message("Folder not found", "The assets folder was not found. Try setting a default asset path in Shatter preferences or open an APK in APK Editor Studio.")
		
		return {"FINISHED"}

class QuickTestCheckup(Operator):
	"""Check for possible quick test problems"""
	
	bl_idname = "shatter.quick_test_checkup"
	bl_label = "Check for possible quick test problems"
	
	def execute(self, context):
		global gQuickPortTest
		
		# Server needs to be offline while we check
		gServerManager.stop()
		
		# Check that we can open port 8000 as a server
		try:
			sock = socket.socket()
			sock.bind(("0.0.0.0", 8000))
			sock.listen()
			sock.close()
			
			gQuickPortTest = True
		except Exception as e:
			util.log(f"*** Exception during quick test checkup ***")
			util.log(traceback.format_exc())
			
			gQuickPortTest = False
		
		# We can start the server again
		gServerManager.start()
		
		return {"FINISHED"}

################################################################################
# Shatter menu
################################################################################

class SHATTER_MT_3DViewportMenu(Menu):
	bl_label = "Shatter"
	
	def draw(self, context):
		self.layout.menu("SHATTER_MT_3DViewportMenuExtras", icon = "TOOL_SETTINGS")
		
		self.layout.separator()
		
		for t in [("box", "MESH_CUBE"), ("obstacle", "MESH_CONE"), ("decal", "TEXTURE"), ("powerup", "SOLO_OFF"), ("water", "MATFLUID")]:
			self.layout.operator(f"shatter.create_{t[0]}", icon = t[1])
		
		self.layout.separator()
		
		self.layout.operator("shatter.export_auto", icon = "MOD_BEVEL")
		
		if (get_prefs().quick_test_server in ["builtin", "nx", "yorshex"]):
			self.layout.operator("shatter.export_test_server", icon = "AUTO")

def SHATTER_MT_3DViewportMenu_draw(self, context):
	self.layout.menu("SHATTER_MT_3DViewportMenu")

class SHATTER_MT_3DViewportMenuExtras(Menu):
	bl_label = "Tools"
	
	def draw(self, context):
		self.layout.label(text = "Tweaking")
		self.layout.operator("shatter.patch_libsmashhit")
		self.layout.operator("shatter.install_knshim")
		self.layout.separator()
		self.layout.label(text = "Export")
		self.layout.operator("shatter.export_all_auto")
		if (get_prefs().quick_test_server in ["builtin", "nx", "yorshex"]):
			self.layout.operator("shatter.export_room")
		self.layout.operator("shatter.export_level_package")
		self.layout.separator()
		self.layout.label(text = "Utilities")
		self.layout.operator("shatter.extract_mtx")
		self.layout.operator("shatter.bake_mtx")
		self.layout.operator("shatter.progression_crypto_encrypt")
		self.layout.operator("shatter.progression_crypto_decrypt")
		self.layout.operator("shatter.rebake_all_meshes")
		self.layout.separator()
		self.layout.label(text = "Actions")
		self.layout.operator("shatter.open_current_asset_folder")
		self.layout.operator("shatter.open_obstacles_txt")
		if butil.get_setting("show_shards_ads"):
			self.layout.separator()
			self.layout.label(text = "Promotion")
			self.layout.operator("shatter.open_shards_discord", text="Join Shards Discord")

###############################################################################

classes = (
	SegmentProperties,
	EntityProperties,
	SegmentPanel,
	EntityPanel,
	ShatterPreferences,
	SegmentExport,
	SegmentExportGz,
	SegmentExportAuto,
	SegmentExportAllAuto,
	SegmentExportTest,
	SegmentImport,
	SegmentImportGz,
	SHATTER_MT_3DViewportMenuExtras,
	SHATTER_MT_3DViewportMenu,
	CreateBox,
	CreateObstacle,
	CreateDecal,
	CreatePowerup,
	CreateWater,
	OpenLicensesIndex,
	OpenShardsCommunity,
	OpenObstaclesTextFile,
	OpenCurrentAssetFolder,
	QuickTestCheckup,
	ForceServerManagerUpdate,
	level_pack_ui.ExportLevelPackage,
	patcher_ui.PatchLibsmashhit,
	progression_crypto_ui.ProgressionCryptoEncrypt,
	progression_crypto_ui.ProgressionCryptoDecrypt,
	room_export.ExportRoom,
	knshim_ui.InstallKnShim,
	rebake_ui.RebakeAllMeshes,
	mtxconv_ui.MtxconvExtract,
	mtxconv_ui.MtxconvBake,
)

keymaps = {
	"D": "shatter.create_box",
	"F": "shatter.create_obstacle",
	"X": "shatter.create_decal",
	"C": "shatter.create_powerup",
	"V": "shatter.create_water",
	
	"R": "shatter.export_auto",
	"Q": "shatter.export_all_auto",
	"E": "shatter.export_test_server",
	"P": "shatter.export_compressed",
	"L": "shatter.export",
	
	"I": "shatter.import",
	"O": "shatter.import_gz",
}

keymaps_registered = []

def register():
	util.log(f"Shatter OSS {butil.ext_version()} starting up!")
	util.log("""    "With the power of the prism, there's nothing I can't do."
         - Tails Nine 2024""")
	
	from bpy.utils import register_class
	
	for cls in classes:
		register_class(cls)
	
	init_obstacle_params()
	
	bpy.types.Scene.sh_properties = PointerProperty(type=SegmentProperties)
	# bpy.types.Scene.shatter_autogen = PointerProperty(type=autogen_ui.AutogenProperties)
	bpy.types.Object.sh_properties = PointerProperty(type=EntityProperties)
	
	# Add the export operator to menu
	bpy.types.TOPBAR_MT_file_export.append(sh_draw_export)
	bpy.types.TOPBAR_MT_file_export.append(sh_draw_export_gz)
	
	# Add import operators to menu
	bpy.types.TOPBAR_MT_file_import.append(sh_draw_import)
	bpy.types.TOPBAR_MT_file_import.append(sh_draw_import_gz)
	
	# Add Shatter menu in 3D viewport
	bpy.types.VIEW3D_MT_editor_menus.append(SHATTER_MT_3DViewportMenu_draw)
	
	# Register keymaps
	window_manager = bpy.context.window_manager
	
	if (window_manager.keyconfigs.addon):
		for a in keymaps:
			keymap = window_manager.keyconfigs.addon.keymaps.new(name = '3D View', space_type = 'VIEW_3D')
			keymap_item = keymap.keymap_items.new(keymaps[a], type = a, value = 'PRESS', shift = 1, alt = 1)
			keymaps_registered.append((keymap, keymap_item))
	
	# Start level server
	global gServerManager
	gServerManager = server_manager.LevelServerManager()
	server_manager_update()

def unregister():
	from bpy.utils import unregister_class
	
	# Remove export operators
	bpy.types.TOPBAR_MT_file_export.remove(sh_draw_export)
	bpy.types.TOPBAR_MT_file_export.remove(sh_draw_export_gz)
	
	# Remove import operators
	bpy.types.TOPBAR_MT_file_import.remove(sh_draw_import)
	bpy.types.TOPBAR_MT_file_import.remove(sh_draw_import_gz)
	
	# Remove editor menu UI
	bpy.types.VIEW3D_MT_editor_menus.remove(SHATTER_MT_3DViewportMenu_draw)
	
	# Delete property types
	del bpy.types.Scene.sh_properties
	# del bpy.types.Scene.shatter_autogen
	del bpy.types.Object.sh_properties
	
	destroy_obstacle_params()
	
	# Delete keymaps
	for a, b in keymaps_registered:
		a.keymap_items.remove(b)
	
	keymaps_registered.clear()
	
	# Unregister classes
	for cls in reversed(classes):
		# Blender decided it would be a piece of shit today 
		try:
			unregister_class(cls)
		except RuntimeError as e:
			util.log(f"Exception while unregistering {cls}:\n\n{e}")
	
	# Shutdown server
	global gServerManager
	gServerManager.stop()
