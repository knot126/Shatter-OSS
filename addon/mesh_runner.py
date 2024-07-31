"""
Provides an abstract interface for baking meshes even when different mesh bakers
are being used.
"""

from . import util
import sys
import os
import shlex
from pathlib import Path

def bake(baker_type, inpath, templates = None, params = {}):
	"""
	Start a bake of a mesh with the specified baker and input xml path. This
	will automatically determine the correct output file name.
	"""
	
	global MESH_BAKE_CALLBACKS
	
	outpath = ""
	
	# there is no sanity on earth owo
	if (inpath.endswith(".xml.gz.mp3")):
		outpath = inpath[:-11] + ".mesh.mp3"
	elif (inpath.endswith(".xml.mp3")):
		outpath = inpath[:-8] + ".mesh.mp3"
	elif (inpath.endswith(".xml.gz")):
		outpath = inpath[:-7] + ".mesh"
	elif (inpath.endswith(".xml")):
		outpath = inpath[:-4] + ".mesh"
	
	util.log(f"Using baker '{baker_type}' for output '{outpath}'")
	
	return MESH_BAKE_CALLBACKS[baker_type](inpath, outpath, templates, params)

################################################################################

def cb_bakemesh(fin, fout, templates, params):
	from . import bake_mesh
	
	# Setup
	bake_mesh.BAKE_UNSEEN_FACES = params.get("BAKE_UNSEEN_FACES", False)
	bake_mesh.ABMIENT_OCCLUSION_ENABLED = params.get("ABMIENT_OCCLUSION_ENABLED", True)
	bake_mesh.LIGHTING_ENABLED = params.get("LIGHTING_ENABLED", False)
	
	# Actually bake the mesh
	bake_mesh.bakeMesh(
		fin,
		fout,
		templates,
	)
	
	return 0

def cb_yorshex(fin, fout, templates, params):
	args = [fin, fout]
	
	if templates: args.append(templates)
	args.append("-a")
	args.append(params.get("ymb_ao", "1"))
	if not params.get("ABMIENT_OCCLUSION_ENABLED", True): args.append("-A")
	if params.get("BAKE_UNSEEN_FACES", False): args.append("-C")
	
	return util.run_native("yorshex_mesh_baker", args)

def cb_command(fin, fout, templates, params):
	cmdline = params["cmd"]
	cmdline = cmdline.replace("$INPUT", shlex.quote(fin))
	cmdline = cmdline.replace("$OUTPUT", shlex.quote(fout))
	cmdline = cmdline.replace("$TEMPLATE", shlex.quote(templates))
	
	util.log(f"Execute: {cmdline}")
	
	status = os.system(cmdline)
	
	util.log(f"External command result: {status}")
	
	return status

MESH_BAKE_CALLBACKS = {
	"bakemesh": cb_bakemesh,
	"yorshex": cb_yorshex,
	"command": cb_command,
}
