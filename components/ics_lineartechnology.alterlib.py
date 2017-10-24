import alterpcb_core

import numpy

alphabet = "ABCDEFGHJKLMNOPQRSTUVWXYZ" # skip I

@component
def lineartechnology_ltc2000(mask=0.05, paste=-0.025):
	pcb = alterpcb_core.Pcb()
	(rows, cols, row_pitch, col_pitch, pad_diameter) = (17, 10, 0.8, 0.8, 0.4)
	(package_w, package_h) = (9.0, 15.0)
	for i in range(rows):
		for j in range(cols):
			pcb.add("pad_circ_smd", x=col_pitch*(j-(cols-1)/2), y=row_pitch*(i-(rows-1)/2), diameter=pad_diameter, mask=mask, paste=paste)
	for sx in [-1, 1]:
		for sy in [-1, 1]:
			xx = list(sx * (package_w / 2 + numpy.array([ 0.2,  0.2, -0.2])))
			yy = list(sy * (package_h / 2 + numpy.array([-0.2,  0.2,  0.2])))
			pcb.add("polygon", layer="copper1-top", x=xx, y=yy, closed=False, outline=0.2)
			pcb.add("polygon", layer="mask-top", x=xx, y=yy, closed=False, outline=0.4)
	pcb.add("rectangle", layer="courtyard-top", x=0.0, y=0.0, width=package_w+2.0, height=package_h+2.0, outline=0.1)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=package_w, height=package_h)
	for i in range(rows):
		pcb.add("text", layer="mech2-top", text=alphabet[rows-1-i], font="DejaVuSans", size=0.4,
				x=-col_pitch*(cols/2+0.25), y=row_pitch*(i-(rows-1)/2), halign="center", valign="center", steps=4)
	for j in range(cols):
		pcb.add("text", layer="mech2-top", text=str(j+1), font="DejaVuSans", size=0.4,
				x=col_pitch*(j-(cols-1)/2), y=row_pitch*(rows/2+0.25), halign="center", valign="center", steps=4)
	return pcb
