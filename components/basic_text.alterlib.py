import alterpcb_core

import math
import numpy
import freetype

def transform_text(shape, xfrom, yfrom, xto, yto, angle, flip, mirror):
	shape = shape.copy()
	(shape["x"], shape["y"]) = alterpcb_core.transform_point(shape["x"], shape["y"], xfrom, yfrom, xto, yto, angle, flip, mirror)
	if flip != mirror:
		shape["angle"] = (angle - shape["angle"]) % 360.0
		shape["mirror"] = not shape["mirror"]
	else:
		shape["angle"] = (angle + shape["angle"]) % 360.0
	if flip:
		shape["layer"] = alterpcb_core.flip_layer(shape["layer"])
	return shape

def bezier1(a, b, t):
	s = 1.0 - t
	return s * a + t * b

def bezier2(a, b, c, t):
	s = 1.0 - t
	return s * s * a + 2 * s * t * b + t * t * c

def bezier3(a, b, c, d, t):
	s = 1.0 - t
	return s * s * (s * a + 3 * t * b) + t * t * (t * d + 3 * s * c)

def polygon_direction(x, y):
	area = 0.0
	for i in range(2, len(x)):
		area += (x[i] - x[0]) * (y[i - 1] - y[0]) - (y[i] - y[0]) * (x[i - 1] - x[0])
	return "cw" if area > 0 else "ccw"

loaded_fonts = {}

@component(transform=transform_text)
def text(x=0.0, y=0.0, angle=0.0, mirror=False, layer="silk-top", text="Text", font="DejaVuSans", size=2.0, halign="left", valign="baseline", spacing=0.0, steps=8, hole=False, order=0):
	pcb = alterpcb_core.Pcb()
	
	# load font
	if font not in loaded_fonts:
		loaded_fonts[font] = freetype.Face("fonts/%s.ttf" % (font))
	face = loaded_fonts[font]
	xscale = size / face.units_per_EM
	yscale = size / face.units_per_EM
	
	# calculate total width
	total_width = 0.0
	for ch in range(len(text)):
		face.load_char(text[ch], freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_SCALE)
		if ch != 0:
			kerning = face.get_kerning(text[ch - 1], text[ch], freetype.FT_KERNING_UNSCALED)
			total_width += kerning.x * xscale + spacing
		total_width += face.glyph.advance.x * xscale
	
	# calculate start position
	if halign == "left":
		pos_x = 0.0
	elif halign == "center":
		pos_x = -total_width / 2
	elif halign == "right":
		pos_x = -total_width
	else:
		raise Exception("Unknown horizontal alignment!")
	if valign == "baseline":
		pos_y = 0.0
	elif valign == "top":
		pos_y = -face.ascender * yscale
	elif valign == "center":
		pos_y = -(face.ascender + face.descender) / 2 * yscale
	elif valign == "bottom":
		pos_y = -face.descender * yscale
	else:
		raise Exception("Unknown vertical alignment!")
	
	# convert to polygons
	for ch in range(len(text)):
		
		# load one glyph
		face.load_char(text[ch], freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_SCALE)
		outline = face.glyph.outline
		
		# move position
		if ch != 0:
			kerning = face.get_kerning(text[ch - 1], text[ch], freetype.FT_KERNING_UNSCALED)
			pos_x += kerning.x * xscale + spacing
		
		# add polygons
		start = 0
		for contour in outline.contours:
			end = contour + 1
			points = outline.points[start:end]
			tags = outline.tags[start:end]
			start = end
			
			oncurve = [bool((tags[i] >> 0) & 1) for i in range(len(points))]
			thirdorder = [bool((tags[i] >> 1) & 1) for i in range(len(points))]
			hasmode = [bool((tags[i] >> 2) & 1) for i in range(len(points))]
			mode = [(tags[i] >> 5) & 0x7 for i in range(len(points))]
			
			t = (numpy.arange(steps) + 1) / steps
			n = len(oncurve)
			px = []
			py = []
			for i in range(len(points)):
				if oncurve[i]:
					if oncurve[i - 1]:
						px.append(points[i][0])
						py.append(points[i][1])
				else:
					assert(not thirdorder[i])
					x1 = points[i - 1][0] if oncurve[i - 1] else (points[i][0] + points[i - 1][0]) / 2
					y1 = points[i - 1][1] if oncurve[i - 1] else (points[i][1] + points[i - 1][1]) / 2
					x2 = points[i + 1 - n][0] if oncurve[i + 1 - n] else (points[i][0] + points[i + 1 - n][0]) / 2
					y2 = points[i + 1 - n][1] if oncurve[i + 1 - n] else (points[i][1] + points[i + 1 - n][1]) / 2
					xx = bezier2(x1, points[i][0], x2, t)
					yy = bezier2(y1, points[i][1], y2, t)
					px.extend(xx)
					py.extend(yy)
			hh = (1 if hole else 0) + (1 if polygon_direction(px, py) == "ccw" else 0)
			px = pos_x + numpy.array(px) * xscale
			py = pos_y + numpy.array(py) * yscale
			(px, py) = alterpcb_core.transform_point(px, py, 0.0, 0.0, x, y, angle, False, mirror)
			pcb.add("polygon", layer=layer, x=px, y=py, hole=bool(hh % 2), order=order + hh // 2)
		
		# move position again
		pos_x += face.glyph.advance.x * xscale
	
	return pcb
