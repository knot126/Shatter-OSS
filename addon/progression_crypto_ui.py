import bpy
import bpy_extras.io_utils
import os
from . import butil
from . import progression_crypto

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

class ProgressionCryptoEncrypt(bpy_extras.io_utils.ImportHelper, Operator):
	"""Encrypts a progression.xml (save file) from any Mediocre game, filled with the key for Smash Hit by default"""
	
	bl_idname = "shatter.progression_crypto_encrypt"
	bl_label = "Encrypt user data file"
	
	filename_ext = ".xml"
	
	key: StringProperty(
		name = "Key",
		description = "The key/password to encrypt with",
		default = "5m45hh1t41ght",
	)
	
	def execute(self, context):
		if (len(self.key) > 0):
			progression_crypto.crypt_file(self.filepath, self.key, False)
		
		self.report({"INFO"}, f"The file has been encrypted.")
		
		return {"FINISHED"}

class ProgressionCryptoDecrypt(bpy_extras.io_utils.ImportHelper, Operator):
	"""Encrypts a progression.xml (save file) from any Mediocre game, filled with the key for Smash Hit by default"""
	
	bl_idname = "shatter.progression_crypto_decrypt"
	bl_label = "Decrypt user data file"
	
	filename_ext = ".xml"
	
	key: StringProperty(
		name = "Key",
		description = "The key/password to decrypt with",
		default = "5m45hh1t41ght",
	)
	
	def execute(self, context):
		if (len(self.key) > 0):
			progression_crypto.crypt_file(self.filepath, self.key, True)
		
		self.report({"INFO"}, f"The file has been decrypted.")
		
		return {"FINISHED"}
