#!/usr/bin/env python3
"""
Libsmashhit.so tweak tool/file patcher

This uses a very similar archiecture as the classic patch.py or tweak tool but
doesn't provide a GUI for it and is a bit cleaner, though not by much.

To add a patch, create a function that accepts (patcher, params) and then add it
to the right patch table.
"""

import struct

class Patcher:
	"""
	A thing we can use to patch a file, in this case libsmashhit.so
	"""
	
	def __init__(self, path):
		"""
		Initialise the patching utility
		"""
		
		if path:
			self.f = open(path, "rb+")
		else:
			self.captured = {}
	
	def __del__(self):
		"""
		When we are done with the file
		"""
		
		if (hasattr(self, "f")):
			self.f.close()
	
	def patch(self, location, data):
		"""
		Write some data to the file at the given location
		"""
		
		if (hasattr(self, "captured")):
			self.captured[location] = data
		else:
			self.f.seek(location, 0)
			self.f.write(data)
	
	def peek(self, location, amount):
		"""
		Peek a certian amount of data from a specific location
		"""
		
		self.f.seek(location, 0)
		return self.f.read(amount)
	
	def get_capture(self):
		return self.captured.copy()

AARCH64_NOP = b"\x1f\x20\x03\xd5"
AARCH64_RET = b"\xc0\x03\x5f\xd6"

AARCH32_NOP = b"\x00\xf0\x20\xe3"
AARCH32_RET = b"\x1e\xff\x2f\xe1"

def _patch_const_mov_instruction_arm64(old, value):
	"""
	Patch something like mov r0, #0x10 to mov r0, #value
	"""
	
	mask = 0b11100000111111110001111100000000
	
	old = old & (~mask)
	
	last = (value & 0b111) << 29
	first = ((value >> 3) & 0b11111111) << 16
	new = last | first
	
	return (old | new)

def _patch_const_subs_instruction_arm64(old, value):
	"""
	Patch something like subs r0, r1, #0x10 to subs r0, r1, #value
	"""
	
	mask = 0b00000000111111000011111100000000
	
	old = old & (~mask)
	
	last = (value & 0b111111) << 18
	first = ((value >> 6) & 0b111111) << 8
	new = last | first
	
	return (old | new)

def _patch_savekey(patcher, params, location, maxlen):
	"""
	Generic function to handle patching of the encryption key. Location is the
	offset to the key and maxlen is the max possible length of the key before it
	would overwrite another used string.
	"""
	
	value = params[0] if len(params) > 0 else ""
	msg = []
	
	if (not value):
		msg.append("The encryption key will be set to Smash Hit's default key, 5m45hh1t41ght, since you did not set one.")
		value = "5m45hh1t41ght"
	
	key = value.encode('utf-8')
	
	if (len(key) >= maxlen):
		msg.append(f"Your encryption key is longer than {maxlen-1} bytes, so it has been truncated.")
		key = key[:maxlen-1]
	
	patcher.patch(location, key + (b"\x00" * (maxlen - len(key))))
	
	if (msg):
		return msg

# ---------------------------------------------

def _patch_v100_arm32_premium(patcher, params):
	"""
	Patch premium for v1.0.0. Note that this version has no anti-tamper...
	Also, there isn't the easy, "one instruction premium hack" like later
	versions, so I just patch out whenever the game checks for premium...
	"""
	
	patcher.patch(0x79c04, b"\x07\x00\x00\xea") # remove premium from cond
	patcher.patch(0x79844, b"\x7a\x00\x00\xea") # remove premium from cond
	patcher.patch(0x77cc0, b"\x00\xf0\x20\xe3") # nop out early exit if no premium
	patcher.patch(0x5d950, b"\x01\x30\xa0\xe3") # just make the compare true == false :)
	patcher.patch(0x785dc, b"\x6f\x00\x00\xea") # remove premium dependent cond
	patcher.patch(0x79ea0, b"\x1e\xff\x2f\xe1") # nop out Player::setPremium

def _patch_v100_arm32_encryption(patcher, params):
	"""
	Make Player::encrypt() and Player::decrypt() nops
	"""
	
	patcher.patch(0x77d94, b"\x1e\xff\x2f\xe1")
	patcher.patch(0x77ce8, b"\x1e\xff\x2f\xe1")

def _patch_v100_arm32_offline(patcher, params):
	"""
	Make HttpThread::run() a nop
	"""
	
	patcher.patch(0x66858, b"\x1e\xff\x2f\xe1")

def _patch_v100_arm32_savekey(patcher, params):
	"""
	Patch save key in 1.0.0
	"""
	
	return _patch_savekey(patcher, params, 0x1c02e4, 16)

_LIBSMASHHIT_V100_ARM32_PATCH_TABLE = {
	"premium": _patch_v100_arm32_premium,
	"encryption": _patch_v100_arm32_encryption,
	"offline": _patch_v100_arm32_offline,
	"savekey": _patch_v100_arm32_savekey,
}

def _patch_v142_v143_arm64_antitamper(patcher, params):
	"""
	Patch antitamper (this is generally required)
	"""
	
	patcher.patch(0x47130, AARCH64_NOP)
	patcher.patch(0x474b8, b"\x3e\xfe\xff\x17")
	patcher.patch(0x47464, b"\x3a\x00\x00\x14")
	patcher.patch(0x47744, b"\x0a\x00\x00\x14")
	patcher.patch(0x4779c, AARCH64_NOP)
	patcher.patch(0x475b4, b"\xff\xfd\xff\x17")
	patcher.patch(0x46360, b"\x13\x00\x00\x14")

def _patch_v142_v143_arm64_premium(patcher, params):
	"""
	Patch permium
	"""
	
	patcher.patch(0x5ace0, AARCH64_NOP)
	patcher.patch(0x598cc, b"\x14\x00\x00\x14")
	patcher.patch(0x59720, b"\xa0\xc2\x22\x39")
	patcher.patch(0x58da8, b"\x36\x00\x00\x14")
	patcher.patch(0x57864, b"\xbc\x00\x00\x14")
	patcher.patch(0x566ec, b"\x04\x00\x00\x14")

def _patch_v142_v143_arm64_lualib(patcher, params):
	"""
	Partially reenable lua's package, io and os modules in scripts
	"""
	
	patcher.patch(0xa71b8, b"\xe0\x03\x13\xaa") # Preserve param_1
	patcher.patch(0xa71c8, b"\xb8\x0e\x00\x14") # Chain to luaopen_package
	patcher.patch(0xaaef4, b"\xe0\x03\x13\xaa") # Preserve param_1
	patcher.patch(0xaaf08, b"\xb1\xf0\xff\x17") # Chain to luaopen_io
	patcher.patch(0xa748c, b"\xe0\x03\x13\xaa") # Preserve param_1
	patcher.patch(0xa74a0, b"\xd1\xfe\xff\x17") # Chain to luaopen_os
	patcher.patch(0xa7004, b"\xa0\x00\x80\x52") # Set return to 5 (2 + 1 + 1 + 1 = 5)
	patcher.patch(0xa7010, AARCH64_RET) # Make sure last is return (not really needed)

def _patch_v142_v143_arm64_encryption(patcher, params):
	"""
	Nop out the save file encryption functions
	"""
	
	patcher.patch(0x567e8, AARCH64_RET)
	patcher.patch(0x5672c, AARCH64_RET)

def _patch_v142_v143_arm64_offline(patcher, params):
	"""
	Make the checkBanners and reportStats nop functions
	"""
	
	# Nop checkBanners
	patcher.patch(0x1ca720, AARCH64_RET)
	
	# Nop reportStats
	patcher.patch(0x1c9ef4, AARCH64_RET)

def _patch_v142_v143_arm64_balls(patcher, params):
	"""
	Patch the number of starting balls
	"""
	
	value = params[0] if len(params) > 0 else None
	
	if (not value):
		return ["You didn't put in a value for how many balls you want to start with. Balls won't be patched!"]
	
	value = int(value)
	
	# Somehow, this works.
	d = struct.unpack(">I", patcher.peek(0x57cf4, 4))[0]
	patcher.patch(0x57cf4, struct.pack(">I", _patch_const_mov_instruction_arm64(d, value)))
	patcher.patch(0x57ff8, struct.pack("<I", value))

def _patch_v142_v143_arm64_savekey(patcher, params):
	"""
	Change the encryption key used to obfuscate savegames
	"""
	
	return _patch_savekey(patcher, params, 0x1f3ca8, 24)

def _patch_v142_v143_arm64_vertical(patcher, params):
	"""
	Patch to allow running in vertical resolutions
	"""
	
	patcher.patch(0x46828, b"\x47\x00\x00\x14") # Patch an if (gWidth < gHeight)
	patcher.patch(0x4693c, b"\x71\x00\x00\x14") # Another if ...
	patcher.patch(0x46a48, AARCH64_NOP)

def _patch_v142_v143_arm64_fov(patcher, params):
	"""
	Set the feild of view for all cameras in the game
	"""
	
	value = params[0] if len(params) > 0 else None
	
	if (not value):
		return ["You didn't put in a value for the FoV you want. FoV won't be patched!"]
	
	patcher.patch(0x1c945c, struct.pack("<f", float(value)))

def _patch_v142_v143_arm64_dropballs(patcher, params):
	"""
	Set the number of balls to drop when a obstacle is hit.
	
	I'm unsure if Yorshex or OL Epic would like this more...
	"""
	
	value = params[0] if len(params) > 0 else None
	
	if (not value):
		return ["You didn't put in a value for how many balls you want to drop when you hit on something. Dropping balls won't be patched!"]
	
	value = int(value)
	
	# Patch the number of balls to subtract from the score
	d = struct.unpack(">I", patcher.peek(0x715f0, 4))[0]
	patcher.patch(0x715f0, struct.pack(">I", _patch_const_subs_instruction_arm64(d, value)))
	
	# Patch the number of balls to drop
	d = struct.unpack(">I", patcher.peek(0x71624, 4))[0]
	patcher.patch(0x71624, struct.pack(">I", _patch_const_mov_instruction_arm64(d, value)))
	
	# This changes from "cmp w23,#0xa" to "cmp w23,w1" so that we don't
	# need to make a specific patch for the comparision.
	patcher.patch(0x7162c, b"\xff\x02\x01\x6b")

def _patch_v142_v143_arm64_roomtime(patcher, params):
	value = float(params[0]) if len(params) > 0 else None
	
	if (not value):
		return ["You didn't put in a room length in seconds so it will be set to default."]
		value = 32.0
	
	# Smash Hit normalises the value to the range [0.0, 1.0] so we need to take the inverse
	patcher.patch(0x73f80, struct.pack("<f", 1 / value))

def _patch_v142_v143_arm64_trainingballs(patcher, params):
	"""
	Remove ball count limit in training mode
	"""
	
	patcher.patch(0x6ba5c, b"\x06\x00\x00\x14")

def _patch_v142_v143_arm64_mglength(patcher, params):
	"""
	Make mgLength count properly in multiplayer mode
	"""
	
	patcher.patch(0x6b6d4, AARCH64_NOP)

def _patch_v142_v143_arm64_noclip(patcher, params):
	"""
	Disable collision detection for the player
	"""
	
	patcher.patch(0x71574, AARCH64_RET)

def _patch_v142_v143_arm64_powerupsfx(patcher, params):
	"""
	Remove the powerup sfx effect
	"""
	
	patcher.patch(0x161384, b"\x90\x00\x00\x14")

def _patch_v142_v143_arm64_timestep(patcher, params):
	"""
	Change the time step statically, allowing for higher framerates on N-hz
	devices but making it slower on others.
	"""
	
	hz = float(params[0]) if len(params) > 0 else 60.0
	time_step = 1.0 / hz
	
	# Game::Game() where Game.time_step is init
	patcher.patch(0x1e7584, struct.pack("<f", time_step))
	
	# Game::update() also sets it
	patcher.patch(0x1e3b1c, struct.pack("<f", time_step))
	
	# Update the string, it doesnt seem to be used anywhere in the binary
	# but could be used in scripts.
	patcher.patch(0x213ee0, str(time_step).encode("utf-8")[:10] + b"\x00")
	
	# android_main() where the main loop usleep()s for any remaining time
	patcher.patch(0x4791c, struct.pack("<f", time_step))

def encode_arm64_movz(sf, hw, imm16, Rd):
	# sf = 0 is 32 and 1 is 64-bit, hw = shift/16
	return struct.pack("<I", (sf << 31) | (0b10100101 << 23) | ((hw >> 4) << 21) | (imm16 << 5) | (Rd))

def encode_arm64_cmp(sf, sh, imm12, Rn):
	# sf is 32/64-bit, sh is shift, imm12 is the immediate
	return struct.pack("<I", (sf << 31) | (0b11100010 << 23) | (imm12 << 10) | (Rn << 5) | 0b11111)

def encode_arm64_ldr(x, imm12, Rn, Rt):
	# x is 32/64-bit, imm12 is offset, Rn is base register and Rt is dest register
	return struct.pack("<I", (1 << 31) | (x << 30) | (0b11100101 << 22) | (((imm12 >> 3) if x else (imm12 >> 2)) << 10) | (Rn << 5) | Rt)

def encode_arm64_str(x, imm12, Rn, Rt):
	return struct.pack("<I", (1 << 31) | (x << 30) | (0b11100100 << 22) | (((imm12 >> 3) if x else (imm12 >> 2)) << 10) | (Rn << 5) | Rt)

def encode_arm64_add(sf, sh, imm12, Rn, Rd):
	return struct.pack("<I", (sf << 31) | (0b00100010 << 23) | (sh << 22) | (imm12 << 10) | (Rn << 5) | Rd)

def _patch_v142_v143_arm64_use_calloc(patcher, params):
	"""
	Really slick hack to use calloc() instead of malloc() for a few structures
	and fixing uninitalised memory with the CP patch.
	"""
	
	# x0 is size for both QiAlloc and QiStdCAlloc (effectively)
	patcher.patch(0x15a9fc, b"\x21\x00\x80\xd2") # mov x1,#0x1
	patcher.patch(0x15aa00, b"\x97\xff\xff\x17") # b QiStdCAlloc

def _patch_v142_v143_arm64_checkpoints(patcher, params):
	"""
	Patch for having more than 13 checkpoints (yes, there are 13, the Wikipedia
	article is wrong and sadly it will stay that way). Due to restrictions of
	the ARM architecture, the max amount of possible checkpoints is 1182.
	"""
	
	value = int(params[0]) if len(params) > 0 else 13
	adjustArrays = value > 13
	
	_patch_v142_v143_arm64_use_calloc(patcher, params)
	
	# This seems to be the number of rendered segments
	patcher.patch(0x799e8, encode_arm64_movz(0, 0, value, 7))
	
	# Don't exactly know what this is for, but I think it's pointers to the meshes
	# by default it's 0x98 large (0x98 / 0x8 = 19) so it seems like there are 19 entries
	# by default
	# This part also limits the max number of checkpoints to at most 8515
	patcher.patch(0x78700, encode_arm64_movz(1, 0, (value + 6) * 8, 0))
	
	# This is in an unused function but I will patch it anyways.
	patcher.patch(0x58010, encode_arm64_movz(0, 0, value, 0))
	
	# Get the highscores even if the checkpoint is above cp12
	patcher.patch(0x57c18, AARCH64_NOP)
	patcher.patch(0x57c44, AARCH64_NOP)
	
	# In Player::reportCheckpoint(int index) we need to report regardless...
	patcher.patch(0x57bb0, AARCH64_NOP)
	
	# Nop out the special cases for zen/versus/coop meshes
	patcher.patch(0x7865c, AARCH64_NOP)
	patcher.patch(0x78664, AARCH64_NOP)
	patcher.patch(0x7866c, AARCH64_NOP)
	
	# Force loading progression data if index > 13
	patcher.patch(0x574d4, AARCH64_NOP)
	
	# Force loading level if the level index isn't zero
	patcher.patch(0x57c7c, b"\x20\x00\x00\x51")
	patcher.patch(0x57c84, b"\x1f\x00\x00\x71")
	patcher.patch(0x57c88, b"\x40\x03\x00\x54")
	
	# Save progression data up to cp index targetCheckpoints - 1
	patcher.patch(0x57ac4, encode_arm64_cmp(0, 0, value, 24))
	
	# The above probably works and realistically I prefer not making drastic
	# changes to Smash Hit's internal data structures in any case I don't have
	# to.
	if not adjustArrays:
		return
	
	# Allocate more memory in Player object for checkpoint progression data
	# This would limit us to 2629 checkpoints (anything greater breaks mov
	# without hacks)
	patcher.patch(0x1e6d9c, encode_arm64_movz(1, 0, 0x980 + (2 * 3 * 4 * value), 0))
	
	# Offsets that need ldr's adjusted for moved array
	# Some of these give us our limit of 1182 checkpoints, since the imm12 can
	# store at most the value 16380 and we need to do
	# ldr Wn,[x0,#(0x980 + 3 * 4 * ncps)] to access streak in some cases.
	pBallsArray = 0x980
	pOffsetFromBallEntryToStreakEntry = (3 * 4 * value)
	pStreakArray = pBallsArray + pOffsetFromBallEntryToStreakEntry
	
	# Load in Player::save()
	patcher.patch(0x57a7c, encode_arm64_ldr(0, pOffsetFromBallEntryToStreakEntry, 22, 1))
	
	# A thing to get the address of balls in Player::save(QiOutputStream *)
	patcher.patch(0x57868, encode_arm64_add(1, 0, pBallsArray, 22, 2))
	
	# Loads and stores in Player::load(QiInputStream *)
	patcher.patch(0x57580, encode_arm64_ldr(0, pBallsArray, 1, 4))
	patcher.patch(0x57584, encode_arm64_ldr(0, pStreakArray, 1, 0))
	patcher.patch(0x57598, encode_arm64_str(0, pBallsArray, 1, 3))
	patcher.patch(0x5759c, encode_arm64_str(0, pStreakArray, 1, 2))
	
	# Loads and stores in Player::reportCheckpoint(int)
	patcher.patch(0x57bd0, encode_arm64_ldr(0, pBallsArray, 1, 3))
	patcher.patch(0x57bd4, encode_arm64_ldr(0, pStreakArray, 1, 2))
	patcher.patch(0x57be0, encode_arm64_str(0, pBallsArray, 1, 3))
	patcher.patch(0x57bf0, encode_arm64_str(0, pStreakArray, 1, 2))
	
	# Loads in Player::loadCheckpoint(int)
	patcher.patch(0x57cac, encode_arm64_ldr(0, pBallsArray, 1, 0))
	patcher.patch(0x57cb4, encode_arm64_ldr(0, pStreakArray, 1, 0))
	
	# Player::getHighScore(int) which is just fucking cursed assembly tbh
	patcher.patch(0x57c2c, encode_arm64_add(1, 0, (pBallsArray >> 2), 1, 1))
	
	# Player::getHighScoreStreak(int) also sucks just a bit less so
	patcher.patch(0x57c5c, encode_arm64_ldr(0, pStreakArray, 0, 2))

_LIBSMASHHIT_V142_V143_ARM64_PATCH_TABLE = {
	"antitamper": _patch_v142_v143_arm64_antitamper,
	"premium": _patch_v142_v143_arm64_premium,
	"lualib": _patch_v142_v143_arm64_lualib,
	"encryption": _patch_v142_v143_arm64_encryption,
	"offline": _patch_v142_v143_arm64_offline,
	"balls": _patch_v142_v143_arm64_balls,
	"savekey": _patch_v142_v143_arm64_savekey,
	"vertical": _patch_v142_v143_arm64_vertical,
	"fov": _patch_v142_v143_arm64_fov,
	"dropballs": _patch_v142_v143_arm64_dropballs,
	"roomtime": _patch_v142_v143_arm64_roomtime,
	"trainingballs": _patch_v142_v143_arm64_trainingballs,
	"mglength": _patch_v142_v143_arm64_mglength,
	"noclip": _patch_v142_v143_arm64_noclip,
	"powerupsfx": _patch_v142_v143_arm64_powerupsfx,
	"timestep": _patch_v142_v143_arm64_timestep,
	"checkpoints": _patch_v142_v143_arm64_checkpoints,
}

def _patch_v142_v143_arm32_antitamper(patcher, params):
	"""
	Patch the genuine checks for arm32 v142 and v143
	"""
	
	# Skip the non-android_main checksum compare
	patcher.patch(0x353e4, b"\x13\x00\x00\xea")
	
	# Skip sig file loading and compare
	patcher.patch(0x36070, b"\x00\xf0\x20\xe3")
	
	# Skip probabialistic checksum check with chance 1/1000
	patcher.patch(0x3633c, b"\x37\x00\x00\xea")
	
	# Skip the smol one
	patcher.patch(0x36398, b"\xd4\xfe\xff\xea")
	
	# Don't stop main loop when gGenuine == 0
	patcher.patch(0x3649c, b"\x93\xfe\xff\xea")

def _patch_v142_v143_arm32_premium(patcher, params):
	"""
	Really basic patch for premium on arm32, maybe it works fully or not, idk
	"""
	
	# One of my favourite jank hacks of all time, just constantly sets premium
	# to true if it isnt set :P
	# streq  r3,[r0,#this->premium]
	patcher.patch(0x47d9c, b"\xe8\x37\x80\x05")

def _patch_v142_v143_arm32_lualib(patcher, params):
	"""
	Allow loading the os, io and package lua libs. To do this we basically merge
	the fuctions for loading multipule lua libs together. On armv7 this is
	easier since there are instructions for higher level stack operations which
	we change just change.
	"""
	
	# Start with luaopen_base
	# return count = 2
	
	# Need to allocate the registers properly because some functions use many
	# of them
	patcher.patch(0x910cc, b"\xf8\x4f\x2d\xe9")
	
	# Need to change setting return value to setting it back to lua context
	patcher.patch(0x91240, b"\x04\x00\xa0\xe1")
	
	# Jump to the start of the next register function (without stmdb)
	# also return count += 1 for luaopen_io
	patcher.patch(0x91244, b"\x0f\x00\x00\xea")
	
	# Change setting return value to preserving param_1 for next call
	patcher.patch(0x9154c, b"\x04\x00\xa0\xe1")
	
	# Jumping to start of luaopen_package
	# Should also add 1 to total retval at this point (we're at 4)
	patcher.patch(0x91550, b"\xf3\x0c\x00\xea")
	
	# Kick the ass of stmdb here :D
	patcher.patch(0x94928, b"\x00\xf0\x20\xe3")
	
	# Now of course we preserve param_1
	patcher.patch(0x94b80, b"\x04\x00\xa0\xe1")
	
	# Anddd jump to luaopen_os
	# (also our total retval should now be 5)
	patcher.patch(0x94b84, b"\x3a\xf1\xff\xea")
	
	# Now we've got everything and we can edit the retval to be 5 and also
	# change ldmia to load all of the old register values properly. We should
	# also kill the annoying stmdb that appears for some reason to be a nop.
	patcher.patch(0x91080, b"\x00\xf0\x20\xe3") # nop out stmdb
	patcher.patch(0x91090, b"\x05\x00\xa0\xe3") # mov r0,#0x5
	patcher.patch(0x91094, b"\xf8\x8f\xbd\xe8") # ldmia sp!,{r3..r11,pc}

def _patch_v142_v143_arm32_encryption(patcher, params):
	"""
	Disable save encryption
	"""
	
	patcher.patch(0x44e88, b"\x1e\xff\x2f\xe1")
	patcher.patch(0x44dd8, b"\x1e\xff\x2f\xe1")

def _patch_v142_v143_arm32_offline(patcher, params):
	"""
	Make the checkBanners and reportStats nop functions
	"""
	
	# Patch checkBanners
	patcher.patch(0x197bdc, b"\x1e\xff\x2f\xe1")
	
	# Patch reportStats
	patcher.patch(0x197318, b"\x1e\xff\x2f\xe1")

def _patch_v142_v143_arm32_savekey(patcher, params):
	"""
	Patch save file key in 1.4.2/3 32bit
	"""
	
	return _patch_savekey(patcher, params, 0x1c7960, 16)

def encode_arm32_mov(Rd, imm12):
	return struct.pack("<I", (0b1110001110100000 << 16) | (Rd << 12) | (imm12 & 0xfff))

def _patch_v142_v143_arm32_balls(patcher, params):
	amount = int(params[0]) if len(params) > 0 else 25
	
	patcher.patch(0x46504, encode_arm32_mov(2, amount))
	patcher.patch(0x462fc, encode_arm32_mov(2, amount))
	patcher.patch(0x61be0, encode_arm32_mov(12, amount))

def encode_arm32_movt(Rd, imm16):
	return struct.pack("<I", (0b111000110100 << 20) | (((imm16 >> 12) & 0xf) << 16) | (Rd << 12) | (imm16 & 0xfff))

def _patch_v142_v143_arm32_fov(patcher, params):
	fov = float(params[0]) if len(params) > 0 else 60.0
	
	topfov = struct.unpack(">I", struct.pack(">f", fov))[0] >> 16
	
	patcher.patch(0x195da0, encode_arm32_movt(2, topfov))

def _patch_v142_v143_arm32_trainingballs(patcher, params):
	patcher.patch(0x59874, AARCH32_NOP)

def _patch_v142_v143_arm32_mglength(patcher, params):
	# Make the first move unconditional
	patcher.patch(0x5d030, "\x3c\x30\x96\xe5")
	
	# Replace the other two with nops
	patcher.patch(0x5d034, 2 * AARCH32_NOP)

def _patch_v142_v143_arm32_noclip(patcher, params):
	patcher.patch(0x5b8a0, AARCH32_RET)

def _patch_v142_v143_arm32_powerupsfx(patcher, params):
	patcher.patch(0x1301e0, b"\x8a\x00\x00\xea")

_LIBSMASHHIT_V142_V143_ARM32_PATCH_TABLE = {
	"antitamper": _patch_v142_v143_arm32_antitamper,
	"premium": _patch_v142_v143_arm32_premium,
	"lualib": _patch_v142_v143_arm32_lualib,
	"encryption": _patch_v142_v143_arm32_encryption,
	"offline": _patch_v142_v143_arm32_offline,
	"savekey": _patch_v142_v143_arm32_savekey,
	"balls": _patch_v142_v143_arm32_balls,
	"fov": _patch_v142_v143_arm32_fov,
	"trainingballs": _patch_v142_v143_arm32_trainingballs,
	"mglength": _patch_v142_v143_arm32_mglength,
	"noclip": _patch_v142_v143_arm32_noclip,
	"powerupsfx": _patch_v142_v143_arm32_powerupsfx,
}

def _patch_v142_x86_antitamper(patcher, params):
	"""
	Hopefully this is enough, I don't have a device to test on...
	"""
	
	patcher.patch(0x3674b, b"\xe9\x00\x01\x00\x00\x90")
	patcher.patch(0x368e3, b"\xe9\x73\xf7\xff\xff\x90")
	patcher.patch(0x367a5, b"\xe9\xb1\xf8\xff\xff\x90")
	patcher.patch(0x35561, b"\xeb\xed")

def _patch_v142_x86_premium(patcher, params):
	"""
	The hack again..
	"""
	
	patcher.patch(0x4f337, b'\x66\xc6\x84\x21\xe8\x07\x00\x00\x01\x90')

_LIBSMASHHIT_V142_X86_PATCH_TABLE = {
	"antitamper": _patch_v142_x86_antitamper,
	"premium": _patch_v142_x86_premium,
}

def _patch_v152_arm64_premium(patcher, params):
	"""
	Patch premium for the beta version 1.5.2
	"""
	
	# Player::tick()
	# This one doesn't seem to cause issues
	patcher.patch(0x116d10, b"\x08\xb0\x08\xb9")
	
	# load()
	# This one overwrites some seemingly unused stores to zero of local vars
	# WARNING causes problem (game crash)
	# patcher.patch(0x118fdc, b"\x20\x00\x80\x52") # mov w0, #0x1
	# patcher.patch(0x118fe4, b"\x80\xc2\x22\x39") # strb this, [x20, #0x8b0]

def _patch_v152_arm64_encryption(patcher, params):
	"""
	Disable save file encryption
	"""
	
	# Player::decrypt()
	patcher.patch(0x117188, AARCH64_RET)
	
	# Player::encrypt()
	patcher.patch(0x118c9c, AARCH64_RET)

_LIBSMASHHIT_V152_ARM64_PATCH_TABLE = {
	"premium": _patch_v152_arm64_premium,
	"encryption": _patch_v152_arm64_encryption,
}

def _patch_v154_v155_arm64_premium(patcher, params):
	"""
	Patch premium for the beta version 1.5.5 (and *probably* 1.5.4)
	"""
	
	# Player::tick()
	# This one doesn't seem to cause issues
	patcher.patch(0x117e1c, b"\x08\xb0\x08\xb9")

_LIBSMASHHIT_V154_V155_ARM64_PATCH_TABLE = {
	"premium": _patch_v154_v155_arm64_premium,
}

def _patch_v159_arm64_premium(patcher, params):
	"""
	Force always premium patch for v1.5.9
	"""
	
	# The same Player::tick() hack...
	patcher.patch(0x11d90c, b"\x68\xb2\x08\xb9")

def _patch_v159_arm64_noenshittification(patcher, params):
	"""
	Try to remove enshittified things from the game. The new versions are
	probably fucked up beyond any repair but \\o/
	"""
	
	### FIREBASE LOGGING ###
	
	# firebase::crashlytics::Initialize
	patcher.patch(0xf3468, AARCH64_RET) # ret
	
	# firebase::crashlytics::Log
	patcher.patch(0x107d14, AARCH64_RET) # ret
	
	### TRACKING ###
	
	## EASY/BASIC THINGS ##
	# These have their own functions and can be fully patched out
	
	# AdTracker::TrackAdNotAvailable
	patcher.patch(0x123b2c, AARCH64_RET) # ret
	
	# AdTracker::TrackAdWatched
	patcher.patch(0x1239e8, AARCH64_RET) # ret
	
	# AdTracker::TrackButtonClick
	patcher.patch(0x123c74, AARCH64_RET) # ret
	
	# TrackGameStart
	patcher.patch(0x1111fc, AARCH64_RET) # ret
	
	# Level::TrackGateReached
	patcher.patch(0x112028, AARCH64_RET) # ret
	
	## INLINED ##
	# For these we just patch out the call to the logging function
	
	# Game::frame
	patcher.patch(0x10519c, AARCH64_NOP)
	patcher.patch(0x105274, AARCH64_NOP)
	patcher.patch(0x105404, AARCH64_NOP)
	patcher.patch(0x105418, AARCH64_NOP)
	
	# Game::handleCommand
	patcher.patch(0x106d5c, AARCH64_NOP)
	patcher.patch(0x106550, AARCH64_NOP)
	patcher.patch(0x1065c4, AARCH64_NOP)
	patcher.patch(0x1069e4, AARCH64_NOP)
	patcher.patch(0x1067e4, AARCH64_NOP)
	patcher.patch(0x106e1c, AARCH64_NOP)
	
	# Level::update
	patcher.patch(0x113330, AARCH64_NOP)
	patcher.patch(0x1138f8, AARCH64_NOP)
	
	# Level::activatePowerup
	patcher.patch(0x116eb4, AARCH64_NOP)
	
	### ADS ###
	
	# AndroidDevice::ShowAd
	patcher.patch(0xf3080, AARCH64_RET) # ret
	
	# AndroidDevice::GetAdResult
	patcher.patch(0xf30f4, b"\x00\x00\x80\x52") # mov w0,#0x0
	patcher.patch(0xf30f8, AARCH64_RET) # ret
	
	# AndroidDevice::IsAdFinished
	patcher.patch(0xf31b8, b"\x20\x00\x80\x52") # mov w0,#0x1
	patcher.patch(0xf31bc, AARCH64_RET) # ret
	
	# AndroidDevice::IsAdLoaded
	patcher.patch(0xf2fe0, b"\x20\x00\x80\x52") # mov w0,#0x1
	patcher.patch(0xf2fe4, AARCH64_RET) # ret
	
	# AndroidDevice::showPrivacyOptions
	patcher.patch(0xf3258, AARCH64_RET) # ret
	
	# mgIsAdLoaded
	patcher.patch(0x1dd314, b"\x20\x00\x80\x52") # mov w0,#0x1
	
	# Game::handleCommand - patch over possible calls to NULL
	# may not be needed
	patcher.patch(0x106454, b"\x20\x00\x80\x52") # mov w0,#0x1
	patcher.patch(0x1064a0, AARCH64_NOP) # nop
	
	### REMOTE CONFIG ###
	
	# AndroidDevice::GetRemoteConfig
	## TODO returns a pointer to a bool value, how to handle? ##
	
	# AndroidDevice::getRemoteConfigBoolParameter
	patcher.patch(0xf2f74, b"\x00\x00\x80\x52") # mov w0,#0x0
	patcher.patch(0xf2f78, AARCH64_RET) # ret
	
	# mgGetRemoteConfigBoolParameter
	patcher.patch(0x1dd364, b"\x00\x00\x80\x52") # mov w0,#0x0

_LIBSMASHHIT_V159_ARM64_PATCH_TABLE = {
	"premium": _patch_v159_arm64_premium,
	"noenshittification": _patch_v159_arm64_noenshittification,
}

def _patch_v1510_arm64_premium(patcher, params):
	"""
	Force always premium patch for v1.5.9
	"""
	
	# The same Player::tick() hack...
	patcher.patch(0x12a9a4, b"\x68\xc2\x22\x39")

def _patch_v1510_force_out_of_balls_ads_to_show(patcher, params):
	patcher.patch(0x1204dc, AARCH64_NOP)
	patcher.patch(0x1204e0, AARCH64_NOP)
	patcher.patch(0x1204e4, AARCH64_NOP)
	patcher.patch(0x1204ec, AARCH64_NOP)
	patcher.patch(0x1204f0, AARCH64_NOP)

_LIBSMASHHIT_V1510_ARM64_PATCH_TABLE = {
	"premium": _patch_v1510_arm64_premium,
	"forceoutofballsadstoshow": _patch_v1510_force_out_of_balls_ads_to_show,
}

PATCHES_LIST = {
	"arm32": {
		"1.0.0": _LIBSMASHHIT_V100_ARM32_PATCH_TABLE,
		"1.4.2": _LIBSMASHHIT_V142_V143_ARM32_PATCH_TABLE,
		"1.4.3": _LIBSMASHHIT_V142_V143_ARM32_PATCH_TABLE,
	},
	"arm64": {
		"1.4.2": _LIBSMASHHIT_V142_V143_ARM64_PATCH_TABLE,
		"1.4.3": _LIBSMASHHIT_V142_V143_ARM64_PATCH_TABLE,
		"1.5.2": _LIBSMASHHIT_V152_ARM64_PATCH_TABLE,
		"1.5.4": _LIBSMASHHIT_V154_V155_ARM64_PATCH_TABLE,
		"1.5.5": _LIBSMASHHIT_V154_V155_ARM64_PATCH_TABLE,
		"1.5.9": _LIBSMASHHIT_V159_ARM64_PATCH_TABLE,
		"1.5.10": _LIBSMASHHIT_V1510_ARM64_PATCH_TABLE,
	},
	"x86": {
		"1.4.2": _LIBSMASHHIT_V142_X86_PATCH_TABLE,
	},
	"x86_64": {},
}

def determine_version(p):
	"""
	Take a guess at finding the version of libsmashhit.so to use. Returns in
	(arch, version) pair.
	"""
	
	# ARM32 v1.0.0
	cand = p.peek(0x1c0030, 5)
	
	if (cand == b"1.0.0"):
		return ("arm32", "1.0.0")
	
	# ARM64 v1.4.2 and v1.4.3
	cand = p.peek(0x1f38a0, 5)
	
	if (cand == b"1.4.2" or cand == b"1.4.3"):
		return ("arm64", cand.decode("utf-8"))
	
	# ARM32 v1.4.2 and v1.4.3
	cand = p.peek(0x1c7608, 5)
	
	if (cand == b"1.4.2" or cand == b"1.4.3"):
		return ("arm32", cand.decode("utf-8"))
	
	# x86 v1.4.2
	cand = p.peek(0x239cd3, 5)
	
	if (cand == b"1.4.2"):
		return ("x86", "1.4.2")
	
	# ARM64 v1.5.2
	# Still identifies as 1.4.3 in the so for some reason
	cand = p.peek(0x84099, 5)
	
	if (cand == b"1.4.3"):
		return ("arm64", "1.5.2")
	
	# ARM64 v1.5.5 (and probably 1.5.4)
	cand = p.peek(0x81880, 5)
	
	if (cand == b"1.5.4" or cand == b"1.5.5"):
		return ("arm64", cand.decode("utf-8"))
	
	# ARM32 v1.5.6
	cand = p.peek(0x7a74e, 5)
	if (cand == b"1.5.6"):
		return ("arm32", "1.5.6")
	
	# ARM64 v1.5.6
	cand = p.peek(0x84f3f, 5)
	if (cand == b"1.5.6"):
		return ("arm64", "1.5.6")
	
	# ARM32 1.5.7
	cand = p.peek(0x00082224, 5)
	if (cand == b"1.5.7"):
		return ("arm32", "1.5.7")
	
	# ARM64 1.5.7
	cand = p.peek(0x0008D381, 5)
	if (cand == b"1.5.7"):
		return ("arm64", "1.5.7")
	
	# ARM32 1.5.8
	cand = p.peek(0x7c402, 5)
	if (cand == b"1.5.8"):
		return ("arm32", "1.5.8")
	
	# ARM64 1.5.8
	cand = p.peek(0x872ed, 5)
	if (cand == b"1.5.8"):
		return ("arm64", "1.5.8")
	
	# ARM32 1.5.9
	cand = p.peek(0x81248, 5)
	if (cand == b"1.5.9"):
		return ("arm32", "1.5.9")
	
	# ARM64 1.5.9
	cand = p.peek(0x8c347, 5)
	if (cand == b"1.5.9"):
		return ("arm64", "1.5.9")
	
	cand = p.peek(0x8eba8, 6)
	if (cand == b"1.5.10"):
		return ("arm64", "1.5.10")
	
	return NotImplemented

def preform_patches(p, patches, arch, ver):
	"""
	Do the actual patching
	"""
	
	archver_patches = PATCHES_LIST[arch][ver]
	all_errors = []
	
	for patch_type in patches:
		print(f"Patching {patch_type} ...")
		if (patch_type in archver_patches):
			errors = archver_patches[patch_type](p, patches[patch_type])
		else:
			errors = [f"Patch {patch_type} does not exist"]
		
		if (errors):
			print(f"The following errors occured while patching {patch_type}:")
			print("\n".join(errors))
			all_errors += errors
	
	return all_errors

def patch_binary(path, patches):
	"""
	Patch a binary at the given path with the given patches and their parameters
	"""
	
	p = Patcher(path)
	
	# Determine the version of libsmashhit.so that's being patched
	so_type = determine_version(p)
	
	if (so_type == NotImplemented):
		return NotImplemented
	
	arch = so_type[0]
	ver = so_type[1]
	
	print(f"Libsmashhit.so version {ver} on {arch} detected")
	
	# Preform the patches
	all_errors = preform_patches(p, patches, arch, ver)
	
	return all_errors

def export_patches(patches, arch, ver):
	"""
	Create a dict with patch info for the given params
	"""
	
	p = Patcher(None)
	
	all_errors = preform_patches(p, patches, arch, ver)
	
	return (all_errors, p.get_capture())

def valid_patches(path):
	"""
	Get (arch, ver, patches) for a given file
	"""
	
	p = Patcher(path)
	
	# Determine the version of libsmashhit.so that's being patched
	so_type = determine_version(p)
	
	if (so_type == NotImplemented):
		return None
	
	# Get patches
	arch = so_type[0]
	ver = so_type[1]
	archver_patches = PATCHES_LIST[arch][ver] if ver in PATCHES_LIST[arch] else {}
	
	patch_list = []
	
	for p in archver_patches:
		patch_list.append(p)
	
	return (arch, ver, patch_list)

_PL_CACHE = {}

def valid_patches_cached(path):
	"""
	Cached version of valid_patches
	"""
	
	if (path not in _PL_CACHE):
		_PL_CACHE[path] = valid_patches(path)
	
	return _PL_CACHE[path]

def _parse_patch_string(ps):
	"""
	Parse a patch string as if it was given on the cmdline
	"""
	
	if ("=" not in ps):
		return (ps, [])
	
	ps = ps.split("=")
	ps[1] = ps[1].split(",")
	
	return ps

def _main():
	import sys
	
	if (len(sys.argv) < 2):
		print(f"Usage: {sys.argv[0]} <so file> [patch0 patch1=param1,param2 ...]")
		return
	
	if (len(sys.argv) < 3):
		print(f"Please specify at least one patch!")
		return
	
	libpath = sys.argv[1]
	patches = dict([_parse_patch_string(x) for x in sys.argv[2:]])
	
	result = patch_binary(libpath, patches)
	
	if (result == NotImplemented):
		print("Error: Either you specified an invalid patch (most likely) or this version and archiecture combination are not supported by the patch tool!")
	elif (result):
		print("Some patches were not successful")
	else:
		print("Success")

if (__name__ == "__main__"):
	_main()
