#!/usr/bin/env python3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import re
import traceback
import json
import zipfile
import io
import ssl

SERVER_VERSION = (1, 4, 0)
QUICK_PORT = 8000
QUICK_PORT_TLS = 8433

# To avoid the need to ship a separate file, and hopefully avoid the beepers and
# buzzers about this being a private key, we decode this base64 (which contains
# a dummy TLS private key + cert) and write it to a tempfile.
DUMMY_CERTIFICATE = """LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JSUV2QUlCQURBTkJna3Foa2lHOXcwQkFRRUZBQVNDQktZd2dnU2lBZ0VBQW9JQkFRRFlQOU5wYWJBMWhxV0MKSnZKeTdUQzRmRjB0RG4zWVNXRVhnYm9WaVN3cHVlSjd5aHQyakNhOXN3eUpLTVBkYnJkQ0g1TFplbFFuK09KZwpxUGtXNGw0MGlvMGNoYnNDQkJCZGVvN2Y2c1NScklGMitoWVE0WXBXcFdwOXdHUUhYYmE3YzFaN3dwS2tWT2pkCnJOcFlWdlFWNlNaZ0p3OFA3dFFvVWlBS2RRM2xzMWw4V1YyUThXSG83OExRK3hGeUFDTzc5eUFFalA5VlZYYjIKcGNyR2R5QURScW16dWZ5NXJoZkNDdkV0QmtSZWgwSW00TU0yT0t2VjJ3MHpFQXpHWEhDOWd2UEpYRy84bFVlcApNa2VyYWhWQWpBYmdzU3U5djhmcjVMdTMwZkRyaXdncTVkN2FOcUJyemJTQXkybkNCQnBteTZQZ2FpMGVFN2U2CklMSVppR1dmQWdNQkFBRUNnZ0VBRW9OQVM0MXZOdDNjakd4ZUpDV1hIcXdTNC9rU0gvS0VPOWx3djBnN2ZpVDYKTlNQRHZ4M1hjVFVEVlRpbXIrMjdCWStqYURmWFBZYktob0RndGl0UjZraVVOUVZqMFpQY2ZNd3hzQXl1b0ZQMgp6Mk13Z1doMWlkNW1ZL2FVK2FaMXJzMThjV0xpWCt3ZTlWOUhYL210c3JSL2d3ckUrTlcyMXU3VTdHQkIvTkI2CkJMQndBaEZMck8waGtoeW5tZ3dWOUIrZ2ZPUVJmdUttNmpRMGlXTUpsSmErQktlZDFmbFRUVVRQUW05aGd3Sm4KSDZneEcrQk5rSkRJNGNQN0NKemJ2QkFWTmRCVFJTWDhER2p6SDBHK01Oc2NMYXpWYXdVOEZjSDBORCtHLzlKOApTU2VWekZ6QnBTNityZW4weUNMdVhQM1NMbVlBaWFrR2hMbk9IZVd1clFLQmdRRHdiaURTekpsc2dMM0NyajRZCm1lTjR1em9odHh1YVpKYkNIUXByZHFOYXJuL05mVDlzQTE5MURrR3ZqeHFhREwxc1lRZnZVL0dmTGJSMGkwbUoKRU1YdmhpeGEveGJQVUpnMFlHNlNOSXRlT3lySW1VREthR0w2eU40dU9rU0IwVWJPdGJ6akVDbFVqUlAyUzdtUgpVMFBMNW5LMm12NkFicHBmMTBOaUxyMnVyUUtCZ1FEbVFOTTh2ZG0zTkhZT1VLMFBpUWRoMCtHc2ZVZzROQnZwCmlQUGhqZ25qVTRlMGhVQXBNd0RObkovZXFPa2lwYi9LYUpjY004d2JBMWkrbzVWNUJ5ZDVaUG12TFB6MXhVY3cKc2w5TkpjczczVk93b213UVpRMUVBQUQzQlQza1RvN0c0S1Q3VmRzYXV3eUZFcWpTYloraThOd0NvMkoxNE1BSgpjRjRENC9UcSt3S0JnQ0RjSEZaVEtrRGZFNUJRK2lHb25xTTRpNGhpR3o2dHNzRVM4UUtnODFDSWV1VWQwaFkwCkc4N0d4UWwyZUg5SGNIZ29oc29aNGZNTWJ4Wmlsd2xKcHBQRzliYjJHQ3I3YStIMHNBZ0JjRzdQalZoZlFiQ28KTmFicTN4cllVZGFnUUpvdDBvUUNDSFFLMkFpWWJ1TkN5d2hLRmJHSlczRTRMSmNldDVIcXEzZjlBb0dBUGVsMApZMExSUmRmUFhxNEd1c1NudllCUmtDWG53MlVQbEU0RTljTlJtVlNlaXNYQnFOSlVCdlYwYjFTUHk0Y3grT1VDCnJNeW90eUxCUEJHVVlZU3c4bzFhTGVZMDVvanpTWDdNN1Z1YU9EQ2REa08rTnZKVkROSExjS0J5TWUrRnFLaEMKOUduemprNTVZVmJSR2pQcjFzNVkra1NnZHYzRjVVUFhvOGdwMVAwQ2dZQlVLU1R1ajI3SUNJVHdUdmZvc0tiZwpxSjMxcWVEZkRxRm1oVnJGZmpTMFh2ZklUaHhyczVIb1Bvc0pERldyUU9BQmRudGZqeHRDQ2cwOXdZbjB0UUxECnZsbVdoZlNxY2MvdGVwK1U4RlNIem9PbEk3ZmwyMHo0NXVmNFRhZTN1UC9tR2Rid2NaM1BKSmZJbllJUUFXL24KSHIrbXl0eWxkQzZkWTZ0MkRqZmhWZz09Ci0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS0KLS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURhekNDQWxPZ0F3SUJBZ0lVTHZTdjVKdzM2Uk5iRnVlYjJHYW42Z0FjM3dnd0RRWUpLb1pJaHZjTkFRRUwKQlFBd1JURUxNQWtHQTFVRUJoTUNRVlV4RXpBUkJnTlZCQWdNQ2xOdmJXVXRVM1JoZEdVeElUQWZCZ05WQkFvTQpHRWx1ZEdWeWJtVjBJRmRwWkdkcGRITWdVSFI1SUV4MFpEQWVGdzB5TlRFd01UUXlNek15TURKYUZ3MHlOVEV3Ck1UVXlNek15TURKYU1FVXhDekFKQmdOVkJBWVRBa0ZWTVJNd0VRWURWUVFJREFwVGIyMWxMVk4wWVhSbE1TRXcKSHdZRFZRUUtEQmhKYm5SbGNtNWxkQ0JYYVdSbmFYUnpJRkIwZVNCTWRHUXdnZ0VpTUEwR0NTcUdTSWIzRFFFQgpBUVVBQTRJQkR3QXdnZ0VLQW9JQkFRRFlQOU5wYWJBMWhxV0NKdkp5N1RDNGZGMHREbjNZU1dFWGdib1ZpU3dwCnVlSjd5aHQyakNhOXN3eUpLTVBkYnJkQ0g1TFplbFFuK09KZ3FQa1c0bDQwaW8wY2hic0NCQkJkZW83ZjZzU1IKcklGMitoWVE0WXBXcFdwOXdHUUhYYmE3YzFaN3dwS2tWT2pkck5wWVZ2UVY2U1pnSnc4UDd0UW9VaUFLZFEzbApzMWw4V1YyUThXSG83OExRK3hGeUFDTzc5eUFFalA5VlZYYjJwY3JHZHlBRFJxbXp1Znk1cmhmQ0N2RXRCa1JlCmgwSW00TU0yT0t2VjJ3MHpFQXpHWEhDOWd2UEpYRy84bFVlcE1rZXJhaFZBakFiZ3NTdTl2OGZyNUx1MzBmRHIKaXdncTVkN2FOcUJyemJTQXkybkNCQnBteTZQZ2FpMGVFN2U2SUxJWmlHV2ZBZ01CQUFHalV6QlJNQjBHQTFVZApEZ1FXQkJUT1FXUWhUbzZSRUticC80RVdpZ2ZVeGptQnp6QWZCZ05WSFNNRUdEQVdnQlRPUVdRaFRvNlJFS2JwCi80RVdpZ2ZVeGptQnp6QVBCZ05WSFJNQkFmOEVCVEFEQVFIL01BMEdDU3FHU0liM0RRRUJDd1VBQTRJQkFRRFcKRlBoZExtOW9qU2RzYVZXaDJIQlFEaVBMVENCNXAvS0VWb1Z0OEdDVDNZL0d2UURXekFLb2c2amxKZTQxS2JJdgowdTQwZXk5elhOa3lxMXZUaDVQajBDRUlNNHhYREVjczB2d3BkNm9JcU1pRnRHY1RDTUlWY1RDUm5pcFFXYmNrCmM3SkpDM3lEQ3pvOEVxS3pITVlvcWR3WXZnOGhwWWFtWEp1RmZhSS9iKzJ5cEpCa2JkUUNUT1puT0lwUXdsOUYKWkpvOUlMcFdRNU43b3djSzI5d1FScFJxVTlJbHVEVjdlVW9Ka2FtQ2JVT0hKbHV5QUIxdEdFUHo4ZkJlb0pNTQpyaWF2QmVRRC9xOHY0SE9aUnEwSE8wUExlMnorRDNMM0Z2UjlWRGo5MmpvN1hVYWVicE1kMmNkajQyMW11ZVJsCkVWdEVPejh6NTQwMDNVVWlZT1pNCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K"""

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
		return f"NXQuick/{SERVER_VERSION[0]}.{SERVER_VERSION[1]}"
	
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
"""

from pathlib import Path, PurePosixPath
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

# Assert that a quick test token exists and matches the current one
def assert_key(request_body):
	if "token" in request_body:
		try:
			if not compare_digest(request_body["token"], quick_config["token"]):
				raise SecurityException("Tokens do not match")
		except:
			raise SecurityException(f"Unknown error, user supplied token = {request_body['token']}")
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
	
	def _read_prot(self, f):
		"""
		Read an asset and return its contents (hopefully(tm) protected against
		bullshittery)
		"""
		
		for root in [self.overlay(), self.path()]:
			if root:
				if not os.path.normpath(os.path.join(root, f)).startswith(root):
					return None
		
		try:
			return Path(os.path.join(self.overlay(), f)).read_bytes()
		except:
			try:
				return Path(os.path.join(self.path(), f)).read_bytes()
			except:
				return None
	
	def read(self, f, as_text=True):
		data = self._read_prot(f)
		
		if not data:
			data = self._read_prot(f + ".mp3")
			
			if not data:
				data = self._read_prot(f + ".gz.mp3")
				
				if data:
					data = gzip.decompress(data)
		
		if data and as_text:
			data = data.decode('utf-8')
		
		if not data:
			raise FileNotFoundError(f"Could not find asset: {f}")
		
		return data
	
	def exists(self, f):
		"""
		Check that a file exists
		"""
		
		try:
			self.fullpath(f)
			return True
		except FileNotFoundError:
			return False
	
	def listDir(self, d, suffixes=None, strip_suffix=False):
		"""
		Recursively list files in the given directory. If suffix is given, it is
		a tuple of suffixes that each file string must match at least one of. If
		strip_suffix is true, the suffix is stripped from the end of the
		filename.
		"""
		
		files = []
		paths = self._fullpaths(d)
		
		for current_dir in paths:
			for dirpath, dirnames, filenames in os.walk(current_dir):
				for filename in filenames:
					cand = os.path.join(dirpath, filename)[len(current_dir)+1:]
					
					if suffixes:
						for suffix in suffixes:
							if cand.endswith(suffix):
								files.append(cand)
								if strip_suffix:
									files[-1] = files[-1][:-len(suffix)]
					else:
						files.append(cand)
		
		return list(set(files))
	
	def readXml(self, f):
		return et.fromstring(self.read(f))
	
	def readTemplatesXml(self, name = "templates.xml"):
		"""
		Read a template XML into a {"template": {"prop": "val"}} style form and
		return it.
		"""
		
		templates = {}
		
		try:
			root = self.readXml(name)
			
			for tmp in root:
				name = tmp.attrib["name"]
				attribs = tmp[0].attrib
				templates[name] = attribs
		except FileNotFoundError:
			pass
		
		return templates
	
	def readLevelXml(self, name, deps = None, rewrite=True):
		"""
		Read a level XML. Optionally, if `deps` is a set, add the original
		name of every room used in this XML to this list.
		"""
		
		root = self.readXml(f"levels/{name}.xml")
		
		for sub in root:
			if "type" in sub.attrib:
				if type(deps) == set: deps.add(sub.attrib["type"])
				
				if rewrite:
					sub.attrib["type"] = "user://rooms/" + sub.attrib["type"]
		
		return et.tostring(root, 'unicode')
	
	def readRoomLua(self, name, deps=None, rewrite=True, music_deps=None):
		"""
		Read a room lua file. If deps is a set, add the name of every segment
		type found to it.
		
		WARNING: deps uses a huristic and may not be completely accurate
		"""
		
		room = self.read(f"rooms/{name}.lua")
		
		# Sort of a HACK/TODO:
		# Any string could be a segment name, so instead of something more sane
		# we check every possible string to see if it is a valid segment. If so,
		# we should include it even if it might not be used. This will ensure
		# that 99% of rooms will work, even if they have a list of segments that
		# aren't in mgSegment() calls (e.g. random rooms mod), though if the
		# user is generating segment strings on the fly or doing other bullshit
		# then this won't work.
		if type(deps) == set:
			for match in re.findall(r'''"([^"]+)"''', room):
				if self.hasSegment(match):
					deps.add(match)
			
			for match in re.findall(r"""'([^']+)'""", room):
				if self.hasSegment(match):
					deps.add(match)
		
		# Same kind of shit for music
		if type(music_deps) == set:
			for match in re.findall(r"""mgMusic\(\s*['"]([^'"]+)['"]\s*\)""", room):
				music_deps.add(match)
		
		# As a workaround for users doing bullshit, we do also check if the
		# segment folder associated with this room contains anything, and if so
		# we add those segments too. Then this kind of thing:
		# 
		# -- room named "sewer/shit"
		# for i=1, 8 do
		#   confSegment("sewer/shit/16_" .. tostring(i), 1)
		# end
		# 
		# ... would still work, which you could imagine happening somewhat often.
		if self.exists(f"segments/{name}"):
			for segment in self.listDir(f"segments/{name}", (".xml", ".xml.gz", ".xml.mp3", ".xml.gz.mp3"), True):
				deps.add(f"{name}/{segment}")
		
		if rewrite:
			room = room.replace("mgSegment(", "__mgSegment_dYXNmdzkzdDlna2Ewd__(")
		
		return (ROOM_SCRIPT_INJECTION if rewrite else "") + room
	
	def hasObstacle(self, obs):
		return self.exists(f"obstacles/{obs}.lua")
	
	def hasSegment(self, seg):
		return self.exists(f"segments/{seg}.xml") or self.exists(f"segments/{seg}.xml.gz")
	
	def hasMesh(self, mesh):
		return self.exists(f"meshes/{mesh}.xml")
	
	def readSegmentXml(self, name, solve = True, deps = None, rewrite=True):
		"""
		Read a segment's XML file. Optionally, if `deps` is a set, add the
		original name of every obstacle type found.
		"""
		
		try:
			root = self.readXml(f"segments/{name}.xml")
		except FileNotFoundError:
			root = self.readXml(f"segments/{name}.xml.gz", gzipped=True)
		
		for sub in root:
			if sub.tag == "obstacle" and "type" in sub.attrib:
				if type(deps) == set:
					deps.add(sub.attrib["type"])
				
				if rewrite:
					# If we don't have the obstacle, assume it's one built in to the
					# client.
					if not self.hasObstacle(sub.attrib["type"]):
						sub.attrib["type"] = "obstacles/" + sub.attrib["type"]
					else:
						sub.attrib["type"] = "user://obstacles/" + sub.attrib["type"]
		
		if solve:
			templates = self.readTemplatesXml()
			
			for sub in root:
				if "template" in sub.attrib:
					sub.attrib = templates.get(sub.attrib["template"], {}) | sub.attrib
					del sub.attrib["template"]
		
		return et.tostring(root, 'unicode')
	
	def readSegmentMesh(self, name):
		"""
		Read the mesh file
		"""
		
		return self.read(f"segments/{name}.mesh", False)
	
	def readObstacleLua(self, name, wanted_meshes=None, wanted_snds=None):
		"""
		Read an obstacle's lua file
		"""
		
		data = self.read(f"obstacles/{name}.lua")
		
		if type(wanted_meshes) == set and type(wanted_snds) == set:
			for match in re.findall(r'''["']([^"']+)["']''', data):
				if self.hasMesh(match):
					wanted_meshes.add(match)
				
				if match.lower().endswith((".ogg", ".wav")) and self.exists(match):
					wanted_snds.add(match)
		
		return data
	
	def readConvexMesh(self, name):
		"""
		Read a convex mesh file
		"""
		
		return self.read(f"meshes/{name}.xml", False)
	
	def readMusic(self, name):
		"""
		Read ogg or wav music data
		"""
		
		data, fmt = (self.read(f"music/{name}.ogg", False), "ogg")
		
		if not data:
			data, fmt = (self.read(f"music/{name}.wav", False), "wav")
		
		return data, fmt
	
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
		data = assets.readLevelXml(request.query["name"], deps)
		
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
		data = assets.readRoomLua(request.query["name"], deps)
		
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
		data = assets.readSegmentXml(request.query["name"], deps = deps)
		
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


@routes.add("GET", r"/v6/obstacle")
def v6_obstacle(request):
	try:
		data = assets.readObstacleLua(request.query["name"])
		
		return NXResponse(200, data, {"Content-Type": "text/plain"})
	except FileNotFoundError:
		return NXResponse(404, f"Obstacle '{request.query['name']}' not found")


@routes.add("GET", r"/v6/packed")
def v6_mega(request):
	"""
	POST /v6/packed?levels=<level1>[;<level2>;<level3>;...]
	
	Responds with an archive in a custom, simple binary format containing the
	level XMLs and their dependents.
	"""
	
	if "levels" not in request.query:
		return NXResponse(400, "Parameter 'levels' is required!")
	
	def pack_int(i):
		# Pack an integer into required format
		return i.to_bytes(4, 'little')
	
	CMD_START = pack_int(100)
	CMD_UNPACK = pack_int(200)
	CMD_MKDIR = pack_int(201)
	CMD_END = pack_int(300)
	
	have_dirs = []
	
	def add_mkdir(arr, name):
		# Add a make dir command
		arr += CMD_MKDIR
		arr += pack_int(len(str(name)) + 1)
		arr += bytes(str(name), 'utf-8') + b"\x00"
	
	def assert_dirs(arr, name):
		# If the path contains dirs that may not exist, add a command to
		# create them.
		nonlocal have_dirs
		for parent in reversed(PurePosixPath(name).parents):
			parent = str(parent)
			if parent not in have_dirs and parent != ".":
				add_mkdir(arr, parent)
				have_dirs.append(parent)
	
	def add_pack(arr, name, data):
		# Add a file to the package
		assert_dirs(arr, name)
		arr += CMD_UNPACK
		arr += pack_int(len(str(name)) + 1)
		arr += bytes(str(name), 'utf-8') + b"\x00"
		arr += pack_int(len(data))
		arr += bytes(data, 'utf-8') if type(data) == str else data
	
	# Start bundling
	package = bytearray()
	package += CMD_START
	package += pack_int(1 | (int.from_bytes(b"NX", 'little') << 16)) # format version
	
	# Construct a set of levels to bundle
	levels_to_load = {x for x in request.query["levels"].split(";")}
	
	# Bundling the level's xml
	level_deps = set()
	for item in levels_to_load:
		try:
			level_data = assets.readLevelXml(item, level_deps)
			add_pack(package, f'levels/{item}.xml', level_data)
		except FileNotFoundError:
			print(f"warning: item {item} not found")
	
	# Bundle any rooms the level is dependent on
	room_deps = set()
	for item in level_deps:
		try:
			room_data = assets.readRoomLua(item, room_deps)
			add_pack(package, f'rooms/{item}.lua', room_data)
		except FileNotFoundError:
			print(f"warning: item {item} not found")
	
	# Bundle any segments the rooms are dependent on
	segment_deps = set()
	for item in room_deps:
		try:
			segment_data = assets.readSegmentXml(item, deps = segment_deps)
			add_pack(package, f'segments/{item}.xml', segment_data)
			mesh_data = assets.readSegmentMesh(item)
			add_pack(package, f'segments/{item}.mesh', mesh_data)
		except FileNotFoundError:
			print(f"warning: item {item} not found")
	
	# Bundle any obstacles the segments are dependent on
	for item in segment_deps:
		try:
			obstacle_data = assets.readObstacleLua(item)
			add_pack(package, f'obstacles/{item}.lua', obstacle_data)
		except FileNotFoundError:
			print(f"warning: item {item} not found")
	
	package += CMD_END
	
	return NXResponse(200, package)


@routes.add("GET", r"/v7/packed")
def v7_full(request):
	"""
	Get the entire assets directory as a zip file
	"""
	
	if "levels" not in request.query:
		return NXResponse(400, "Parameter 'levels' is required!")
	
	# Start writing zip file
	f = io.BytesIO(b"")
	z = zipfile.ZipFile(f, 'w')
	
	# templates.xml
	try:
		z.writestr(f'templates.xml', assets.read("templates.xml"), zipfile.ZIP_DEFLATED)
	except FileNotFoundError:
		print(f"Warning: cannot find templates")
	
	# game.xml
	try:
		levels = request.query["levels"].split(";")
		
		while len(levels) < 15:
			levels.append(levels[-1])
		
		game_xml = "<game>\n\t<levels>\n"
		
		for level in levels:
			game_xml += f"\t\t<level name=\"{level}\"/>\n"
		
		game_xml += "\t</levels>\n</game>"
		
		z.writestr(f'game.xml', game_xml, zipfile.ZIP_DEFLATED)
	except FileNotFoundError:
		print(f"Warning: cannot find templates")
	
	wanted_levels = {x for x in request.query["levels"].split(";")}
	
	# Level XMLs and getting wanted room types
	wanted_rooms = set()
	
	for item in wanted_levels:
		try:
			data = assets.readLevelXml(item, wanted_rooms, False)
			z.writestr(f'levels/{item}.xml', data, zipfile.ZIP_DEFLATED)
		except FileNotFoundError:
			print(f"Warning: cannot find level '{item}'")
	
	# Room lua's and getting wanted segments
	wanted_segments = set()
	wanted_music = set()
	
	for item in wanted_rooms:
		try:
			data = assets.readRoomLua(item, wanted_segments, False, music_deps=wanted_music)
			z.writestr(f'rooms/{item}.lua', data, zipfile.ZIP_DEFLATED)
		except FileNotFoundError:
			print(f"Warning: cannot find room '{item}'")
	
	if "boss_in" in wanted_music:
		wanted_music.add("boss_loop0")
		wanted_music.add("boss_loop1")
		wanted_music.add("boss_loop2")
		wanted_music.add("boss_loop3")
		wanted_music.add("boss_end")
	
	# Segment xmls and meshes, and wanted obstacles
	wanted_obstacles = set()
	
	for item in wanted_segments:
		try:
			data = assets.readSegmentXml(item, False, wanted_obstacles, False)
			z.writestr(f'segments/{item}.xml', data, zipfile.ZIP_DEFLATED)
			
			data = assets.readSegmentMesh(item)
			z.writestr(f'segments/{item}.mesh', data, zipfile.ZIP_STORED)
		except FileNotFoundError:
			print(f"Warning: cannot find segment or mesh '{item}'")
	
	# Obstacle luas
	wanted_meshes = set()
	wanted_snds = set()
	
	for item in wanted_obstacles:
		try:
			data = assets.readObstacleLua(item, wanted_meshes, wanted_snds)
			z.writestr(f'obstacles/{item}.lua', data, zipfile.ZIP_DEFLATED)
		except FileNotFoundError:
			print(f"Warning: cannot find obstacle '{item}'")
	
	# Convex meshes
	for item in wanted_meshes:
		try:
			data = assets.readConvexMesh(item)
			z.writestr(f'meshes/{item}.xml', data, zipfile.ZIP_DEFLATED)
		except FileNotFoundError:
			print(f"Warning: cannot find convex mesh '{item}'")
	
	# Sound effects
	for item in wanted_snds:
		try:
			data = assets.read(item, False)
			z.writestr(item, data, zipfile.ZIP_DEFLATED if item.lower().endswith(".wav") else zipfile.ZIP_STORED)
		except FileNotFoundError:
			print(f"Warning: cannot find sound effect '{item}'")
	
	# Wanted music tracks
	for item in wanted_music:
		try:
			data, fmt = assets.readMusic(item)
			z.writestr(f'music/{item}.{fmt}', data, zipfile.ZIP_DEFLATED if fmt == 'wav' else zipfile.ZIP_STORED)
		except FileNotFoundError:
			print(f"Warning: cannot find music '{item}'")
	
	z.close()
	
	return NXResponse(200, f.getbuffer(), {"Content-Type": "application/zip"})


@routes.add("GET", r"/v7/packed/all")
def v7_packed_all(request):
	# Start writing zip file
	f = io.BytesIO(b"")
	z = zipfile.ZipFile(f, 'w')
	
	asset_list = assets.listDir('')
	
	for item in asset_list:
		item = item.removesuffix('.gz.mp3').removesuffix('.mp3')
		data = assets.read(item, False)
		z.writestr(item, data)
	
	z.close()
	
	return NXResponse(200, f.getbuffer(), {"Content-Type": "application/zip"})


@routes.add("GET", r"/v6/ping")
def v6_ping(request):
	return NXResponse(200, "Connected", {"X-Features": "user overlay mega"})


@routes.add("GET", r"/v6/config")
def v6_download_config(request):
	assert_key({"token": request.query['token']})
	conf = quick_config.copy()
	if "token" in conf: del conf["token"]
	return NXResponse(200, {"success": True, "config": conf})


@routes.add("POST", r"/v6/config")
def v6_update_config(request):
	assert_key(request.data)
	global quick_config
	quick_config |= request.data
	return NXResponse(200, {"success": True})


def run_server(use_tls=False):
	global server
	server = ThreadingHTTPServer(('0.0.0.0', QUICK_PORT if not use_tls else QUICK_PORT_TLS), NXRequestHandler)
	
	if use_tls:
		import base64
		import tempfile
		import os
		import time
		
		tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
		tls.minimum_version = ssl.TLSVersion.TLSv1_2
		
		certname = tempfile.gettempdir() + f"/nxquick-dummy-certificate-{time.time()}.pem"
		
		with open(certname, "wb") as fp:
			fp.write(base64.b64decode(DUMMY_CERTIFICATE))
		
		tls.load_cert_chain(certname)
		os.remove(certname)
		
		server.socket = tls.wrap_socket(server.socket, server_side=True)
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
	
	server.server_close()

APP_DESC = "Serves assets to Shatter Quick Test clients using protocol v6 or later"
ASSETS_HELP = "Set the directory where the server looks for assets from"
ASSETS_OVERLAY_HELP = "Set the asset overlay directory where the server looks for files before going to the asset directory"
TOKEN_HELP = "Set the authentication token required to communicate with Shatter on the local computer"
INSECURE_HELP = "Allow the server to run without an authentication token"
TLS_HELP = "Use HTTP over TLS (HTTPS) to secure the connection between the test client and server"

def main():
	import argparse
	
	args = argparse.ArgumentParser(
		prog = "Quick Test server",
		description = APP_DESC,
	)
	args.add_argument("-a", "--assets", required=False, help=ASSETS_HELP)
	args.add_argument("-o", "--assets-overlay", required=False, help=ASSETS_OVERLAY_HELP)
	args.add_argument("-t", "--token", required=False, help=TOKEN_HELP)
	args.add_argument("-i", "--insecure", action="store_true", help=INSECURE_HELP)
	args.add_argument("-s", "--tls", action="store_true", help=TLS_HELP)
	args = args.parse_args()
	
	quick_config["assets"] = args.assets
	quick_config["assets_overlay"] = args.assets_overlay
	
	if not args.token and not args.insecure:
		print("Error: No auth token specified and flag not passed to disable it!")
		return
	
	if not args.insecure:
		quick_config["token"] = args.token
	
	run_server(args.tls)

if __name__ == "__main__":
	main()
