"""
Some stuff related to managing the assets folder.
"""

from . import butil
from . import util
import os
import re
from time import time
import xml.etree.ElementTree as ET

class AssetLister:
	"""
	An object which can list assets with caching results
	"""
	
	def __init__(self, category, cache_time=2.0):
		self.category = category
		self.cache_data = []
		self.cache_updated = 0
		self.cache_time = cache_time
	
	def _list(self):
		assets = butil.find_apk()
		items = []
		
		if assets:
			try:
				striplen = len(f"{assets}/{self.category}") + 1
				
				for dirpath, dirnames, filenames in os.walk(f"{assets}/{self.category}"):
					for filename in filenames:
						item = os.path.join(dirpath, filename)[striplen:]
						
						# Strip extensions
						for ext in [".mp3", ".gz", ".lua", ".xml"]:
							if item.endswith(ext):
								item = item[:-len(ext)]
						
						# HACK: Windows paths force my hand...
						items.append(item.replace("\\", "/"))
			except:
				pass
		
		return items
	
	def get(self):
		if (self.cache_updated + self.cache_time) < time():
			self.cache_data = self._list()
			self.cache_updated = time()
		
		return self.cache_data
	
	def get_uncached(self):
		return self._list()

levels = AssetLister("levels")
rooms = AssetLister("rooms")
obstacles = AssetLister("obstacles")

class TemplateLister(AssetLister):
	"""
	Anddd today's "Object Hierarchy That Makes No Sense" ...
	"""
	
	def _list(self):
		items = []
		
		# This is really a hack, but should be fast and should work most of the
		# time.
		try:
			with util.shopen(f"{butil.find_apk()}/templates.xml", "r") as f:
				for line in f:
					item = line.partition('<template name="')[2].partition('"')[0]
					
					if item:
						items.append(item)
		except:
			pass
		
		return items

templates = TemplateLister(None)

def parse_templates(data):
	"""
	Yet another function to parse template data.
	"""
	
	templates = {}
	
	root = ET.fromstring(data)
	
	if root.tag != 'templates':
		raise ValueError('Not a templates xml')
	
	for template in root:
		if template.tag == 'template':
			template_name = template.attrib["name"]
			properties = template[0]
			
			if properties.tag == 'properties':
				templates[template_name] = properties.attrib
	
	return templates

class FullTemplateLister(AssetLister):
	"""
	Like TemplateLister but fully parses and lists all templates
	"""
	
	def _list(self):
		items = {}
		
		try:
			items = parse_templates(util.shload(f"{butil.find_apk()}/templates.xml"))
		except:
			pass
		
		return items
	
	def get_param_placeholder_data(self, template_name):
		properties = self.get().get(template_name, {})
		
		data = []
		
		for i in range(0, 12):
			if f"param{i}" in properties:
				x = properties[f"param{i}"].split('=', 1)
				
				if len(x) == 2:
					data.append(x)
				else:
					data.append([x[0], ''])
			else:
				data.append(['', ''])
		
		return data

full_templates = FullTemplateLister(None, 5.0)

def between(string, start, end):
	return string.partition(start)[2].partition(end)[0]

class ObstacleParameterLister(AssetLister):
	"""
	List available parameters of a specific obstacle
	"""
	
	def _list(self):
		items = []
		
		try:
			with util.shopen(f"{butil.find_apk()}/obstacles/{self.category}.lua", "r") as f:
				for line in f:
					type = between(line, "mgGet", "(")
					
					if (type):
						item = between(line, '"', '"')
						
						if not item:
							item = between(line, "'", "'")
						
						default = between(between(line, "mgGet", "\n"), ",", ")").strip(" \"\'").replace(", ", " ")
						
						if type == "Bool":
							default = "0" if default == "false" else "1"
						
						if item:
							items.append((item, type.lower(), default))
		except:
			pass
		
		return items

class MultiObstacleParameterLister:
	def __init__(self, cache_time):
		self.lists = {}
		self.cache_time = cache_time
	
	def get(self, name):
		if name not in self.lists:
			self.lists[name] = ObstacleParameterLister(name, self.cache_time)
		
		return self.lists[name].get()

obs_params = MultiObstacleParameterLister(10.0)

class APKInfo:
	"""
	Retrieve metadata about an APK
	"""
	
	def __init__(self, path):
		self.path = path
		self.title = None
		
		try:
			# Example: ddb99a48-3841-443f-8e3f-40799c9222ea
			match = re.search(r"{([0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12})}", path)
			self.uuid = match[1]
		except:
			self.uuid = None
		
		try:
			strings = ET.parse(os.path.join(path, 'res/values/strings.xml')).getroot()
			
			for string in strings:
				if string.attrib["name"] == "app_name":
					self.title = string.text
		except:
			pass
		
		try:
			manifest = ET.parse(os.path.join(path, 'AndroidManifest.xml')).getroot()
			self.package = manifest.attrib["package"]
		except:
			self.package = None
	
	def assets(self):
		return self.path + "/assets"
	
	def itemize(self):
		return (self.path, f"{self.title} ({self.package})", f"Opened with UUID: {self.uuid}")

class ExtraAssetDirInfo():
	"""
	Bare asset directory
	"""
	
	def __init__(self, path):
		self.path = path
	
	def assets(self):
		return self.path
	
	def itemize(self):
		return (self.path, "Directory: " + self.path, "Bare asset directory")
