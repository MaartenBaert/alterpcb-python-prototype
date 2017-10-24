import alterpcb_core

# TODO give components access to layer stack
layers_copper = ["copper1-top", "copper1-bot", "copper2-top", "copper2-bot"]

@component
def solder_jumper():
	pcb = alterpcb_core.Pcb()
	pcb.add("pad_oval_smd", x=-0.4, y=0.0, width=0.5, height=1.0)
	pcb.add("pad_oval_smd", x= 0.4, y=0.0, width=0.5, height=1.0)
	return pcb

@component
def mounting_hole_m25(layers_pad=["copper1-top", "copper1-bot"]):
	pcb = alterpcb_core.Pcb()
	pcb.add("pad_rect_th", x=0.0, y=0.0, drill_diameter=2.7, width=5.0, height=5.0, hole_diameter=4.2, layers_pad=layers_pad)
	for layer in layers_copper:
		if layer not in layers_pad:
			pcb.add("rectangle", layer=layer, x=0.0, y=0.0, width=6.0, height=6.0, hole=True, order=-1)
	for sx in [-1, 1]:
		for sy in [-1, 1]:
			pcb.add("via", x=sx*1.9, y=sy*1.9, drill_diameter=0.8, outer_diameter=1.2, inner_diameter=1.2, hole_diameter=1.6, layers_pad=layers_pad)
	return pcb

@component
def mark_copper_2(size=2.0):
	pcb = alterpcb_core.Pcb()
	pcb.add("rectangle", layer="mask-top", x=0.0, y=0.0, width=2.6*size, height=size, hole=True, order=-1)
	pcb.add("rectangle", layer="mask-bot", x=0.0, y=0.0, width=2.6*size, height=size, hole=True, order=-1)
	pcb.add("text", x=0.0, y=0.0, mirror=False, layer="copper1-top", text="TOP", font="DejaVuSans-Bold", size=size, halign="center", valign="center", spacing=0.05)
	pcb.add("text", x=0.0, y=0.0, mirror=True , layer="copper1-bot", text="BOT", font="DejaVuSans-Bold", size=size, halign="center", valign="center", spacing=0.05)
	return pcb

@component
def mark_copper_4(size=2.0):
	pcb = alterpcb_core.Pcb()
	pcb.add("rectangle", layer="mask-top", x=0.0, y=0.0, width=2.6*size, height=size, hole=True, order=-1)
	pcb.add("rectangle", layer="mask-bot", x=0.0, y=0.0, width=2.6*size, height=size, hole=True, order=-1)
	pcb.add("rectangle", layer="copper2-top", x=0.0, y=0.0, width=2.6*size, height=size, hole=True, order=-1)
	pcb.add("rectangle", layer="copper2-bot", x=0.0, y=0.0, width=2.6*size, height=size, hole=True, order=-1)
	pcb.add("text", x=-0.9*size, y=0.0, mirror=False, layer="copper1-top", text="1", font="DejaVuSans-Bold", size=0.9*size, halign="center", valign="center", spacing=0.05)
	pcb.add("text", x=-0.3*size, y=0.0, mirror=False, layer="copper2-top", text="2", font="DejaVuSans-Bold", size=0.9*size, halign="center", valign="center", spacing=0.05)
	pcb.add("text", x= 0.3*size, y=0.0, mirror=True , layer="copper2-bot", text="3", font="DejaVuSans-Bold", size=0.9*size, halign="center", valign="center", spacing=0.05)
	pcb.add("text", x= 0.9*size, y=0.0, mirror=True , layer="copper1-bot", text="4", font="DejaVuSans-Bold", size=0.9*size, halign="center", valign="center", spacing=0.05)
	return pcb
