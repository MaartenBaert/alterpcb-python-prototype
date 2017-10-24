import alterpcb_core

# TODO give components access to layer stack
layers_copper = ["copper1-top", "copper1-bot", "copper2-top", "copper2-bot"]

@component
def via(drill_diameter=0.3, outer_diameter=0.6, inner_diameter=0.6, hole_diameter=0.9, layers_pad=["copper1-top", "copper1-bot"]):
	pcb = alterpcb_core.Pcb()
	pcb.add("circle", layer="drill-plated", x=0.0, y=0.0, radius=drill_diameter/2, pad=True)
	for layer in layers_copper:
		if layer in layers_pad:
			if layer.startswith("copper1-"):
				pcb.add("circle", layer=layer, x=0.0, y=0.0, radius=outer_diameter/2, pad=True)
			else:
				pcb.add("circle", layer=layer, x=0.0, y=0.0, radius=inner_diameter/2, pad=True)
		else:
			pcb.add("circle", layer=layer, x=0.0, y=0.0, radius=hole_diameter/2, hole=True, order=-1, pad=True)
	return pcb

@component
def mechanical_hole(drill_diameter=1.0, hole_diameter=1.8, mask=0.1):
	pcb = alterpcb_core.Pcb()
	pcb.add("circle", layer="drill-unplated", x=0.0, y=0.0, radius=drill_diameter/2, pad=True)
	for layer in layers_copper:
		pcb.add("circle", layer=layer, x=0.0, y=0.0, radius=hole_diameter/2, hole=True, order=-1, pad=True)
	pcb.add("circle", layer="mask-top", x=0.0, y=0.0, radius=drill_diameter/2+mask, pad=True)
	pcb.add("circle", layer="mask-bot", x=0.0, y=0.0, radius=drill_diameter/2+mask, pad=True)
	return pcb

@component
def pad_circ_th(drill_diameter=1.0, outer_diameter=1.8, inner_diameter=1.8, hole_diameter=1.8, layers_pad=["copper1-top", "copper1-bot"], mask=0.1):
	pcb = alterpcb_core.Pcb()
	pcb.add("circle", layer="drill-plated", x=0.0, y=0.0, radius=drill_diameter/2, pad=True)
	for layer in layers_copper:
		if layer in layers_pad:
			if layer.startswith("copper1-"):
				pcb.add("circle", layer=layer, x=0.0, y=0.0, radius=outer_diameter/2, pad=True)
			else:
				pcb.add("circle", layer=layer, x=0.0, y=0.0, radius=inner_diameter/2, pad=True)
		else:
			pcb.add("circle", layer=layer, x=0.0, y=0.0, radius=hole_diameter/2, hole=True, order=-1, pad=True)
	pcb.add("circle", layer="mask-top", x=0.0, y=0.0, radius=outer_diameter/2+mask, pad=True)
	pcb.add("circle", layer="mask-bot", x=0.0, y=0.0, radius=outer_diameter/2+mask, pad=True)
	return pcb

@component
def pad_circ_smd(diameter=1.0, mask=0.1, paste=0.0):
	pcb = alterpcb_core.Pcb()
	pcb.add("circle", layer="copper1-top", x=0.0, y=0.0, radius=diameter/2, pad=True)
	pcb.add("circle", layer="mask-top", x=0.0, y=0.0, radius=diameter/2+mask, pad=True)
	if paste is not None:
		pcb.add("circle", layer="paste-top", x=0.0, y=0.0, radius=diameter/2+min(mask,0)+paste, pad=True)
	return pcb

@component
def pad_rect_th(drill_diameter=1.0, width=1.8, height=1.8, hole_diameter=1.8, layers_pad=["copper1-top", "copper1-bot"], mask=0.1):
	pcb = alterpcb_core.Pcb()
	pcb.add("circle", layer="drill-plated", x=0.0, y=0.0, radius=drill_diameter/2, pad=True)
	for layer in layers_copper:
		if layer in layers_pad:
			pcb.add("rectangle", layer=layer, x=0.0, y=0.0, width=width, height=height, pad=True)
		else:
			pcb.add("circle", layer=layer, x=0.0, y=0.0, radius=hole_diameter/2, hole=True, order=-1, pad=True)
	pcb.add("rectangle", layer="copper1-top", x=0.0, y=0.0, width=width, height=height, pad=True)
	pcb.add("rectangle", layer="copper1-bot", x=0.0, y=0.0, width=width, height=height, pad=True)
	pcb.add("rectangle", layer="mask-top", x=0.0, y=0.0, width=width+mask*2, height=height+mask*2, pad=True)
	pcb.add("rectangle", layer="mask-bot", x=0.0, y=0.0, width=width+mask*2, height=height+mask*2, pad=True)
	return pcb

@component
def pad_rect_smd(width=1.0, height=1.0, mask=0.1, paste=0.0):
	pcb = alterpcb_core.Pcb()
	pcb.add("rectangle", layer="copper1-top", x=0.0, y=0.0, width=width, height=height, pad=True)
	pcb.add("rectangle", layer="mask-top", x=0.0, y=0.0, width=width+mask*2, height=height+mask*2, pad=True)
	if paste is not None:
		pcb.add("rectangle", layer="paste-top", x=0.0, y=0.0, width=width+min(mask*2,0)+paste*2, height=height+min(mask*2,0)+paste*2, pad=True)
	return pcb

@component
def pad_oval_th(drill_diameter=1.0, width=1.8, height=1.8, hole_diameter=1.8, layers_pad=["copper1-top", "copper1-bot"], mask=0.1):
	pcb = alterpcb_core.Pcb()
	pcb.add("circle", layer="drill-plated", x=0.0, y=0.0, radius=drill_diameter/2, pad=True)
	for layer in layers_copper:
		if layer in layers_pad:
			pcb.add("oval", layer=layer, x=0.0, y=0.0, width=width, height=height, pad=True)
		else:
			pcb.add("circle", layer=layer, x=0.0, y=0.0, radius=hole_diameter/2, hole=True, order=-1, pad=True)
	pcb.add("oval", layer="copper1-top", x=0.0, y=0.0, width=width, height=height, pad=True)
	pcb.add("oval", layer="copper1-bot", x=0.0, y=0.0, width=width, height=height, pad=True)
	pcb.add("oval", layer="mask-top", x=0.0, y=0.0, width=width+mask*2, height=height+mask*2, pad=True)
	pcb.add("oval", layer="mask-bot", x=0.0, y=0.0, width=width+mask*2, height=height+mask*2, pad=True)
	return pcb

@component
def pad_oval_smd(width=1.0, height=1.0, mask=0.1, paste=0.0):
	pcb = alterpcb_core.Pcb()
	pcb.add("oval", layer="copper1-top", x=0.0, y=0.0, width=width, height=height, pad=True)
	pcb.add("oval", layer="mask-top", x=0.0, y=0.0, width=width+mask*2, height=height+mask*2, pad=True)
	if paste is not None:
		pcb.add("oval", layer="paste-top", x=0.0, y=0.0, width=width+min(mask*2,0)+paste*2, height=height+min(mask*2,0)+paste*2, pad=True)
	return pcb

@component
def pad_rect_smd_vias(width=2.0, height=2.0, rows=2, cols=2, row_pitch=1.0, col_pitch=1.0,
		drill_diameter=0.4, outer_diameter=1.0, inner_diameter=1.0, hole_diameter=1.0, layers_pad=["copper1-top", "copper1-bot"], merge=True):
	pcb = alterpcb_core.Pcb()
	for i in range(rows):
		for j in range(cols):
			pcb.add("via", x=col_pitch*(j-(cols-1)/2), y=row_pitch*(i-(rows-1)/2), drill_diameter=drill_diameter, outer_diameter=outer_diameter,
					inner_diameter=inner_diameter, hole_diameter=hole_diameter, layers_pad=layers_pad)
	for layer in layers_copper:
		if layer in layers_pad:
			if layer == "copper1-top":
				pcb.add("pad_rect_smd", x=0.0, y=0.0, flip=False, width=width, height=height, paste=None)
			elif layer == "copper1-bot":
				pcb.add("pad_rect_smd", x=0.0, y=0.0, flip=True, width=width, height=height, paste=None)
			elif merge:
				#pcb.add("rectangle", layer=layer, x=0.0, y=0.0, width=col_pitch*(cols-1)+inner_diameter, height=row_pitch*(rows-1)+inner_diameter, pad=True)
				pcb.add("rectangle", layer=layer, x=0.0, y=0.0, width=width, height=height, pad=True)
		elif merge:
			pcb.add("rectangle", layer=layer, x=0.0, y=0.0, width=col_pitch*(cols-1)+hole_diameter, height=row_pitch*(rows-1)+hole_diameter, hole=True, order=-1, pad=True)
	return pcb

@component
def via_array(width=2.0, height=2.0, rows=2, cols=2, row_pitch=1.0, col_pitch=1.0,
		drill_diameter=0.4, outer_diameter=1.0, inner_diameter=1.0, hole_diameter=1.0, layers_pad=["copper1-top", "copper1-bot"], merge=True):
	pcb = alterpcb_core.Pcb()
	for i in range(rows):
		for j in range(cols):
			pcb.add("via", x=col_pitch*(j-(cols-1)/2), y=row_pitch*(i-(rows-1)/2), drill_diameter=drill_diameter, outer_diameter=outer_diameter,
					inner_diameter=inner_diameter, hole_diameter=hole_diameter, layers_pad=layers_pad)
	if merge:
		for layer in layers_copper:
			if layer in layers_pad:
				pcb.add("rectangle", layer=layer, x=0.0, y=0.0, width=width, height=height)
			else:
				pcb.add("rectangle", layer=layer, x=0.0, y=0.0, width=col_pitch*(cols-1)+hole_diameter, height=row_pitch*(rows-1)+hole_diameter, hole=True, order=-1)
	return pcb
