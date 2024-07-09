"""
Bundler - create bundles of standalone binaries for multipule platforms

Bundle format:

File -> (little endian) {
	Header header;
	Entry entries[];
	byte rest[];
}

Header -> {
	uint32 bundle_version = 1;
	uint32 entry_count;
	uint32 bundle_name_length;
	char bundle_name[];
}

Entry -> {
	uint32 platform_id;
	uint32 offset; // offset into file of binary data
	uint32 size;
}

This is probably compressed somehow (e.g. lzma)

Also, to make a bundle create a json file of the following format:

{
	"name": "yorshex_meshbake",
	"files": {
		"linux": "path/to.elf",
		"darwin": "with/to.macho",
		"win32": "path/to.exe"
	}
}

Then pass it to the make command
"""

from enum import IntEnum
import sys
import os
import json
import lzma
import subprocess
from pathlib import Path

BUNDLE_INSTALL_DIR = None

class Object:
	pass

class BundleReadError(Exception):
	pass

class BundlePathError(Exception):
	pass

class BundleInstallError(Exception):
	pass

class BundlePlatformError(Exception):
	pass

class Platform(IntEnum):
	Linux = 1
	Windows = 2
	MacOS = 3
	
	@classmethod
	def toString(self, platform):
		if (platform == Platform.Linux):
			return "linux"
		elif (platform == Platform.Windows):
			return "win32"
		elif (platform == Platform.MacOS):
			return "darwin"
		else:
			raise BundlePlatformError(f"Could not recognise platform: '{platform}'")
	
	@classmethod
	def fromString(self, platform):
		if (platform == "linux"):
			return Platform.Linux
		elif (platform == "win32"):
			return Platform.Windows
		elif (platform == "darwin"):
			return Platform.MacOS
		else:
			raise BundlePlatformError(f"Could not recognise platform: '{platform}'")
	
	@classmethod
	def current(self):
		return self.fromString(sys.platform)

class BundleFile:
	"""
	Helper to read bundle files easily
	"""
	
	def __init__(self, path, mode = "r"):
		self.path = path
		
		if (mode == "w"):
			self.f = open(f"{path}.tmp", f"w+b")
		else:
			self.f = lzma.open(path, f"{mode}b")
		
		self.mode = mode
	
	def read(self, nbytes):
		return self.f.read(nbytes)
	
	def write(self, data):
		self.f.write(data)
	
	def readInt(self):
		return int.from_bytes(self.read(4), 'little')
	
	def writeInt(self, data):
		self.write(data.to_bytes(4, 'little'))
	
	def getPos(self):
		return self.f.tell()
	
	def setPos(self, pos):
		return self.f.seek(pos, 0)
	
	def close(self):
		if (self.mode == "w"):
			self.f.seek(0, 2)
			l = self.f.tell()
			self.f.seek(0, 0)
			
			f = lzma.open(self.path, "wb")
			f.write(self.read(l))
			f.close()
			
			self.f.close()
			
			os.remove(f"{self.path}.tmp")
		else:
			self.f.close()

class Bundle:
	def __init__(self, path):
		"""
		Initialise a bundle with the path to the bundle
		"""
		
		self.path = path
		self.name = None
		self.entries = {}
	
	def _read_header(self, bf):
		"""
		Read the bundle file
		"""
		
		bf.setPos(0)
		version = bf.readInt()
		
		if (version != 1):
			raise BundleReadError(f"Invalid bundle version {version}")
		
		ent_count = bf.readInt()
		name_len = bf.readInt()
		
		self.name = bf.read(name_len).decode('latin-1')
		
		for i in range(ent_count):
			ent = Object()
			ent.platform = bf.readInt()
			ent.offset = bf.readInt()
			ent.size = bf.readInt()
			ent.path = self.name if ent.platform != Platform.Windows else f"{self.name}.exe"
			self.entries[ent.platform] = ent
	
	def _extract(self, bf, platform, output):
		"""
		Extract the exec for the given platform
		"""
		
		bf.setPos(self.entries[platform].offset)
		Path(output).write_bytes(bf.read(self.entries[platform].size))
		
		if (platform != Platform.Windows):
			os.chmod(output, 0o755)
	
	def load_json(self, input_path):
		"""
		Load a JSON-format file used for packing bundles
		"""
		
		data = json.loads(Path(input_path).read_text())
		
		self.name = data["name"]
		
		for entry in data["files"]:
			ent = Object()
			ent.platform = Platform.fromString(entry)
			ent.offset = 0
			ent.size = 0
			ent.path = data["files"][entry]
			self.entries[ent.platform] = ent
	
	def write(self):
		"""
		Write bundle file data (only works with load_json)
		"""
		
		bf = BundleFile(self.path, "w")
		bf.writeInt(1)
		bf.writeInt(len(self.entries))
		bf.writeInt(len(self.name))
		bf.write(self.name.encode("latin-1"))
		entstartpos = bf.getPos()
		bf.write(b'\x00' * 12 * len(self.entries)) # We will write these later
		
		# write binary data
		for ent in self.entries.values():
			binary_data = Path(ent.path).read_bytes()
			ent.offset = bf.getPos()
			ent.size = len(binary_data)
			bf.write(binary_data)
		
		# now write the entries
		bf.setPos(entstartpos)
		for ent in self.entries.values():
			bf.writeInt(ent.platform)
			bf.writeInt(ent.offset)
			bf.writeInt(ent.size)
		
		bf.close()
	
	def install(self):
		"""
		Install the correct binary to the given location.
		
		append_format: If the format name (eg .exe, .elf) should be appeneded
		"""
		
		install_dir = get_install_dir()
		
		bf = BundleFile(self.path)
		self._read_header(bf)
		
		if Platform.current() not in self.entries:
			raise BundlePlatformError("This platform is not supported by this bundle.")
		
		self._extract(bf, Platform.current(), f"{install_dir}/{self.entries[Platform.current()].path}")
		
		bf.close()
	
	def installed(self):
		"""
		Check if the given bundle is installed
		"""
		
		install_dir = get_install_dir()
		
		if not self.entries:
			bf = BundleFile(self.path)
			self._read_header(bf)
			bf.close()
		
		if Platform.current() not in self.entries:
			raise BundlePlatformError("This platform is not supported by this bundle.")
		
		return os.path.isfile(f"{install_dir}/{self.entries[Platform.current()].path}")
	
	def run(self, args):
		"""
		Run the binary with the given command line arguments and return the
		return code.
		
		args: a list of arguments to pass to the program
		"""
		
		install_dir = get_install_dir()
		
		if not self.entries:
			bf = BundleFile(self.path)
			self._read_header(bf)
			bf.close()
		
		return subprocess.run([f"{install_dir}/{self.entries[Platform.current()].path}"] + args).returncode

def set_install_dir(path):
	global BUNDLE_INSTALL_DIR
	BUNDLE_INSTALL_DIR = path
	os.makedirs(BUNDLE_INSTALL_DIR, exist_ok = True)

def get_install_dir():
	if (not BUNDLE_INSTALL_DIR):
		raise BundlePathError("Could not find install directory")
	
	return BUNDLE_INSTALL_DIR

def print_help_and_exit():
	print(f"""Knot's bundler - make, install and run multiplatform binary bundles

Usage:
{sys.argv[0]} make <input json> <output bundle>
{sys.argv[0]} install <install dir> <input bundle>
{sys.argv[0]} run <install dir> <input bundle> [args ...]""")
	sys.exit(127)

def main():
	if (len(sys.argv) < 2):
		print_help_and_exit()
	
	cmd = sys.argv[1]
	
	if (cmd == "make"):
		bundle = Bundle(sys.argv[3])
		bundle.load_json(sys.argv[2])
		bundle.write()
	elif (cmd == "install"):
		set_install_dir(sys.argv[2])
		bundle = Bundle(sys.argv[3])
		bundle.install()
	elif (cmd == "run"):
		set_install_dir(sys.argv[2])
		bundle = Bundle(sys.argv[3])
		if (not bundle.installed()):
			print("Cannot run bundle: the bundle has not been installed.")
		else:
			bundle.run(sys.argv[4:])
	else:
		print_help_and_exit()

if (__name__ == "__main__"):
	main()
