import inspect
import json
import math
import numpy
import os
import subprocess

import traceback

circle_step = 5

primitives = {"circle", "rectangle", "polygon"}
params_circle = [
	("layer"  , "copper1-top"),
	("x"      , 0.0          ),
	("y"      , 0.0          ),
	("radius" , 1.0          ),
	("outline", 0.0          ),
	("hole"   , False        ),
	("order"  , 0            ),
	("pad"    , False        ),
]
params_rectangle = [
	("layer"  , "copper1-top"),
	("x"      , 0.0          ),
	("y"      , 0.0          ),
	("width"  , 2.0          ),
	("height" , 2.0          ),
	("angle"  , 0.0          ),
	("outline", 0.0          ),
	("hole"   , False        ),
	("order"  , 0            ),
	("pad"    , False        ),
]
params_polygon = [
	("layer"  , "copper1-top"    ),
	("x"      , [-1.0,  1.0, 0.0]),
	("y"      , [-1.0, -1.0, 1.0]),
	("closed" , True             ),
	("outline", 0.0              ),
	("hole"   , False            ),
	("order"  , 0                ),
	("pad"    , False            ),
]
params_component = [
	("x"      , 0.0          ),
	("y"      , 0.0          ),
	("angle"  , 0.0          ),
	("flip"   , False        ),
	("mirror" , False        ),
]

def equalize_lists(*lists):
	n = min(len(x) for x in lists)
	return tuple(x[:n] for x in lists)

def equalize_arrays(*arrays):
	n = min(len(x) for x in arrays)
	return tuple(numpy.array(x)[:n] for x in arrays)

def flip_layer(layer):
	if layer.endswith("-top"):
		return layer[:-4] + "-bot"
	if layer.endswith("-bot"):
		return layer[:-4] + "-top"
	return layer

def transform_point(x, y, xfrom, yfrom, xto, yto, angle, flip, mirror):
	angle_sin = math.sin(math.radians(angle))
	angle_cos = math.cos(math.radians(angle))
	m11 = angle_cos
	m12 = -angle_sin
	m21 = angle_sin
	m22 = angle_cos
	if flip != mirror:
		m11 = -m11
		m21 = -m21
	offset_x = xto - xfrom * m11 - yfrom * m12
	offset_y = yto - xfrom * m21 - yfrom * m22
	return (
		offset_x + x * m11 + y * m12,
		offset_y + x * m21 + y * m22,
	)

def transform_circle(shape, xfrom, yfrom, xto, yto, angle, flip, mirror):
	shape = shape.copy()
	(shape["x"], shape["y"]) = transform_point(shape["x"], shape["y"], xfrom, yfrom, xto, yto, angle, flip, mirror)
	if flip:
		shape["layer"] = flip_layer(shape["layer"])
	return shape

def transform_rectangle(shape, xfrom, yfrom, xto, yto, angle, flip, mirror):
	shape = shape.copy()
	(shape["x"], shape["y"]) = transform_point(shape["x"], shape["y"], xfrom, yfrom, xto, yto, angle, flip, mirror)
	if flip != mirror:
		shape["angle"] = (angle - shape["angle"]) % 360.0
	else:
		shape["angle"] = (angle + shape["angle"]) % 360.0
	if flip:
		shape["layer"] = flip_layer(shape["layer"])
	return shape

def transform_polygon(shape, xfrom, yfrom, xto, yto, angle, flip, mirror):
	shape = shape.copy()
	(px, py) = equalize_arrays(shape["x"], shape["y"])
	(px, py) = transform_point(px, py, xfrom, yfrom, xto, yto, angle, flip, mirror)
	(shape["x"], shape["y"]) = (list(px), list(py))
	if flip:
		shape["layer"] = flip_layer(shape["layer"])
	return shape

def transform_component(shape, xfrom, yfrom, xto, yto, angle, flip, mirror):
	shape = shape.copy()
	(shape["x"], shape["y"]) = transform_point(shape["x"], shape["y"], xfrom, yfrom, xto, yto, angle, flip, mirror)
	if flip != mirror:
		shape["angle"] = (angle - shape["angle"]) % 360.0
	else:
		shape["angle"] = (angle + shape["angle"]) % 360.0
	if flip:
		shape["flip"] = not shape["flip"]
	if mirror:
		shape["mirror"] = not shape["mirror"]
	return shape

def transform_coordinate(x, y, origin_x, origin_y, angle):
	angle_sin = math.sin(math.radians(angle))
	angle_cos = math.cos(math.radians(angle))
	return (
		origin_x + x * angle_cos - y * angle_sin,
		origin_y + y * angle_cos + x * angle_sin,
	)

def invtransform_coordinate(x, y, origin_x, origin_y, angle):
	angle_sin = math.sin(math.radians(angle))
	angle_cos = math.cos(math.radians(angle))
	return (
		(x - origin_x) * angle_cos + (y - origin_y) * angle_sin,
		(y - origin_y) * angle_cos - (x - origin_x) * angle_sin,
	)

def snap_value(x, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle):
	grid_step = min(grid_step_x, grid_step_y)
	return numpy.round(x / grid_step) * grid_step

def snap_point(x, y, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle):
	(local_x, local_y) = invtransform_coordinate(x, y, grid_origin_x, grid_origin_y, grid_angle)
	local_x = numpy.round(local_x / grid_step_x) * grid_step_x
	local_y = numpy.round(local_y / grid_step_y) * grid_step_y
	return transform_coordinate(local_x, local_y, grid_origin_x, grid_origin_y, grid_angle)

def snap_circle(shape, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle):
	shape = shape.copy()
	if shape["pad"]:
		(shape["x"], shape["y"]) = snap_point(shape["x"], shape["y"], grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
	else:
		(shape["x"], shape["y"]) = snap_point(shape["x"], shape["y"], grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
		shape["radius"] = snap_value(shape["radius"], grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
		pass
	return shape

def snap_rectangle(shape, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle):
	shape = shape.copy()
	if shape["pad"]:
		(shape["x"], shape["y"]) = snap_point(shape["x"], shape["y"], grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
	else:
		(x1, y1) = snap_point(shape["x"] - shape["width"] / 2, shape["y"] - shape["height"] / 2, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
		(x2, y2) = snap_point(shape["x"] + shape["width"] / 2, shape["y"] + shape["height"] / 2, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
		(shape["x"], shape["y"]) = ((x1 + x2) / 2, (y1 + y2) / 2)
		(shape["width"], shape["height"]) = (x2 - x1, y2 - y1)
	return shape

def snap_polygon(shape, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle):
	shape = shape.copy()
	(px, py) = equalize_arrays(shape["x"], shape["y"])
	(px, py) = snap_point(px, py, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
	(shape["x"], shape["y"]) = (list(px), list(py))
	return shape

def snap_component(shape, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle):
	shape = shape.copy()
	(shape["x"], shape["y"]) = snap_point(shape["x"], shape["y"], grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
	return shape

def handles_circle(shape):
	(x, y, r) = (shape["x"], shape["y"], shape["radius"])
	return [
		{"x": x    , "y": y    },
		{"x": x - r, "y": y    },
		{"x": x + r, "y": y    },
		{"x": x    , "y": y - r},
		{"x": x    , "y": y + r},
	]

def handles_rectangle(shape):
	(x, y, w, h) = (shape["x"], shape["y"], shape["width"] / 2, shape["height"] / 2)
	angle_sin = math.sin(math.radians(shape["angle"]))
	angle_cos = math.cos(math.radians(shape["angle"]))
	return [
		{"x": x                                , "y": y                                },
		{"x": x - w * angle_cos                , "y": y - w * angle_sin                },
		{"x": x + w * angle_cos                , "y": y + w * angle_sin                },
		{"x": x + h * angle_sin                , "y": y - h * angle_cos                },
		{"x": x - h * angle_sin                , "y": y + h * angle_cos                },
		{"x": x - w * angle_cos + h * angle_sin, "y": y - w * angle_sin - h * angle_cos},
		{"x": x + w * angle_cos + h * angle_sin, "y": y + w * angle_sin - h * angle_cos},
		{"x": x - w * angle_cos - h * angle_sin, "y": y - w * angle_sin + h * angle_cos},
		{"x": x + w * angle_cos - h * angle_sin, "y": y + w * angle_sin + h * angle_cos},
	]

def handles_polygon_callback_delete(shape, index):
	shape = shape.copy()
	shape["x"] = shape["x"].copy()
	shape["y"] = shape["y"].copy()
	shape["x"].pop(index)
	shape["y"].pop(index)
	return shape

def handles_polygon_callback_add_before(shape, index):
	shape = shape.copy()
	shape["x"] = shape["x"].copy()
	shape["y"] = shape["y"].copy()
	n = min(len(shape["x"]), len(shape["y"]))
	shape["x"].insert(index, (shape["x"][index] + shape["x"][(index - 1) % n]) / 2)
	shape["y"].insert(index, (shape["y"][index] + shape["y"][(index - 1) % n]) / 2)
	return shape

def handles_polygon_callback_add_after(shape, index):
	shape = shape.copy()
	shape["x"] = shape["x"].copy()
	shape["y"] = shape["y"].copy()
	n = min(len(shape["x"]), len(shape["y"]))
	shape["x"].insert(index + 1, (shape["x"][index] + shape["x"][(index + 1) % n]) / 2)
	shape["y"].insert(index + 1, (shape["y"][index] + shape["y"][(index + 1) % n]) / 2)
	return shape

def handles_polygon(shape):
	actions = [
		{"name": "Delete point", "callback": handles_polygon_callback_delete},
		{"name": "Add point before", "callback": handles_polygon_callback_add_before},
		{"name": "Add point after", "callback": handles_polygon_callback_add_after},
	]
	return [{"x": shape["x"][i], "y": shape["y"][i], "actions": actions} for i in range(min(len(shape["x"]), len(shape["y"])))]

def handles_component(shape):
	return [
		{"x": shape["x"], "y": shape["y"]},
	]

def handlemove_circle(shape, index, x, y):
	shape = shape.copy()
	if index == 0:
		shape["x"] = x
		shape["y"] = y
	elif index == 1 or index == 2:
		shape["radius"] = abs(x - shape["x"])
	else:
		shape["radius"] = abs(y - shape["y"])
	return shape

def handlemove_rectangle(shape, index, x, y):
	shape = shape.copy()
	angle_sin = math.sin(math.radians(shape["angle"]))
	angle_cos = math.cos(math.radians(shape["angle"]))
	if index == 0:
		shape["x"] = x
		shape["y"] = y
	else:
		if index in (1, 5, 7):
			d = (x - shape["x"]) * angle_cos + (y - shape["y"]) * angle_sin
			e = -shape["width"] / 2
			shape["x"] += angle_cos * (d - e) / 2
			shape["y"] += angle_sin * (d - e) / 2
			shape["width"] -= (d - e)
		if index in (2, 6, 8):
			d = (x - shape["x"]) * angle_cos + (y - shape["y"]) * angle_sin
			e = shape["width"] / 2
			shape["x"] += angle_cos * (d - e) / 2
			shape["y"] += angle_sin * (d - e) / 2
			shape["width"] += (d - e)
		if index in (3, 5, 6):
			d = (y - shape["y"]) * angle_cos - (x - shape["x"]) * angle_sin
			e = -shape["height"] / 2
			shape["x"] -= angle_sin * (d - e) / 2
			shape["y"] += angle_cos * (d - e) / 2
			shape["height"] -= (d - e)
		if index in (4, 7, 8):
			d = (y - shape["y"]) * angle_cos - (x - shape["x"]) * angle_sin
			e = shape["height"] / 2
			shape["x"] -= angle_sin * (d - e) / 2
			shape["y"] += angle_cos * (d - e) / 2
			shape["height"] += (d - e)
	return shape

def handlemove_polygon(shape, index, x, y):
	shape = shape.copy()
	shape["x"] = shape["x"].copy()
	shape["y"] = shape["y"].copy()
	shape["x"][index] = x
	shape["y"][index] = y
	return shape

def handlemove_component(shape, index, x, y):
	shape = shape.copy()
	shape["x"] = x
	shape["y"] = y
	return shape

class Library:
	
	def __init__(self):
		self.components = {}
		self.global_list = []
		self.register_primitive("circle"   , params_circle   , transform_circle   , snap_circle   , handles_circle   , handlemove_circle   )
		self.register_primitive("rectangle", params_rectangle, transform_rectangle, snap_rectangle, handles_rectangle, handlemove_rectangle)
		self.register_primitive("polygon"  , params_polygon  , transform_polygon  , snap_polygon  , handles_polygon  , handlemove_polygon  )
	
	def register_primitive(self, name, base_params, transform, snap, handles, handlemove):
		self.components[name] = {
			"type": "primitive",
			"base_params": base_params,
			"transform": transform,
			"snap": snap,
			"handles": handles,
			"handlemove": handlemove,
		}
	
	def register_component_func(self, name, func, params=None, transform=None, snap=None, handles=None, handlemove=None):
		if params is None:
			(args, _, _, defaults) = inspect.getargspec(func)
			if len(args) != 0 and (defaults is None or len(args) != len(defaults)):
				raise Exception("Function-based component '%s' does not have default values for all parameters!" % (name))
			params = []
			for i in range(len(args)):
				params.append((args[i], defaults[i]))
		if transform is None:
			transform = transform_component
		if snap is None:
			snap = snap_component
		if handles is None:
			handles = handles_component
		if handlemove is None:
			handlemove = handlemove_component
		self.components[name] = {
			"type": "func",
			"func": func,
			"params": params,
			"base_params": params_component if transform is transform_component else [],
			"transform": transform,
			"snap": snap,
			"handles": handles,
			"handlemove": handlemove,
		}
	
	def register_component_shapes(self, name, shapes):
		self.components[name] = {
			"type": "shapes",
			"shapes": shapes,
			"base_params": params_component,
			"transform": transform_component,
			"snap": snap_component,
			"handles": handles_component,
			"handlemove": handlemove_component,
		}
	
	def load_json(self, filename):
		with open(filename, "r") as f:
			data = json.load(f)
		for component in data:
			self.register_component_shapes(component["name"], component["shapes"])
	
	def load_python(self, filename):
		def component(func=None, name=None, params=None, transform=None, snap=None, handles=None, handlemove=None):
			if func is None:
				return (lambda func, name=name, params=params, transform=transform, snap=snap, handles=handles, handlemove=handlemove:
						component(func, name, params, transform, snap, handles, handlemove))
			if name is None:
				name = func.__name__
			self.register_component_func(name, func, params, transform, snap, handles, handlemove)
			return func
		global_vars = {
			"component": component,
		}
		with open(filename, "r") as f:
			code = compile(f.read(), filename, "exec")
		exec(code, global_vars)
		self.global_list.append(global_vars) # preserve environment so we can call the functions later
	
	def component_exists(self, name):
		return (name in self.components)
	
	def component_params(self, shape):
		comp = self.components.get(shape["type"])
		if comp is None:
			raise Exception("Component '%s' does not exist!" % (shape["type"]))
		params = [("type", shape["type"])]
		for par in comp["base_params"]:
			params.append((par[0], shape.get(par[0], par[1])))
		if comp["type"] == "func":
			for par in comp["params"]:
				params.append((par[0], shape.get(par[0], par[1])))
		return params
	
	def component_defaults(self, shape):
		comp = self.components.get(shape["type"])
		if comp is None:
			raise Exception("Component '%s' does not exist!" % (shape["type"]))
		shape2 = {"type": shape["type"]}
		for par in comp["base_params"]:
			shape2[par[0]] = shape.get(par[0], par[1])
		if comp["type"] == "func":
			for par in comp["params"]:
				shape2[par[0]] = shape.get(par[0], par[1])
		return shape2
	
	def component_transform(self, shape, xfrom=0.0, yfrom=0.0, xto=0.0, yto=0.0, angle=0.0, flip=False, mirror=False):
		comp = self.components.get(shape["type"])
		if comp is None:
			raise Exception("Component '%s' does not exist!" % (shape["type"]))
		return comp["transform"](shape, xfrom, yfrom, xto, yto, angle, flip, mirror)
	
	def component_snap(self, shape, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle):
		comp = self.components.get(shape["type"])
		if comp is None:
			raise Exception("Component '%s' does not exist!" % (shape["type"]))
		return comp["snap"](shape, grid_step_x, grid_step_y, grid_origin_x, grid_origin_y, grid_angle)
	
	def component_handles(self, shape):
		comp = self.components.get(shape["type"])
		if comp is None:
			raise Exception("Component '%s' does not exist!" % (shape["type"]))
		return comp["handles"](shape)
	
	def component_handlemove(self, shape, index, x, y):
		comp = self.components.get(shape["type"])
		if comp is None:
			raise Exception("Component '%s' does not exist!" % (shape["type"]))
		return comp["handlemove"](shape, index, x, y)
	
	def component_shapes(self, shape):
		comp = self.components.get(shape["type"])
		if comp is None:
			raise Exception("Component '%s' does not exist!" % (shape["type"]))
		if comp["type"] == "func":
			params = {}
			for par in comp["params"]:
				params[par[0]] = shape.get(par[0], par[1])
			shapes = comp["func"](**params).shapes
		elif comp["type"] == "shapes":
			shapes = comp["shapes"]
		else:
			raise Exception("Unknown type!")
		shapes2 = []
		for shape2 in shapes:
			shape2 = self.component_defaults(shape2)
			if comp["transform"] is transform_component:
				shape2 = self.component_transform(shape2, 0.0, 0.0, shape["x"], shape["y"], shape["angle"], shape["flip"], shape["mirror"])
			shapes2.append(shape2)
		#print("***** SHAPES *****\n" + str(shape) + "\n----------\n" + str(shapes2))
		return shapes2
	
	def component_flatten(self, shape, blacklist=None):
		if blacklist is None:
			blacklist = set()
		output = []
		#shape = self.component_defaults(shape)
		if shape["type"] in primitives:
			output.append(shape)
		elif shape["type"] in blacklist:
			print("Detected self-reference in component '%s'!" % (shape["type"]))
			#traceback.print_stack()
		else:
			blacklist.add(shape["type"])
			for shape2 in self.component_shapes(shape):
				output += self.component_flatten(shape2, blacklist=blacklist)
			blacklist.remove(shape["type"])
		return output

class Pcb:
	
	def __init__(self):
		self.shapes = []
	
	def add(self, typ, **kwargs):
		shape = {
			"type": typ,
		}
		shape.update(kwargs)
		self.shapes.append(shape)
	
	#def add_pcb(self, pcb, x=0.0, y=0.0, angle=0.0, flip=False, mirror=False):
		#for shape in pcb.shapes:
			#self.shapes.append(shape_transform(shape, 0.0, 0.0, x, y, angle, flip, mirror))
	
	def load_json(self, filename):
		with open(filename, "r") as f:
			self.shapes = json.load(f)
	
	def save_json(self, filename):
		with open(filename, "w") as f:
			json.dump(self.shapes, f, indent=1)#, default=lambda x: list(x) if isinstance(x, numpy.ndarray) else x)
	
	def export(self, path, name, layerstack, use_arcs=False):
		
		# delete old files
		if os.path.isdir(path + "/" + name):
			fnames = os.listdir(path + "/" + name)
			for fname in fnames:
				ok = False
				for layer in layerstack:
					if layer["type"] is not None:
						if fname == name + layer["ext"]:
							ok = True
				if not ok:
					raise Exception("Output directory contains unknown file '%s' which would be deleted by export." % (fname))
			for fname in fnames:
				os.remove(path + "/" + name + "/" + fname)
		else:
			os.mkdir(path + "/" + name)
		
		# write new files
		unknown_layers = set()
		for shape in self.shapes:
			unknown_layers.add(shape["layer"])
		for layer in layerstack:
			unknown_layers.discard(layer["name"])
		if len(unknown_layers) != 0:
			print("Unknown layers: " + ", ".join(unknown_layers))
		for layer in layerstack:
			if layer["type"] is not None:
				filename = path + "/" + name + "/" + name + layer["ext"]
				if layer["type"] == "gerber":
					self.export_gerber(layer["name"], filename, use_arcs)
				elif layer["type"] == "drill":
					self.export_drill(layer["name"], filename)
				else:
					raise Exception("Unknown layer type!")
		
		# create zip file
		if os.path.isfile(path + "/" + name + ".zip"):
			os.remove(path + "/" + name + ".zip")
		subprocess.call(["zip", "-r", name + ".zip", name], cwd=path)
	
	def export_gerber(self, layer, filename, use_arcs):
		
		scale = 10**4 # 4.4 format, mm
		tools = []
		tools_circle = {}
		tools_rectangle = {}
		shapes_order = {}
		toolcounter = 10 # first D-code for tools is D10
		needs_rr = False
		
		def ff(num):
			if num < 0:
				return "-%08d" % (-num)
			else:
				return "%08d" % (num)
		
		def add_circle(diam):
			nonlocal toolcounter
			diam = int(round(diam * scale))
			if diam not in tools_circle:
				tools.append((toolcounter, "circle", diam))
				tools_circle[diam] = toolcounter
				toolcounter += 1
		def add_rectangle(width, height, angle):
			nonlocal toolcounter, needs_rr
			width = int(round(abs(width) * scale))
			height = int(round(abs(height) * scale))
			angle = int(round(angle * scale)) % 1800000
			if angle >= 900000:
				(width, height) = (height, width)
				angle -= 900000
			if angle != 0:
				needs_rr = True
			if (width, height, angle) not in tools_rectangle:
				tools.append((toolcounter, "rectangle", width, height, angle))
				tools_rectangle[(width, height, angle)] = toolcounter
				toolcounter += 1
		def find_circle(diam):
			diam = int(round(diam * scale))
			return tools_circle[diam]
		def find_rectangle(width, height, angle):
			width = int(round(abs(width) * scale))
			height = int(round(abs(height) * scale))
			angle = int(round(angle * scale)) % 1800000
			if angle >= 900000:
				(width, height) = (height, width)
				angle -= 900000
			return tools_rectangle[(width, height, angle)]
		
		def flatten_circle(x, y, radius):
			angle = numpy.linspace(0, 2 * math.pi, 360 // circle_step, endpoint=False)
			rx = x + radius * numpy.cos(angle)
			ry = y + radius * numpy.sin(angle)
			return (rx, ry)
		def flatten_rectangle(x, y, width, height, angle):
			rx = numpy.array([-width  / 2,  width  / 2,  width  / 2, -width  / 2])
			ry = numpy.array([-height / 2, -height / 2,  height / 2,  height / 2])
			rrx = x + rx * math.cos(math.radians(angle)) - ry * math.sin(math.radians(angle))
			rry = y + rx * math.sin(math.radians(angle)) + ry * math.cos(math.radians(angle))
			return (rrx, rry)
		
		def write_flash(num, x, y):
			f.write("D%02d*\n" % (num))
			f.write("X%sY%sD03*\n" % (ff(int(round(x * scale))), ff(int(round(y * scale)))))
		def write_region(rx, ry):
			px = numpy.round(rx * scale).astype(numpy.int32)
			py = numpy.round(ry * scale).astype(numpy.int32)
			f.write("G36*\n")
			f.write("G01*\n")
			f.write("X%sY%sD02*\n" % (ff(px[0]), ff(py[0])))
			for j in range(1, len(px)):
				f.write("X%sY%sD01*\n" % (ff(px[j]), ff(py[j])))
			f.write("X%sY%sD01*\n" % (ff(px[0]), ff(py[0])))
			f.write("D02*\n")
			f.write("G37*\n")
		def write_region_circle(x, y, radius):
			x1 = int(round((x - radius) * scale))
			x2 = int(round(x * scale))
			y1 = int(round(y * scale))
			y2 = int(round(y * scale))
			f.write("G36*\n")
			f.write("G02*\n")
			f.write("G75*\n")
			f.write("X%sY%sD02*\n" % (ff(x1), ff(y1)))
			f.write("X%sY%sI%sJ%sD01*\n" % (ff(x1), ff(y1), ff(x2 - x1), ff(y2 - y1)))
			f.write("D02*\n")
			f.write("G37*\n")
		def write_outline(num, rx, ry, closed):
			px = numpy.round(rx * scale).astype(numpy.int32)
			py = numpy.round(ry * scale).astype(numpy.int32)
			f.write("D%02d*\n" % (num))
			f.write("G01*\n")
			f.write("X%sY%sD02*\n" % (ff(px[0]), ff(py[0])))
			for j in range(1, len(px)):
				f.write("X%sY%sD01*\n" % (ff(px[j]), ff(py[j])))
			if closed:
				f.write("X%sY%sD01*\n" % (ff(px[0]), ff(py[0])))
		def write_outline_circle(num, x, y, radius):
			x1 = int(round((x - radius) * scale))
			x2 = int(round(x * scale))
			y1 = int(round(y * scale))
			y2 = int(round(y * scale))
			f.write("D%02d*\n" % (num))
			f.write("G02*\n")
			f.write("G75*\n")
			f.write("X%sY%sD02*\n" % (ff(x1), ff(y1)))
			f.write("X%sY%sI%sJ%sD01*\n" % (ff(x1), ff(y1), ff(x2 - x1), ff(y2 - y1)))
		
		# collect tools
		for shape in self.shapes:
			if shape["layer"] != layer:
				continue
			if shape["outline"] == 0.0:
				if shape["type"] == "circle":
					if shape["pad"]:
						add_circle(shape["radius"] * 2)
				elif shape["type"] == "rectangle":
					if shape["pad"]:
						add_rectangle(shape["width"], shape["height"], shape["angle"])
				elif shape["type"] == "polygon":
					pass
				else:
					raise Exception("Unknown shape type!")
			else:
				add_circle(shape["outline"])
			order = shape["order"] * 2 + 1 if shape["hole"] else shape["order"] * 2
			if order not in shapes_order:
				shapes_order[order] = []
			shapes_order[order].append(shape)
		
		# write file
		with open(filename, "w") as f:
			f.write("%FSLAX44Y44*%\n")
			f.write("%MOMM*%\n")
			if needs_rr:
				f.write("%AMRR*21,1,$1,$2,0,0,$3*%\n")
			for tool in tools:
				if tool[1] == "circle":
					f.write("%%ADD%02dC,%.4f*%%\n" % (tool[0], tool[2] / scale))
				elif tool[1] == "rectangle":
					if tool[4] == 0:
						f.write("%%ADD%02dR,%.4fX%.4f*%%\n" % (tool[0], tool[2] / scale, tool[3] / scale))
					else:
						f.write("%%ADD%02dRR,%.4fX%.4fX%.4f*%%\n" % (tool[0], tool[2] / scale, tool[3] / scale, tool[4] / scale))
			orders = list(shapes_order.keys())
			orders.sort()
			for order in orders:
				if order % 2 == 0:
					f.write("%LPD*%\n")
				else:
					f.write("%LPC*%\n")
				for shape in shapes_order[order]:
					if shape["outline"] == 0.0:
						if shape["type"] == "circle":
							if shape["pad"]:
								num = find_circle(shape["radius"] * 2)
								write_flash(num, shape["x"], shape["y"])
							elif use_arcs:
								write_region_circle(shape["x"], shape["y"], shape["radius"])
							else:
								(rx, ry) = flatten_circle(shape["x"], shape["y"], shape["radius"])
								write_region(rx, ry)
						elif shape["type"] == "rectangle":
							if shape["pad"]:
								num = find_rectangle(shape["width"], shape["height"], shape["angle"])
								write_flash(num, shape["x"], shape["y"])
							else:
								(rx, ry) = flatten_rectangle(shape["x"], shape["y"], shape["width"], shape["height"], shape["angle"])
								write_region(rx, ry)
						elif shape["type"] == "polygon":
							(rx, ry) = equalize_arrays(shape["x"], shape["y"])
							write_region(rx, ry)
						else:
							raise Exception("Unknown shape type!")
					else:
						num = find_circle(shape["outline"])
						if shape["type"] == "circle":
							if use_arcs:
								write_outline_circle(num, shape["x"], shape["y"], shape["radius"])
							else:
								(rx, ry) = flatten_circle(shape["x"], shape["y"], shape["radius"])
								write_outline(num, rx, ry, True)
						elif shape["type"] == "rectangle":
							(rx, ry) = flatten_rectangle(shape["x"], shape["y"], shape["width"], shape["height"], shape["angle"])
							write_outline(num, rx, ry, True)
						elif shape["type"] == "polygon":
							(rx, ry) = equalize_arrays(shape["x"], shape["y"])
							write_outline(num, rx, ry, shape["closed"])
						else:
							raise Exception("Unknown shape type!")
			f.write("M02*\n")
	
	def export_drill(self, layer, filename):
		
		scale = 10**4 # 4.4 format, mm
		
		def ff(num):
			if num < 0:
				return "-%08d" % (-num)
			else:
				return "%08d" % (num)
		
		# collect tools
		tools = {}
		for shape in self.shapes:
			if shape["layer"] != layer:
				continue
			if shape["type"] != "circle":
				raise Exception("Drill file only supports circular holes!")
			diam = shape["radius"] * 2
			if diam not in tools:
				tools[diam] = []
			tools[diam].append((shape["x"], shape["y"]))
		
		# write file
		with open(filename, "w") as f:
			f.write("M48\n")
			f.write("METRIC\n")
			num = 0
			for diam in tools:
				num += 1
				f.write("T%02dC%.4f\n" % (num, diam))
			f.write("%\n")
			num = 0
			for diam in tools:
				num += 1
				holes = tools[diam]
				f.write("T%02d\n" % (num))
				for hole in holes:
					f.write("X%sY%s\n" % (ff(int(round(hole[0] * scale))), ff(int(round(hole[1] * scale)))))
			f.write("M30\n")
	
	def export_svg(self, filename, layerstack):
		
		# calculate size
		bbox_xmin = 1e99
		bbox_xmax = -1e99
		bbox_ymin = 1e99
		bbox_ymax = -1e99
		for shape in self.shapes:
			(px, py) = shape_to_polygon(shape)
			expand = shape["outline"] / 2
			bbox_xmin = min(bbox_xmin, numpy.amin(px) - expand)
			bbox_xmax = max(bbox_xmax, numpy.amax(px) + expand)
			bbox_ymin = min(bbox_ymin, numpy.amin(py) - expand)
			bbox_ymax = max(bbox_ymax, numpy.amax(py) + expand)
		xmin = round(bbox_xmin - 1.0)
		xmax = round(bbox_xmax + 1.0)
		ymin = round(bbox_ymin - 1.0)
		ymax = round(bbox_ymax + 1.0)
		
		# generate SVG
		scale = 1.0 #90.0 / 25.4
		with open(filename, "w") as f:
			f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n")
			#f.write("<svg xmlns=\"http://www.w3.org/2000/svg\" xmlns:inkscape=\"http://www.inkscape.org/namespaces/inkscape\" version=\"1.1\" width=\"%.3fpx\" height=\"%.3fpx\">\n"
				#% ((xmax - xmin) * scale, (ymax - ymin) * scale))
			f.write("<svg xmlns=\"http://www.w3.org/2000/svg\" xmlns:inkscape=\"http://www.inkscape.org/namespaces/inkscape\" version=\"1.1\" " +
					"width=\"%.3fmm\" height=\"%.3fmm\" viewBox=\"%.3f %.3f %.3f %.3f\">\n"
				% (xmax - xmin, ymax - ymin, 0.0, 0.0, xmax - xmin, ymax - ymin))
			for layer in layerstack:
				edgecolor=(layer["color"][0]*0.5, layer["color"][1]*0.5, layer["color"][2]*0.5, 0.5)
				facecolor=(layer["color"][0], layer["color"][1], layer["color"][2], 0.3)
				f.write("<g id=\"%s\" inkscape:groupmode=\"layer\" fill=\"%s\" fill-opacity=\"%.3f\" stroke=\"%s\" stroke-opacity=\"%.3f\" stroke-width=\"%.3fmm\">\n"
					% (layer["name"], color_hex(facecolor), facecolor[3], color_hex(edgecolor), edgecolor[3], 0.02 * scale))
				for shape in self.shapes:
					if shape["layer"] != layer["name"]:
						continue
					(px, py) = shape_to_polygon(shape)
					if shape["outline"] == 0.0:
						px = (px - xmin) * scale
						py = (ymax - py) * scale
						f.write("<path d=\"")
						f.write("M%.3f,%.3f " % (px[0], py[0]))
						for j in range(1, len(px)):
							f.write("L%.3f,%.3f " % (px[j], py[j]))
						f.write("Z\"/>\n")
					else:
						first = 1 if shape["type"] == "polygon" and not shape["closed"] else 0
						if len(px) - first > 1:
							f.write("<g>\n")
						for i in range(first, len(px)):
							(px2, py2) = stroke_line(px[i - 1], py[i - 1], px[i], py[i], shape["outline"])
							px2 = (px2 - xmin) * scale
							py2 = (ymax - py2) * scale
							f.write("<path d=\"")
							f.write("M%.3f,%.3f " % (px2[0], py2[0]))
							for j in range(1, len(px2)):
								f.write("L%.3f,%.3f " % (px2[j], py2[j]))
							f.write("Z\"/>\n")
						if len(px) - first > 1:
							f.write("</g>\n")
				f.write("</g>\n")
			f.write("</svg>\n")

def color_hex(color):
	return "#%02x%02x%02x" % (
		max(0, min(255, int(round(color[0] * 255)))),
		max(0, min(255, int(round(color[1] * 255)))),
		max(0, min(255, int(round(color[2] * 255)))),
	)

def stroke_line(x1, y1, x2, y2, width):
	angle = math.atan2(y2 - y1, x2 - x1) + numpy.linspace(-math.pi / 2, math.pi / 2, 180 // circle_step + 1)
	return (
		numpy.concatenate((x1 - width / 2 * numpy.cos(angle), x2 + width / 2 * numpy.cos(angle))),
		numpy.concatenate((y1 - width / 2 * numpy.sin(angle), y2 + width / 2 * numpy.sin(angle))),
	)

def shape_to_polygon(shape):
	if shape["type"] == "circle":
		angle = numpy.linspace(0, 2 * math.pi, 360 // circle_step, endpoint=False)
		return (
			shape["x"] + shape["radius"] * numpy.cos(angle),
			shape["y"] + shape["radius"] * numpy.sin(angle),
		)
	elif shape["type"] == "rectangle":
		rx = numpy.array([-shape["width"]  / 2,  shape["width"]  / 2,  shape["width"]  / 2, -shape["width"]  / 2])
		ry = numpy.array([-shape["height"] / 2, -shape["height"] / 2,  shape["height"] / 2,  shape["height"] / 2])
		return (
			shape["x"] + rx * math.cos(math.radians(shape["angle"])) - ry * math.sin(math.radians(shape["angle"])),
			shape["y"] + rx * math.sin(math.radians(shape["angle"])) + ry * math.cos(math.radians(shape["angle"])),
		)
	elif shape["type"] == "polygon":
		return equalize_arrays(shape["x"], shape["y"])
	else:
		raise Exception("Unknown shape type!")
