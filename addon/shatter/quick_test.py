"""
HTTP server for test mod

Notes:

 - Smash Hit does not actually implement the Host header correctly and
   excludes the port. We have to fix that.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process
import tempfile
import xml.etree.ElementTree as et
from urllib.parse import parse_qs
import pathlib
import os
import os.path
import json

CONTENT_LEVEL = """<level>
	<room type="http://{}:8000/room?ignore=" distance="1000" start="true" end="true" />
</level>"""

TEMPDIR = tempfile.gettempdir() + "/shbt-testserver/"

def parsePath(url):
	"""
	Parse the path into parameters and the real URL
	"""
	
	url = url.split("?")
	params = parse_qs(url[1]) if len(url) > 1 else {}
	
	# Only use the first one
	for p in params:
		params[p] = params[p][0]
	
	url = url[0]
	
	return (url, params)

def loadFileBytes(path):
	"""
	Load a file's bytes.
	"""
	
	return pathlib.Path(path).read_bytes()

def loadJsonFile(path):
	"""
	Load a JSON file
	"""
	
	return json.loads(pathlib.Path(path).read_text())

def toCommaArray(string):
	return ", ".join(string.split())

def getSegmentOptions():
	"""
	Get the segment fog colour, music, particles, reverb strings
	"""
	
	attrib = loadJsonFile(TEMPDIR + "/room.json")
	
	fog = toCommaArray(attrib.get("fog", "0 0 0 1 1 1"))
	music = attrib.get("music", None)
	particles = attrib.get("particles", None)
	reverb = toCommaArray(attrib.get("reverb", ""))
	echo = toCommaArray(attrib.get("echo", ""))
	rot = toCommaArray(attrib.get("rot", ""))
	length = attrib.get("length", 90)
	gravity = attrib.get("gravity", 1.0)
	difficulty = attrib.get("difficulty", 0.0)
	code = attrib.get("code", "")
	assets = attrib.get("assets", None)
	
	return {
		"fog": fog,
		"music": music,
		"particles": particles,
		"reverb": reverb,
		"echo": echo,
		"rot": rot,
		"length": length,
		"gravity": gravity,
		"difficulty": difficulty,
		"code": code,
		"assets": assets,
	}

KNOWN_OBSTACLES = ["3dcross", "babytoy", "bar", "beatmill", "beatsweeper", "beatwindow", "bigcrank", "bigpendulum", "boss", "bowling", "box", "cactus", "credits1", "credits2", "creditssign", "cubeframe", "dna", "doors", "dropblock", "elevatorgrid", "elevator", "fence", "flycube", "foldwindow", "framedwindow", "gear", "grid", "gyro", "hitblock", "laser", "levicube", "ngon", "pyramid", "revolver", "rotor", "scorediamond", "scoremulti", "scorestar", "scoretop", "sidesweeper", "stone", "suspendbox", "suspendcube", "suspendcylinder", "suspendhollow", "suspendside", "suspendwindow", "sweeper", "test", "tree", "vs_door", "vs_sweeper", "vs_wall", "boss/cube", "boss/matryoshka", "boss/single", "boss/telecube", "boss/triple", "doors/45", "doors/basic", "doors/double", "fence/carousel", "fence/dna", "fence/slider"]

def fixupObstaclesForSegment(data, remote_prefix, remote_midfix):
	"""
	Fix the path to obstacles to be accurate. Prefix is what goes before the path
	on QT 3.0+ and midfix goes between the type and the ".lua" part.
	"""
	
	global KNOWN_OBSTACLES
	
	root = et.fromstring(data)
	
	for element in root:
		if (element.tag == "obstacle"):
			known = element.attrib["type"] in KNOWN_OBSTACLES
			
			prefix = "obstacles/" if known else remote_prefix
			midfix = "" if known else remote_midfix
			
			element.attrib["type"] = prefix + element.attrib["type"] + midfix
	
	return et.tostring(root, encoding = "unicode").encode()

def generateRoomText(hostname, options):
	"""
	Generate the content for a room file
	"""
	
	music = options["music"]
	particles = options["particles"]
	reverb = options["reverb"]
	echo = options["echo"]
	rot = options["rot"]
	gravity = options["gravity"]
	difficulty = options["difficulty"]
	length = options["length"] 
	code = options["code"]
	
	music = ("\"" + music + "\"") if music else "tostring(math.random(0, 28))"
	particles = (f"\n\tmgParticles(\"{particles}\")") if particles else ""
	reverb = (f"\n\tmgReverb({reverb})") if reverb else ""
	echo = (f"\n\tmgEcho({echo})") if echo else ""
	rot = (f"\n\tmgSetRotation({rot})") if rot else ""
	difficulty = (f"\n\tmgSetDifficulty({difficulty})") if difficulty > 0.0 else ""
	
	room = f"""function init()
	mgMusic({music})
	mgFogColor({options["fog"]}){echo}{reverb}{rot}{particles}{difficulty}
	mgGravity({gravity})
	{code}
	
	confSegment("http://{hostname}:8000/segment?filetype=", 1)
	
	l = 0
	
	local targetLen = {length}
	while l < targetLen do
		s = nextSegment()
		l = l + mgSegment(s, -l)
	end
	
	mgLength(l)
end

function tick()
end"""
	
	return bytes(room, "utf-8")

def doError(self, s = ""):
	data = bytes(f"404 File Not Found\n\n{s}", "utf-8")
	self.send_response(404)
	self.send_header("Content-Length", str(len(data)))
	self.send_header("Content-Type", "text/plain")
	self.end_headers()
	self.wfile.write(data)

gProtocolVersion = {}

class AdServer(BaseHTTPRequestHandler):
	"""
	The request handler for the test server
	"""
	
	def log_request(self, code = '-', size = '-'):
		pass
	
	def do_GET(self):
		# Log the request
		client_ip = self.client_address[0]
		client_port = self.client_address[1]
		
		print(f"{client_ip}:{client_port}", self.command, self.path)
		
		# Set data
		data = b""
		contenttype = "text/xml"
		
		# Parsing parameters
		path, params = parsePath(self.path)
		
		# Get the host's name (that is us!)
		# Taking only the IP makes nonbugged clients (e.g. not SH) work.
		host = self.headers["Host"].split(":")[0]
		
		# If we have the 'pv' parameter, then we need to set the protocol version
		# to use.
		global gProtocolVersion
		protocol = params.get("pv", None)
		
		# If we are currently setting the protocol version
		if (protocol != None):
			gProtocolVersion[client_ip] = int(protocol)
		# If we need to get the protocol version (or use default)
		else:
			protocol = gProtocolVersion.get(client_ip, 2)
		
		# Get segment and assets options
		options = getSegmentOptions()
		
		# Handle what data to return
		try:
			### LEVEL ###
			if (path.endswith("level")):
				data = bytes(CONTENT_LEVEL.format(host), "utf-8")
			
			### ROOM ###
			elif (path.endswith("room")):
				data = generateRoomText(host, options)
				contenttype = "text/plain"
			
			### SEGMENT ###
			elif (path.endswith("segment") and (params["filetype"] == ".xml")):
				data = loadFileBytes(TEMPDIR + "segment.xml")
				
				# If we are using protocol version >= 3, that means the client expects
				# obstacle paths to be absolute.
				if (protocol >= 3):
					data = fixupObstaclesForSegment(data, f"http://{host}:8000/obstacle?type=", "&ignore=")
			
			### MESH ###
			elif (path.endswith("segment") and (params["filetype"] == ".mesh")):
				data = loadFileBytes(TEMPDIR + "segment.mesh")
				contenttype = "application/octet-stream"
			
			### OBSTACLE ###
			elif (path.endswith("obstacle") and options["assets"]):
				obs_path = options["assets"] + "/obstacles/" + params["type"].replace("..", "") + ".lua.mp3"
				
				if (os.path.exists(obs_path)):
					data = loadFileBytes(obs_path)
					contenttype = "text/plain"
			
			### MENU UI ###
			elif (path.endswith("menu")):
				data = bytes(f'''<ui texture="menu/start.png" selected="menu/button_select.png"><rect coords="0 0 294 384" cmd="level.start level:http://{host}:8000/level?ignore="/></ui>''', "utf-8")
		except Exception as e:
			# Error on other files
			import traceback
			doError(self, traceback.format_exc())
			return
		
		# Send response
		self.send_response(200)
		self.send_header("Content-Length", str(len(data)))
		self.send_header("Content-Type", contenttype)
		self.end_headers()
		self.wfile.write(data)

def makeTestFiles():
	"""
	Create test files
	"""
	
	print("SegServ: Creating test files...")
	
	# Make the folder itself
	os.makedirs(TEMPDIR, exist_ok = True)
	
	# Make test segment
	pathlib.Path(TEMPDIR + "segment.xml").write_text('<segment size="12 10 16"><box pos="0 -0.5 -8" size="1.0 0.5 1.0" visible="1" color="0.3 0.9 0.3" tile="20"/><obstacle type="scoretop" pos="0 0.5 -8"/></segment>')
	
	# Cook mesh for it
	r = os.system(f"python3 ./bake_mesh.py {TEMPDIR + 'segment.xml'} {TEMPDIR + 'segment.mesh'}")
	
	# windows
	if (r):
		os.system(f"py ./bake_mesh.py {TEMPDIR + 'segment.xml'} {TEMPDIR + 'segment.mesh'}")

def runServer(no_blender = False):
	"""
	Run the server
	"""
	
	server = HTTPServer(("0.0.0.0", 8000), AdServer)
	
	if (no_blender):
		makeTestFiles()
	
	print("** SegServ v1.0 - Smash Hit Quick Test Server **")
	
	try:
		server.serve_forever()
	except Exception as e:
		print("SegServ has crashed!!\n", e)
	
	server.server_close()

def runServerProcess():
	"""
	Run the server in a different process
	"""
	
	p = Process(target = runServer, args = ())
	p.start()
	return p

if (__name__ == "__main__"):
	runServer(no_blender = True)
