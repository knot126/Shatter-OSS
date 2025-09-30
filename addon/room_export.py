"""
Really simple feature to export the current quick test config and scene names
as a room file.
"""

import bpy
from . import butil
from . import util

class ExportRoom(bpy.types.Operator, butil.ExportHelper2):
	"""Export a room with the same settings as those selected in the Quick Test panel"""
	
	bl_idname = "shatter.export_room"
	bl_label = "Export Quick Test Settings to Room"
	
	filename_ext = ".lua.mp3"
	filter_glob = bpy.props.StringProperty(default='*.lua.mp3', options={'HIDDEN'}, maxlen=255)
	
	def execute(self, context):
		export_room(self.filepath)
		return {"FINISHED"}

def make_list(lst):
	return ", ".join([str(x) for x in lst])

def make_list_str(s):
	return make_list(s.split())

def func(cond, name, params):
	return f"\t{name}({params})\n" if cond else ""

def export_room(path, scene=None):
	s = scene.sh_properties or bpy.context.scene.sh_properties
	
	segpath = s.sh_level if (s.sh_level and not s.sh_room and not s.sh_segment) else f"{s.sh_level or 'level'}/{s.sh_room or 'room'}/{s.sh_segment or 'segment'}"
	
	data = f"""function init()
	pStart = mgGetBool("start", true)
	pEnd = mgGetBool("end", true)
	
	mgMusic("{s.sh_music or '0'}")
	mgFogColor({make_list(s.sh_fog_colour_bottom)}, {make_list(s.sh_fog_colour_top)})
	mgGravity({s.sh_gravity})
{func(s.sh_reverb, 'mgReverb', make_list_str(s.sh_reverb))}{func(s.sh_echo, 'mgEcho', make_list_str(s.sh_echo))}{func(s.sh_echo, 'mgSetRotation', make_list_str(s.sh_echo))}{func(s.sh_particles != 'None', 'mgParticles', f'"{s.sh_particles}"')}{func(s.sh_difficulty, 'mgSetDifficulty', s.sh_difficulty)}\t
	-- put other segments after the first one!
	confSegment("{segpath}", 1)
	
	if pStart then
		--l = l + mgSegment("put your start segment here!", -l)
	end
	
	l = 0
	
	local targetLen = {s.sh_room_length} 
	while l < targetLen do
		s = nextSegment()
		l = l + mgSegment(s, -l)
	end
	
	if pEnd then 
		--l = l + mgSegment("put your end segment here!", -l)
	end
	
	mgLength(l)
end

function tick()
end"""
	
	util.set_file(path, data)
