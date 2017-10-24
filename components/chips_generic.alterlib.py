import alterpcb_core

@component
def chip_generic_parametric(package_w=2.0, package_h=1.0, courtyard_w=4.0, courtyard_h=2.0, pad_w=1.4, pad_h=1.4, pad_offset=1.0, mask=0.1, silk=True):
	pcb = alterpcb_core.Pcb()
	pcb.add("pad_rect_smd", x=-pad_offset, y=0.0, width=pad_w, height=pad_h, mask=mask)
	pcb.add("pad_rect_smd", x= pad_offset, y=0.0, width=pad_w, height=pad_h, mask=mask)
	pcb.add("rectangle", layer="courtyard-top", x=0.0, y=0.0, width=courtyard_w, height=courtyard_h, outline=0.1)
	if silk:
		pcb.add("rectangle", layer="silk-top", x=0.0, y=0.0, width=courtyard_w, height=courtyard_h, outline=0.2)
	pcb.add("rectangle", layer="mech1-top", x=0.0, y=0.0, width=package_w, height=package_h)
	return pcb

# IPC standard footprints
#@component
#def chip_generic_0201():
	#return chip_generic_parametric(0.60, 0.30, 1.42, 0.72, 0.46, 0.42, 0.33)
#@component
#def chip_generic_0402():
	#return chip_generic_parametric(1.00, 0.50, 1.84, 0.92, 0.57, 0.62, 0.48)
#@component
#def chip_generic_0603():
	#return chip_generic_parametric(1.60, 0.80, 3.10, 1.50, 0.95, 1.00, 0.80)
#@component
#def chip_generic_0805():
	#return chip_generic_parametric(2.00, 1.25, 3.40, 2.00, 1.00, 1.45, 0.95)
#@component
#def chip_generic_1206():
	#return chip_generic_parametric(3.20, 1.60, 4.60, 2.30, 1.15, 1.80, 1.45)
#@component
#def chip_generic_1210():
	#return chip_generic_parametric(3.20, 2.50, 4.60, 3.20, 1.15, 2.70, 1.45)

@component
def chip_generic_0201(mask=0.1, silk=True):
	return chip_generic_parametric(0.60, 0.30, 1.40, 0.80, 0.40, 0.40, 0.30, mask=mask, silk=silk)
@component
def chip_generic_0402(mask=0.1, silk=True):
	return chip_generic_parametric(1.00, 0.50, 2.00, 1.00, 0.60, 0.60, 0.50, mask=mask, silk=silk)
@component
def chip_generic_0603(mask=0.1, silk=True):
	return chip_generic_parametric(1.60, 0.80, 3.20, 1.60, 1.00, 1.00, 0.80, mask=mask, silk=silk)
@component
def chip_generic_0805(mask=0.1, silk=True):
	return chip_generic_parametric(2.00, 1.25, 3.60, 2.00, 1.20, 1.40, 0.90, mask=mask, silk=silk)
@component
def chip_generic_1206(mask=0.1, silk=True):
	return chip_generic_parametric(3.20, 1.60, 4.80, 2.40, 1.40, 1.80, 1.40, mask=mask, silk=silk)
@component
def chip_generic_1210(mask=0.1, silk=True):
	return chip_generic_parametric(3.20, 2.50, 4.80, 3.40, 1.40, 2.80, 1.40, mask=mask, silk=silk)
