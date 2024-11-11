#!/usr/bin/env python3
import argparse
import shutil
import os
from pathlib import Path

LIB_DIR = str(Path(__file__).parent) + "/data/shim"

def install(path):
	for arch in os.listdir(f"{path}/lib"):
		lsh_orig = f"{path}/lib/{arch}/libsmashhit.so"
		
		if os.path.isfile(lsh_orig):
			os.makedirs(f"{path}/assets/native/{arch}", exist_ok=True)
			os.replace(lsh_orig, f"{path}/assets/native/{arch}/libsmashhit.so.mp3")
	
	shutil.copytree(LIB_DIR, f"{path}/lib", dirs_exist_ok=True)
	
	amx = Path(f"{path}/AndroidManifest.xml")
	amx.write_bytes(amx.read_bytes().replace(b'android:name="android.app.lib_name" android:value="smashhit"', b'android:name="android.app.lib_name" android:value="shim"'))
	
	try:
		from . import patcher
		
		for arch in ["armeabi-v7a", "arm64-v8a"]:
			try:
				patcher.patch_binary(f"{path}/assets/native/{arch}/libsmashhit.so.mp3", {"antitamper": []})
			except:
				print(f"Warning: Failed to patch {arch} binary.")
	except ImportError:
		print("Note: The patcher could not be found, so you will need to patch libsmashhit.so against anti-tamper manually.")

def main():
	args = argparse.ArgumentParser()
	args.add_argument("file", help="Install KnShim to an extracted Smash Hit APK directory")
	args = args.parse_args()
	
	install(args.file)

if __name__ == "__main__":
	main()
