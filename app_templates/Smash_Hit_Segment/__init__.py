"""
Shatter app template
"""

import traceback
import bpy
from bpy.app.handlers import persistent
import addon_utils

def enable_shatter():
	if (addon_utils.check("shatter")):
		print("Enable shatter addon for use in app template")
		addon_utils.enable("shatter", default_set = True, persistent = True)
	else:
		print("Shatter is already enabled")

def remove_unneeded_viewport_options():
	pass

load_handler_functions = (
	remove_unneeded_viewport_options,
	enable_shatter,
)

@persistent
def load_handler(_):
	for f in load_handler_functions:
		try:
			f()
		except Exception as e:
			print(f"*** Exception while running {f.__name__}() in app template ***")
			print(traceback.format_exc())

def register():
	bpy.app.handlers.load_factory_startup_post.append(load_handler)

def unregister():
	bpy.app.handlers.load_factory_startup_post.remove(load_handler)
