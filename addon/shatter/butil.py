"""
Blender-specific utilities
"""

import os
import os.path as ospath
import pathlib
import tempfile
import bpy

class UIDrawingHelper():
	"""
	Helpful thing to draw UIs easier than the Blender API allows for. Basically
	takes a context and layout and starts drawing based on what you say. No need
	to manipulate variables or anything either.
	
	The current object to pull properties from is just stored as part of the
	state. The layouts are kept on a stack and always poped with end().
	"""
	
	def __init__(self, context, layout, obj, *, compact = False):
		self.context = context
		self.layout = [layout]
		self.obj = obj
		self.compact = compact
	
	def set_object(self, obj):
		"""
		Set the object to take properties from
		"""
		
		self.obj = obj
	
	def get_object(self):
		"""
		Get the object used to take properties from
		"""
		
		return self.obj
	
	def get(self, symbol):
		"""
		Get the value of the given property (symbol) on the current object
		"""
		
		return getattr(self.obj, symbol)
	
	def begin(self):
		"""
		Begin a new (non-region) layout
		"""
		
		sub = self.layout[-1].column()
		self.layout.append(sub)
	
	def beginFake(self):
		"""
		Begin a fake layout (just pushes the current one again)
		"""
		
		self.layout.append(self.layout[-1])
	
	def end(self):
		"""
		Pop the current layout off of the stack
		"""
		
		self.layout.pop()
	
	def region(self, icon = "", title = "", new = True, force = False):
		"""
		Create a new UI region (e.g. boxed area with title)
		
		If `new` is set, then any previous box will automatically be poped from
		the stack
		"""
		
		if (self.compact and not force):
			return self.beginFake()
		
		if (new and len(self.layout) > 1):
			self.end()
		
		self.layout.append(self.layout[-1].box())
		
		self.layout[-1].label(text = title, icon = icon)
	
	def label(self, text):
		"""
		Draw a basic label
		"""
		
		self.layout[-1].label(text = text)
	
	def prop(self, symbol, *, icon = None, text = None, text_compact = None, use_button = False, disabled = False, use_tabs = False):
		"""
		Draw the property with the given options
		
		Returns the value of the property drawn
		"""
		
		args = {}
		
		# Set up properties
		if (text != None):
			args["text"] = text
		
		if (self.compact and text_compact != None):
			args["text"] = text_compact
		
		if (icon):
			args["icon"] = icon
		
		if (use_button):
			args["toggle"] = True
		
		if (disabled):
			self.begin()
			self.layout[-1].enabled = False
		
		if (type(self.get(symbol)) != set):
			self.layout[-1].prop(self.obj, symbol, **args)
		else:
			if (use_tabs):
				self.layout[-1].props_enum(self.obj, symbol, **args)
			else:
				self.layout[-1].props_enum(self.obj, symbol, **args)
		
		if (disabled):
			self.end()
		
		return self.get(symbol)
	
	def op(self, opname):
		self.layout[-1].operator(opname)
		
		return self
	
	def warn(self, message):
		self.region("ERROR", message, new = False)
		self.end()

class ExportHelper2:
	"""
	Extended from blender's default ExportHelper to fix some bugs.
	"""
	
	filepath: bpy.props.StringProperty(
		name = "File Path",
		description = "Filepath used for exporting the file",
		maxlen = 1024,
		subtype = 'FILE_PATH',
	)
	
	check_existing: bpy.props.BoolProperty(
		name = "Check Existing",
		description = "Check and warn on overwriting existing files",
		default = True,
		options = {'HIDDEN'},
	)
	
	# subclasses can override with decorator
	# True == use ext, False == no ext, None == do nothing.
	check_extension = True
	
	def invoke(self, context, _event):
		if not self.filepath:
			blend_filepath = context.blend_data.filepath
			if not blend_filepath:
				blend_filepath = "untitled"
			else:
				blend_filepath = os.path.splitext(blend_filepath)[0]
			
			self.filepath = blend_filepath + self.filename_ext
		
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	
	def check(self, _context):
		"""
		Custom version of filepath check that fixes issues with two dots in names
		"""
		
		change_ext = False
		
		if self.check_extension is not None and self.check_extension:
			if not self.filepath.endswith(self.filename_ext):
				self.filepath += self.filename_ext
				change_ext = True
		
		return change_ext

def find_assets_paths(*, search_default = True, search_apk = True):
	"""
	Detect all valid assets paths and return them as a list
	"""
	
	paths = []
	
	# Search for the default (that is, manually picked) path
	override = bpy.context.preferences.addons["shatter"].preferences.default_assets_path
	
	if (search_default and override and ospath.exists(override)):
		paths.append(override)
	
	# Find assets paths from open APKs in APK Editor Studio
	if (search_apk):
		try:
			# Get the search path
			search_path = tempfile.gettempdir() + "/apk-editor-studio/apk"
			
			# Enumerate files
			dirs = os.listdir(search_path)
			
			for d in dirs:
				cand = str(os.path.abspath(search_path + "/" + d + "/assets/templates.xml.mp3"))
				
				if ospath.exists(cand):
					paths.append(str(pathlib.Path(cand).parent))
					break
		except FileNotFoundError:
			pass
	
	return paths

def find_apk(*, allow_override = True):
	"""
	Find the path to an APK
	
	DEPRECATED It's better to have more than one path that people can
	dynamically pick between
	"""
	
	result = find_assets_paths(search_default = allow_override)
	
	if (result):
		return result[0]
	else:
		return ""

def prefs():
	"""
	Get a reference to the addon preferences
	"""
	
	return bpy.context.preferences.addons["shatter"].preferences

def add_box(pos, size):
	"""
	Add a box to the scene and return reference to it
	
	See: https://blender.stackexchange.com/questions/2285/how-to-get-reference-to-objects-added-by-an-operator
	"""
	
	bpy.ops.mesh.primitive_cube_add(
		size = 1.0,
		location = (pos[0], pos[1], pos[2]),
		scale = (size[0] * 2, size[1] * 2, size[2] * 2)
	)
	
	return bpy.context.active_object

def add_empty():
	"""
	Add an empty object and return a reference to it
	"""
	
	o = bpy.data.objects.new("empty", None)
	
	bpy.context.scene.collection.objects.link(o)
	
	o.empty_display_size = 1
	o.empty_display_type = "PLAIN_AXES"
	
	set_active(o)
	
	return o

def set_active(obj):
	"""
	Set an object as the only active, selected object
	"""
	
	# Unselect all objects
	for o in bpy.data.objects:
		o.select_set(False)
	
	# Set selected
	obj.select_set(True)
	
	# Set active
	bpy.context.view_layer.objects.active = obj

def show_message(title = "Info", message = "", icon = "INFO"):
	"""
	Show a message as a popup
	"""
	
	def draw(self, context):
		self.layout.label(text = message)
	
	bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

def ui_region(layout, label = None, icon = None):
	"""
	Get the next UI region, with respect to compact mode
	"""
	
	sub = layout
	
	if (not bpy.context.preferences.addons["shatter"].preferences.compact_ui):
		sub = layout.box()
		sub.label(text = label, icon = icon)
	
	return sub

