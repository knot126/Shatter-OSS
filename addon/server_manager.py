"""
Level test server manager

Manages the level server(s) that are being run in the background.
"""

from . import util
from pathlib import Path
from subprocess import Popen
import os
import sys

class LevelServerManager():
	def __init__(self):
		self.server_type = "none"
		self.server_process = None
		self.params = tuple()
	
	def set_type(self, server_type):
		"""
		Set the server type
		
		NOTE: Server needs to be stopped first!
		"""
		
		self.server_type = server_type
	
	def set_params(self, params):
		"""
		Sets the params that will be given to the server run function.
		"""
		
		self.params = params
	
	def start(self):
		"""
		Starts the server if not already started
		"""
		
		if (not self.server_process and self.server_type != "none"):
			if (self.server_type not in SERVER_CALLBACKS):
				util.log(f"{self.server_type} is not a supported server type")
				return
			
			# Since Shatter OSS 1.0.5 the callback has changed to just returning
			# the Popen object.
			self.server_process = SERVER_CALLBACKS[self.server_type](*self.params)
			
			util.log(f"Server started with pid {self.server_process.pid}")
	
	def stop(self):
		"""
		Stop the server
		"""
		
		if (self.server_process):
			self.server_process.terminate()
			
			util.log(f"Terminated server with pid {self.server_process.pid}")
		
		self.server_process = None
	
	def restart(self):
		"""
		Restarts the server
		"""
		
		self.stop()
		self.start()


def cb_builtin():
	"""
	Run the builtin level server
	"""
	
	python_path = os.path.realpath(sys.executable)
	script_path = str(Path(__file__).parent) + "/quick_test.py"
	
	proc = Popen([python_path, script_path])
	
	return proc

def cb_yorshex(asset_dir, level):
	"""
	Run yorshex's level server
	"""
	
	python_path = os.path.realpath(sys.executable)
	script_path = str(Path(__file__).parent) + "/asset_server.py"
	
	proc = Popen([python_path, script_path, asset_dir, "-l", level, "-o"])
	
	return proc

SERVER_CALLBACKS = {
	"none": None,
	"builtin": cb_builtin,
	"yorshex": cb_yorshex,
}



def main():
	sm = LevelServerManager()
	sm.set_type(sys.argv[1])
	sm.set_params(sys.argv[2:])
	sm.start()
	
	while (True):
		cmd = input(">>> ")
		
		if (cmd == "stop"):
			sm.stop()
		if (cmd.startswith("type")):
			sm.set_type(cmd[5:])
		if (cmd.startswith("params")):
			sm.set_params(cmd[7:].split("#"))
		if (cmd == "start"):
			sm.start()
		if (cmd == "exit"):
			break
	
	sm.stop()

if (__name__ == "__main__"):
	main()
