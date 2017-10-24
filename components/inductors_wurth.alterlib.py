import alterpcb_core

@component
def inductor_wurth_rfh_1008():
	pcb = alterpcb_core.Pcb()
	pcb.add("chip_generic_parametric", package_w=2.6, package_h=2.1, courtyard_w=3.8, courtyard_h=2.8, pad_w=1.0, pad_h=2.2, pad_offset=1.1)
	return pcb
