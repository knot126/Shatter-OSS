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
		
		self.client_ip = handler.client_address[0]
		self.client_port = handler.client_address[1]

class NXResponse:
	"""
	Response information and data
	"""
	
	def __init__(self, status_code, data, headers = {}):
		self.status_code = status_code
		self.data = data
		self.headers = headers
		
		# Turn dicts into json
		if type(self.data) == dict:
			self.data = json.dumps(data)
			self.headers["Content-Type"] = "application/json"
		
		# Turn strings into bytes
		# Also used in fallthrough to turn the json string into bytes
		if type(self.data) == str:
			self.data = self.data.encode('utf-8')
	
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
"""

quick_config = {}

@routes.add("GET", r"/v6/ping")
def v6_ping(request):
	return NXResponse(200, "Connected")

@routes.add("POST", r"/v6/config")
def v6_upload_config(request):
	return NXResponse(200, {"success": True})

def run_server():
	server = ThreadingHTTPServer(('0.0.0.0', QUICK_PORT), NXRequestHandler)
	
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		pass
	
	server.server_close()

def main():
	run_server()

if __name__ == "__main__":
	main()
