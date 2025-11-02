#!/usr/bin/env python3
import argparse
import shutil
import os
from zipfile import ZipFile
from pathlib import Path

def install(package, path):
	# Move lib/<arch>/libsmashhit.so to assets/native/<arch>/libsmashhit.so.mp3
	for arch in os.listdir(f"{path}/lib"):
		lsh_orig = f"{path}/lib/{arch}/libsmashhit.so"
		
		if os.path.isfile(lsh_orig):
			os.makedirs(f"{path}/assets/native/{arch}", exist_ok=True)
			os.replace(lsh_orig, f"{path}/assets/native/{arch}/libsmashhit.so.mp3")
	
	# Extract packaged knshim zip archive
	with ZipFile(package) as z:
		z.extractall(f"{path}/lib")
	
	# HACK: *Very* jank way to tell android to load libshim instead of libsmashhit
	amx = Path(f"{path}/AndroidManifest.xml")
	amx.write_bytes(amx.read_bytes().replace(b'android:name="android.app.lib_name" android:value="smashhit"', b'android:name="android.app.lib_name" android:value="shim"'))

def main():
	args = argparse.ArgumentParser()
	args.add_argument("package", help="Path to a packaged KnShim zip file to source libshim (and other wanted libraries) from")
	args.add_argument("apk", help="The unpacked APK to install KnShim to")
	args = args.parse_args()
	
	install(args.package, args.apk)

if __name__ == "__main__":
	main()
