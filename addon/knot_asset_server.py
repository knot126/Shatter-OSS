#!/usr/bin/env python3
"""
Asset Server for Smash Hit (NOT a quick test server)
"""

from socketserver import ThreadingTCPServer, BaseRequestHandler
import struct
from pathlib import Path
import os
import traceback
import gzip

SET_PATH_EXT_ENABLED = False

class SocketStream:
	"""
	Class to provide helper functions when reading and writing data.
	"""
	
	def __init__(self, req):
		self.req = req
	
	def read(self, size):
		data = self.req.recv(size)
		
		if not data:
			return None
		
		return data
	
	def write(self, data):
		self.req.sendall(data)
	
	def readInt32(self):
		d = self.read(4)
		return struct.unpack(">i", d)[0] if d else None
	
	def readString(self):
		l = self.readInt32()
		if l == None or l < 0 or l > 4096: return None
		return self.read(l).decode('utf-8')
	
	def writeBool(self, data):
		self.write(b'\x01' if data else b'\x00')
	
	def writeInt32(self, data):
		self.write(struct.pack(">i", data))

class AssetManager:
	"""
	Manages an asset directory
	"""
	
	def __init__(self, path=None):
		self.setPath(path)
	
	def setPath(self, path):
		self.path = os.path.realpath(path) if path else None
	
	def read(self, path, fixup=True):
		try:
			orig_path = path
			path = os.path.realpath(f"{self.path}/{path}")
			
			# Try to enforce that we didn't traverse outside the directory.
			if not path.startswith(self.path):
				return None
			
			# Read the file, if it exists and is actually a file
			if (os.path.isfile(path)):
				return Path(path).read_bytes()
			elif (os.path.isfile(path + ".mp3")):
				return Path(path + ".mp3").read_bytes()
			elif (os.path.isfile(path + ".gz.mp3")):
				return gzip.decompress(Path(path + ".gz.mp3").read_bytes())
			else:
				# Smash Hit doesn't seem to include the levels, rooms, segments
				# or obstacles part when trying to load from the asset server :/
				if fixup:
					return self.read(f"levels/{orig_path}", False) or self.read(f"rooms/{orig_path}", False) or self.read(f"segments/{orig_path}", False) or self.read(f"obstacles/{orig_path}", False)
				
				return None
		except:
			return None

asset_manager = AssetManager()

class AssetServerRequestHandler(BaseRequestHandler):
	"""
	Request handler for the Smash Hit asset server
	"""
	
	def handle(self):
		global asset_manager
		
		socket = SocketStream(self.request)
		socket.writeInt32(0xfa1afe1)
		
		print(f"{self.client_address[0]}: Connected")
		
		try:
			while True:
				path = socket.readString()
				
				if path == None:
					break
				
				# Shatter extension: path "*SET-PATH*" is special and sets the
				# current path if it's a request from localhost.
				if (SET_PATH_EXT_ENABLED and self.client_address[0] == "127.0.0.1" and path == "*SET-PATH*"):
					print(f"{self.client_address[0]}: Set asset directory")
					asset_manager.setPath(socket.readString())
					break
				
				data = asset_manager.read(path)
				
				if data:
					print(f"{self.client_address[0]}: Serve {path}")
					socket.writeBool(True)
					socket.writeInt32(len(data))
					socket.write(data)
				else:
					print(f"{self.client_address[0]}: Not found {path}")
					socket.writeBool(False)
		except:
			traceback.print_exc()
			pass
		
		print(f"{self.client_address[0]}: Disconnected")

def run():
	try:
		with ThreadingTCPServer(("0.0.0.0", 24555), AssetServerRequestHandler) as srv:
			srv.serve_forever()
	except KeyboardInterrupt:
		print("Exiting...")

def main():
	global SET_PATH_EXT_ENABLED
	import argparse
	
	args = argparse.ArgumentParser(prog="assetserver", description="Asset server for Smash Hit and other Mediocre games")
	args.add_argument("--enable-setpath", action='store_true', help="Enables the set-path extension needed for Shatter to update the asset path without restarting the server.")
	args.add_argument("assets", help="Directory to load assets from")
	args = args.parse_args()
	
	SET_PATH_EXT_ENABLED = args.enable_setpath
	asset_manager.setPath(args.assets)
	
	run()

if __name__ == "__main__":
	main()
