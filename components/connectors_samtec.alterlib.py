import alterpcb_core

alphabet = "ABCDEFGHJKLMNOPQRSTUVWXYZ" # skip I

@component
def connector_samtec_erm8(cols=20, mask=0.1, paste=-0.05):
	pcb = alterpcb_core.Pcb()
	(pad_w, pad_h, row_pitch, col_pitch, pin_w, pin_h) = (0.5, 1.1, 3.8, 0.8, 0.3, 0.9)
	body_w1 = cols * col_pitch + 6.0
	body_w2 = cols * col_pitch + 4.2
	body_h1 = 5.6
	body_h2 = 3.2
	hole_x = cols * col_pitch / 2 + 1.4
	hole_y = 1.5
	hole_diameter = 1.45
	shapes = []
	for i in range(cols):
		xx = col_pitch * (i - (cols - 1) / 2)
		pcb.add("pad_rect_smd", x=xx, y=-row_pitch/2, width=pad_w, height=pad_h, mask=mask, paste=paste)
		pcb.add("pad_rect_smd", x=xx, y= row_pitch/2, width=pad_w, height=pad_h, mask=mask, paste=paste)
	xx1 = cols * col_pitch / 2 + 0.2
	xx2 = body_w1 / 2
	pcb.add("mechanical_hole", x=-hole_x, y=-hole_y, drill_diameter=hole_diameter, hole_diameter=hole_diameter+0.6)
	pcb.add("mechanical_hole", x= hole_x, y=-hole_y, drill_diameter=hole_diameter, hole_diameter=hole_diameter+0.6)
	pcb.add("polygon", layer="silk-top", x=[-xx1, -xx2, -xx2, -xx1], y=[-body_h1/2, -body_h1/2, body_h1/2, body_h1/2], closed=False, outline=0.2)
	pcb.add("polygon", layer="silk-top", x=[ xx1,  xx2,  xx2,  xx1], y=[-body_h1/2, -body_h1/2, body_h1/2, body_h1/2], closed=False, outline=0.2)
	pcb.add("line", layer="silk-top", x1=-body_w1/2, y1=body_h1/2-1.6, x2=-body_w1/2+1.6, y2=body_h1/2, width=0.2)
	pcb.add("rectangle", layer="courtyard-top", x=0.0, y=0.0, width=body_w1+1.0, height=body_h1+1.0, outline=0.1)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=body_w1, height=body_h1)
	pcb.add("rectangle", layer="mech2-top", x=0.0, y=0.0, width=body_w2, height=body_h2)
	for i in range(cols):
		xx = col_pitch * (i - (cols - 1) / 2)
		pcb.add("rectangle", layer="mech2-top", x=xx, y=-row_pitch/2, width=pin_w, height=pin_h)
		pcb.add("rectangle", layer="mech2-top", x=xx, y= row_pitch/2, width=pin_w, height=pin_h)
	return pcb

@component
def connector_samtec_erf8(cols=20, mask=0.1, paste=-0.05):
	pcb = alterpcb_core.Pcb()
	(pad_w, pad_h, row_pitch, col_pitch, pin_w, pin_h) = (0.5, 1.1, 4.5, 0.8, 0.3, 0.9)
	body_w1 = cols * col_pitch + 6.0
	body_w2 = cols * col_pitch + 4.2
	body_h1 = 5.6
	body_h2 = 3.2
	hole_x = cols * col_pitch / 2 + 1.4
	hole_y = 1.5
	hole_diameter = 1.45
	shapes = []
	for i in range(cols):
		xx = col_pitch * (i - (cols - 1) / 2)
		pcb.add("pad_rect_smd", x=xx, y=-row_pitch/2, width=pad_w, height=pad_h, mask=mask, paste=paste)
		pcb.add("pad_rect_smd", x=xx, y= row_pitch/2, width=pad_w, height=pad_h, mask=mask, paste=paste)
	xx1 = cols * col_pitch / 2 + 0.2
	xx2 = body_w1 / 2
	pcb.add("mechanical_hole", x=-hole_x, y=-hole_y, drill_diameter=hole_diameter, hole_diameter=hole_diameter+0.6)
	pcb.add("mechanical_hole", x= hole_x, y=-hole_y, drill_diameter=hole_diameter, hole_diameter=hole_diameter+0.6)
	pcb.add("polygon", layer="silk-top", x=[-xx1, -xx2, -xx2, -xx1], y=[-body_h1/2, -body_h1/2, body_h1/2, body_h1/2], closed=False, outline=0.2)
	pcb.add("polygon", layer="silk-top", x=[ xx1,  xx2,  xx2,  xx1], y=[-body_h1/2, -body_h1/2, body_h1/2, body_h1/2], closed=False, outline=0.2)
	pcb.add("line", layer="silk-top", x1=-body_w1/2, y1=body_h1/2-1.6, x2=-body_w1/2+1.6, y2=body_h1/2, width=0.2)
	pcb.add("rectangle", layer="courtyard-top", x=0.0, y=0.0, width=body_w1+1.0, height=body_h1+1.0, outline=0.1)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=body_w1, height=body_h1)
	pcb.add("rectangle", layer="mech2-top", x=0.0, y=0.0, width=body_w2, height=body_h2)
	for i in range(cols):
		xx = col_pitch * (i - (cols - 1) / 2)
		pcb.add("rectangle", layer="mech2-top", x=xx, y=-row_pitch/2, width=pin_w, height=pin_h)
		pcb.add("rectangle", layer="mech2-top", x=xx, y= row_pitch/2, width=pin_w, height=pin_h)
	return pcb

@component
def connector_samtec_fmc_hpc(mask=0.1, paste=0.1):
	pcb = alterpcb_core.Pcb()
	(rows, cols, row_pitch, col_pitch, pad_diameter) = (10, 40, 1.27, 1.27, 0.635)
	for i in range(rows):
		for j in range(cols):
			pcb.add("pad_circ_smd", x=col_pitch*(j-(cols-1)/2), y=row_pitch*(i-(rows-1)/2), diameter=pad_diameter, mask=mask, paste=paste)
	pcb.add("mechanical_hole", x=-2.141*25.4/2, y=-0.12*25.4, drill_diameter=1.27, hole_diameter=1.27+0.6)
	pcb.add("mechanical_hole", x= 2.141*25.4/2, y= 0.00*25.4, drill_diameter=1.27, hole_diameter=1.27+0.6)
	pcb.add("pad_circ_th", x=-31.5, y=-2.0, drill_diameter=3.2, outer_diameter=5.5, hole_diameter=5.2)
	pcb.add("pad_circ_th", x= 31.5, y=-2.0, drill_diameter=3.2, outer_diameter=5.5, hole_diameter=5.2)
	pcb.add("rectangle", layer="silk-top", x=0.0, y=0.0, width=2.196*25.4, height=0.578*25.4, outline=0.2)
	pcb.add("rectangle", layer="silk-top", x=(2.196+0.035)*25.4/2, y=0.0, width=0.035*25.4, height=0.060*25.4, outline=0.2)
	pcb.add("rectangle", layer="courtyard-top", x=0.45, y=0.0, width=58.7, height=16.7, outline=0.1)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=2.196*25.4, height=0.578*25.4)
	pcb.add("rectangle", layer="mech1-top", x=(2.196+0.035)*25.4/2, y=0.0, width=0.035*25.4, height=0.060*25.4)
	for i in range(rows):
		pcb.add("text", x=col_pitch*(cols/2+0.25), y=row_pitch*(i-(rows-1)/2), layer="mech2-top", text=alphabet[9-i], font="DejaVuSans", size=0.6, halign="center", valign="center", steps=4)
	for j in range(cols):
		pcb.add("text", x=col_pitch*(j-(cols-1)/2), y=row_pitch*(rows/2+0.25), layer="mech2-top", text=str(cols - j), font="DejaVuSans", size=0.6, halign="center", valign="center", steps=4)
	return pcb
