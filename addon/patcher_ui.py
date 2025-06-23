import bpy
import bpy_extras.io_utils
import os
from . import butil
from . import patcher

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

class PatchLibsmashhit(bpy_extras.io_utils.ImportHelper, Operator):
	"""Patches libsmashhit.so, allowing you to make various tweaks to the gameplay and fix problems or add features. This will not work on all versions and architectures, please refer to the wiki for more information"""
	
	bl_idname = "shatter.patch_libsmashhit"
	bl_label = "Patch libsmashhit.so"
	
	filename_ext = ".so"
	
	do_premium: BoolProperty(
		name = "Force enable premium",
		description = "Forces premium to always be enabled",
		default = False,
	)
	
	do_encryption: BoolProperty(
		name = "Disable save encryption",
		description = "Disable save file encryption",
		default = False,
	)
	
	do_lualib: BoolProperty(
		name = "Reenable io, os, package modules",
		description = "Reenables the io, os and package modules",
		default = False,
	)
	
	do_offline: BoolProperty(
		name = "Remove tracking and banners",
		description = "Nops out the HttpThread::checkBanners and HttpThread::reportStats functions. NOTE: This only applies for PRE-COFFEE STAIN tracking and does not fully remove tracking from 1.5.x and later",
		default = False,
	)
	
	do_noenshittification: BoolProperty(
		name = "Denshittify",
		description = "Disable or remove consumer unfriendly features, like tracking and ads",
		default = False,
	)
	
	do_balls: BoolProperty(
		name = "Change starting ball count",
		description = "Change the number of balls the player has at the beginning of the game",
		default = False,
	)
	
	balls: IntProperty(
		name = "Balls",
		description = "",
		default = 25,
	)
	
	do_savekey: BoolProperty(
		name = "Change save key",
		description = "Change the encryption key used with save files. Make you you've not also disabled them",
		default = False,
	)
	
	savekey: StringProperty(
		name = "Key",
		description = "",
		default = "",
	)
	
	do_fov: BoolProperty(
		name = "Change FoV",
		description = "Change the feild of view for all cameras in smash hit",
		default = False,
	)
	
	fov: FloatProperty(
		name = "Angle (degrees)",
		description = "",
		default = 60.0,
	)
	
	do_dropballs: BoolProperty(
		name = "Change dropped balls",
		description = "Allows you to change how many balls are dropped when the player is hit with an obstacle. Please remember to use this wisely and feel free to make any joke you want about the name of this tickbox OwO",
		default = False,
	)
	
	dropballs: IntProperty(
		name = "Balls",
		description = "",
		default = 10,
	)
	
	do_roomtime: BoolProperty(
		name = "Change room time",
		description = "Change the amount of time spent in each room, in seconds",
		default = False,
	)
	
	roomtime: FloatProperty(
		name = "Time (seconds)",
		description = "",
		default = 32.0,
	)
	
	do_trainingballs: BoolProperty(
		name = "Unlimit training balls",
		description = "Remove the limit of 500 balls in training mode",
		default = False,
	)
	
	do_mglength: BoolProperty(
		name = "Respect mgLength in mutliplayer",
		description = "Normally all rooms in mutliplayer have distance 200, this unlocks that and uses the given mgLength-given value instead",
		default = False,
	)
	
	do_vertical: BoolProperty(
		name = "Allow portrait mode",
		description = "Allows running the game in vertical-tall resolutions like the Shorts mod",
		default = False,
	)
	
	do_noclip: BoolProperty(
		name = "Enable no clip",
		description = "Allows the player to avoid getting hit by obstacles",
		default = False,
	)
	
	do_powerupsfx: BoolProperty(
		name = "Disable powerup audio effects",
		description = "Disables the audio effects when activating a powerup",
		default = False,
	)
	
	do_timestep: BoolProperty(
		name = "Change target frame rate",
		description = "Updates the maximum framerate Smash Hit is allowed to run at and adjusts the physics time step to compensate. A side effect of the way this patch works will lead to slow-motion-like gameplay on devices which update their screen at a rate less than the target framerate. For example, Smash Hit usually targets 60 FPS, and runs normally on 60 FPS devices, but setting it to 120 FPS here will allow you to play the game at 120 FPS on a 120 Hz device, though the physics will be strange on a 60 Hz device",
		default = False,
	)
	
	timestep: FloatProperty(
		name = "Frame rate",
		description = "",
		default = 60.0,
	)
	
	do_timestep: BoolProperty(
		name = "Change target frame rate",
		description = "Updates the maximum framerate Smash Hit is allowed to run at and adjusts the physics time step to compensate. A side effect of the way this patch works will lead to slow-motion-like gameplay on devices which update their screen at a rate less than the target framerate. For example, Smash Hit usually targets 60 FPS, and runs normally on 60 FPS devices, but setting it to 120 FPS here will allow you to play the game at 120 FPS on a 120 Hz device, though the physics will be strange on a 60 Hz device",
		default = False,
	)
	
	do_nowidewide: BoolProperty(
		name = "Support ultra-wide screens",
		description = "Disables Smash Hit's limits on ultra-wide (> 2:1) screens",
		default = False,
	)
	
	checkpoints: IntProperty(
		name = "Checkpoints",
		description = "",
		default = 13,
		min = 3,
		max = 1182,
	)
	
	do_checkpoints: BoolProperty(
		name = "Set checkpoint count",
		description = "Set the number of checkpoints that appear in-game and are saved",
		default = False,
	)
	
	do_fillbufferfix: BoolProperty(
		name = "Fix crash while upading audio buffers",
		description = "This applies a workaround to a crash that sometimes occurs in QiAudioChannel::fillBuffer() while trying to process non-streaming, mono channel audio with the APK's target SDK set to >= 31",
		default = False,
	)
	
	all_patches = [
		"premium",
		"encryption",
		"lualib",
		"offline",
		"noenshittification",
		"balls",
		"savekey",
		"fov",
		"dropballs",
		"roomtime",
		"trainingballs",
		"mglength",
		"vertical",
		"noclip",
		"powerupsfx",
		"timestep",
		"nowidewide",
		"checkpoints",
		"fillbufferfix",
	]
	
	def drawItem(self, ui, name, pl = []):
		# ui.prop(f"do_{name}", disabled = (name not in pl and pl))
		ui.prop(f"do_{name}", disabled = (name not in pl) and (not ui.get(f"do_{name}")))
		
		if (hasattr(self, name) and getattr(self, f"do_{name}")):
			ui.prop(name)
	
	def getFileInfo(self):
		# Create previous filepath and cached patches, they might not exist
		if (not hasattr(self, "prev_filepath")):
			self.prev_filepath = ""
		
		if (not hasattr(self, "cached_patches")):
			self.cached_patches = None
		
		# Get valid patches list, if cache is outdated
		try:
			if (self.prev_filepath != self.filepath):
				self.cached_patches = patcher.valid_patches(self.filepath)
		except:
			self.cached_patches = None
		
		# Save previous filepath
		self.prev_filepath = self.filepath
		
		return self.cached_patches
	
	def draw(self, context):
		ui = butil.UIDrawingHelper(context, self.layout, self)
		
		fi = self.getFileInfo()
		pl = [] if not fi else fi[2]
		
		if fi:
			ui.label(f"Version: {fi[1]}")
			ui.label(f"Arch: {fi[0]}")
		else:
			ui.label("Unknown version")
		
		for item in self.all_patches:
			self.drawItem(ui, item, pl)
	
	def execute(self, context):
		patches = {}
		
		if (self.cached_patches and "antitamper" in self.cached_patches[2]):
			patches["antitamper"] = []
		
		# More dynamic version so i dont have to keep adding 69 fucking things
		# to add a new patch :p
		for entry in self.all_patches:
			if entry != "antitamper" and getattr(self, f"do_{entry}"):
				patches[entry] = [getattr(self, entry)] if hasattr(self, entry) else []
		
		result = patcher.patch_binary(self.filepath, patches)
		
		if (result == NotImplemented):
			butil.show_message("Error trying to patch", "It seems like the version or architecture of libsmashhit.so that you are trying to patch isn't yet supported by this tool.")
		elif (result):
			butil.show_message("Error while applying patches", "Some errors occured while patching:\n" + ("\n".join(result)))
		else:
			self.report({"INFO"}, "The patches have successfully been applied.")
		
		return {"FINISHED"}
