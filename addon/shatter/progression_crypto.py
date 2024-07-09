"""
Smash Hit progression.xml crypto tool

The Smash Hit save encryption algorithm is a really cheap combination of a
polyalphabetic and monoalphabetic cipher.
"""

import pathlib

def progression_crypt(data, key, decrypt = False):
	"""
	Core encrypt or decrypt function for smash hit progression files
	"""
	
	data = bytearray(data)
	out = bytearray()
	key = bytearray(key, "utf-8")
	mono = len(data)
	direction = -1 if decrypt else 1
	
	for i in range(len(data)):
		out.append((data[i] + direction * (key[i % len(key)] + mono)) & 0xff)
	
	return out

def crypt_file(path, key, decrypt = False):
	"""
	Encrypt or decrypt a file
	"""
	
	pt = pathlib.Path(path).read_bytes()
	ct = progression_crypt(pt, key, decrypt)
	pathlib.Path(path).write_bytes(ct)

def _main():
	import sys
	
	filename = ""
	decrypt = False
	key = "5m45hh1t41ght"
	
	cur = ""
	
	for arg in sys.argv[1:]:
		print(arg, cur)
		if (cur == "-e"):
			decrypt = False
			cur = arg
		elif (cur == "-d"):
			decrypt = True
			cur = arg
		elif (cur == "-f"):
			filename = arg
			cur = ""
		elif (cur == "-k"):
			key = arg
			cur = ""
		else:
			cur = arg
	
	if (not filename):
		print(f"Usage: {sys.argv[0]} [-e|-d] [-k <key>] [-f <file>]")
		print()
		print("  -e or -d   Encrypt or decrypt")
		print("  -k         Key to use (defaults to smash hit default)")
		print("  -f         File to encrypt")
		print()
		print("Smash Hit save crypto tool by Knot126")
		return
	
	crypt_file(filename, key, decrypt)

if (__name__ == "__main__"):
	_main()