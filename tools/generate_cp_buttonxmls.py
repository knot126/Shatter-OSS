#!/usr/bin/env python3
import sys

cps = int(sys.argv[1])

for i in range(1, cps):
	with open(f"button{i}.xml.mp3", "w") as f:
		f.write(f'''<ui texture="button.png" selected="button_select.png">	
	<rect coords="0 0 294 384" cmd="script:level {i-1}"/>
</ui>''')

with open(f"button{cps}.xml.mp3", "w") as f:
	f.write(f'''<ui texture="endless.png" selected="button_select.png">	
	<rect coords="0 0 294 384" cmd="script:level {cps}"/>
</ui>''')
