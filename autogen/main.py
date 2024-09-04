"""
Main file for Smash Hit Autogen
"""

import bpy
from . import autogen_ui
from bpy.utils import register_class, unregister_class
from bpy.props import PointerProperty

classes = (
	autogen_ui.AutogenProperties,
	autogen_ui.AutogenPanel,
	autogen_ui.RunRandomiseSeedAction,
	autogen_ui.RunAutogenAction,
)

def register():
	for c in classes:
		register_class(c)
	
	bpy.types.Scene.shatter_autogen = PointerProperty(type=autogen_ui.AutogenProperties)

def unregister():
	del bpy.types.Scene.shatter_autogen
	
	for c in reversed(classes):
		unregister_class(c)
