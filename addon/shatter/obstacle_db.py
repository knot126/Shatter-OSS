import common as common
import util

# For obstacle picker
OBSTACLES = [
	("boss/cube", "Boss: Cube", ""),
	("boss/matryoshka", "Boss: Matryoshka", ""),
	("boss/single", "Boss: Single", ""),
	("boss/telecube", "Boss: Telecube", ""),
	("boss/triple", "Boss: Triple", ""),
	None,
	("doors/45", "Door: 45", ""),
	("doors/basic", "Door: Basic", ""),
	("doors/double", "Door: Double", ""),
	None,
	("fence/carousel", "Fence: Carousel", ""),
	("fence/dna", "Fence: Dna", ""),
	("fence/slider", "Fence: Slider", ""),
	None,
	("scoretop", "Crystal: Payramid (+3)", ""),
	("scorediamond", "Crystal: Diamond (+5)", ""),
	("scorestar", "Crystal: Star (+10)", ""),
	("scoremulti", "Crystal: Transcendal", ""),
	None,
	("3dcross", "3D cross", ""),
	("creditssign", "Credits sign", ""),
	("hitblock", "Hit block", ""),
	("suspendcube", "Suspsended cube", ""),
	("babytoy", "Baby toy", ""),
	("cubeframe", "Cube frame", ""),
	("laser", "Laser", ""),
	("suspendcylinder", "Suspsended cylinder", ""),
	("bar", "Bar", ""),
	("dna", "Dna", ""),
	("levicube", "Jumping cube", ""),
	("suspendhollow", "Suspended rombahidria", ""),
	("beatmill", "Beat mill", ""),
	("ngon", "N-gon shape", ""),
	("suspendside", "Suspended sweeper", ""),
	("beatsweeper", "Beat sweeper", ""),
	("dropblock", "Drop block", ""),
	("pyramid", "Cube pyramid", ""),
	("suspendwindow", "Suspended window", ""),
	("beatwindow", "Beat window", ""),
	("elevatorgrid", "Elevator grid", ""),
	("revolver", "Revolver", ""),
	("sweeper", "Sweeper", ""),
	("bigcrank", "Big crank", ""),
	("elevator", "Elevator", ""),
	("rotor", "Rotor", ""),
	("test", "Test obstacle", ""),
	("bigpendulum", "Pendulum (hammer)", ""),
	("tree", "Tree", ""),
	("flycube", "Flying cube", ""),
	("vs_door", "Verus door", ""),
	("bowling", "Bowling row", ""),
	("foldwindow", "Folding window", ""),
	("vs_sweeper", "Versus sweeper", ""),
	("box", "Box", ""),
	("framedwindow", "Framed window", ""),
	("vs_wall", "Versus wall", ""),
	("cactus", "Cactus", ""),
	("gear", "Gear", ""),
	("sidesweeper", "Side sweeper", ""),
	("credits1", "Credits obstacle 1", ""),
	("grid", "Grid", ""),
	("stone", "Stone", ""),
	("credits2", "Credits obstacle 2", ""),
	("gyro", "Gyro", ""),
	("suspendbox", "Suspended box", ""),
	None,
]

# Find custom obstacles
# TODO Make this not shit anymore (that is: a JSON file) :-)
try:
	with open(common.TOOLS_HOME_FOLDER + "/obstacles.txt", "r") as f:
		content = f.read()
		content = content.split("\n")
		
		for line in content:
			s = line.replace("= ", "=").replace(" =", "=").split("=")
			
			if (len(s) == 2 and not s[0].startswith("#")):
				OBSTACLES.append((s[0], s[1], ""))
except FileNotFoundError:
	util.log("Could not find text file for custom obstacles!")
	try:
		with open(common.TOOLS_HOME_FOLDER + "/obstacles.txt", "w") as f:
			f.write("# Put custom obstacles here!\n\n")
		
		util.log("New empty custom obstacles file has been created.")
	except:
		pass
