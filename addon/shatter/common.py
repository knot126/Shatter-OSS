"""
Common constants and tools between blender-specific modules
"""

import pathlib
import os
import os.path
import shutil

"""
Addon info

HACK Blender only parses the AST for bl_info so we can't just define it here if it's
not already cached, which it isn't for new installs
"""

# Get the path to the Shatter install
SHATTER_PATH = str(pathlib.Path(__file__).parent) + "/"

# Find the addons path
BLENDER_ADDONS_PATH = str(pathlib.Path(__file__).parent.parent) + "/"

# Read main file
BL_INFO = pathlib.Path(SHATTER_PATH + "/__init__.py").read_text()

# Get the stuff
# NOTE Breaks if we ever have { or } in bl_info
BL_INFO = eval(BL_INFO[BL_INFO.index("{"):BL_INFO.index("}") + 1])

"""
Max length for property strings
"""
MAX_STRING_LENGTH = 512

"""
Update info URL
"""
UPDATE_INFO = "https://shatter-team.github.io/Shatter-Meta/update-v2.json"

"""
Bad user info url
"""
BAD_USER_INFO = "https://shatter-team.github.io/Shatter-Meta/badusers.json"

"""
Shatter API endpoint
"""
SHATTER_API = "https://smashhitlab.000webhostapp.com/shatter/api.php?action="

"""
Blender Tools configuration directory
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
