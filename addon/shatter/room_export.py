"""
Really simple feature to export the current quick test config and scene names
as a room file.
"""

import bpy
import butil
import util

class ExportRoom(bpy.types.Operator, butil.ExportHelper2):
	"""Export a room with the same settings as those selected in the Quick Test panel"""
	
	bl_idname = "shatter.export_room"
	bl_label = "Export Quick Test config to room"
	
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

def export_room(path):
	s = bpy.context.scene.sh_properties
	
	data = f"""function init()
	pStart = mgGetBool("start", true)
	pEnd = mgGetBool("end", true)
	
	mgMusic("{s.sh_music}")
	mgFogColor({make_list(s.sh_fog_colour_bottom)}, {make_list(s.sh_fog_colour_top)})
	mgGravity({s.sh_gravity})
{func(s.sh_reverb, 'mgReverb', make_list_str(s.sh_reverb))}{func(s.sh_echo, 'mgEcho', make_list_str(s.sh_echo))}{func(s.sh_echo, 'mgSetRotation', make_list_str(s.sh_echo))}{func(s.sh_particles != 'None', 'mgParticles', f'"{s.sh_particles}"')}{func(s.sh_difficulty, 'mgSetDifficulty', s.sh_difficulty)}{s.sh_extra_code}\t
	if pStart then
		--l = l + mgSegment("put your start segment here!!", -l)
	end
	
	local targetLen = {s.sh_room_length} 
	while l < targetLen do
		s = nextSegment()
		l = l + mgSegment(s, -l)	
	end
	
	if pEnd then 
		--l = l + mgSegment("put your end segment here!!", -l)
	end
end

function tick()
end"""
	
	util.set_file(path, data)
