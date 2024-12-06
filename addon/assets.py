"""
Some stuff related to managing the assets folder.
"""

from . import butil
from . import util
import os
from time import time

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
						
						items.append(item)
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
			with open(f"{butil.find_apk()}/templates.xml.mp3", "r") as f:
				for line in f:
					item = line.partition('<template name="')[2].partition('"')[0]
					
					if item:
						items.append(item)
		except:
			pass
		
		return items

templates = TemplateLister(None)

def between(string, start, end):
	return string.partition(start)[2].partition(end)[0]

class ObstacleParameterLister(AssetLister):
	"""
	List available parameters of a specific obstacle
	"""
	
	def _list(self):
		items = []
		
		try:
			with open(f"{butil.find_apk()}/obstacles/{self.category}.lua.mp3", "r") as f:
				for line in f:
					type = between(line, "mgGet", "(")
					
					if (type):
						item = between(line, '"', '"')
						
						if not item:
							item = between(line, "'", "'")
						
						default = between(between(line, "mgGet", "\n"), ",", ")").strip(" \"\'").replace(", ", " ")
						
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
