import alterpcb_core

@component
def ic_generic_dfn(package_w=6.0, package_h=6.0, center_w=4.6, center_h=4.6, pad_w=0.3, pad_l=0.8,
		pad_offset=3.0, pad_pitch=0.5, pad_num=10, center_mask=0.1, pad_mask=0.1, center_paste=-0.15, pad_paste=-0.025, silk=True):
	pcb = alterpcb_core.Pcb()
	pcb.add("pad_rect_smd", x=0.0, y=0.0, width=center_w, height=center_h, mask=center_mask, paste=center_paste)
	for i in range(pad_num):
		pcb.add("pad_oval_smd", y=pad_pitch*(i-(pad_num-1)/2), x=-pad_offset, height=pad_w, width=pad_l, mask=pad_mask, paste=pad_paste)
		pcb.add("pad_oval_smd", y=pad_pitch*(i-(pad_num-1)/2), x= pad_offset, height=pad_w, width=pad_l, mask=pad_mask, paste=pad_paste)
	pcb.add("rectangle", layer="courtyard-top", x=0.0, y=0.0, width=package_w+1.4, height=package_h+1.0, outline=0.1)
	if silk:
		pcb.add("rectangle", layer="silk-top", x=0.0, y=0.0, width=package_w+1.4, height=package_h+1.0, outline=0.2)
		pcb.add("circle", layer="silk-top", x=-package_w/2-0.2, y=package_h/2, radius=0.2)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=package_w, height=package_h)
	return pcb

@component
def ic_generic_dfn_rect(package_w=6.0, package_h=6.0, center_w=4.6, center_h=4.6, pad_w=0.3, pad_l=0.8,
		pad_offset=3.0, pad_pitch=0.5, pad_num=10, center_mask=0.1, pad_mask=0.1, center_paste=-0.15, pad_paste=-0.025, silk=True):
	pcb = alterpcb_core.Pcb()
	pcb.add("pad_rect_smd", x=0.0, y=0.0, width=center_w, height=center_h, mask=center_mask, paste=center_paste)
	for i in range(pad_num):
		pcb.add("pad_rect_smd", y=pad_pitch*(i-(pad_num-1)/2), x=-pad_offset, height=pad_w, width=pad_l, mask=pad_mask, paste=pad_paste)
		pcb.add("pad_rect_smd", y=pad_pitch*(i-(pad_num-1)/2), x= pad_offset, height=pad_w, width=pad_l, mask=pad_mask, paste=pad_paste)
	pcb.add("rectangle", layer="courtyard-top", x=0.0, y=0.0, width=package_w+0.9, height=package_h+0.5, outline=0.1)
	if silk:
		pcb.add("rectangle", layer="silk-top", x=0.0, y=0.0, width=package_w+0.9, height=package_h+0.5, outline=0.2)
		#pcb.add("circle", layer="silk-top", x=-package_w/2, y=package_h/2+0.4, radius=0.2)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=package_w, height=package_h)
	return pcb

@component
def ic_generic_qfn(package_w=6.0, package_h=6.0, center_w=4.6, center_h=4.6, pad_w=0.3, pad_l=0.8,
		pad_offset_x=3.0, pad_offset_y=3.0, pad_pitch_x=0.5, pad_pitch_y=0.5, pad_num_x=10, pad_num_y=10,
#		via_pitch_x=1.2, via_pitch_y=1.2, via_num_x=4, via_num_y=4,
		paste_num=3,
		center_mask=0.1, pad_mask=0.1, center_paste=-0.15, pad_paste=-0.025):
	pcb = alterpcb_core.Pcb()
	pcb.add("pad_rect_smd", x=0.0, y=0.0, width=center_w, height=center_h, mask=center_mask, paste=None)
	#for i in range(via_num_y):
		#for j in range(via_num_x):
			#(vx, vy) = (via_pitch_x*(j-(via_num_x-1)/2), via_pitch_y*(i-(via_num_y-1)/2))
			# TODO: GND via here
	for i in range(paste_num):
		for j in range(paste_num):
			pcb.add("rectangle", layer="paste-top", x=center_w/paste_num*(j-(paste_num-1)/2), y=center_h/paste_num*(i-(paste_num-1)/2),
					width=center_w/paste_num+center_paste*2, height=center_h/paste_num+center_paste*2)
	for i in range(pad_num_x):
		pcb.add("pad_oval_smd", x=pad_pitch_x*(i-(pad_num_x-1)/2), y=-pad_offset_y, width=pad_w, height=pad_l, mask=pad_mask, paste=pad_paste)
		pcb.add("pad_oval_smd", x=pad_pitch_x*(i-(pad_num_x-1)/2), y= pad_offset_y, width=pad_w, height=pad_l, mask=pad_mask, paste=pad_paste)
	for i in range(pad_num_y):
		pcb.add("pad_oval_smd", y=pad_pitch_y*(i-(pad_num_y-1)/2), x=-pad_offset_x, height=pad_w, width=pad_l, mask=pad_mask, paste=pad_paste)
		pcb.add("pad_oval_smd", y=pad_pitch_y*(i-(pad_num_y-1)/2), x= pad_offset_x, height=pad_w, width=pad_l, mask=pad_mask, paste=pad_paste)
	pcb.add("rectangle", layer="courtyard-top", x=0.0, y=0.0, width=package_w+1.4, height=package_h+1.4, outline=0.1)
	pcb.add("rectangle", layer="silk-top", x=0.0, y=0.0, width=package_w+1.4, height=package_h+1.4, outline=0.2)
	pcb.add("circle", layer="silk-top", x=-package_w/2-0.2, y=package_h/2+0.2, radius=0.2)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=package_w, height=package_h)
	return pcb

@component
def ic_generic_dip(pins=8, row_pitch=2.54*3, pin_pitch=2.54, drill_diameter=1.0, outer_diameter=1.8, inner_diameter=1.8, hole_diameter=1.8):
	pcb = alterpcb_core.Pcb()
	for i in range(pins // 2):
		pcb.add("pad_circ_th", x=-row_pitch/2, y=pin_pitch*(i-(pins//2-1)/2), drill_diameter=drill_diameter, outer_diameter=outer_diameter, inner_diameter=inner_diameter, hole_diameter=hole_diameter)
		pcb.add("pad_circ_th", x= row_pitch/2, y=pin_pitch*(i-(pins//2-1)/2), drill_diameter=drill_diameter, outer_diameter=outer_diameter, inner_diameter=inner_diameter, hole_diameter=hole_diameter)
	sw = row_pitch - outer_diameter - 0.6
	sh =  pin_pitch * (pins // 2) - 1.0
	pcb.add("rectangle", layer="silk-top", x=0.0, y=0.0, width=sw, height=sh, outline=0.2)
	pcb.add("circle", layer="silk-top", x=-sw/2+0.5, y=sh/2-0.5, radius=0.2)
	pcb.add("arc", layer="silk-top", x=0.0, y=sh/2, radius=0.8, angle1=-180.0, angle2=0.0, width=0.2)
	pcb.add("rectangle", layer="courtyard-top", x=0.0, y=0.0, width=row_pitch+pin_pitch, height=pin_pitch*(pins//2), outline=0.1)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=row_pitch-0.4, height=pin_pitch*(pins//2)-0.8)
	return pcb

@component
def smd_dual_generic(package_w=3.9, package_h=4.9, pin_w=0.43, pin_l=1.05, pad_w=0.6, pad_l=1.6, pad_offset=2.7, pad_pitch=1.27, pad_num=4):
	pcb = alterpcb_core.Pcb()
	for i in range(pad_num):
		yy = pad_pitch * (i - (pad_num - 1) / 2)
		pcb.add("pad_oval_smd", x=-pad_offset, y=yy, width=pad_l, height=pad_w)
		pcb.add("pad_oval_smd", x= pad_offset, y=yy, width=pad_l, height=pad_w)
	sw = pad_offset * 2 - pad_l - 0.6
	sh = package_h - 0.2
	pcb.add("rectangle", layer="silk-top", x=0.0, y=0.0, width=sw, height=sh, outline=0.2)
	pcb.add("circle", layer="silk-top", x=-sw/2+0.5, y=sh/2-0.5, radius=0.2)
	pcb.add("rectangle", layer="courtyard-top", x=0.0, y=0.0, width=pad_offset*2+pad_l+0.6, height=pad_pitch*pad_num, outline=0.1)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=package_w, height=package_h)
	for i in range(pad_num):
		yy = pad_pitch * (i - (pad_num - 1) / 2)
		pcb.add("rectangle", layer="mech1-top", x=-package_w/2-pin_l/2, y=yy, width=pin_l, height=pin_w)
		pcb.add("rectangle", layer="mech1-top", x= package_w/2+pin_l/2, y=yy, width=pin_l, height=pin_w)
	return pcb

@component
def smd_dual_generic_center(package_w=3.9, package_h=4.9, center_w=2.8, center_h=4.0, pin_w=0.43, pin_l=1.05, pad_w=0.6, pad_l=1.6, pad_offset=2.7, pad_pitch=1.27, pad_num=4):
	pcb = alterpcb_core.Pcb()
	pcb.add("pad_rect_smd", x=0.0, y=0.0, width=center_w, height=center_h)
	for i in range(pad_num):
		yy = pad_pitch * (i - (pad_num - 1) / 2)
		pcb.add("pad_oval_smd", x=-pad_offset, y=yy, width=pad_l, height=pad_w)
		pcb.add("pad_oval_smd", x= pad_offset, y=yy, width=pad_l, height=pad_w)
	sw = pad_offset * 2 - pad_l - 0.6
	sh = package_h - 0.2
	pcb.add("circle", layer="silk-top", x=-pad_offset+pad_l/2+0.2, y=pad_pitch*(pad_num-1)/2+pad_w/2+0.2, radius=0.2)
	pcb.add("rectangle", layer="courtyard-top", x=0.0, y=0.0, width=pad_offset*2+pad_l+0.6, height=pad_pitch*pad_num, outline=0.1)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=package_w, height=package_h)
	for i in range(pad_num):
		yy = pad_pitch * (i - (pad_num - 1) / 2)
		pcb.add("rectangle", layer="mech1-top", x=-package_w/2-pin_l/2, y=yy, width=pin_l, height=pin_w)
		pcb.add("rectangle", layer="mech1-top", x= package_w/2+pin_l/2, y=yy, width=pin_l, height=pin_w)
	return pcb

#@component
#def soic_narrow(pins):
	#return smd_dual_generic(pins, 5.2, 1.27, 2.2, 0.6, 3.9, 1.27 * (pins // 2) - 0.18, 0.43, 1.05, 7.8, 1.27 * (pins // 2))

#@component
#def soic_wide(pins):
	#return smd_dual_generic(pins, 9.2, 1.27, 2.2, 0.6, 7.5, 1.27 * (pins // 2) - 0.18, 0.43, 1.05, 11.8, 1.27 * (pins // 2))
