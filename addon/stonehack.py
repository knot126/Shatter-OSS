#!/usr/bin/env python3
"""
Add stone obstacles for every box in a Smash Hit segment
"""

import xml.etree.ElementTree as ET
from pathlib import Path

def tovec3(s):
	v = s.split()
	while len(v) < 3:
		v.append("0")
	return v

def cook(filepath, obstacle = "stone"):
	root = ET.fromstring(Path(filepath).read_text())
	
	stones = []
	
	for element in root:
		if element.tag == "box":
			size = tovec3(element.attrib["size"])
			color = tovec3(element.attrib.get("color", "0 0 0"))
			
			props = {
				"pos": element.attrib["pos"],
				"type": obstacle,
				"param9": f"sizeX={size[0]}",
				"param10": f"sizeY={size[1]}",
				"param11": f"sizeZ={size[2]}",
				"shbt-ignore": "1",
			}
			
			if "template" in element.attrib:
				props["template"] = element.attrib["template"]
			
			if "color" in element.attrib:
				props["param8"] = f"color={color[0]} {color[1]} {color[2]}"
			
			if "tile" in element.attrib:
				props["param7"] = f"tile={element.attrib['tile']}"
			
			stones.append(ET.Element("obstacle", props))
	
	for element in stones:
		element.tail = "\n\t"
		root.append(element)
	
	Path(filepath).write_bytes(ET.tostring(root))

def main():
	import argparse
	
	args = argparse.ArgumentParser(
		prog="stonehack",
		description="Adds special obstacles for every box in a segment",
	)
	args.add_argument("file", help="File to bake")
	args.add_argument("--obstacle", default="stone", help="Obstacle to use, defaults to stone")
	args = args.parse_args()
	
	cook(args.file, args.obstacle)

if __name__ == "__main__":
	main()
