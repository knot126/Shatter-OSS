"""
Sample NX packed data unpacker
"""

import sys

class NXArchiveStreamer:
	def __init__(self, path):
		self.f = open(path, "rb")
		self.size = 0
	
	def read(self, num):
		self.size += num
		return self.f.read(num)
	
	def readInt(self):
		return int.from_bytes(self.read(4), 'little')
	
	def readString(self):
		return self.read(self.readInt())[:-1].decode('utf-8')

def main():
	archive_path = sys.argv[1]
	archive = NXArchiveStreamer(archive_path)
	
	reading = True
	
	while reading:
		cmd = archive.readInt()
		
		match cmd:
			case 100:
				print(f"{cmd} Begin reading archive")
				print(f"Magic: {hex(archive.readInt())}")
			case 200:
				print(f"{cmd} Extract file: {archive.readString()}",end="")
				size = archive.readInt()
				print(f" ({size / 1000} KB)")
				archive.read(size)
			case 201:
				print(f"{cmd} Make directory: {archive.readString()}")
			case 300:
				print(f"{cmd} End of archive")
				reading = False
			case _:
				print(f"No known cmd {cmd}")
	
	print(f"Archive is {archive.size / 1000} KB")

if __name__ == "__main__":
	main()
