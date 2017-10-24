import alterpcb_core

@component
def inductor_murata_lqh3np_1212():
	pcb = alterpcb_core.Pcb()
	pcb.add("chip_generic_parametric", package_w=3.0, package_h=3.0, courtyard_w=3.8, courtyard_h=3.8, pad_w=1.0, pad_h=3.2, pad_offset=1.0)
	return pcb

@component
def inductor_murata_lqh66s_2525():
	pcb = alterpcb_core.Pcb()
	pcb.add("chip_generic_parametric", package_w=6.3, package_h=6.3, courtyard_w=7.2, courtyard_h=7.2, pad_w=2.0, pad_h=3.8, pad_offset=2.0)
	return pcb
