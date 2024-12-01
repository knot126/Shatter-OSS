"""
Shatter for Blender segment export

TODO This code sucks actual ass. Make it not.
"""

import xml.etree.ElementTree as et
import bpy
import gzip
import os
import os.path as ospath
import pathlib
import tempfile
import json
import pathlib
from . import mesh_runner
from . import obstacle_db
from . import util
from . import butil
from . import assets

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
)

NX_QUICK_TEST_LEVEL = """<level>
	<room type="test" length="300" start="true" end="true"/>
	<room type="test" length="300" start="true" end="true"/>
	<room type="test" length="300" start="true" end="true"/>
</level>
"""

prefs = butil.prefs

class ExportWarnings():
	"""
	Keep track of export warnings
	"""
	
	def __init__(self):
		self.warnings = set()
	
	def add(self, text):
		"""
		Add an export warning
		"""
		
		self.warnings.add(text)
	
	def display(self):
		"""
		Display a message with warnings
		"""
		
		if (len(self.warnings) and prefs().enable_segment_warnings):
			warnlist = []
			
			for warn in self.warnings:
				warnlist.append(warn)
			
			warnlist = ", ".join(warnlist)
			
			butil.show_message("Export warnings", f"The segment exported successfully, but some possible issues were noticed: {warnlist}.")

class ExportCounter():
	"""
	Helps count things
	"""
	
	def __init__(self):
		self.count = 0
	
	def inc(self):
		self.count += 1
	
	def has_any(self):
		return self.count > 0

def tryTemplatesPath():
	"""
	Try to get the path of the templates.xml file automatically
	"""
	
	# Try to find templates.xml using util.find_apk() first
	path = butil.find_apk()
	
	if (path):
		path += "/templates.xml.mp3"
	
	##
	## Templates file from home directory
	##
	
	if not path:
		path = util.codedir() + "/data/templates.xml"
	
	util.log(f"Got templates file: \"{path}\"")
	
	return path

def exportList(lst):
	return " ".join([str(x) for x in lst])

def exportPointList(lst):
	return f"{lst[1]} {lst[2]} {lst[0]}"

def isIndexableEqual(a, b):
	"""
	Check if two values that can be indexed are equal but don't care about their
	types. Examples:
	
	[1, 0] == [1, 0] -> True	
	(1, 0) == [1, 0] -> True
	[0, 1] == [1, 0] -> False
	(0, 1) == [1, 0] -> False
	"""
	
	if (len(a) != len(b)):
		return False
	
	for i in range(len(a)):
		if (a[i] != b[i]):
			return False
	
	return True

## Segment Export
## All of the following is related to exporting segments.

def sh_create_root(scene, params):
	"""
	Creates the main root and returns it
	"""
	
	size = [scene.sh_len[0], scene.sh_len[1], scene.sh_len[2]]
	
	# Automatic length detection
	if (scene.sh_auto_length):
		sizeZ = 0.0
		
		for o in bpy.context.scene.objects:
			# Find backmost part
			candZ = o.location[0] - (o.dimensions[0] / 2)
			
			# If it's lower that is the new semgent length
			if (candZ < sizeZ):
				sizeZ = candZ
		
		size[0] = 12.0
		size[1] = 10.0
		size[2] = -sizeZ
	
	# VR Multiply setting
	sh_vrmultiply = params.get("sh_vrmultiply", 1.0)
	
	if (sh_vrmultiply != 1.0):
		size[2] = size[2] * sh_vrmultiply
	
	# Segment size warning
	if (size[2] <= 0.0):
		params["warnings"].add("the segment length is zero or less which may behave weirdly")
	
	# Initial segment properties, like size
	seg_props = {
		"size": exportList(size)
	}
	
	# Check for the template attrib and set
	if (scene.sh_template):
		seg_props["template"] = scene.sh_template
	elif (scene.sh_default_template):
		seg_props["template"] = f"{scene.sh_default_template}_s"
	
	# Default template
	if (scene.sh_default_template):
		seg_props["shbt-default-template"] = scene.sh_default_template
	
	# Lighting
	# We no longer export lighting info if the template is present since that should
	# be taken care of there.
	if (not scene.sh_template):
		if (scene.sh_light_left != 1.0):   seg_props["lightLeft"] = str(scene.sh_light_left)
		if (scene.sh_light_right != 1.0):  seg_props["lightRight"] = str(scene.sh_light_right)
		if (scene.sh_light_top != 1.0):    seg_props["lightTop"] = str(scene.sh_light_top)
		if (scene.sh_light_bottom != 1.0): seg_props["lightBottom"] = str(scene.sh_light_bottom)
		if (scene.sh_light_front != 1.0):  seg_props["lightFront"] = str(scene.sh_light_front)
		if (scene.sh_light_back != 1.0):   seg_props["lightBack"] = str(scene.sh_light_back)
	
	# Check for softshadow attrib and set
	if (not (0.59999 < scene.sh_softshadow < 0.60001)):
		seg_props["softshadow"] = str(scene.sh_softshadow)
	
	# Add ambient lighting if enabled
	if (scene.sh_lighting):
		seg_props["ambient"] = exportList(scene.sh_lighting_ambient)
	
	# Create main root and return it
	level_root = et.Element("segment", seg_props)
	level_root.text = "\n\t"
	
	return level_root

def list_to_str(List):
	return " ".join([str(x) for x in List])

def make_subelement_from_entity(level_root, scene, obj, params):
	"""
	This will add an obstacle to level_root. Note that there is no big
	swtich-case like thing here, it's basically checking what type of entity we
	have each time we want to add a property, so adding a property appears only
	once but checks for the type of entity appear many times.
	
	`level_root` is the root xml entity we should add to
	`scene` is actually just bpy.context.scene.sh_properties
	`obj` is the object to export
	`params` is a dictionary of export settings
	"""
	
	# These positions are swapped
	position = {"X": obj.location[1], "Y": obj.location[2], "Z": obj.location[0]}
	
	# VR Multiply setting
	sh_vrmultiply = params.get("sh_vrmultiply", 1.0)
	
	if (sh_vrmultiply != 1.0):
		position["Z"] = position["Z"] * sh_vrmultiply
	
	# The only gaurrented to exsist is pos
	properties = {
		"pos": str(position["X"]) + " " + str(position["Y"]) + " " + str(position["Z"]),
	}
	
	# Shorthand for obj.sh_properties.sh_type
	sh_type = obj.sh_properties.sh_type
	
	# Count as a box if it's a box
	if (sh_type == "BOX"):
		params["box_counter"].inc()
	
	# Type for obstacles
	if (sh_type == "OBS"):
		properties["type"] = obj.sh_properties.sh_obstacle_chooser if obj.sh_properties.sh_use_chooser else obj.sh_properties.sh_obstacle
	
	# Type for power-ups
	if (sh_type == "POW"):
		properties["type"] = obj.sh_properties.sh_powerup
		
	# Hidden for all types
	if (not obj.visible_get()):
		properties["hidden"] = "1"
	else:
		properties["hidden"] = "0"
	
	# Again, swapped becuase of Smash Hit's demensions
	size = {"X": obj.dimensions[1] / 2, "Y": obj.dimensions[2] / 2, "Z": obj.dimensions[0] / 2}
	
	# Add size for boxes
	if (sh_type == "BOX"):
		# VR Multiply setting
		if (sh_vrmultiply != 1.0):
			size["Z"] = size["Z"] * sh_vrmultiply
		
		properties["size"] = str(size["X"]) + " " + str(size["Y"]) + " " + str(size["Z"])
		
		if (params.get("ignore_small_boxes", False)):
			return
	
	# Add rotation paramater if any rotation has been done
	if (sh_type == "OBS" or sh_type == "DEC"):
		if (obj.rotation_euler[1] != 0.0 or obj.rotation_euler[2] != 0.0 or obj.rotation_euler[0] != 0.0):
			properties["rot"] = exportPointList(obj.rotation_euler)
	
	# Add template
	if (obj.sh_properties.sh_template):
		properties["template"] = obj.sh_properties.sh_template
	# Use default template from scene if we don't have one
	elif (scene.sh_default_template):
		default_template = scene.sh_default_template
		
		# We use the standard naming convention from most Smash Hit templates
		# for these:
		#   Box -> {basename}
		#   Crystal obstacle -> {basename}_st
		#   Non-crystal Obstacle -> {basename}_glass
		#   Segment -> {basename}_s
		if (default_template):
			if (sh_type == "BOX"):
				properties["template"] = default_template
			elif (sh_type == "OBS"):
				if (properties["type"].startswith("score")):
					properties["template"] = f"{default_template}_st"
				else:
					properties["template"] = f"{default_template}_glass"
			elif (sh_type == "DEC"):
				properties["template"] = f"{default_template}_decal"
			elif (sh_type == "POW"):
				properties["template"] = f"{default_template}_pu"
			elif (sh_type == "WAT"):
				properties["template"] = f"{default_template}_water"
	
	# Add mode appearance tag
	if (sh_type == "OBS"):
		mask = 0b0
		
		for v in [("training", 1), ("classic", 2), ("expert", 4), ("versus", 16), ("coop", 32)]:
			if (v[0] in obj.sh_properties.sh_mode):
				mask |= v[1]
		
		if (mask != 0b110111):
			properties["mode"] = str(mask)
	
	# Add difficulty for relevant entity types
	if (sh_type in ["OBS", "POW", "DEC"]):
		diffic = obj.sh_properties.sh_difficulty
		
		# Only export if it's not default of (0.0, 1.0)
		if (diffic[0] != 0.0 or diffic[1] != 1.0):
			properties["difficulty"] = exportList(diffic)
	
	# Add reflection property for boxes if not default
	if (sh_type == "BOX" and obj.sh_properties.sh_reflective):
		properties["reflection"] = "1"
	
	# Add glow property for boxes if not default
	if (sh_type == "BOX" and obj.sh_properties.sh_glow != 0.0):
		properties["glow"] = str(obj.sh_properties.sh_glow)
	
	# Add decal number if this is a decal
	if (sh_type == "DEC"):
		properties["tile"] = str(obj.sh_properties.sh_decal)
	
	# Add decal size if this is a decal
	# Based on sh_size if its not some kind of plane
	if (sh_type == "DEC"):
		if (obj.dimensions[1] == 0.0 and obj.dimensions[2] == 0.0):
			properties["size"] = exportList(obj.sh_properties.sh_size)
		else:
			size = {"X": obj.dimensions[1] / 2, "Y": obj.dimensions[2] / 2}
			properties["size"] = str(size["X"]) + " " + str(size["Y"])
	
	# Add water size if this is a water (based on physical plane properties)
	# Also adds quality if not default
	if (sh_type == "WAT"):
		size = {"X": obj.dimensions[1] / 2, "Z": obj.dimensions[0] / 2}
		
		properties["size"] = str(size["X"]) + " " + str(size["Z"] * sh_vrmultiply)
		
		if (not isIndexableEqual(obj.sh_properties.sh_resolution, [32.0, 32.0])):
			properties["resolution"] = exportList(obj.sh_properties.sh_resolution)
	
	# Set each of the tweleve paramaters if they are needed.
	if (sh_type == "OBS"):
		for i in range(12):
			val = getattr(obj.sh_properties, "sh_param" + str(i))
			
			if (val):
				properties["param" + str(i)] = val
	
	# Warning for param0 and template being set
	if (sh_type == "OBS" and obj.sh_properties.sh_param0 and obj.sh_properties.sh_template):
		params["warnings"].add("both param0 and a template are set on some obstacles making param0 override the template - since param0 is often used for colours this might result in clear glass")
	
	# Set tint for decals
	if (sh_type == "DEC" and obj.sh_properties.sh_havetint):
		properties["color"] = exportList(obj.sh_properties.sh_tint)
	
	# Set blend for decals
	if (sh_type == "DEC" and obj.sh_properties.sh_blend != 1.0):
		properties["blend"] = str(obj.sh_properties.sh_blend)
	
	if (sh_type == "BOX"):
		if (not obj.sh_properties.sh_visible and not obj.sh_properties.sh_template):
			properties["visible"] = "0"
		else:
			properties["visible"] = "1"
	
	# Set tile info for boxes if visible
	# # This basically overrides any point to having a template
	if (sh_type == "BOX"):
		# Chose colour string depending on if multitint is enabled
		if (not obj.sh_properties.sh_use_multitint):
			# Export if not default
			if (obj.sh_properties.sh_tint[0] != 1.0 or obj.sh_properties.sh_tint[1] != 1.0 or obj.sh_properties.sh_tint[2] != 1.0):
				properties["color"] = exportList(obj.sh_properties.sh_tint[:3])
		else:
			properties["color"] = str(obj.sh_properties.sh_tint1[0]) + " " + str(obj.sh_properties.sh_tint1[1]) + " " + str(obj.sh_properties.sh_tint1[2]) + " " + str(obj.sh_properties.sh_tint2[0]) + " " + str(obj.sh_properties.sh_tint2[1]) + " " + str(obj.sh_properties.sh_tint2[2]) + " " + str(obj.sh_properties.sh_tint3[0]) + " " + str(obj.sh_properties.sh_tint3[1]) + " " + str(obj.sh_properties.sh_tint3[2])
		
		# Depnding on if tile per side is selected
		if (not obj.sh_properties.sh_use_multitile):
			if (obj.sh_properties.sh_tile != 0):
				properties["tile"] = str(obj.sh_properties.sh_tile)
		else:
			properties["tile"] = str(obj.sh_properties.sh_tile1) + " " + str(obj.sh_properties.sh_tile2) + " " + str(obj.sh_properties.sh_tile3)
		
		# Tile size for boxes
		if (obj.sh_properties.sh_tilesize[0] != 1.0 or obj.sh_properties.sh_tilesize[1] != 1.0 or obj.sh_properties.sh_tilesize[2] != 1.0):
			properties["tileSize"] = exportList(obj.sh_properties.sh_tilesize)
		
		# Tile rotation
		if (obj.sh_properties.sh_tilerot[1] > 0.0 or obj.sh_properties.sh_tilerot[2] > 0.0 or obj.sh_properties.sh_tilerot[0] > 0.0):
			properties["tileRot"] = exportList(obj.sh_properties.sh_tilerot)
		
		# Box gradients
		v = obj.sh_properties.sh_graddir
		
		# No gradient
		if (v == "none"):
			pass
		# Points mode
		elif (v == "relative" or v == "absolute"):
			final = "" if v == "relative" else "A "
			
			final += list_to_str(obj.sh_properties.sh_gradpoint1)
			final += " " + list_to_str(obj.sh_properties.sh_gradpoint2)
			final += " " + list_to_str(obj.sh_properties.sh_gradcolour1)
			final += " " + list_to_str(obj.sh_properties.sh_gradcolour2)
			
			properties["mb-gradient"] = final
		# Basic mode
		else:
			final = {
				"left": "1 0 0 -1 0 0",
				"right": "-1 0 0 1 0 0",
				"top": "0 -1 0 0 1 0",
				"bottom": "0 1 0 0 -1 0",
				"front": "0 0 -1 0 0 1",
				"back": "0 0 1 0 0 -1",
			}[v]
			
			final += " " + list_to_str(obj.sh_properties.sh_gradcolour1)
			final += " " + list_to_str(obj.sh_properties.sh_gradcolour2)
			
			properties["mb-gradient"] = final
	
	# Set the tag name
	element_type = "shbt-unknown-entity"
	
	if (sh_type == "BOX"):
		element_type = "box"
	elif (sh_type == "OBS"):
		element_type = "obstacle"
	elif (sh_type == "DEC"):
		element_type = "decal"
	elif (sh_type == "POW"):
		element_type = "powerup"
	elif (sh_type == "WAT"):
		element_type = "water"
	else:
		params["warnings"].add("an unknown type of entity was found")
	
	# Add the element to the document
	el = et.SubElement(level_root, element_type, properties)
	el.tail = "\n\t"
	if (params["isLast"]): # Fixes the issues with the last line of the file
		el.tail = "\n"
	
	# Some things to handle legacy colour model
	use_legacy = params["stone_legacy_colour_model"]
	default_colour = params["stone_legacy_colour_default"]
	
	if (params.get("sh_box_bake_mode", "Mesh") == "StoneHack" and sh_type == "BOX" and (obj.sh_properties.sh_visible or use_legacy)):
		"""
		Export a fake obstacle that will represent stone in the level.
		"""
		
		el.tail = "\n\t\t"
		
		size = {"X": obj.dimensions[1] / 2, "Y": obj.dimensions[2] / 2, "Z": obj.dimensions[0] / 2}
		position = {"X": obj.location[1], "Y": obj.location[2], "Z": obj.location[0]}
		
		# VR Multiply setting
		position["Z"] = position["Z"] * sh_vrmultiply
		size["Z"] = size["Z"] * sh_vrmultiply
		
		properties = {
			"pos": str(position["X"]) + " " + str(position["Y"]) + " " + str(position["Z"]),
			"type": params.get("stone_type", "stone"),
			"param9": "sizeX=" + str(size["X"]),
			"param10": "sizeY=" + str(size["Y"]),
			"param11": "sizeZ=" + str(size["Z"]),
			"shbt-ignore": "1",
		}
		
		if (obj.sh_properties.sh_template):
			properties["template"] = obj.sh_properties.sh_template
		else:
			colour = obj.sh_properties.sh_tint if obj.sh_properties.sh_visible else default_colour
			
			properties["param7"] = "tile=" + str(obj.sh_properties.sh_decal)
			properties["param8"] = "color=" + str(colour[0]) + " " + str(colour[1]) + " " + str(colour[2])
		
		el_stone = et.SubElement(level_root, "obstacle", properties)
		el_stone.tail = "\n\t"
		if (params["isLast"]):
			el_stone.tail = "\n"

def createSegmentText(scene, params):
	"""
	Export the XML part of a segment to a string
	"""
	
	# Set some params
	params["stone_type"] = scene.sh_properties.sh_stone_obstacle_name
	params["stone_legacy_colour_model"] = scene.sh_properties.sh_legacy_colour_model
	params["stone_legacy_colour_default"] = scene.sh_properties.sh_legacy_colour_default
	
	level_root = sh_create_root(scene.sh_properties, params)
	
	# Enumerate which objects we should export right now
	
	### Export all objects ###
	
	# NOTE: 2023-10-10 This was changed so that it now uses objects only in the
	# current selected scene in the blend file and not just exports all objects
	# even if they are not in the current scene
	objects = scene.objects
	
	# A list of objects that will actually be exported (e.g. those that have
	# sh_export set)
	exportedObjectsList = []
	
	for o in objects:
		if (o.sh_properties.sh_export):
			exportedObjectsList.append(o)
	
	objects = exportedObjectsList
	
	# Export every object in the scene
	for i in range(len(objects)):
		obj = objects[i]
		
		if (not obj.sh_properties.sh_export):
			continue
		
		params["isLast"] = False
		
		# This is a bit ugly but at least isn't not broken with the pre-computed
		# export list anymore :)
		if (i == (len(objects) - 1)):
			params["isLast"] = True
		
		make_subelement_from_entity(level_root, scene.sh_properties, obj, params)
	
	# Check the warning for box count being zero
	if (not params["box_counter"].has_any()):
		params["warnings"].add("there are no boxes which causes the segment to load improperly")
	
	# Add file header with version
	file_header = f"<!-- Exporter: Shatter OSS {butil.ext_version()} -->\n"
	
	# Get final string
	content = file_header + et.tostring(level_root, encoding = "unicode")
	
	return content

def writeQuicktestInfo(tempdir, scene):
	"""
	Write the quick test `room.json` file
	"""
	
	fb = scene.sh_fog_colour_bottom
	ft = scene.sh_fog_colour_top
	
	info = {
		"fog": f"{fb[0]} {fb[1]} {fb[2]} {ft[0]} {ft[1]} {ft[2]}",
		"length": scene.sh_room_length,
		"gravity": scene.sh_gravity,
	}
	
	if (scene.sh_music):
		info["music"] = scene.sh_music
	
	if (scene.sh_reverb):
		info["reverb"] = scene.sh_reverb
	
	if (scene.sh_echo):
		info["echo"] = scene.sh_echo
	
	if (scene.sh_rotation):
		info["rot"] = scene.sh_rotation
	
	if (scene.sh_difficulty > 0.0):
		info["difficulty"] = scene.sh_difficulty
	
	if (scene.sh_extra_code):
		info["code"] = scene.sh_extra_code
	
	if (scene.sh_particles != "None"):
		info["particles"] = scene.sh_particles
	
	# Try to find where to load remote obstacles from
	apk_path = butil.find_apk()
	
	if (apk_path):
		info["assets"] = apk_path
	
	pathlib.Path(tempdir + "/room.json").write_text(json.dumps(info))

def get_room_data(scene):
	scene = scene.sh_properties
	room = util.get_file(util.codedir() + "/data/quick.lua")
	
	music = f"mgMusic({repr(scene.sh_music)})" if scene.sh_music else "mgMusic(tostring(math.random(0, 28)))"
	room = room.replace("__shatter_quick_music__", music)
	
	fog = f"mgFogColor({scene.sh_fog_colour_bottom[0]}, {scene.sh_fog_colour_bottom[1]}, {scene.sh_fog_colour_bottom[2]}, {scene.sh_fog_colour_top[0]}, {scene.sh_fog_colour_top[1]}, {scene.sh_fog_colour_top[2]})"
	room = room.replace("__shatter_quick_fog__", fog)
	
	for field in ["echo", "reverb", "rotation", "difficulty", "gravity"]:
		data = getattr(scene, f"sh_{field}")
		
		if not data:
			room = room.replace(f"__shatter_quick_{field}__\n\t", "")
			continue
		
		# Setter function name
		funcname = "mg" + field.title()
		if field == "rotation": funcname = "mgSetRotation"
		if field == "difficulty": funcname = "mgSetDifficulty"
		
		# The params
		params = "(" + ", ".join(str(data).split()) + ")"
		
		# Substitution
		room = room.replace(f"__shatter_quick_{field}__", funcname + params)
	
	particles = f"mgParticles({repr(scene.sh_particles)})" if not scene.sh_particles == "None" else ""
	room = room.replace("__shatter_quick_particles__", particles)
	
	room = room.replace("__shatter_quick_length__", str(scene.sh_room_length))
	
	return room

def bake_mesh(input_file, templates, params):
	new_params = {
		"BAKE_UNSEEN_FACES": params.get("bake_menu_segment", False),
		"bake_menu_segment": params.get("bake_menu_segment", False),
		"ABMIENT_OCCLUSION_ENABLED": params.get("bake_vertex_light", True),
		"LIGHTING_ENABLED": params.get("lighting_enabled", False),
		"ymb_ao": params.get("ymb_ao", "1"),
		"ymb_tiles": butil.get_setting('ymb_tiles'),
		
		"cmd": prefs().mesh_command,
	}
	
	mesh_runner.bake(prefs().mesh_baker, input_file, templates, new_params)

def sh_export_segment_ext(filepath, context, scene, compress = False, params = {}):
	"""
	This function exports the blender scene to a Smash Hit compatible XML file.
	(Mutli-scene-agnostic version)
	"""
	
	# Set wait cursor
	context.window.cursor_set('WAIT')
	context.window_manager.progress_begin(0.0, 1.0)
	
	# Warnings related
	params["warnings"] = ExportWarnings()
	params["box_counter"] = ExportCounter()
	
	# AO quality
	if (prefs().mesh_baker == "yorshex" and scene.sh_properties.ambient_occlusion_quality != "-1"):
		params["ymb_ao"] = scene.sh_properties.ambient_occlusion_quality
	
	# If the filepath is None, then find it from the apk, force enable
	# compression.
	if (filepath == None and params.get("auto_find_filepath", False)):
		props = scene.sh_properties
		
		filepath = butil.find_apk()
		
		if (not filepath):
			butil.show_message("Export error", "There is currently no APK open in APK Editor Studio or your asset override path isn't set. Please open a Smash Hit APK with a valid structure or set an asset path in Shatter settings and try again.")
			return {"FINISHED"}
		
		if ((not props.sh_level or not props.sh_room or not props.sh_segment) and (not props.sh_segment)):
			butil.show_message("Export error", "You have not set one of the level, room or segment name properties needed to use auto export to apk feature. Please set these in the scene tab and try again.")
			return {"FINISHED"}
		
		# Real file path
		filepath += "/segments/" + props.sh_level + "/" + props.sh_room + "/" + props.sh_segment + (".xml.gz.mp3" if compress else ".xml.mp3")
		
		util.prepare_folders(filepath)
		
		util.log(f"Real file path will be {filepath}")
	
	# Export to xml string
	content = createSegmentText(scene, params)
	
	# Get templates path, needed for later
	templates = params.get("sh_meshbake_template", None)
	
	# Do some extra quick test related things
	if (params.get("sh_test_server", False) == True):
		server_type = prefs().quick_test_server
		
		if (server_type == "builtin"):
			util.log("Builtin test server export")
			
			# Solve templates if we have them
			if (templates):
				content = util.solve_templates(content, util.load_templates(templates))
			
			# Make dirs
			tempdir = butil.storage_path("testserver")
			os.makedirs(tempdir, exist_ok = True)
			
			# Make XML path
			filepath = ospath.join(tempdir, "segment.xml")
			
			# Write quick test JSON room info file
			writeQuicktestInfo(tempdir, context.scene.sh_properties)
		elif (server_type == "nx"):
			util.log("Exporting segment for NxQuick test server")
			
			# NxServer uses asset folder overlays which override certian files
			# in one asset folder with another instead of the simlper but pretty
			# jank tempdir that the old ('builtin') server uses.
			# 
			# Create the overlay structure, if not already created
			overlay = butil.storage_path("testserver")
			
			os.makedirs(f"{overlay}/levels", exist_ok=True)
			os.makedirs(f"{overlay}/rooms", exist_ok=True)
			os.makedirs(f"{overlay}/segments", exist_ok=True)
			
			util.set_file(f"{overlay}/levels/test.xml.mp3", NX_QUICK_TEST_LEVEL)
			util.set_file(f"{overlay}/rooms/test.lua.mp3", get_room_data(scene))
			filepath = f"{overlay}/segments/test.xml.mp3"
			compress = False
			
			# Async POST /v6/config to update config for asset dir if needed
			util.do_async_json_post("http://localhost:8000/v6/config", {
				"token": params.get("nx_token", "unknown"),
				"assets": butil.find_apk(),
			})
		elif (server_type == "yorshex"):
			util.log("Export to yorshex asset server in quick test mode")
			
			# NxServer uses asset folder overlays which override certian files
			# in one asset folder with another instead of the simlper but pretty
			# jank tempdir that the old ('builtin') server uses.
			# 
			# Create the overlay structure, if not already created
			asset_dir = butil.find_apk()
			
			util.set_file(f"{asset_dir}/levels/test.xml.mp3", NX_QUICK_TEST_LEVEL)
			util.set_file(f"{asset_dir}/rooms/test.lua.mp3", get_room_data(scene))
			filepath = f"{asset_dir}/segments/test.xml.mp3"
			compress = False
	else:
		# Preform template resolution if it is enabled for all segments and not
		# in quick test mode.
		if (prefs().resolve_templates and templates):
			content = util.solve_templates(content, util.load_templates(templates))
	
	##
	## Write the file
	##
	
	# Write out file
	with (gzip.open(filepath, "wb") if compress else open(filepath, "wb")) as f:
		f.write(content.encode())
	
	# Cook the mesh if we need to
	if (params.get("sh_box_bake_mode", "Mesh") == "Mesh"):
		bake_mesh(filepath, templates, params)
	
	# Display export warnings, if any and if enabled
	params["warnings"].display()
	
	# Progress display cleanup
	context.window_manager.progress_update(1.0)
	context.window_manager.progress_end()
	context.window.cursor_set('DEFAULT')

def sh_export_all_segments(context, compress = True, aotype = '1'):
	for s in bpy.data.scenes:
		util.log(f"Exporting a scene: {s} ...")
		
		sh_properties = s.sh_properties
		
		sh_export_segment_ext(None, context, s, compress, params = {
				"sh_vrmultiply": sh_properties.sh_vrmultiply,
				"sh_box_bake_mode": sh_properties.sh_box_bake_mode,
				"sh_meshbake_template": tryTemplatesPath(),
				"bake_menu_segment": sh_properties.sh_menu_segment,
				"bake_vertex_light": sh_properties.sh_ambient_occlusion,
				"lighting_enabled": sh_properties.sh_lighting,
				"auto_find_filepath": True,
				"ymb_ao": aotype,
			})

def sh_export_segment(filepath, context, compress = False, testserver = False, nx_token = None, aotype = '1'):
	sh_properties = context.scene.sh_properties
	
	params = {
		"sh_vrmultiply": sh_properties.sh_vrmultiply,
		"sh_box_bake_mode": sh_properties.sh_box_bake_mode,
		"bake_menu_segment": sh_properties.sh_menu_segment,
		"bake_vertex_light": sh_properties.sh_ambient_occlusion,
		"lighting_enabled": sh_properties.sh_lighting,
		"sh_test_server": testserver,
		"nx_token": nx_token,
		"sh_meshbake_template": tryTemplatesPath(),
		"auto_find_filepath": not testserver, # HACK to make this work
		"ymb_ao": aotype,
	}
	
	util.log(f"Exporting a segment:\n\tfilepath = {filepath}\n\tcompress = {compress}\n\ttestserver = {testserver}\n\tparams = {params}")
	
	sh_export_segment_ext(filepath, context, context.scene, compress, params)


