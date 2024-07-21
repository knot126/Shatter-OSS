"""
Autogen UI stuff
"""

import bpy
import random
import autogen
import butil

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

###############
### AUTOGEN ###
###############

class AutogenProperties(PropertyGroup):
	
	seed: IntProperty(
		name = "Seed",
		description = "The seed to feed to the randomiser. Knowing the seed that you will run with allows you to recreate the exact results later",
		default = 0,
	)
	
	auto_randomise: BoolProperty(
		name = "Auto randomise",
		description = "Automatically generate a new, random seed every time a generation action is run",
		default = True,
	)
	
	type: EnumProperty(
		name = "Type",
		description = "Type of thing you would like to generate",
		items = [
			('BasicRoom', "Room structure", "Adds a basic room-like structure, optionally including a door area"),
			('SingleRow', "Row of boxes", "A single row of boxes, often used before and after chasms. Look at the first room of the game for an example of this"),
			('ArchWay', "Archway", "Creates an arch-like structure with bumps and floor parts"),
		],
		default = "SingleRow",
	)
	
	algorithm: EnumProperty(
		name = "Algorithm",
		description = "Algorithm to use to generate the thing",
		items = [
			('ActualRandom', "ActualRandom", "Purely random box heights"),
			('UpAndDownPath', "UpAndDownPath", ""),
			('ArithmeticProgressionSet', "ArithmeticProgressionSet", "Randomly selected from a subset of a arithmetic series (ex: random of 1/2, 1/4, 1/6)"),
			('GeometricProgressionSet', "GeometricProgressionSet", "Randomly selected from a subset of a geometric series (ex: random of 1/2, 1/4, 1/8)"),
		],
		default = "ActualRandom",
	)
	
	template: StringProperty(
		name = "Template",
		description = "Template to use for these boxes. You can also select a target box to copy properties from that box",
		default = "",
	)
	
	direction: EnumProperty(
		name = "Direction",
		description = "The direction that autogen will consider up",
		items = [
			('up', "Up", ""),
			('down', "Down", ""),
			('left', "Left", ""),
			('right', "Right", ""),
			('front', "Front", ""),
			('back', "Back", ""),
		],
		default = "up",
	)
	
	size: FloatVectorProperty(
		name = "Box size",
		description = "First is width, second is depth. Height is the random part",
		default = (1.0, 1.0), 
		size = 2,
	)
	
	max_height: FloatProperty(
		name = "Max height",
		description = "",
		default = 0.5,
	)
	
	### Up and down path options ###
	
	udpath_start: FloatProperty(
		name = "Initial height",
		description = "",
		default = 0.25,
	)
	
	udpath_step: FloatProperty(
		name = "Step",
		description = "",
		default = 0.125,
	)
	
	udpath_minmax: FloatVectorProperty(
		name = "Min/max height",
		description = "",
		default = (0.125, 0.5), 
		size = 2,
	)
	
	### Geometric/Airthmetic progression generator options ###
	
	geometric_ratio: FloatProperty(
		name = "Ratio",
		description = "",
		default = 0.5,
	)
	
	geometric_exponent_minmax: IntVectorProperty(
		name = "Exponent",
		description = "",
		default = (1, 4),
		size = 2,
	)
	
	geometric_require_unique: BoolProperty(
		name = "No repeating heights",
		description = "",
		default = False,
	)
	
	### Room ###
	
	room_length: FloatProperty(
		name = "Length",
		description = "",
		default = 16.0,
	)
	
	room_door_part: BoolProperty(
		name = "Door part",
		description = "",
		default = False,
	)
	
	room_yoffset: FloatProperty(
		name = "Height offset",
		description = "How high or low the room will appear to the player",
		default = 1.0,
	)
	
	### Arch ###
	
	arch_top_parts: BoolProperty(
		name = "Top decorations",
		description = "",
		default = True,
	)

class AutogenPanel(Panel):
	bl_label = "Shatter Autogen"
	bl_idname = "OBJECT_PT_autogen_panel"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Autogen"
	
	@classmethod
	def poll(self, context):
		return True
	
	def draw(self, context):
		layout = self.layout
		props = context.scene.shatter_autogen
		
		sub = layout.box()
		sub.label(text = "Seed", icon = "GRAPH")
		sub.prop(props, "auto_randomise")
		if (not props.auto_randomise):
			sub.prop(props, "seed")
			sub.operator("shatter.randomise_autogen_seed", text = "Randomise seed")
		
		sub = layout.box()
		sub.label(text = "Generate", icon = "BRUSHES_ALL")
		sub.prop(props, "type")
		if (props.type == "SingleRow"):
			sub.prop(props, "algorithm")
		if (not context.object):
			sub.prop(props, "template")
		else:
			sub.label(text = "Copying props from selected")
		if (props.type == "SingleRow" and props.algorithm != "ArithmeticProgressionSet"):
			sub.prop(props, "max_height")
		
		sub.prop(props, "direction")
		sub.prop(props, "size")
		
		# Single row options
		if (props.type == "SingleRow"):
			if (props.algorithm in ["UpAndDownPath"]):
				sub.prop(props, "udpath_start")
				sub.prop(props, "udpath_step")
				sub.prop(props, "udpath_minmax")
			
			if (props.algorithm in ["GeometricProgressionSet", "ArithmeticProgressionSet"]):
				sub.prop(props, "geometric_ratio")
				sub.prop(props, "geometric_exponent_minmax", text = "Exponent" if props.algorithm.startswith("G") else "Scalar")
				sub.prop(props, "geometric_require_unique")
		
		# Room options
		if (props.type == "BasicRoom"):
			sub.prop(props, "room_length")
			sub.prop(props, "room_yoffset")
			sub.prop(props, "room_door_part")
		
		# Archway
		if (props.type == "ArchWay"):
			sub.prop(props, "arch_top_parts")
		
		sub.operator("shatter.run_autogen", text = "Generate")
		
		layout.separator()

class RunRandomiseSeedAction(bpy.types.Operator):
	"""Choses a random seed in the range [0, 2 ^ 31 - 1]"""
	
	bl_idname = "shatter.randomise_autogen_seed"
	bl_label = "Randomise Autogen Seed"
	
	def execute(self, context):
		context.scene.shatter_autogen.seed = random.randint(0, 2 ** 31 - 1)
		
		return {'FINISHED'}

def real_loc(x, y, z, up = "up"):
	"""
	Get the real output location after accounting for which direction is used
	as up.
	"""
	
	if (up == "up"):
		return (x, y, z)
	elif (up == "down"):
		return (x, y, -z)
	elif (up == "left"):
		return (-y, x, z)
	elif (up == "right"):
		return (y, -x, z)
	elif (up == "front"):
		return (x, -z, y)
	elif (up == "back"):
		return (x, z, -y)

def fake_loc(x, y, z, up = "up"):
	"""
	Inverse of real_loc()
	"""
	
	if (up == "up"):
		return (x, y, z)
	elif (up == "down"):
		return (x, y, -z)
	elif (up == "left"):
		return (y, -x, z)
	elif (up == "right"):
		return (-y, x, z)
	elif (up == "front"):
		return (x, z, -y)
	elif (up == "back"):
		return (x, -z, y)

class BlenderPlacer:
	"""
	Provides an interface for the autogenerator to create boxes in blender in
	a generic way.
	"""
	
	def __init__(self, basePos, baseSize, direction, param3):
		if (basePos and baseSize):
			self.setUpDir(direction)
			self.setBase(basePos, baseSize)
		else:
			self.setUpDir(direction)
		
		# This is probably a bit insane, but it's probably not the worst way of
		# doing this...
		if (type(param3) == str):
			self.template = param3
		else:
			self.visible_object_props = param3.sh_properties
		
		self.objects = []
	
	def setUpDir(self, direction):
		self.direction = direction
	
	def setBase(self, basePos, baseSize):
		"""
		Make a base box from the blender location and size
		"""
		
		x, y, z = fake_loc(basePos[1], basePos[2], basePos[0], self.direction)
		sx, sy, sz = fake_loc(baseSize[1] / 2, baseSize[2] / 2, baseSize[0] / 2, self.direction)
		
		self.base = autogen.Box(autogen.Vector3(x, y, z), autogen.Vector3(sx, sy, sz))
	
	def getBase(self):
		"""
		Get the base box as a generic box
		"""
		
		return self.base if hasattr(self, "base") else None
	
	def inheritProperties(self, obj, template_append = ""):
		"""
		Inherit the template or visible properties
		"""
		
		# Use the base box if one exists, otherwise just fallback to using the
		# template value
		if (hasattr(self, "base")):
			update_properties = ["sh_visible", "sh_template", "sh_tint", "sh_use_multitint", "sh_tint1", "sh_tint2", "sh_tint3", "sh_tile", "sh_use_multitile", "sh_tile1", "sh_tile2", "sh_tile3", "sh_tilerot", "sh_tilesize"]
			
			for prop in update_properties:
				val = getattr(self.visible_object_props, prop)
				setattr(obj.sh_properties, prop, val)
		else:
			obj.sh_properties.sh_template = self.template + template_append
	
	def addBox(self, box):
		"""
		Add a box to the scene
		"""
		
		# Add the mesh
		bpy.ops.mesh.primitive_cube_add(size = 1.0, location = real_loc(box.pos.z, box.pos.x, box.pos.y, self.direction), scale = real_loc(box.size.z * 2, box.size.x * 2, box.size.y * 2, self.direction))
		
		# The added mesh is always selected after, so we do this to get the object
		box = bpy.context.active_object
		
		# Set the template or visible settings
		self.inheritProperties(box)
		
		# Append the box to the list of objects we have made
		self.objects.append(box)
	
	def addObstacle(self, obs):
		"""
		Add an obstacle to the scene
		"""
		
		o = bpy.data.objects.new("empty", None)
		
		bpy.context.scene.collection.objects.link(o)
		
		o.empty_display_size = 1
		o.empty_display_type = "PLAIN_AXES"
		
		o.location = real_loc(obs.pos.z, obs.pos.x, obs.pos.y, self.direction)
		
		o.sh_properties.sh_type = "OBS"
		o.sh_properties.sh_obstacle = obs.type
		self.inheritProperties(o, "_glass")
		
		self.objects.append(o)
	
	def addDecal(self, dec):
		"""
		Add a new decal to the scene
		"""
		
		o = bpy.data.objects.new("empty", None)
		
		bpy.context.scene.collection.objects.link(o)
		
		o.empty_display_size = 1
		o.empty_display_type = "PLAIN_AXES"
		
		o.location = real_loc(dec.pos.z, dec.pos.x, dec.pos.y, self.direction)
		
		o.sh_properties.sh_type = "DEC"
		o.sh_properties.sh_decal = dec.id
		self.inheritProperties(o)
		
		self.objects.append(o)
	
	def selectAll(self):
		"""
		Select all objects that were part of this round
		"""
		
		for o in self.objects:
			o.select_set(True)

class RunAutogenAction(bpy.types.Operator):
	"""Runs the automatic generator with the current settings"""
	
	bl_idname = "shatter.run_autogen"
	bl_label = "Run Shatter Autogen"
	
	def execute(self, context):
		"""
		Furries Furries Furries Furries Furries Furries Furries Furries Furries
		Furries Furries Furries Furries Furries Furries Furries Furries Furries
		Furries Furries Furries Furries Furries Furries Furries Furries Furries
		Furries Furries Furries Furries Furries Furries Furries Furries Furries
		
		COMMENT @knot126: npesta moment
		"""
		
		props = context.scene.shatter_autogen
		
		if (props.auto_randomise):
			context.scene.shatter_autogen.seed = random.randint(0, 2 ** 31 - 1)
		
		placer = BlenderPlacer(
			context.object.location if context.object else None,
			context.object.dimensions if context.object else None,
			props.direction,
			context.object if context.object and (context.object.sh_properties.sh_visible or not props.template) else props.template,
		)
		
		params = {
			"seed": props.seed,
			"type": props.type,
			"size": props.size,
			"max_height": props.max_height,
		}
		
		# For all single row types
		if (props.type == "SingleRow"):
			# Check if a box is currently selected, error if not
			if (not placer.getBase()):
				butil.show_message("Shatter Autogen error", "To use the single row generator, please select a box to build on top of.")
				return {"FINISHED"}
			
			params["algorithm"] = props.algorithm
			
			# Geometric options
			if (props.algorithm in ["GeometricProgressionSet", "ArithmeticProgressionSet"]):
				params["geometric_exponent_minmax"] = props.geometric_exponent_minmax
				params["geometric_ratio"] = props.geometric_ratio
				params["geometric_require_unique"] = props.geometric_require_unique
			
			# UpDownPath options
			if (props.algorithm in ["UpAndDownPath"]):
				params["udpath_min"] = props.udpath_minmax[0]
				params["udpath_max"] = props.udpath_minmax[1]
				params["udpath_start"] = props.udpath_start
				params["udpath_step"] = props.udpath_step
		
		# Room options
		if (props.type == "BasicRoom"):
			params["room_length"] = props.room_length
			params["room_yoffset"] = props.room_yoffset
			params["room_door_part"] = props.room_door_part
		
		# Archway
		if (props.type == "ArchWay"):
			params["top_parts"] = props.arch_top_parts
		
		autogen.generate(placer, params)
		
		placer.selectAll()
		
		return {'FINISHED'}
