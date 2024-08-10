function init()
	__shatter_quick_music__
	__shatter_quick_fog__
	__shatter_quick_echo__
	__shatter_quick_reverb__
	__shatter_quick_rotation__
	__shatter_quick_particles__
	__shatter_quick_difficulty__
	__shatter_quick_gravity__
	
	confSegment("test", 1)
	confSegment("test", 1)
	confSegment("test", 1)
	confSegment("test", 1)
	confSegment("test", 1)
	
	l = 0
	
	local targetLen = __shatter_quick_length__
	
	while l < targetLen do
		s = nextSegment()
		l = l + mgSegment(s, -l)
	end
	
	mgLength(l)
end

function tick()
end
