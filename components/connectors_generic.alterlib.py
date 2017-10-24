import alterpcb_core

@component
def connector_generic_pin_header_vertical(rows=1, cols=4):
	(row_pitch, col_pitch) = (2.54, 2.54)
	pcb = alterpcb_core.Pcb()
	for i in range(rows):
		for j in range(cols):
			pcb.add("pad_circ_th", x=col_pitch*(j-(cols-1)/2), y=row_pitch*(i-(rows-1)/2), drill_diameter=1.0, outer_diameter=1.8, inner_diameter=1.8, hole_diameter=1.8)
	sw = col_pitch * cols
	sh = row_pitch * rows
	pcb.add("rectangle", layer="silk-top", x=0.0, y=0.0, width=sw, height=sh, outline=0.2)
	pcb.add("line", layer="silk-top", x1=-sw/2, y1=sh/2-0.8, x2=-sw/2+0.8, y2=sh/2, width=0.2)
	pcb.add("rectangle", layer="courtyard-top", x=0.0, y=0.0, width=col_pitch*cols+0.8, height=row_pitch*rows+0.8, outline=0.1)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=col_pitch*cols, height=row_pitch*rows)
	return pcb

@component
def connector_generic_sma_edge(w1=2.0, h1=4.0, w2=0.8, h2=3.5, w3=1.35, h3=2.75, s1=3.0, hole=True, hole_w=9.0, hole_h=5.0, edge_space=0.5):
	pcb = alterpcb_core.Pcb()
	pcb.add("pad_rect_smd", x=0.0, y=-edge_space-h2/2, width=w2, height=h2, paste=None)
	pcb.add("pad_rect_smd_vias", x=-s1, y=-edge_space-h1/2, width=w1, height=h1,
			rows=3, cols=2, row_pitch=1.6, col_pitch=1.2, drill_diameter=0.4, outer_diameter=0.8, inner_diameter=0.8, hole_diameter=1.2, layers_pad=["copper1-top", "copper1-bot", "copper2-top"])
	pcb.add("pad_rect_smd_vias", x=s1, y=-edge_space-h1/2, width=w1, height=h1,
			rows=3, cols=2, row_pitch=1.6, col_pitch=1.2, drill_diameter=0.4, outer_diameter=0.8, inner_diameter=0.8, hole_diameter=1.2, layers_pad=["copper1-top", "copper1-bot", "copper2-top"])
	if hole:
		pcb.add("rectangle", layer="copper2-top", x=0.0, y=-edge_space-h2+h3/2, width=w3, height=h3, hole=True)
		pcb.add("rectangle", layer="copper2-bot", x=0.0, y=-hole_h/2, width=hole_w, height=hole_h, hole=True)
	return pcb

@component
def connector_multicomp_sma_edge():
	return connector_generic_sma_edge(w1=2.0, h1=4.0, w2=0.8, h2=3.5, w3=1.35, h3=2.75, s1=3.0, hole_w=9.0, hole_h=5.0, edge_space=0.5)

@component
def connector_generic_sma_edge_cde(w1=3.0, h1=4.0, w2=0.8, h2=3.5, w3=1.35, h3=2.75, s1=3.5, hole=True, hole_w=11.0, hole_h=5.0, edge_space=0.5):
	pcb = alterpcb_core.Pcb()
	pcb.add("pad_rect_smd", x=0.0, y=-edge_space-h2/2, width=w2, height=h2, paste=None)
	pcb.add("pad_rect_smd", x=-s1, y=-edge_space-h1/2, width=w1, height=h1, paste=None)
	pcb.add("pad_rect_smd", x=s1, y=-edge_space-h1/2, width=w1, height=h1, paste=None)
	if hole:
		pcb.add("rectangle", layer="copper1-bot", x=0.0, y=-edge_space-h2+h3/2, width=w3, height=h3, hole=True)
	return pcb

@component
def connector_multicomp_sma_edge_cde():
	return connector_generic_sma_edge_cde(w1=3.0, h1=4.0, w2=0.8, h2=3.5, w3=1.35, h3=2.75, s1=3.5, hole=True, hole_w=11.0, hole_h=5.0, edge_space=0.5)
