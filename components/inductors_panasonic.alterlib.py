import alterpcb_core

@component
def inductor_panasonic_ell8tp():
	pcb = alterpcb_core.Pcb()
	pcb.add("pad_rect_smd", x=2.9, y=2.9, width=3.0, height=1.65, angle=-45.0)
	pcb.add("pad_rect_smd", x=-2.9, y=-2.9, width=3.0, height=1.65, angle=-45.0)
	pcb.add("rectangle", layer="courtyard-top", x=0.0, y=0.0, width=9.0, height=9.0, outline=0.1)
	pcb.add("polygon", layer="silk-top", x=[-1.3,  4.0,  4.0], y=[-4.0, -4.0,  1.3], closed=False, outline=0.2)
	pcb.add("polygon", layer="silk-top", x=[ 1.3, -4.0, -4.0], y=[ 4.0,  4.0, -1.3], closed=False, outline=0.2)
	#pcb.add("rectangle", layer="silk-top", x=0.0, y=0.0, width=9.0, height=9.0, outline=0.2)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=8.0, height=8.0)
	return pcb
