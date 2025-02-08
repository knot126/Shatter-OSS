#!/usr/bin/bash

# More menu segment data
cp "$1/assets/segments/menu/6.mesh.mp3" "$1/assets/segments/menu/14.mesh.mp3"
cp "$1/assets/segments/menu/7.mesh.mp3" "$1/assets/segments/menu/15.mesh.mp3"
cp "$1/assets/segments/menu/8.mesh.mp3" "$1/assets/segments/menu/16.mesh.mp3"
cp "$1/assets/segments/menu/9.mesh.mp3" "$1/assets/segments/menu/17.mesh.mp3"
cp "$1/assets/segments/menu/10.mesh.mp3" "$1/assets/segments/menu/18.mesh.mp3"
cp "$1/assets/segments/menu/11.mesh.mp3" "$1/assets/segments/menu/19.mesh.mp3"

# Patch
cp -f "$1/lib/arm64-v8a/libsmashhit.so.bak" "$1/lib/arm64-v8a/libsmashhit.so"
python ./addon/patcher.py "$1/lib/arm64-v8a/libsmashhit.so" antitamper checkpoints=19
