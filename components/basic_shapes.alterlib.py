import alterpcb_core

import math
import numpy

def transform_line(shape, xfrom, yfrom, xto, yto, angle, flip, mirror):
	shape = shape.copy()
	(shape["x1"], shape["y1"]) = alterpcb_core.transform_point(shape["x1"], shape["y1"], xfrom, yfrom, xto, yto, angle, flip, mirror)
	(shape["x2"], shape["y2"]) = alterpcb_core.transform_point(shape["x2"], shape["y2"], xfrom, yfrom, xto, yto, angle, flip, mirror)
	if flip:
		shape["layer"] = alterpcb_core.flip_layer(shape["layer"])
	return shape

def transform_arc(shape, xfrom, yfrom, xto, yto, angle, flip, mirror):
	shape = shape.copy()
	(shape["x"], shape["y"]) = alterpcb_core.transform_point(shape["x"], shape["y"], xfrom, yfrom, xto, yto, angle, flip, mirror)
	if flip != mirror:
		d = shape["angle2"] - shape["angle1"]
		shape["angle1"] = (angle - shape["angle1"] + 180.0) % 360.0
		shape["angle2"] = shape["angle1"] - d
	else:
		d = shape["angle2"] - shape["angle1"]
		shape["angle1"] = (angle + shape["angle1"]) % 360.0
		shape["angle2"] = shape["angle1"] + d
	if flip:
		shape["layer"] = alterpcb_core.flip_layer(shape["layer"])
	return shape

def transform_path(shape, xfrom, yfrom, xto, yto, angle, flip, mirror):
	shape = shape.copy()
	(px, py) = alterpcb_core.equalize_arrays(shape["x"], shape["y"])
	(px, py) = alterpcb_core.transform_point(px, py, xfrom, yfrom, xto, yto, angle, flip, mirror)
	(shape["x"], shape["y"]) = (list(px), list(py))
	if flip != mirror:
		if type(shape["width"]) == list:
			shape["width"] = shape["width"][::-1]
		if type(shape["space"]) == list:
			shape["space"] = shape["space"][::-1]
		shape["centerline"] = -shape["centerline"]
	if flip:
		shape["layer"] = alterpcb_core.flip_layer(shape["layer"])
	return shape

def snap_line(shape, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle):
	shape = shape.copy()
	(shape["x1"], shape["y1"]) = alterpcb_core.snap_point(shape["x1"], shape["y1"], grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
	(shape["x2"], shape["y2"]) = alterpcb_core.snap_point(shape["x2"], shape["y2"], grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
	return shape

def snap_arc(shape, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle):
	shape = shape.copy()
	(shape["x"], shape["y"]) = alterpcb_core.snap_point(shape["x"], shape["y"], grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
	shape["radius"] = alterpcb_core.snap_value(shape["radius"], grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
	return shape

def snap_path(shape, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle):
	shape = shape.copy()
	(px, py) = alterpcb_core.equalize_arrays(shape["x"], shape["y"])
	(px, py) = alterpcb_core.snap_point(px, py, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
	(shape["x"], shape["y"]) = (list(px), list(py))
	return shape

def handles_line(shape):
	return [
		{"x": shape["x1"], "y": shape["y1"]},
		{"x": shape["x2"], "y": shape["y2"]},
	]

def handles_path(shape):
	return [{"x": shape["x"][i], "y": shape["y"][i]} for i in range(min(len(shape["x"]), len(shape["y"])))]

def handlemove_line(shape, index, x, y):
	shape = shape.copy()
	if index == 0:
		shape["x1"] = x
		shape["y1"] = y
	else:
		shape["x2"] = x
		shape["y2"] = y
	return shape

def handlemove_path(shape, index, x, y):
	shape = shape.copy()
	shape["x"] = shape["x"].copy()
	shape["y"] = shape["y"].copy()
	shape["x"][index] = x
	shape["y"][index] = y
	return shape

def decasteljau(x, py):
	x = numpy.array(x)
	d = numpy.array(py)[:,None]
	while len(d) > 1:
		d = d[:-1] + (d[1:] - d[:-1]) * x[None,:]
	return d[0]

def normalize(vx, vy):
	d = numpy.hypot(vx, vy)
	with numpy.errstate(divide='ignore', invalid='ignore'):
		return (numpy.nan_to_num(vx / d), numpy.nan_to_num(vy / d))

def shift_path1(pathx, pathy, tx1, ty1, tx2, ty2, shift):
	assert(len(pathx) == len(pathy))
	assert(len(pathx) >= 2)
	qx = numpy.zeros(len(pathx))
	qy = numpy.zeros(len(pathx))
	
	# begin cap
	qx[0] = pathx[0] - ty1 * shift[0]
	qy[0] = pathy[0] + tx1 * shift[0]
	
	# end cap
	qx[-1] = pathx[-1] - ty2 * shift[-1]
	qy[-1] = pathy[-1] + tx2 * shift[-1]
	
	# middle part
	(vx1, vy1) = normalize(pathx[1:-1] - pathx[:-2], pathy[1:-1] - pathy[:-2])
	(vx2, vy2) = normalize(pathx[2:] - pathx[1:-1], pathy[2:] - pathy[1:-1])
	d = numpy.maximum(0.2, 1.0 + vx1 * vx2 + vy1 * vy2)
	nx = (vy1 + vy2) / d
	ny = -(vx1 + vx2) / d
	qx[1:-1] = pathx[1:-1] - nx * shift[1:-1]
	qy[1:-1] = pathy[1:-1] - ny * shift[1:-1]
	
	return (qx, qy)

def shift_path2(pathx, pathy, tx1, ty1, tx2, ty2, shift):
	assert(len(pathx) == len(pathy))
	assert(len(pathx) >= 2)
	qx = numpy.zeros(len(pathx))
	qy = numpy.zeros(len(pathx))
	
	# begin cap
	qx[0] = pathx[0] - ty1 * shift[0]
	qy[0] = pathy[0] + tx1 * shift[0]
	
	# end cap
	qx[-1] = pathx[-1] - ty2 * shift[-1]
	qy[-1] = pathy[-1] + tx2 * shift[-1]
	
	# middle part
	#(vx1, vy1) = normalize(qx[1:-1] - qx[:-2], qy[1:-1] - qy[:-2])
	#(vx2, vy2) = normalize(qx[2:] - qx[1:-1], qy[2:] - qy[1:-1])
	#d = numpy.maximum(0.2, 1.0 + vx1 * vx2 + vy1 * vy2)
	#nx = (vy1 + vy2) / d
	#ny = -(vx1 + vx2) / d
	#qx[1:-1] = pathx[1:-1] + nx * shift[1:-1]
	#qy[1:-1] = pathy[1:-1] + ny * shift[1:-1]
	alpha = numpy.arcsin(numpy.clip((shift[1:] - shift[:-1]) / numpy.hypot(pathx[1:] - pathx[:-1], pathy[1:] - pathy[:-1]), -1.0, 1.0))
	beta = numpy.arctan2(pathy[1:] - pathy[:-1], pathx[1:] - pathx[:-1])
	gamma = (beta[1:] - beta[:-1]) - numpy.round((beta[1:] - beta[:-1]) / (2 * math.pi)) * (2 * math.pi)
	r = shift[1:-1] / numpy.maximum(0.1, numpy.cos((alpha[:-1] - alpha[1:]) / 2))
	qx[1:-1] = pathx[1:-1] - numpy.sin(beta[:-1] + (gamma + alpha[:-1] + alpha[1:]) / 2) * r
	qy[1:-1] = pathy[1:-1] + numpy.cos(beta[:-1] + (gamma + alpha[:-1] + alpha[1:]) / 2) * r
	#px4 = pathx[1:-1] + numpy.sin(beta[:-1] + (gamma - alpha[:-1] - alpha[1:]) / 2) * r
	#py4 = pathy[1:-1] - numpy.cos(beta[:-1] + (gamma - alpha[:-1] - alpha[1:]) / 2) * r
	
	return (qx, qy)

def stroke_path(pathx, pathy, tx1, ty1, tx2, ty2, width, shift, steps=18):
	assert(len(pathx) == len(pathy))
	assert(len(pathx) >= 2)
	
	#(pathx, pathy) = shift_path(pathx, pathy, tx1, ty1, tx2, ty2, shift)
	(ptx1, pty1) = normalize(pathx[ 1] - pathx[ 0], pathy[ 1] - pathy[ 0])
	(ptx2, pty2) = normalize(pathx[-1] - pathx[-2], pathy[-1] - pathy[-2])
	
	px1 = numpy.zeros(steps + 1)
	py1 = numpy.zeros(steps + 1)
	px2 = numpy.zeros(len(pathx) - 2)
	py2 = numpy.zeros(len(pathx) - 2)
	px3 = numpy.zeros(steps + 1)
	py3 = numpy.zeros(steps + 1)
	px4 = numpy.zeros(len(pathx) - 2)
	py4 = numpy.zeros(len(pathx) - 2)
	
	alpha = numpy.arcsin(numpy.clip((width[1:] - width[:-1]) / (2 * numpy.hypot(pathx[1:] - pathx[:-1], pathy[1:] - pathy[:-1])), -1.0, 1.0))
	beta = numpy.arctan2(pathy[1:] - pathy[:-1], pathx[1:] - pathx[:-1])
	gamma = (beta[1:] - beta[:-1]) - numpy.round((beta[1:] - beta[:-1]) / (2 * math.pi)) * (2 * math.pi)
	
	#print("width = " + str(width))
	#print("alpha = " + str(alpha))
	#print("beta  = " + str(beta ))
	#print("gamma = " + str(gamma))
	
	# begin cap
	t = (numpy.arange(steps + 1) / (steps) - 0.5) * (math.pi - 2 * alpha[0])
	px1 = pathx[0] - ptx1 * width[0] / 2 * numpy.cos(t) - pty1 * width[0] / 2 * numpy.sin(t)
	py1 = pathy[0] - pty1 * width[0] / 2 * numpy.cos(t) + ptx1 * width[0] / 2 * numpy.sin(t)
	
	# end cap
	t = (numpy.arange(steps + 1) / (steps) - 0.5) * (math.pi + 2 * alpha[-1])
	px3 = pathx[-1] + ptx2 * width[-1] / 2 * numpy.cos(t) + pty2 * width[-1] / 2 * numpy.sin(t)
	py3 = pathy[-1] + pty2 * width[-1] / 2 * numpy.cos(t) - ptx2 * width[-1] / 2 * numpy.sin(t)
	
	# middle part
	r = width[1:-1] / (2 * numpy.maximum(0.1, numpy.cos((alpha[:-1] - alpha[1:]) / 2)))
	px2 = pathx[1:-1] - numpy.sin(beta[:-1] + (gamma + alpha[:-1] + alpha[1:]) / 2) * r
	py2 = pathy[1:-1] + numpy.cos(beta[:-1] + (gamma + alpha[:-1] + alpha[1:]) / 2) * r
	px4 = pathx[1:-1] + numpy.sin(beta[:-1] + (gamma - alpha[:-1] - alpha[1:]) / 2) * r
	py4 = pathy[1:-1] - numpy.cos(beta[:-1] + (gamma - alpha[:-1] - alpha[1:]) / 2) * r
	
	#(vx1, vy1) = normalize(pathx[1:-1] - pathx[ :-2], pathy[1:-1] - pathy[ :-2])
	#(vx2, vy2) = normalize(pathx[2:  ] - pathx[1:-1], pathy[2:  ] - pathy[1:-1])
	#d = 1 + vx1 * vx2 + vy1 * vy2
	#nx = (vy1 + vy2) / d
	#ny = -(vx1 + vx2) / d
	#aa = steps1 // 2
	#bb = steps1 // 2 + steps2 // 2 + len(pathx) - 1
	#px2 = pathx[1:-1] - nx * width[1:-1] / 2
	#py2 = pathy[1:-1] - ny * width[1:-1] / 2
	#px4 = pathx[1:-1] + nx * width[1:-1] / 2
	#py4 = pathy[1:-1] + ny * width[1:-1] / 2
	
	return (numpy.concatenate((px1, px2, px3, px4[::-1])), numpy.concatenate((py1, py2, py3, py4[::-1])))

def array_extend(arr, n):
	#if type(arr) != list:
	#	arr = [arr]
	res = zeros(n)
	res[:len(arr)] = arr
	res[len(arr):] = arr[-1]
	return res

def maybe_list(x, i):
	if type(x) == list:
		return x[min(i, len(x) - 1)]
	else:
		return x

@component(transform=transform_line, snap=snap_line, handles=handles_line, handlemove=handlemove_line)
def line(layer="copper1-top", x1=0.0, y1=0.0, x2=1.0, y2=1.0, width=1.0, hole=False, order=0):
	pcb = alterpcb_core.Pcb()
	pcb.add("polygon", layer=layer, x=[x1, x2], y=[y1, y2], closed=False, outline=width, hole=hole, order=order)
	return pcb

@component(transform=transform_arc, snap=snap_arc)
def arc(layer="copper1-top", x=0.0, y=0.0, radius=4.0, angle1=0.0, angle2=90.0, width=1.0, hole=False, order=0):
	pcb = alterpcb_core.Pcb()
	steps = max(2, 1 + int(round(abs(angle1 - angle2) / alterpcb_core.circle_step)))
	angle = numpy.linspace(angle1 * math.pi / 180, angle2 * math.pi / 180, steps)
	pcb.add("polygon", layer=layer, x=list(x+radius*numpy.cos(angle)), y=list(y+radius*numpy.sin(angle)), closed=False, outline=width, hole=hole, order=order)
	return pcb

@component(transform=alterpcb_core.transform_rectangle, snap=alterpcb_core.snap_rectangle, handles=alterpcb_core.handles_rectangle, handlemove=alterpcb_core.handlemove_rectangle)
def oval(layer="copper1-top", x=0.0, y=0.0, width=2.0, height=1.0, angle=0.0, outline=0.0, hole=False, order=0, pad=False):
	pcb = alterpcb_core.Pcb()
	width = abs(width)
	height = abs(height)
	s = math.sin(math.radians(angle))
	c = math.cos(math.radians(angle))
	if width > height:
		if outline == 0.0:
			pcb.add("rectangle", layer=layer, x=x, y=y, width=width-height, height=height, angle=angle, outline=outline, hole=hole, order=order, pad=pad)
			pcb.add("circle", layer=layer, x=x-c*(width-height)/2, y=y-s*(width-height)/2, radius=height/2, outline=outline, hole=hole, order=order, pad=pad)
			pcb.add("circle", layer=layer, x=x+c*(width-height)/2, y=y+s*(width-height)/2, radius=height/2, outline=outline, hole=hole, order=order, pad=pad)
		else:
			pcb.add("line", layer=layer, x1=x-c*(width-height)/2-s*height/2, y1=y-s*(width-height)/2+c*height/2, x2=x+c*(width-height)/2-s*height/2, y2=y+s*(width-height)/2+c*height/2, width=outline, hole=hole, order=order)
			pcb.add("line", layer=layer, x1=x-c*(width-height)/2+s*height/2, y1=y-s*(width-height)/2-c*height/2, x2=x+c*(width-height)/2+s*height/2, y2=y+s*(width-height)/2-c*height/2, width=outline, hole=hole, order=order)
			pcb.add("arc", layer=layer, x=x-c*(width-height)/2, y=y-s*(width-height)/2, radius=height/2, angle1=angle+90.0, angle2=angle+270.0, width=outline, hole=hole, order=order)
			pcb.add("arc", layer=layer, x=x+c*(width-height)/2, y=y+s*(width-height)/2, radius=height/2, angle1=angle-90.0, angle2=angle+90.0, width=outline, hole=hole, order=order)
	elif width < height:
		if outline == 0.0:
			pcb.add("rectangle", layer=layer, x=x, y=y, width=width, height=height-width, angle=angle, outline=outline, hole=hole, order=order, pad=pad)
			pcb.add("circle", layer=layer, x=x-s*(height-width)/2, y=y+c*(height-width)/2, radius=width/2, outline=outline, hole=hole, order=order, pad=pad)
			pcb.add("circle", layer=layer, x=x+s*(height-width)/2, y=y-c*(height-width)/2, radius=width/2, outline=outline, hole=hole, order=order, pad=pad)
		else:
			pcb.add("line", layer=layer, x1=x-s*(height-width)/2-c*width/2, y1=y+c*(height-width)/2-s*width/2, x2=x+s*(height-width)/2-c*width/2, y2=y-c*(height-width)/2-s*width/2, width=outline, hole=hole, order=order)
			pcb.add("line", layer=layer, x1=x-s*(height-width)/2+c*width/2, y1=y+c*(height-width)/2+s*width/2, x2=x+s*(height-width)/2+c*width/2, y2=y-c*(height-width)/2+s*width/2, width=outline, hole=hole, order=order)
			pcb.add("arc", layer=layer, x=x-s*(height-width)/2, y=y+c*(height-width)/2, radius=width/2, angle1=angle, angle2=angle+180.0, width=outline, hole=hole, order=order)
			pcb.add("arc", layer=layer, x=x+s*(height-width)/2, y=y-c*(height-width)/2, radius=width/2, angle1=angle-180.0, angle2=angle, width=outline, hole=hole, order=order)
	else:
		pcb.add("circle", layer=layer, x=x, y=y, radius=width/2, outline=outline, hole=hole, order=order, pad=pad)
	return pcb

@component(transform=transform_path, snap=snap_path, handles=handles_path, handlemove=handlemove_path)
def path(layer="copper1-top", x=[0.0, 0.0, 1.0, 1.0], y=[0.0, 1.0, 2.0, 3.0], width=[1.0], space=[], steps=16, centerline=0, hole=False, order=0):
	pcb = alterpcb_core.Pcb()
	(px, py) = alterpcb_core.equalize_arrays(x, y)
	if len(px) < 2:
		return pcb
	t = numpy.arange(steps + 1) / steps
	pathx = decasteljau(t, px)
	pathy = decasteljau(t, py)
	(tx1, ty1) = normalize(px[ 1] - px[ 0], py[ 1] - py[ 0])
	(tx2, ty2) = normalize(px[-1] - px[-2], py[-1] - py[-2])
	tracks = min(len(width), len(space) + 1)
	if tracks < 1:
		return pcb
	path_width = [decasteljau(t, w) if type(w) == list else numpy.repeat(w, steps + 1) for w in width]
	path_space = [decasteljau(t, s) if type(s) == list else numpy.repeat(s, steps + 1) for s in space]
	
	#span = numpy.zeros(steps + 1)
	#for track in range(tracks):
		#span += path_width[track]
		#if track != tracks - 1:
			#span += path_space[track]
	#path_shift = -span / 2
	#for track in range(tracks):
		#path_shift += path_width[track] / 2
		#(qx, qy) = shift_path(pathx, pathy, tx1, ty1, tx2, ty2, path_shift)
		#for i in range(len(qx)):
			#pcb.add("circle", layer=layer, x=qx[i], y=qy[i], radius=path_width[track][i]/2, hole=hole, order=order)
		##(qx, qy) = stroke_path(pathx, pathy, tx1, ty1, tx2, ty2, path_width[track], path_shift)
		##pcb.add("polygon", layer=layer, x=list(qx), y=list(qy), closed=True, hole=hole, order=order)
		#path_shift += path_width[track] / 2
		#if track != tracks - 1:
			#path_shift += path_space[track]
	
	#(qx, qy) = shift_path(pathx, pathy, tx1, ty1, tx2, ty2, path_shift)
	
	# center line
	ci = max(0, min(tracks * 4 - 2, centerline + tracks * 2 - 1))
	if ci % 4 == 1:
		(rx, ry) = stroke_path(pathx, pathy, tx1, ty1, tx2, ty2, path_width[ci // 4], numpy.zeros(steps + 1))
		pcb.add("polygon", layer=layer, x=list(rx), y=list(ry), closed=True, hole=hole, order=order)
	
	# positive side
	(qx, qy) = (pathx, pathy)
	for ii in range(ci, tracks * 4 - 3):
		if ii % 4 == 0:
			(qx, qy) = shift_path1(qx, qy, tx1, ty1, tx2, ty2, path_width[ii // 4] / 2)
			(rx, ry) = stroke_path(qx, qy, tx1, ty1, tx2, ty2, path_width[ii // 4], numpy.zeros(steps + 1))
			pcb.add("polygon", layer=layer, x=list(rx), y=list(ry), closed=True, hole=hole, order=order)
		elif ii % 4 == 1:
			(qx, qy) = shift_path2(qx, qy, tx1, ty1, tx2, ty2, path_width[ii // 4] / 2)
		elif ii % 4 == 2:
			(qx, qy) = shift_path1(qx, qy, tx1, ty1, tx2, ty2, path_space[ii // 4] / 2)
		else:
			(qx, qy) = shift_path2(qx, qy, tx1, ty1, tx2, ty2, path_space[ii // 4] / 2)
	
	# negative size
	(qx, qy) = (pathx, pathy)
	for ii in range(ci, 1, -1):
		if ii % 4 == 0:
			(qx, qy) = shift_path1(qx, qy, tx1, ty1, tx2, ty2, -path_space[ii // 4 - 1] / 2)
		elif ii % 4 == 1:
			(qx, qy) = shift_path2(qx, qy, tx1, ty1, tx2, ty2, -path_width[ii // 4] / 2)
		elif ii % 4 == 2:
			(qx, qy) = shift_path1(qx, qy, tx1, ty1, tx2, ty2, -path_width[ii // 4] / 2)
			(rx, ry) = stroke_path(qx, qy, tx1, ty1, tx2, ty2, path_width[ii // 4], numpy.zeros(steps + 1))
			pcb.add("polygon", layer=layer, x=list(rx), y=list(ry), closed=True, hole=hole, order=order)
		else:
			(qx, qy) = shift_path2(qx, qy, tx1, ty1, tx2, ty2, -path_space[ii // 4] / 2)
	
	#for track in range(tracks):
		##pcb.add("polygon", layer=layer, x=list(qx), y=list(qy), closed=False, outline=0.01, hole=hole, order=order)
		#(qx, qy) = shift_path1(qx, qy, tx1, ty1, tx2, ty2, path_width[track] / 2)
		#(rx, ry) = stroke_path(qx, qy, tx1, ty1, tx2, ty2, path_width[track], numpy.zeros(steps + 1))
		#pcb.add("polygon", layer=layer, x=list(rx), y=list(ry), closed=True, hole=hole, order=order)
		#(qx, qy) = shift_path2(qx, qy, tx1, ty1, tx2, ty2, path_width[track] / 2)
		#if track != tracks - 1:
			#(qx, qy) = shift_path1(qx, qy, tx1, ty1, tx2, ty2, path_space[track] / 2)
			#(qx, qy) = shift_path2(qx, qy, tx1, ty1, tx2, ty2, path_space[track] / 2)
	return pcb
