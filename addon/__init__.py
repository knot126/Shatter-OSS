"""
The Shatter Smash Hit Level Editor Addon for Blender

====================================================

This is the main file of Shatter. It configures imports, loads the main module
and calls the register and ungregister functions.
"""

# bl_info = {
# 	"name": "Shatter OSS",
# 	"description": "Blender-based tools for editing, saving and loading Smash Hit segments.",
# 	"author": "Shatter Team",
# 	"version": (1, 0, 6),
# 	"blender": (3, 0, 0),
# 	"location": "File > Import/Export and 3D View > Tools",
# 	"warning": "",
# 	"doc_url": "https://github.com/Shatter-Team/Shatter/wiki",
# 	"tracker_url": "https://github.com/Shatter-Team/Shatter/issues",
# 	"category": "Development",
# }

import main

register = main.register
unregister = main.unregister
