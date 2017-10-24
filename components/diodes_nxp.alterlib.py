import alterpcb_core

@component
def diode_nxp_sod882d():
	pcb = alterpcb_core.Pcb()
	pcb.add("chip_generic_parametric", package_w=1.0, package_h=0.6, courtyard_w=1.8, courtyard_h=1.2, pad_w=0.5, pad_h=0.7, pad_offset=0.4)
	return pcb
