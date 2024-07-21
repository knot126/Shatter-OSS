"""
Common constants and tools between blender-specific modules
"""

import pathlib
import os
import os.path
import shutil

"""
Addon info
"""

# Get the path to the Shatter install
SHATTER_PATH = str(pathlib.Path(__file__).parent) + "/"

# Find the addons path
BLENDER_ADDONS_PATH = str(pathlib.Path(__file__).parent.parent) + "/"

# TODO: Not having BL_INFO breaks a lot of stuff until we can fix shit.
BL_INFO = {
	"version": (0, 0, 0),
}

"""
Max length for property strings
"""
MAX_STRING_LENGTH = 512

"""
Blender Tools configuration directory

TODO Replace this with Extension user data
"""
HOME_FOLDER = str(pathlib.Path.home())
TOOLS_HOME_FOLDER = (os.environ["APPDATA"] + "/Shatter Team/Shatter") if "APPDATA" in os.environ else (HOME_FOLDER + "/.shatter")
TOOLS_HOME_FOLDER_OLD = HOME_FOLDER + "/Shatter"

# Move old home folder to new location
if (os.path.exists(TOOLS_HOME_FOLDER_OLD) and not os.path.exists(TOOLS_HOME_FOLDER)):
	print("Moving old shatter homedir to new location...")
	# HACK Yes the joins and splits are hacks but I dont care and they work.
	os.makedirs("/".join(TOOLS_HOME_FOLDER.split("/")[:-1]), exist_ok = True)
	shutil.move(TOOLS_HOME_FOLDER_OLD, TOOLS_HOME_FOLDER)

# Create shatter folder if it does not exist
os.makedirs(TOOLS_HOME_FOLDER, exist_ok = True)
