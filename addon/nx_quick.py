#!/usr/bin/env python3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import re
import traceback
import json

QUICK_PORT = 8000

"""
Very small framework written for the test server
"""

class NXRequest:
	"""
	Information about the request
	"""
	
	def __init__(self, handler):
		self.method = handler.command
		parsed_url = urlparse(handler.path)
		self.path = parsed_url.path
		self.query = {}
		
		for key, value in parse_qs(parsed_url.query).items():
			self.query[key] = value[0]
		
		self.headers = handler.headers
		
		if self.method == "POST":
			self.data = handler.rfile.read(int(self.headers["Content-Length"]))
		else:
			self.data = None
		
		if self.data and "Content-Type" in self.headers and self.headers["Content-Type"] == "application/json":
			self.data = json.loads(self.data.decode("utf-8"))
		
		self.client_ip = handler.client_address[0]
		self.client_port = handler.client_address[1]

class NXResponse:
	"""
	Response information and data
	"""
	
	def __init__(self, status_code, data, headers = None):
		self.status_code = status_code
		self.data = data
		self.headers = headers or {}
		
		# Turn dicts into json
		if type(self.data) == dict:
			self.data = json.dumps(data)
			self.headers["Content-Type"] = "application/json"
		
		# Turn strings into bytes
		# Also used in fallthrough to turn the json string into bytes
		if type(self.data) == str:
			self.data = self.data.encode("utf-8")
	
	def send(self, handler):
		# Send response header (ex HTTP/1.1 200 OK)
		handler.send_response(self.status_code)
		
		# Send user's custom headers
		for key, value in self.headers.items():
			handler.send_header(key, value)
		
		# Send content length, end headers and send actual content
		handler.send_header("Content-Length", str(len(self.data)))
		handler.end_headers()
		
		handler.wfile.write(self.data)

class NXRoutes:
	"""
	Registry of routes
	"""
	
	protocol_version = 'HTTP/1.1'
	
	def __init__(self):
		self.routes = {}
	
	def add_route(self, method, pattern, func):
		"""
		Associate a function with a given (method, path) pair. The pattern may
		be any regex.
		"""
		
		self.routes[(method, re.compile(pattern))] = func
	
	def add(self, method, pattern):
		"""
		Similar to add_route, to be used as a decorator.
		@routes.add("GET", "/v6/ping")
		"""
		
		# Since
		#  @decor
		#  def myfunc(): ...
		# is basically just myfunc = (decor)(myfunc),
		# 
		#  @decor(params)
		#  def myfunc():
		# is basically just myfunc = (decor(params))(myfunc),
		# 
		# and @routes.add("GET", "/") is myfunc = (routes.add("GET", "/"))(myfunc),
		# 
		# so we need to return a function that when called returns a decorator
		# which will register the route. this is returning a decorator which can
		# register a route with the given specific params.
		def decorate(func):
			self.add_route(method, pattern, func)
			return func
		
		return decorate
	
	def match_route(self, method, path):
		"Return a route that can handle the given METHOD and /path"
		
		for route, func in self.routes.items():
			if route[0] == method and route[1].fullmatch(path) != None:
				return func
		
		return None
	
	def preform(self, request):
		"""
		Preform the request by calling the route's associated function with the
		request object as the first argument. Return the value returned by the
		function called.
		"""
		
		endpoint = self.match_route(request.method, request.path)
		
		if not endpoint:
			return NXResponse(404, "Route is not supported")
		
		try:
			return endpoint(request)
		except:
			traceback.print_exc()
			return NXResponse(500, "There was an error processing your request")

routes = NXRoutes()

class NXRequestHandler(BaseHTTPRequestHandler):
	def version_string(self):
		return "NXQuick/1.0"
	
	def do_GET(self):
		self.do_response()
	
	def do_POST(self):
		self.do_response()
	
	def do_response(self):
		request = NXRequest(self)
		result = routes.preform(request)
		result.send(self)

"""
The routes specific to quick test v6 and later

TODO:
  - Template resolution
  - Remote scripts, so we have more compatiblity with other APIs
"""

from pathlib import Path
from hmac import compare_digest
import os
import os.path
import xml.etree.ElementTree as et
import gzip

RAW_CONTENT_TYPES = {
	".xml": "text/xml",
	".lua": "text/plain",
	".fnt": "text/plain",
	".glsl": "text/plain",
	".mesh": "application/octet-stream",
	".gz": "application/gzip",
	".png": "image/png",
	".mtx": "image/mtx",
	".ogg": "audio/ogg",
}

ROOM_SCRIPT_INJECTION = """-- BEGIN ROOM INJECTION
function __mgSegment_dYXNmdzkzdDlna2Ewd__(path, l)
	knLog(LOG_INFO, "Load segment: " .. path)
	return mgSegment("user://segments/" .. path, l)
end
-- END ROOM INJECTION

"""

# Global config options - set via POST /v6/config
quick_config = {}

# When there is no key with config update attempt we throw this exception
class SecurityException(Exception): pass

# Assert that either (a) there is no token required or (b) it exists and matches
def assert_key(request_body):
	if "token" not in quick_config:
		return
	
	if "token" in request_body:
		if not compare_digest(request_body["token"], quick_config["token"]):
			raise SecurityException("Tokens do not match")
	else:
		raise SecurityException("Token not in body")

class AssetManager:
	"""
	Read assets from Smash Hit
	"""
	
	def __init__(self):
		pass
	
	def path(self):
		p = quick_config["assets"]
		return os.path.normpath(p) if p else None
	
	def overlay(self):
		p = quick_config["assets_overlay"]
		return os.path.normpath(p) if p else None
	
	def _fullpaths(self, f):
		"""
		Get the full path(s) to the file f, if it exists. May be empty. Should
		not return any paths outside of path and overlay.
		"""
		
		cands = []
		paths = []
		if self.overlay():
			np = os.path.normpath(os.path.join(self.overlay(), f))
			cands.append(np)
			cands.append(f"{np}.mp3")
		if self.path():
			np = os.path.normpath(os.path.join(self.path(), f))
			cands.append(np)
			cands.append(f"{np}.mp3")
		
		for cand in cands:
			if os.path.exists(cand):
				# This check is needed to ensure we're not loading files outside
				# of the asset dir(s)
				# NOTE: If you did something like "../assets/templates.xml" that
				# would pass and this is technically an exploit to find
				# directory names and/or confirm that folders exist but I don't
				# believe it will be a big problem for the moment.
				# NOTE: Another one, is not having a / at the end causing any
				# file in the parent of the asset/overlay folder to be readable
				# if it shares a prefix the name of the folder?
				if (self.overlay() and cand.startswith(self.overlay())) or (self.path() and cand.startswith(self.path())):
					paths.append(cand)
		
		return paths
	
	def fullpath(self, f):
		"""
		Get the real path to the asset-relative file path.
		"""
		
		paths = self._fullpaths(f)
		
		if not paths:
			raise FileNotFoundError()
		
		return paths[0]
	
	def read(self, f, is_text=True, gzipped=False):
		"""
		Read a (text or binary) file and return its contents
		"""
		
		path = Path(self.fullpath(f))
		
		if not gzipped:
			return path.read_text() if is_text else path.read_bytes()
		else:
			g = gzip.open(path, "r" if is_text else "rb")
			data = g.read()
			g.close()
			return data
	
	def listDir(self, d, suffixes=None, strip_suffix=False):
		"""
		Recursively list files in the given directory. If suffix is given, it is
		a tuple of suffixes that each file string must match at least one of. If
		strip_suffix is true, the suffix is stripped from the end of the
		filename.
		"""
		
		files = []
		fulldirpath = self.fullpath(d)
		
		for dirpath, dirnames, filenames in os.walk(fulldirpath):
			for filename in filenames:
				cand = os.path.join(dirpath, filename)[len(fulldirpath)+1:]
				
				if suffixes:
					for suffix in suffixes:
						if cand.endswith(suffix):
							files.append(cand)
							if strip_suffix:
								files[-1] = files[-1][:-len(suffix)]
				else:
					files.append(cand)
		
		return files
	
	def readXml(self, f, gzipped=False):
		return et.fromstring(self.read(f, gzipped=gzipped))
	
	def readLevelXml(self, name, prepend = "", append = "", deps = None):
		"""
		Read a level XML, prepending `prepend` and appending `append` to room
		type attributes. Optionally, if `deps` is a set, add the original
		name of every room used in this XML to this list.
		"""
		
		root = self.readXml(f"levels/{name}.xml")
		
		for sub in root:
			if "type" in sub.attrib:
				if type(deps) == set: deps.add(sub.attrib["type"])
				sub.attrib["type"] = prepend + sub.attrib["type"] + append
		
		return et.tostring(root, 'unicode')
	
	def readRoomLua(self, name, prepend = "", append = "", deps = None):
		"""
		Read a room lua file. If deps is a set, add the name of every segment
		type found to it.
		
		WARNING: deps uses a huristic and may not be completely accurate
		"""
		
		room = self.read(f"rooms/{name}.lua")
		
		# TODO fix this
		if type(deps) == set:
			for match in re.findall(r'mgSegment\s*\(\s*"([^"]+)"', room):
				deps.add(match)
			
			for match in re.findall(r'confSegment\s*\(\s*"([^"]+)"', room):
				deps.add(match)
		
		room = room.replace("mgSegment(", "__mgSegment_dYXNmdzkzdDlna2Ewd__(")
		
		return prepend + room + append
	
	def readSegmentXml(self, name, prepend = "", append = "", deps = None):
		"""
		Read a segment's XML file, prepending and appending the given strings
		to each obstacle's type attributes. Optionally, if `deps` is a set,
		add the original name of every obstacle type found.
		
		TODO: Remote obstacle loading
		"""
		
		try:
			root = self.readXml(f"segments/{name}.xml")
		except FileNotFoundError:
			root = self.readXml(f"segments/{name}.xml.gz", gzipped=True)
		
		for sub in root:
			if sub.tag == "obstacle" and "type" in sub.attrib:
				if type(deps) == set: deps.add(sub.attrib["type"])
				sub.attrib["type"] = prepend + sub.attrib["type"] + append
		
		return et.tostring(root, 'unicode')
	
	def readSegmentMesh(self, name):
		"""
		Read the mesh file
		"""
		
		return self.read(f"segments/{name}.mesh", False)
	
	def write(self, f, data):
		"""
		Write the data to a file at f. Always writes to the overlay!
		"""
		
		overlay = self.overlay()
		
		if not overlay:
			raise FileNotFoundError()
		
		f = os.path.join(overlay, f)
		
		Path(f).write_text(data) if type(data) == str else Path(f).write_bytes(data)

assets = AssetManager()

def guess_mime_type(filename):
	for k, v in RAW_CONTENT_TYPES.items():
		if filename.endswith(k):
			return v
	
	return "application/octet-stream"

def join_content_and_deps_set(content, deps):
	content = bytearray(content, 'utf-8')
	
	for dep in deps:
		content += b"\x00" + bytes(dep, 'utf-8')
	
	return content

@routes.add("GET", r"/v6/raw")
def v6_raw(request):
	try:
		return NXResponse(200, assets.read(request.query["name"], False), {
			"Content-Type": guess_mime_type(request.query["name"]),
		})
	except FileNotFoundError:
		return NXResponse(404, f"File '{request.query['name']}' not found")


@routes.add("GET", r"/v6/level/list")
def v6_level_list(request):
	levels = assets.listDir("levels", (".xml.mp3", ".xml"), True)
	
	if 'raw' in request.query:
		return NXResponse(200, b"\x00".join([bytes(x, 'utf-8') for x in levels]))
	else:
		return NXResponse(200, {'success': True, 'levels': levels})

@routes.add("GET", r"/v6/level")
def v6_level(request):
	try:
		deps = set()
		data = assets.readLevelXml(request.query["name"], "user://rooms/", "", deps)
		
		if 'depends' in request.query:
			return NXResponse(200, join_content_and_deps_set(data, deps), {"Content-Type": "application/octet-stream"})
		else:
			return NXResponse(200, data, {"Content-Type": "text/xml"})
	except FileNotFoundError:
		return NXResponse(404, f"Level '{request.query['name']}' not found")


@routes.add("GET", r"/v6/room")
def v6_room(request):
	try:
		deps = set()
		data = assets.readRoomLua(request.query["name"], ROOM_SCRIPT_INJECTION, "", deps)
		
		if 'depends' in request.query:
			return NXResponse(200, join_content_and_deps_set(data, deps), {"Content-Type": "application/octet-stream"})
		else:
			return NXResponse(200, data, {"Content-Type": "text/plain"})
	except FileNotFoundError:
		return NXResponse(404, f"Room '{request.query['name']}' not found")


@routes.add("GET", r"/v6/segment/xml")
def v6_segment_xml(request):
	try:
		deps = set()
		data = assets.readSegmentXml(request.query["name"], "obstacles/", "", deps)
		
		if 'depends' in request.query:
			return NXResponse(200, join_content_and_deps_set(data, deps), {"Content-Type": "application/octet-stream"})
		else:
			return NXResponse(200, data, {"Content-Type": "text/xml"})
	except FileNotFoundError:
		return NXResponse(404, f"Segment '{request.query['name']}' not found")


@routes.add("GET", r"/v6/segment/mesh")
def v6_segment_mesh(request):
	try:
		data = assets.readSegmentMesh(request.query["name"])
		return NXResponse(200, data, {"Content-Type": "application/octet-stream"})
	except FileNotFoundError:
		return NXResponse(404, f"Segment '{request.query['name']}' not found")


@routes.add("POST", r"/v6/mega")
def v6_download_bundled(request):
	return NXResponse(404, f"Mega bundling is not supported by this server")


@routes.add("GET", r"/v6/ping")
def v6_ping(request):
	return NXResponse(200, "Connected")


@routes.add("GET", r"/v6/config")
def v6_download_config(request):
	conf = quick_config.copy()
	del conf["token"]
	return NXResponse(200, {"success": True, "config": conf})


@routes.add("POST", r"/v6/config")
def v6_update_config(request):
	assert_key(request.data)
	global quick_config
	quick_config |= request.data
	return NXResponse(200, {"success": True})


def run_server():
	global server
	server = ThreadingHTTPServer(('0.0.0.0', QUICK_PORT), NXRequestHandler)
	
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
	
	server.server_close()

APP_DESC = "Serves assets to Shatter Quick Test clients using protocol v6 or later"
ASSETS_HELP = "Set the directory where the server looks for assets from"
ASSETS_OVERLAY_HELP = "Set the asset overlay directory where the server looks for files before going to the asset directory"
TOKEN_HELP = "Set the security token required to communicate with Shatter"
INSECURE_HELP = "Allow the server to run without a security token"

def main():
	import argparse
	
	args = argparse.ArgumentParser(
		prog = "Quick Test server",
		description = APP_DESC,
	)
	args.add_argument("-a", "--assets", required = False, help = ASSETS_HELP)
	args.add_argument("-o", "--assets-overlay", required = False, help = ASSETS_OVERLAY_HELP)
	args.add_argument("-t", "--token", required = False, help = TOKEN_HELP)
	args.add_argument("-i", "--insecure", action = "store_true", help = INSECURE_HELP)
	args = args.parse_args()
	
	quick_config["assets"] = args.assets
	quick_config["assets_overlay"] = args.assets_overlay
	
	if not args.token and not args.insecure:
		print("Error: No token specified and server in secure mode!")
		return
	
	if not args.insecure:
		quick_config["token"] = args.token
	
	run_server()

if __name__ == "__main__":
	main()
