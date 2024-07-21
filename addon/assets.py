"""
Some stuff related to managing the assets folder.
"""

import butil
import util
import os

def list_levels(cache = None):
	"""
	List out the levels in an available assets folder
	"""
	
	try:
		if (cache and util.get_time() < cache["expire"]):
			return cache
		
		results = []
		
		files = util.list_folder(butil.find_apk() + "/levels/", False)
		
		for f in files:
			results.append(os.path.basename(f)[:-8])
		
		return {"results": results, "expire": util.get_time() + 5}
	except:
		return {"results": [], "expire": util.get_time() + 1000}
