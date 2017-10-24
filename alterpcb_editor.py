#!/usr/bin/env python3

import alterpcb_core

import inspect
import json
import math
import numpy
import os
import sys
from PySide.QtCore import Qt, QSize, QPointF
from PySide.QtGui import QApplication, QMainWindow, QWidget, QMenu
from PySide.QtGui import QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy
from PySide.QtGui import QLabel, QPushButton, QLineEdit, QSplitter, QScrollArea, QTextBrowser
from PySide.QtGui import QClipboard, QShortcut, QKeySequence, QFileDialog, QInputDialog, QDialog
from PySide.QtGui import QPainter, QImage, QPen, QBrush, QColor, QFont, QPolygonF

import time

class Instance:
	def __init__(self, shape, selected, flat, handles):
		self.shape = shape
		self.selected = selected
		self.flat = flat
		self.handles = handles

class History:
	def __init__(self, instances, soft):
		self.instances = instances
		self.soft = soft

class Component:
	
	max_history = 20
	
	def __init__(self, name, instances, view_x=None, view_y=None, view_scale=None, grid_origin_x=None, grid_origin_y=None, grid_angle=None, grid_step_x=None, grid_step_y=None):
		
		self.name = name
		self.instances = instances
		self.view_x = 0.0 if view_x is None else view_x
		self.view_y = 0.0 if view_y is None else view_y
		self.view_scale = 10.0 if view_scale is None else view_scale
		self.grid_origin_x = 0.0 if grid_origin_x is None else grid_origin_x
		self.grid_origin_y = 0.0 if grid_origin_y is None else grid_origin_y
		self.grid_angle = 0.0 if grid_angle is None else grid_angle
		self.grid_step_x = 0.1 if grid_step_x is None else grid_step_x
		self.grid_step_y = 0.1 if grid_step_y is None else grid_step_y
		
		# initialize history
		self.history_clear()
	
	def history_clear(self):
		self.history_instances = [History(self.instances, False)]
		self.history_position = 0
		print("CLEAR: %d/%d" % (self.history_position + 1, len(self.history_instances)))
	
	def history_revert(self):
		self.instances = self.history_instances[self.history_position].instances
		print("REVERT: %d/%d" % (self.history_position + 1, len(self.history_instances)))
	
	def history_push(self, soft=False):
		self.history_instances = self.history_instances[:self.history_position + 1]
		if soft and self.history_instances[-1].soft:
			self.history_instances[-1] = History(self.instances, soft)
		else:
			self.history_instances.append(History(self.instances, soft))
			if len(self.history_instances) > self.max_history:
				self.history_instances.pop(0)
		self.history_position = len(self.history_instances) - 1
		print("PUSH: %d/%d" % (self.history_position + 1, len(self.history_instances)))
	
	def history_undo(self):
		if self.history_position > 0:
			self.history_position -= 1
			self.instances = self.history_instances[self.history_position].instances
			print("UNDO: %d/%d" % (self.history_position + 1, len(self.history_instances)))
	
	def history_redo(self):
		if self.history_position < len(self.history_instances) - 1:
			self.history_position += 1
			self.instances = self.history_instances[self.history_position].instances
			print("REDO: %d/%d" % (self.history_position + 1, len(self.history_instances)))
	
class LayoutViewer(QWidget):
	
	color_background = QColor.fromRgbF(1.0, 1.0, 1.0)
	color_grid1 = QColor.fromRgbF(0.0, 0.0, 0.0, 0.1)
	color_grid2 = QColor.fromRgbF(0.0, 0.0, 0.0, 0.2)
	color_suppress = QColor.fromRgbF(1.0, 1.0, 1.0, 0.5)
	#color_selectionpen = QColor.fromRgbF(0.3, 0.3, 0.3, 0.5)
	#color_selectionbrush = QColor.fromRgbF(1.0, 1.0, 1.0, 0.5)
	color_selectionpen = QColor.fromRgbF(0.0, 0.0, 0.0, 0.2)
	color_selectionbrush = QColor.fromRgbF(0.0, 0.0, 0.0, 0.1)
	color_handlepen = QColor.fromRgbF(0.2, 0.2, 0.2)
	color_handlebrush = QColor.fromRgbF(0.8, 0.8, 0.8)
	color_cursor = QColor.fromRgbF(0.0, 0.0, 0.0, 0.3)
	
	quality_low = 0
	quality_medium = 1
	quality_high = 2
	quality_count = 3
	
	layer_mode_all = 0
	layer_mode_half = 1
	layer_mode_single = 2
	layer_mode_count = 3
	
	def __init__(self, main, parent):
		super(LayoutViewer, self).__init__(parent)
		self.main = main
		
		# initialize editor
		self.antialias = False
		self.quality = self.quality_medium
		self.layer_mode = self.layer_mode_all
		
		# initialize cursor
		self.mouse_x = 0.0
		self.mouse_y = 0.0
		self.cursor_active = False
		self.cursor_x = 0.0
		self.cursor_y = 0.0
		
		# initialize actions
		self.pan_active = False
		self.select_active = False
		self.select_x1 = 0.0
		self.select_y1 = 0.0
		self.select_x2 = 0.0
		self.select_y2 = 0.0
		self.drag_active = False
		self.handle_active = False
		self.handle_instance = 0
		self.handle_index = 0
		
		# load the libraries
		self.load_library()
		
		# load a blank design
		self.load_blank()
		
		# widget settings
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
		self.setFocusPolicy(Qt.ClickFocus)
		self.setMouseTracking(True)
		self.setCursor(Qt.CrossCursor)
		self.setAttribute(Qt.WA_OpaquePaintEvent)
		
		# shortcuts
		self.shortcuts = []
		
		self.add_shortcut("F1", self.show_help, "Show help")
		self.add_shortcut("F5", self.key_reload, "Reload")
		self.add_shortcut("Ctrl+N", self.key_file_new, "New file")
		self.add_shortcut("Ctrl+O", self.key_file_open, "Open file")
		self.add_shortcut("Ctrl+S", self.key_file_save, "Save file")
		self.add_shortcut("Ctrl+Shift+S", self.key_file_save_as, "Save file as")
		self.add_shortcut("Ctrl+E", self.key_export, "Export")
		self.add_shortcut("Ctrl+I", self.key_export_image, "Export image")
		self.add_shortcut("A", self.key_antialias, "Antialias")
		self.add_shortcut("Q", self.key_quality, "Qualitiy")
		self.add_shortcut("W", self.key_layer_mode, "Layer mode")
		self.add_shortcut("Escape", self.key_cancel_actions, "Cancel actions")
		self.add_shortcut("Delete", self.key_delete, "Delete")
		self.add_shortcut("Ctrl+A", self.key_select_all, "Select all")
		self.add_shortcut("Ctrl+Shift+A", self.key_select_none, "Deselect all")
		self.add_shortcut("Ctrl+Z", self.key_undo, "Undo")
		self.add_shortcut("Ctrl+Shift+Z", self.key_redo, "Redo")
		self.add_shortcut("Ctrl+X", self.key_cut, "Cut")
		self.add_shortcut("Ctrl+C", self.key_copy, "Copy")
		self.add_shortcut("Ctrl+V", self.key_paste, "Paste")
		self.add_shortcut("D", self.key_drag, "Drag")
		self.add_shortcut("R", self.key_rotate, "Rotate")
		self.add_shortcut("F", self.key_flip, "Flip")
		self.add_shortcut("M", self.key_mirror, "Mirror")
		self.add_shortcut("S", self.key_snap, "Snap")
		self.add_shortcut("G", self.key_change_grid, "Change grid")
		self.add_shortcut("Ctrl+G", self.key_move_grid, "Move grid")
		self.add_shortcut("Ctrl+Shift+G", self.key_reset_grid, "Reset grid")
		self.add_shortcut("1", lambda: self.key_place_component("circle"), "Place circle")
		self.add_shortcut("2", lambda: self.key_place_component("rectangle"), "Place rectangle")
		self.add_shortcut("3", lambda: self.key_place_component("polygon"), "Place polygon")
		self.add_shortcut("4", lambda: self.key_place_component("line"), "Place line")
		self.add_shortcut("5", lambda: self.key_place_component("arc"), "Place arc")
		self.add_shortcut("6", lambda: self.key_place_component("text"), "Place text")
		self.add_shortcut("0", lambda: self.key_place_component(), "Place component")
		self.add_shortcut("Ctrl+L", lambda: self.key_add_component(), "Add component to library")
	
	def add_shortcut(self, key, func, description=""):
		QShortcut(key, self, func)
		self.shortcuts.append((key,description))
	
	def show_help(self):
		self.helpdialog = HelpDialog(self.shortcuts)
		self.helpdialog.show()
	
	def load_library(self):
		self.library = alterpcb_core.Library()
		for path in sys.argv[1:]:
			if path.endswith("/"):
				path = path[:-1]
			for filename in os.listdir(path):
				if filename.endswith(".alterlib.json"):
					print("Loading '" + path + "/" + filename + "' ...")
					self.library.load_json(path + "/" + filename)
				if filename.endswith(".alterlib.py"):
					print("Loading '" + path + "/" + filename + "' ...")
					self.library.load_python(path + "/" + filename)
		print("Libraries loaded.")
	
	def update_title(self):
		if self.file_name is None:
			name = "Untitled"
		else:
			name = os.path.basename(self.file_name)
		if self.file_modified:
			name += "*"
		self.main.setWindowTitle(name + " - " + self.main.window_title)
	
	def make_instance(self, shape, selected, source=None):
		if source is None:
			return Instance(shape, selected, self.library.component_flatten(shape), self.library.component_handles(shape))
		else:
			return Instance(shape, selected, source.flat, source.handles)
	
	def update_instance(self, inst):
		inst.shape = self.library.component_defaults(inst.shape)
		inst.flat = self.library.component_flatten(inst.shape)
		inst.handles = self.library.component_handles(inst.shape)
	
	def load_blank(self):
		
		# components
		self.components = []
		self.component_current = 0
		
		# file management
		self.file_name = None
		self.file_modified = False
		
		# update everything
		self.main.openlibraryviewer.update()
		self.update_title()
		self.update_params()
		self.update()
	
	def load_json(self, filename):
		self.components = []
		self.component_current = 0
		with open(filename, "r") as f:
			data = json.load(f)
		for component in data:
			instances = []
			for shape in component["shapes"]:
				shape = self.library.component_defaults(shape)
				instances.append(self.make_instance(shape, False))
			self.components.append(Component(
				component["name"], instances,
				view_x=component.get("view_x"), view_y=component.get("view_y"), view_scale=component.get("view_scale"),
				grid_origin_x=component.get("grid_origin_x"), grid_origin_y=component.get("grid_origin_y"), grid_angle=component.get("grid_angle"), grid_step_x=component.get("grid_step_x"), grid_step_y=component.get("grid_step_y"),
			))  
		self.file_name = filename
		self.file_modified = False
		self.main.openlibraryviewer.update()
		self.update_title()
		self.update_params()
		self.update()
	
	def save_json(self, filename):
		data = []
		for component in self.components:
			shapes = []
			for inst in component.instances:
				shapes.append(inst.shape)
			data.append({
				"name": component.name,
				"shapes": shapes,
				"view_x": component.view_x,
				"view_y": component.view_y,
				"view_scale": component.view_scale,
				"grid_step_x": component.grid_step_x,
				"grid_step_y": component.grid_step_y,
			}) 
		with open(filename, "w") as f:
			json.dump(data, f, indent=1)
		self.file_name = filename
		self.file_modified = False
		self.update_title()
	
	def has_component(self):
		return self.component_current < len(self.components)
	
	def get_component(self):
		return self.components[self.component_current]
	
	def change_component(self, index):
		self.cancel_actions()
		self.component_current = index
		self.main.openlibraryviewer.update()
		self.update_title()
		self.update_cursor()
		self.update_params()
		self.update()
	
	def update_cursor(self):
		if self.has_component():
			comp = self.get_component()
			(mx, my) = self.screen_to_pcb(self.mouse_x, self.mouse_y)
			(self.cursor_x, self.cursor_y) = self.snap_to_grid(mx, my)
	
	def screen_to_pcb(self, x, y):
		assert(self.has_component())
		comp = self.get_component()
		return (
			comp.view_x + (x - self.width()  / 2) / comp.view_scale,
			comp.view_y - (y - self.height() / 2) / comp.view_scale,
		)
	
	def pcb_to_screen(self, x, y):
		assert(self.has_component())
		comp = self.get_component()
		return (
			self.width()  / 2 + (x - comp.view_x) * comp.view_scale,
			self.height() / 2 - (y - comp.view_y) * comp.view_scale,
		)
	
	def zoom_around(self, x, y, newscale):
		assert(self.has_component())
		comp = self.get_component()
		comp.view_x += (x - self.width()  / 2) * (1 / comp.view_scale - 1 / newscale)
		comp.view_y -= (y - self.height() / 2) * (1 / comp.view_scale - 1 / newscale)
		comp.view_scale = newscale
		self.update()
	
	def effective_grid_step_x(self):
		assert(self.has_component())
		comp = self.get_component()
		return comp.grid_step_x * 10**max(0, round(math.log10(20.0 / comp.view_scale / comp.grid_step_x)))

	def effective_grid_step_y(self):
		assert(self.has_component())
		comp = self.get_component()
		return comp.grid_step_y * 10**max(0, round(math.log10(20.0 / comp.view_scale / comp.grid_step_y)))
	
	def grid_transform(self, x, y):
		assert(self.has_component())
		comp = self.get_component()
		return alterpcb_core.transform_coordinate(x, y, comp.grid_origin_x, comp.grid_origin_y, comp.grid_angle)
	
	def grid_invtransform(self, x, y):
		assert(self.has_component())
		comp = self.get_component()
		return alterpcb_core.invtransform_coordinate(x, y, comp.grid_origin_x, comp.grid_origin_y, comp.grid_angle)
	
	def snap_to_grid(self, x, y):
		assert(self.has_component())
		comp = self.get_component()
		return alterpcb_core.snap_point(x, y, self.effective_grid_step_x(), self.effective_grid_step_y(), comp.grid_origin_x, comp.grid_origin_y, comp.grid_angle)
	
	def get_layer_order(self):
		layer_current = self.main.layerviewer.get_current()
		layers_copper_top = []
		layers_copper_bot = []
		layers_board_top = []
		layers_board_bot = []
		layers_other = []
		layers_highlight = []
		for layer in self.main.layerviewer.layerstack:
			if self.layer_mode == self.layer_mode_single and layer["name"] == layer_current:
				layers_highlight.append(layer)
			elif layer["name"].endswith("-top"):
				if layer["name"].startswith("copper"):
					layers_copper_top.append(layer)
				else:
					layers_board_top.append(layer)
			elif layer["name"].endswith("-bot"):
				if layer["name"].startswith("copper"):
					layers_copper_bot.append(layer)
				else:
					layers_board_bot.append(layer)
			else:
				layers_other.append(layer)
		if layer_current.endswith("-bot"):
			layers_ordered = layers_board_top[::-1] + layers_copper_top + layers_copper_bot[::-1] + layers_board_bot + layers_other + layers_highlight
			if self.layer_mode == self.layer_mode_all:
				layers_suppressed = 0
			elif self.layer_mode == self.layer_mode_half:
				layers_suppressed = len(layers_board_top) + len(layers_copper_top)
			else:
				layers_suppressed = len(layers_board_top) + len(layers_copper_top) + len(layers_copper_bot) + len(layers_board_bot) + len(layers_other)
		else:
			layers_ordered = layers_board_bot[::-1] + layers_copper_bot + layers_copper_top[::-1] + layers_board_top + layers_other + layers_highlight
			if self.layer_mode == self.layer_mode_all:
				layers_suppressed = 0
			elif self.layer_mode == self.layer_mode_half:
				layers_suppressed =  len(layers_board_bot) + len(layers_copper_bot)
			else:
				layers_suppressed = len(layers_board_bot) + len(layers_copper_bot) + len(layers_copper_top) + len(layers_board_top) + len(layers_other)
		return (layers_ordered, layers_suppressed)
	
	def get_instances_point(self, x, y, globalpos):
		assert(self.has_component())
		comp = self.get_component()
		(layers_ordered, layers_suppressed) = self.get_layer_order()
		layers_active = set()
		for i in range(layers_suppressed, len(layers_ordered)):
			layers_active.add(layers_ordered[i]["name"])
		results = []
		for inst in comp.instances:
			hit = False
			for shape in inst.flat:
				if shape["layer"] not in layers_active:
					continue
				(px, py) = alterpcb_core.shape_to_polygon(shape)
				if shape["outline"] == 0.0:
					poly = QPolygonF([QPointF(px[i], py[i]) for i in range(len(px))])
					if poly.containsPoint(QPointF(x, y), Qt.OddEvenFill):
						hit = True
						break
				else:
					first = 1 if shape["type"] == "polygon" and not shape["closed"] else 0
					for i in range(first, len(px)):
						(px2, py2) = alterpcb_core.stroke_line(px[i - 1], py[i - 1], px[i], py[i], shape["outline"])
						poly = QPolygonF([QPointF(px2[i], py2[i]) for i in range(len(px2))])
						if poly.containsPoint(QPointF(x, y), Qt.OddEvenFill):
							hit = True
							break
			if hit:
				results.append(inst)
		if len(results) > 1:
			menu = QMenu()
			action_all = menu.addAction("All")
			menu.addSeparator()
			actions = []
			for inst in results:
				name = inst.shape["type"]
				if "layer" in inst.shape:
					name += " (" + inst.shape["layer"] + ")"
				actions.append(menu.addAction(name))
			action = menu.exec_(globalpos)
			if action is None:
				results = None
			elif action is not action_all:
				for i in range(len(actions)):
					if actions[i] is action:
						results = [results[i]]
						break
		return results
	
	def get_instances_rect(self, x1, y1, x2, y2):
		assert(self.has_component())
		comp = self.get_component()
		xmin = min(x1, x2)
		xmax = max(x1, x2)
		ymin = min(y1, y2)
		ymax = max(y1, y2)
		(layers_ordered, layers_suppressed) = self.get_layer_order()
		layers_active = set()
		for i in range(layers_suppressed, len(layers_ordered)):
			layers_active.add(layers_ordered[i]["name"])
		results = []
		for inst in comp.instances:
			bbox_xmin = 1e99
			bbox_xmax = -1e99
			bbox_ymin = 1e99
			bbox_ymax = -1e99
			for shape in inst.flat:
				if shape["layer"] not in layers_active:
					continue
				(px, py) = alterpcb_core.shape_to_polygon(shape)
				expand = shape["outline"] / 2
				bbox_xmin = min(bbox_xmin, numpy.amin(px) - expand)
				bbox_xmax = max(bbox_xmax, numpy.amax(px) + expand)
				bbox_ymin = min(bbox_ymin, numpy.amin(py) - expand)
				bbox_ymax = max(bbox_ymax, numpy.amax(py) + expand)
			if bbox_xmin <= bbox_xmax and bbox_ymin <= bbox_ymax and bbox_xmin >= xmin and bbox_xmax <= xmax and bbox_ymin >= ymin and bbox_ymax <= ymax:
				results.append(inst)
		return results
	
	def get_handle_point(self, x, y):
		assert(self.has_component())
		comp = self.get_component()
		dist = 6.0 / comp.view_scale
		for i in range(len(comp.instances)):
			inst = comp.instances[i]
			if inst.selected:
				for j in range(len(inst.handles)):
					handle = inst.handles[j]
					if math.hypot(x - handle["x"], y - handle["y"]) <= dist:
						return (i, j)
		return (None, None)
	
	def transform_selection(self, xfrom=0.0, yfrom=0.0, xto=0.0, yto=0.0, angle=0.0, flip=False, mirror=False):
		assert(self.has_component())
		comp = self.get_component()
		newinstances = []
		for inst in comp.instances:
			if inst.selected:
				shape = self.library.component_transform(inst.shape, xfrom=xfrom, yfrom=yfrom, xto=xto, yto=yto, angle=angle, flip=flip, mirror=mirror)
				newinstances.append(self.make_instance(shape, True))
			else:
				newinstances.append(inst)
		comp.instances = newinstances
		if not self.drag_active and not self.handle_active:
			self.complete_action()
		self.update_params()
		self.update()
	
	def cancel_actions(self):
		assert(self.has_component())
		comp = self.get_component()
		self.select_active = False
		if self.drag_active:
			comp.history_revert()
			self.update_params()
			self.drag_active = False
		if self.handle_active:
			comp.history_revert()
			self.update_params()
			self.handle_active = False
		self.update()
	
	def complete_action(self, soft=False):
		assert(self.has_component())
		comp = self.get_component()
		comp.history_push(soft)
		if not soft and not self.file_modified:
			self.file_modified = True
			self.update_title()
	
	def update_params(self):
		params = []
		if self.has_component():
			comp = self.get_component()
			params_known = set()
			for inst in comp.instances:
				if inst.selected:
					for par in self.library.component_params(inst.shape):
						if par[0] not in params_known:
							params.append(par)
							params_known.add(par[0])
		self.main.paramviewer.set_params(params)
	
	def change_param(self, name, value):
		if not self.has_component():
			return
		comp = self.get_component()
		self.cancel_actions()
		typechange = (name == "type")
		if typechange and not self.library.component_exists(value):
			print("Component '%s' does not exist!" % (value))
			self.update_params()
		else:
			newinstances = []
			for inst in comp.instances:
				if inst.selected and name in inst.shape:
					shape = inst.shape.copy()
					shape[name] = value
					if typechange:
						shape = self.library.component_defaults(shape)
					newinstances.append(self.make_instance(shape, True))
				else:
					newinstances.append(inst)
			comp.instances = newinstances
			self.complete_action()
			# this causes problems when cancel_actions() was called
			#if typechange:
				#self.update_params()
			self.update_params()
			self.update()
	
	def key_reload(self):
		del self.library
		self.load_library()
		instances = set()
		for comp in self.components:
			for i in range(len(comp.history_instances)):
				for inst in comp.history_instances[i].instances:
					instances.add(inst)
			for inst in comp.instances:
				instances.add(inst)
		for inst in instances:
			self.update_instance(inst)
		self.update_params()
		self.update()
	
	def key_file_new(self):
		if self.has_component():
			self.cancel_actions()
		self.load_blank()
	
	def key_file_open(self):
		if self.has_component():
			self.cancel_actions()
		if self.file_name is None:
			directory = ""
		else:
			directory = os.path.dirname(self.file_name)
		(filename, selected_filter) = QFileDialog.getOpenFileName(self, "Open File - " + self.main.window_title, directory, "AlterPCB library files (*.alterlib.json);;All files (*.*)")
		if len(filename) != 0:
			self.load_json(filename)
	
	def key_file_save(self):
		if self.file_name is None:
			self.key_file_save_as()
		else:
			if self.has_component():
				self.cancel_actions()
			self.save_json(self.file_name)
	
	def key_file_save_as(self):
		if self.has_component():
			self.cancel_actions()
		if self.file_name is None:
			directory = ""
		else:
			directory = self.file_name
		(filename, selected_filter) = QFileDialog.getSaveFileName(self, "Save File - " + self.main.window_title, directory, "AlterPCB library files (*.alterlib.json);;All files (*.*)")
		if len(filename) != 0:
			if not filename.endswith(".alterlib.json"):
				filename += ".alterlib.json"
			self.save_json(filename)
	
	def key_export(self):
		if not self.has_component():
			return
		comp = self.get_component()
		if self.file_name is None:
			directory = ""
		else:
			directory = self.file_name
		(filename, selected_filter) = QFileDialog.getSaveFileName(self, "Export Gerber/Drill Files - " + self.main.window_title, directory, "Zip files (*.zip);;All files (*.*)")
		if len(filename) != 0:
			if filename.endswith(".zip"):
				filename = filename[:-4]
			pcb = alterpcb_core.Pcb()
			for inst in comp.instances:
				pcb.shapes += inst.flat
			pcb.export(os.path.dirname(filename), os.path.basename(filename), self.main.layerviewer.layerstack)
	
	def key_export_image(self):
		if not self.has_component():
			return
		comp = self.get_component()
		if self.file_name is None:
			directory = ""
		else:
			directory = self.file_name
		(filename, selected_filter) = QFileDialog.getSaveFileName(self, "Export SVG File - " + self.main.window_title, directory, "SVG files (*.svg);;All files (*.*)")
		if len(filename) != 0:
			if not filename.endswith(".svg"):
				filename += ".svg"
			pcb = alterpcb_core.Pcb()
			for inst in comp.instances:
				pcb.shapes += inst.flat
			pcb.export_svg(filename, self.main.layerviewer.layerstack)
	
	def key_antialias(self):
		self.antialias = not self.antialias
		self.update()
	
	def key_quality(self):
		self.quality = (self.quality + 1) % self.quality_count
		self.update()
	
	def key_layer_mode(self):
		self.layer_mode = (self.layer_mode + 1) % self.layer_mode_count
		self.update()
	
	def key_cancel_actions(self):
		self.main.paramviewer.cancel_change()
		self.setFocus(Qt.OtherFocusReason)
		if self.has_component():
			self.cancel_actions()
	
	def key_delete(self):
		if not self.has_component():
			return
		comp = self.get_component()
		self.cancel_actions()
		newinstances = []
		for inst in comp.instances:
			if not inst.selected:
				newinstances.append(inst)
		comp.instances = newinstances
		self.complete_action()
		self.update_params()
		self.update()
	
	def key_select_all(self):
		if not self.has_component():
			return
		comp = self.get_component()
		self.cancel_actions()
		newinstances = []
		for inst in comp.instances:
			newinstances.append(self.make_instance(inst.shape, True, source=inst)),
		comp.instances = newinstances
		self.complete_action(True)
		self.update_params()
		self.update()
	
	def key_select_none(self):
		if not self.has_component():
			return
		comp = self.get_component()
		self.cancel_actions()
		newinstances = []
		for inst in comp.instances:
			newinstances.append(self.make_instance(inst.shape, False, source=inst)),
		comp.instances = newinstances
		self.complete_action(True)
		self.update_params()
		self.update()
	
	def key_undo(self):
		if not self.has_component():
			return
		comp = self.get_component()
		self.cancel_actions()
		comp.history_undo()
		if not self.file_modified:
			self.file_modified = True
			self.update_title()
		self.update_params()
		self.update()
	
	def key_redo(self):
		if not self.has_component():
			return
		comp = self.get_component()
		self.cancel_actions()
		comp.history_redo()
		if not self.file_modified:
			self.file_modified = True
			self.update_title()
		self.update_params()
		self.update()
	
	def key_cut(self):
		if not self.has_component():
			return
		comp = self.get_component()
		self.cancel_actions()
		shapes = []
		newinstances = []
		for inst in comp.instances:
			if inst.selected:
				shapes.append(self.library.component_transform(inst.shape, xfrom=self.cursor_x, yfrom=self.cursor_y))
			else:
				newinstances.append(inst)
		comp.instances = newinstances
		self.complete_action()
		self.update_params()
		self.update()
		text = json.dumps(shapes, indent=1)
		clipboard = QApplication.clipboard()
		clipboard.setText(text)
	
	def key_copy(self):
		if not self.has_component():
			return
		comp = self.get_component()
		self.cancel_actions()
		shapes = []
		for inst in comp.instances:
			if inst.selected:
				shapes.append(self.library.component_transform(inst.shape, xfrom=self.cursor_x, yfrom=self.cursor_y))
		text = json.dumps(shapes, indent=1)
		clipboard = QApplication.clipboard()
		clipboard.setText(text)
	
	def key_paste(self):
		if not self.has_component():
			return
		comp = self.get_component()
		self.cancel_actions()
		clipboard = QApplication.clipboard()
		text = clipboard.text()
		if len(text) == 0:
			return
		try:
			shapes = json.loads(text)
		except Exception as e:
			print(e)
		else:
			newinstances = []
			for inst in comp.instances:
				newinstances.append(self.make_instance(inst.shape, False, source=inst))
			for shape in shapes:
				shape = self.library.component_transform(self.library.component_defaults(shape), xto=self.cursor_x, yto=self.cursor_y)
				newinstances.append(self.make_instance(shape, True))
			comp.instances = newinstances
			self.complete_action()
			self.drag_active = True
			self.update_params()
			self.update()
	
	def key_drag(self):
		if not self.has_component():
			return
		comp = self.get_component()
		if not self.drag_active:
			self.cancel_actions()
			self.drag_active = True
	
	def key_rotate(self):
		if not self.has_component():
			return
		comp = self.get_component()
		self.transform_selection(xfrom=self.cursor_x, yfrom=self.cursor_y, xto=self.cursor_x, yto=self.cursor_y, angle=90.0)
	
	def key_flip(self):
		if not self.has_component():
			return
		comp = self.get_component()
		self.transform_selection(xfrom=self.cursor_x, yfrom=self.cursor_y, xto=self.cursor_x, yto=self.cursor_y, flip=True)
	
	def key_mirror(self):
		if not self.has_component():
			return
		comp = self.get_component()
		self.transform_selection(xfrom=self.cursor_x, yfrom=self.cursor_y, xto=self.cursor_x, yto=self.cursor_y, mirror=True)
	
	def key_snap(self):
		if not self.has_component():
			return
		comp = self.get_component()
		self.cancel_actions()
		newinstances = []
		for inst in comp.instances:
			if inst.selected:
				shape = self.library.component_snap(inst.shape, self.effective_grid_step_x(), self.effective_grid_step_y(), comp.grid_origin_x, comp.grid_origin_y, comp.grid_angle)
				newinstances.append(self.make_instance(shape, True))
			else:
				newinstances.append(inst)
		comp.instances = newinstances
		self.complete_action()
		self.update_params()
		self.update()
	
	def key_change_grid(self):
		if not self.has_component():
			return
		comp = self.get_component()
		(value, ok) = QInputDialog.getDouble(self, "Change grid", "Grid step:", comp.grid_step_x, 0.0001, 100.0, 4)
		if not ok:
			return
		comp.grid_step_x = value
		comp.grid_step_y = value
		self.update_cursor()
		self.update()
	
	def key_move_grid(self):
		if not self.has_component():
			return
		comp = self.get_component()
		comp.grid_origin_x = 0.0
		comp.grid_origin_y = 0.0
		comp.grid_angle = 0.0
		for inst in comp.instances:
			if inst.selected:
				comp.grid_origin_x = inst.shape.get("x", 0.0)
				comp.grid_origin_y = inst.shape.get("y", 0.0)
				comp.grid_angle = inst.shape.get("angle", 0.0)
				break
		self.update_cursor()
		self.update()
	
	def key_reset_grid(self):
		if not self.has_component():
			return
		comp = self.get_component()
		comp.grid_origin_x = 0.0
		comp.grid_origin_y = 0.0
		comp.grid_angle = 0.0
		self.update_cursor()
		self.update()
	
	def key_place_component(self, name=None):
		if not self.has_component():
			return
		comp = self.get_component()
		if name is None:
			(name, ok) = QInputDialog.getText(self, "Place component", "Component name:", QLineEdit.Normal, "")
			if not ok:
				return
		self.cancel_actions()
		newinstances = []
		for inst in comp.instances:
			newinstances.append(self.make_instance(inst.shape, False, source=inst))
		shape = {
			"type": name,
			"layer": self.main.layerviewer.get_current(),
		}
		shape = self.library.component_transform(self.library.component_defaults(shape), xto=self.cursor_x, yto=self.cursor_y)
		newinstances.append(self.make_instance(shape, True))
		comp.instances = newinstances
		self.complete_action()
		self.drag_active = True
		self.update_params()
		self.update()
	
	def key_add_component(self):
		(name, ok) = QInputDialog.getText(self, "Add component to library", "Component name:", QLineEdit.Normal, "")
		if not ok:
			return
		if self.has_component():
			self.cancel_actions()
		self.components.append(Component(name, []))
		self.component_current = len(self.components) - 1
		self.file_modified = True
		self.main.openlibraryviewer.update()
		self.update_title()
		self.update_params()
		self.update()
	
	def sizeHint(self):
		return QSize(600, 600)
	def minimumSizeHint(self):
		return QSize(200, 200)
	
	def wheelEvent(self, event):
		if self.has_component():
			comp = self.get_component()
			self.zoom_around(event.x(), event.y(), comp.view_scale * 10**(event.delta() / 1200))
		event.accept()
	
	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			if self.has_component():
				comp = self.get_component()
				if self.drag_active:
					self.drag_active = False
					self.complete_action()
				else:
					(x, y) = self.screen_to_pcb(event.x(), event.y())
					(instance, index) = self.get_handle_point(x, y)
					if instance is None:
						self.select_active = True
						(self.select_x1, self.select_y1) = (x, y)
						(self.select_x2, self.select_y2) = (self.select_x1, self.select_y1)
					else:
						self.handle_active = True
						(self.handle_instance, self.handle_index) = (instance, index)
				self.update()
			event.accept()
		elif event.button() == Qt.MidButton:
			if self.has_component():
				comp = self.get_component()
				self.pan_active = True
				(self.pan_x, self.pan_y) = self.screen_to_pcb(event.x(), event.y())
			event.accept()
		elif event.button() == Qt.RightButton:
			if self.has_component():
				comp = self.get_component()
				(x, y) = self.screen_to_pcb(event.x(), event.y())
				(instance, index) = self.get_handle_point(x, y)
				if instance is not None:
					inst = comp.instances[instance]
					handles = inst.handles[index]
					actions = handles.get("actions", [])
					if len(actions) != 0:
						menu = QMenu()
						actions2 = []
						for action in actions:
							actions2.append(menu.addAction(action["name"]))
						action = menu.exec_(event.globalPos())
						if action is not None:
							for i in range(len(actions)):
								if actions2[i] is action:
									newinstances = []
									for j in range(len(comp.instances)):
										inst = comp.instances[j]
										if j == instance:
											shape = actions[i]["callback"](inst.shape, index)
											newinstances.append(self.make_instance(shape, True))
										else:
											newinstances.append(inst)
									comp.instances = newinstances
									self.complete_action()
									self.update_params()
									self.update()
									break
			event.accept()
		elif event.button() == Qt.XButton1:
			self.main.layerviewer.key_previous_layer()
			event.accept()
		elif event.button() == Qt.XButton2:
			self.main.layerviewer.key_next_layer()
			event.accept()
	
	def mouseReleaseEvent(self, event):
		if event.button() == Qt.LeftButton:
			if self.has_component():
				comp = self.get_component()
				if self.select_active:
					self.select_active = False
					if math.hypot(self.select_x2 - self.select_x1, self.select_y2 - self.select_y1) * comp.view_scale < 2.5:
						results = self.get_instances_point(self.select_x1, self.select_y1, event.globalPos())
					else:
						results = self.get_instances_rect(self.select_x1, self.select_y1, self.select_x2, self.select_y2)
					if results is not None:
						tables = [
							[False, True , False, True ],
							[False, True , True , True ],
							[False, False, True , False],
							[False, False, False, True ],
						]
						ctrl = ((event.modifiers() & Qt.CTRL) != 0)
						shift = ((event.modifiers() & Qt.SHIFT) != 0)
						table = tables[ctrl * 2 + shift]
						results = set(results)
						newinstances = []
						for inst in comp.instances:
							newinstances.append(self.make_instance(inst.shape, table[inst.selected * 2 + (inst in results)], source=inst)),
						comp.instances = newinstances
						self.complete_action(True)
						self.update_params()
					self.update()
				if self.handle_active:
					self.handle_active = False
					self.complete_action()
					self.update()
			event.accept()
		elif event.button() == Qt.MidButton:
			if self.has_component():
				comp = self.get_component()
				self.pan_active = False
			event.accept()
	
	def mouseMoveEvent(self, event):
		self.mouse_x = event.x()
		self.mouse_y = event.y()
		if self.has_component():
			comp = self.get_component()
			(mx, my) = self.screen_to_pcb(self.mouse_x, self.mouse_y)
			if self.pan_active:
				comp.view_x += self.pan_x - mx
				comp.view_y += self.pan_y - my
				mx = self.pan_x
				my = self.pan_y
			(cx, cy) = self.snap_to_grid(mx, my)
			if self.select_active:
				(self.select_x2, self.select_y2) = (mx, my)
			if self.drag_active and (cx != self.cursor_x or cy != self.cursor_y):
				newinstances = []
				for inst in comp.instances:
					if inst.selected:
						shape = self.library.component_transform(inst.shape, self.cursor_x, self.cursor_y, cx, cy, 0.0, False, False)
						newinstances.append(self.make_instance(shape, True))
					else:
						newinstances.append(inst)
				comp.instances = newinstances
				self.update_params()
			if self.handle_active:
				newinstances = []
				for i in range(len(comp.instances)):
					inst = comp.instances[i]
					if i == self.handle_instance:
						shape = self.library.component_handlemove(inst.shape, self.handle_index, cx, cy)
						newinstances.append(self.make_instance(shape, True))
					else:
						newinstances.append(inst)
				comp.instances = newinstances
				self.update_params()
			self.cursor_active = True
			(self.cursor_x, self.cursor_y) = (cx, cy)
			self.update()
		event.accept()
	
	def leaveEvent(self, event):
		if self.has_component():
			comp = self.get_component()
		self.cursor_active = False
		self.update()
		event.accept()
	
	def paintEvent(self, event):
		painter = QPainter(self)
		if self.antialias:
			painter.setRenderHint(QPainter.Antialiasing)
		
		#t1 = time.clock()
		
		# background
		painter.fillRect(0, 0, self.width(), self.height(), self.color_background)
		
		if not self.has_component():
			return
		comp = self.get_component()
		
		def set_transform(painter):
			painter.translate(self.width() / 2, self.height() / 2)
			painter.scale(comp.view_scale, -comp.view_scale)
			painter.translate(-comp.view_x, -comp.view_y)
		
		# view setup
		set_transform(painter)
		view_xmin = comp.view_x - self.width() / (2 * comp.view_scale)
		view_xmax = comp.view_x + self.width() / (2 * comp.view_scale)
		view_ymin = comp.view_y - self.height() / (2 * comp.view_scale)
		view_ymax = comp.view_y + self.height() / (2 * comp.view_scale)
		step_x = self.effective_grid_step_x()
		step_y = self.effective_grid_step_y()
		(gx1, gy1) = self.grid_invtransform(view_xmin, view_ymin)
		(gx2, gy2) = self.grid_invtransform(view_xmax, view_ymin)
		(gx3, gy3) = self.grid_invtransform(view_xmin, view_ymax)
		(gx4, gy4) = self.grid_invtransform(view_xmax, view_ymax)
		gxmin = min(gx1, gx2, gx3, gx4)
		gxmax = max(gx1, gx2, gx3, gx4)
		gymin = min(gy1, gy2, gy3, gy4)
		gymax = max(gy1, gy2, gy3, gy4)
		
		# get layer order
		(layers_ordered, layers_suppressed) = self.get_layer_order()
		
		# collect shapes by layer
		layer_shapes = {}
		for layer in layers_ordered:
			layer_shapes[layer["name"]] = []
		for inst in comp.instances:
			for shape in inst.flat:
				ls = layer_shapes.get(shape["layer"])
				if ls is not None:
					ls.append(shape)
		
		# draw layers
		for ll in range(len(layers_ordered)):
			layer = layers_ordered[ll]
			
			# draw grid
			if ll == layers_suppressed:
				if layers_suppressed != 0:
					painter.resetTransform()
					painter.fillRect(0, 0, self.width(), self.height(), self.color_suppress)
					set_transform(painter)
				for xi in range(int(math.ceil(gxmin / step_x)), int(math.floor(gxmax / step_x)) + 1):
					xx = xi * step_x
					painter.setPen(self.color_grid2 if xi % 10 == 0 else self.color_grid1)
					(px1, py1) = self.grid_transform(xx, gymin)
					(px2, py2) = self.grid_transform(xx, gymax)
					painter.drawLine(QPointF(px1, py1), QPointF(px2, py2))
				for yi in range(int(math.ceil(gymin / step_y)), int(math.floor(gymax / step_y)) + 1):
					yy = yi * step_y
					painter.setPen(self.color_grid2 if yi % 10 == 0 else self.color_grid1)
					(px1, py1) = self.grid_transform(gxmin, yy)
					(px2, py2) = self.grid_transform(gxmax, yy)
					painter.drawLine(QPointF(px1, py1), QPointF(px2, py2))
			
			# choose color
			if ll < layers_suppressed:
				if self.quality == self.quality_low:
					continue
				layerpen   = QColor.fromRgbF(layer["color"][0]*0.2+0.4, layer["color"][1]*0.2+0.4, layer["color"][2]*0.2+0.4, 0.50)
				layerbrush = QColor.fromRgbF(layer["color"][0]*0.4+0.4, layer["color"][1]*0.4+0.4, layer["color"][2]*0.4+0.4, 0.25)
			else:
				layerpen   = QColor.fromRgbF(layer["color"][0]*0.5, layer["color"][1]*0.5, layer["color"][2]*0.5, 0.50)
				layerbrush = QColor.fromRgbF(layer["color"][0]    , layer["color"][1]    , layer["color"][2]    , 0.25)
			
			# collect shapes by order
			order_shapes = {}
			for shape in layer_shapes[layer["name"]]:
				order = shape["order"] * 2 + 1 if shape["hole"] else shape["order"] * 2
				if order not in order_shapes:
					order_shapes[order] = []
				order_shapes[order].append(shape)
			orders = list(order_shapes.keys())
			orders.sort()
			
			if self.quality == self.quality_high:
				
				# create image
				img = QImage(self.width(), self.height(), QImage.Format_ARGB32_Premultiplied)
				img.fill(0)
				imgpainter = QPainter(img)
				if self.antialias:
					imgpainter.setRenderHint(QPainter.Antialiasing)
				set_transform(imgpainter)
				
				# draw shapes in order
				imgpainter.setPen(Qt.NoPen)
				imgpainter.setBrush(QColor(0, 0, 0, 255)) # layer["color"][0], layer["color"][1], layer["color"][2]
				for order in orders:
					imgpainter.setCompositionMode(QPainter.CompositionMode_SourceOver if order % 2 == 0 else QPainter.CompositionMode_DestinationOut)
					for shape in order_shapes[order]:
						(px, py) = alterpcb_core.shape_to_polygon(shape)
						if shape["outline"] == 0.0:
							imgpainter.drawPolygon([QPointF(px[i], py[i]) for i in range(len(px))])
						else:
							first = 1 if shape["type"] == "polygon" and not shape["closed"] else 0
							for i in range(first, len(px)):
								(px2, py2) = alterpcb_core.stroke_line(px[i - 1], py[i - 1], px[i], py[i], shape["outline"])
								imgpainter.drawPolygon([QPointF(px2[i], py2[i]) for i in range(len(px2))])
				imgpainter.resetTransform()
				imgpainter.setCompositionMode(QPainter.CompositionMode_SourceIn)
				imgpainter.fillRect(0, 0, self.width(), self.height(), layerbrush)
				imgpainter.end()
				
				# draw the image
				painter.resetTransform()
				painter.drawImage(0, 0, img)
				set_transform(painter)
			
			# draw the outline
			for order in orders:
				painter.setPen(layerpen)
				painter.setBrush(layerbrush if order % 2 == 0 and self.quality != self.quality_high else Qt.NoBrush)
				for shape in order_shapes[order]:
					(px, py) = alterpcb_core.shape_to_polygon(shape)
					if shape["outline"] == 0.0:
						painter.drawPolygon([QPointF(px[i], py[i]) for i in range(len(px))])
					else:
						first = 1 if shape["type"] == "polygon" and not shape["closed"] else 0
						for i in range(first, len(px)):
							(px2, py2) = alterpcb_core.stroke_line(px[i - 1], py[i - 1], px[i], py[i], shape["outline"])
							painter.drawPolygon([QPointF(px2[i], py2[i]) for i in range(len(px2))])
		
		# draw selection
		for pen in (False, True):
			painter.setPen(self.color_selectionpen if pen else Qt.NoPen)
			painter.setBrush(Qt.NoBrush if pen else self.color_selectionbrush)
			for inst in comp.instances:
				if inst.selected:
					for shape in inst.flat:
						(px, py) = alterpcb_core.shape_to_polygon(shape)
						if shape["outline"] == 0.0:
							painter.drawPolygon([QPointF(px[i], py[i]) for i in range(len(px))])
						else:
							first = 1 if shape["type"] == "polygon" and not shape["closed"] else 0
							for i in range(first, len(px)):
								(px2, py2) = alterpcb_core.stroke_line(px[i - 1], py[i - 1], px[i], py[i], shape["outline"])
								painter.drawPolygon([QPointF(px2[i], py2[i]) for i in range(len(px2))])
		
		# draw handles
		painter.setPen(self.color_handlepen)
		painter.setBrush(self.color_handlebrush)
		for inst in comp.instances:
			if inst.selected:
				for handle in inst.handles:
					painter.drawEllipse(QPointF(handle["x"], handle["y"]), 4.0 / comp.view_scale, 4.0 / comp.view_scale)
		
		# draw cursor
		painter.setPen(QPen(self.color_cursor, 0, Qt.DashLine))
		painter.setBrush(Qt.NoBrush)
		if self.select_active:
			if self.select_x1 != self.select_x2:
				painter.drawLine(QPointF(self.select_x1, self.select_y1), QPointF(self.select_x2, self.select_y1))
				painter.drawLine(QPointF(self.select_x1, self.select_y2), QPointF(self.select_x2, self.select_y2))
			if self.select_y1 != self.select_y2:
				painter.drawLine(QPointF(self.select_x1, self.select_y1), QPointF(self.select_x1, self.select_y2))
				painter.drawLine(QPointF(self.select_x2, self.select_y1), QPointF(self.select_x2, self.select_y2))
		elif self.cursor_active:
			(cx, cy) = self.grid_invtransform(self.cursor_x, self.cursor_y)
			(px1, py1) = self.grid_transform(cx, gymin)
			(px2, py2) = self.grid_transform(cx, gymax)
			painter.drawLine(QPointF(px1, py1), QPointF(px2, py2))
			(px1, py1) = self.grid_transform(gxmin, cy)
			(px2, py2) = self.grid_transform(gxmax, cy)
			painter.drawLine(QPointF(px1, py1), QPointF(px2, py2))
		
		# draw cursor coordinates
		painter.resetTransform()
		painter.setPen(QColor(168, 34, 3))
		font = QFont("Monospace")
		font.setPixelSize(12)
		painter.setFont(font)
		painter.drawText(QPointF(10,20), "X: " + str(self.cursor_x))
		painter.drawText(QPointF(10,40), "Y: " + str(self.cursor_y))
		#t2 = time.clock()
		#print("Draw time: %6.3f s" % (t2 - t1))

class LayerViewer(QWidget):
	
	rowheight = 20
	
	def __init__(self, main, parent):
		super(LayerViewer, self).__init__(parent)
		self.main = main
		
		# initialize variables
		self.layerstack = []
		self.layer_current = 0;
		
		# widget settings
		self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
		self.setFocusPolicy(Qt.ClickFocus)
		self.setAttribute(Qt.WA_OpaquePaintEvent)
		
		# shortcuts
		QShortcut(QKeySequence(Qt.Key_PageUp), self, self.key_previous_layer)
		QShortcut(QKeySequence(Qt.Key_PageDown), self, self.key_next_layer)
		QShortcut(QKeySequence(Qt.Key_V), self, self.key_flip_layer)
	
	def load_json(self, filename):
		with open(filename, "r") as f:
			self.layerstack = json.load(f)
		self.update()
	
	def get_current(self):
		return self.layerstack[self.layer_current]["name"] if self.layer_current < len(self.layerstack) else ""
	
	def key_previous_layer(self):
		self.layer_current = (self.layer_current - 1) % len(self.layerstack)
		self.update()
		self.main.layoutviewer.update()
	
	def key_next_layer(self):
		self.layer_current = (self.layer_current + 1) % len(self.layerstack)
		self.update()
		self.main.layoutviewer.update()
	
	def key_flip_layer(self):
		old = self.layerstack[self.layer_current]["name"]
		new = alterpcb_core.flip_layer(old)
		if old != new:
			for i in range(len(self.layerstack)):
				if self.layerstack[i]["name"] == new:
					self.layer_current = i
					break
			self.update()
			self.main.layoutviewer.update()
	
	def sizeHint(self):
		return QSize(150, 200)
	def minimumSizeHint(self):
		return QSize(150, 200)
	
	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			row = event.y() // self.rowheight
			if row >= 0 and row < len(self.layerstack):
				self.layer_current = row
				self.update()
				self.main.layoutviewer.update()
			event.accept()
		elif event.button() == Qt.XButton1:
			self.key_previous_layer()
			event.accept()
		elif event.button() == Qt.XButton2:
			self.key_next_layer()
			event.accept()
		
	def paintEvent(self, event):
		painter = QPainter(self)
		
		# background
		painter.fillRect(0, 0, self.width(), self.height(), QColor(255, 255, 255))
		
		# current layer
		painter.fillRect(0, self.layer_current * self.rowheight, self.width(), self.rowheight, QColor(192, 192, 192))
		
		# layers
		font = QFont("Sans")
		font.setPixelSize(12)
		painter.setFont(font)
		for i in range(len(self.layerstack)):
			layer = self.layerstack[i]
			painter.setPen(QColor.fromRgbF(layer["color"][0]*0.5, layer["color"][1]*0.5, layer["color"][2]*0.5))
			painter.setBrush(QColor.fromRgbF(layer["color"][0]*0.5+0.5, layer["color"][1]*0.5+0.5, layer["color"][2]*0.5+0.5))
			painter.drawRect(2, i * self.rowheight + 2, self.rowheight - 5, self.rowheight - 5)
			painter.setPen(QColor(0, 0, 0))
			painter.drawText(self.rowheight + 2, i * self.rowheight, self.width() - self.rowheight - 4, self.rowheight, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextSingleLine, layer["name"])

class OpenLibraryViewer(QWidget):
	
	rowheight = 20
	
	def __init__(self, main, parent):
		super(OpenLibraryViewer, self).__init__(parent)
		self.main = main
		
		# widget settings
		self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
		self.setFocusPolicy(Qt.ClickFocus)
		self.setAttribute(Qt.WA_OpaquePaintEvent)
	
	def sizeHint(self):
		return QSize(150, 200)
	def minimumSizeHint(self):
		return QSize(150, 200)
	
	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			row = event.y() // self.rowheight
			if row >= 0 and row < len(self.main.layoutviewer.components):
				self.main.layoutviewer.change_component(row)
			event.accept()
		
	def paintEvent(self, event):
		painter = QPainter(self)
		
		# background
		painter.fillRect(0, 0, self.width(), self.height(), QColor(255, 255, 255))
		
		# current layer
		painter.fillRect(0, self.main.layoutviewer.component_current * self.rowheight, self.width(), self.rowheight, QColor(192, 192, 192))
		
		# layers
		font = QFont("Sans")
		font.setPixelSize(12)
		painter.setFont(font)
		for i in range(len(self.main.layoutviewer.components)):
			component = self.main.layoutviewer.components[i]
			painter.setPen(QColor(0, 0, 0))
			painter.drawText(2, i * self.rowheight, self.width() - 4, self.rowheight, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextSingleLine, component.name)

class ParamViewer(QWidget):
	
	def __init__(self, main, parent):
		super(ParamViewer, self).__init__(parent)
		self.main = main
		
		# initialize variables
		self.params = []
		self.labels = []
		self.editors = []
		
		# widget settings
		self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
		self.setFocusPolicy(Qt.ClickFocus)
		
		# layout
		self.gridlayout = QGridLayout(self)
	
	def sizeHint(self):
		hint = super(ParamViewer, self).sizeHint()
		return QSize(200, hint.height())
	def minimumSizeHint(self):
		hint = super(ParamViewer, self).minimumSizeHint()
		return QSize(200, hint.height())
	
	def set_params(self, params):
		
		# save old widgets for reuse
		oldwidgets = {}
		for i in range(len(self.params)):
			(name, value) = self.params[i]
			self.gridlayout.removeWidget(self.labels[i])
			self.gridlayout.removeWidget(self.editors[i])
			oldwidgets[name] = (self.labels[i], self.editors[i])
		
		# delete old widgets
		#for label in self.labels:
			#label.deleteLater()
		#for editor in self.editors:
			#editor.deleteLater()
		
		# create new ones
		self.params = params
		self.labels = []
		self.editors = []
		#layout = QGridLayout(self)
		for i in range(len(self.params)):
			(name, value) = self.params[i]
			if name in oldwidgets:
				(label, editor) = oldwidgets.pop(name)
				editor.setText(repr(value))
			else:
				label = QLabel(name, self)
				editor = QLineEdit(repr(value), self)
			editor.returnPressed.connect(lambda: self.main.layoutviewer.setFocus(Qt.OtherFocusReason))
			editor.editingFinished.connect(lambda i=i: self.change_param(i))
			self.gridlayout.addWidget(label, i, 0)
			self.gridlayout.addWidget(editor, i, 1)
			self.labels.append(label)
			self.editors.append(editor)
		self.gridlayout.setRowStretch(len(params), 1)
		self.resize(self.sizeHint())
		
		# delete old widgets
		for name in oldwidgets:
			(label, editor) = oldwidgets[name]
			label.deleteLater()
			editor.deleteLater()
	
	def change_param(self, i):
		(name, value) = self.params[i]
		editor = self.editors[i]
		text = editor.text()
		if text != repr(value):
			try:
				global_vars = {}
				for pair in inspect.getmembers(math):
					if not pair[0].startswith("_"):
						global_vars[pair[0]] = pair[1]
				value2 = type(value)(eval(editor.text(), global_vars))
			except Exception as e:
				print(e)
				editor.setText(repr(value))
			else:
				editor.setText(repr(value2))
				self.params[i] = (name, value2)
				self.main.layoutviewer.change_param(name, value2) # this may trigger a call to set_params()
	
	def cancel_change(self):
		for i in range(len(self.params)):
			(name, value) = self.params[i]
			self.editors[i].setText(repr(value))

class MainWindow(QMainWindow):
	
	window_title = "AlterPCB"
	
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent)
		
		# widget settings
		self.setWindowTitle(self.window_title)
		#self.setMinimumSize(400, 400)
		
		# central widget and layout
		self.splitter1 = QSplitter(Qt.Horizontal, self)
		self.setCentralWidget(self.splitter1)
		
		self.splitter2 = QSplitter(Qt.Vertical, self.splitter1)
		
		layerviewer_scroll = QScrollArea(self.splitter2)
		self.layerviewer = LayerViewer(self, layerviewer_scroll)
		layerviewer_scroll.setWidget(self.layerviewer)
		layerviewer_scroll.setWidgetResizable(True)
		layerviewer_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		layerviewer_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		
		openlibraryviewer_scroll = QScrollArea(self.splitter2)
		self.openlibraryviewer = OpenLibraryViewer(self, openlibraryviewer_scroll)
		openlibraryviewer_scroll.setWidget(self.openlibraryviewer)
		openlibraryviewer_scroll.setWidgetResizable(True)
		openlibraryviewer_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		openlibraryviewer_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		
		self.splitter2.addWidget(layerviewer_scroll)
		self.splitter2.addWidget(openlibraryviewer_scroll)
		self.splitter2.setStretchFactor(0, 1)
		self.splitter2.setStretchFactor(1, 1)
		
		paramviewer_scroll = QScrollArea(self.splitter1)
		self.paramviewer = ParamViewer(self, paramviewer_scroll)
		paramviewer_scroll.setWidget(self.paramviewer)
		paramviewer_scroll.setWidgetResizable(True)
		paramviewer_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		paramviewer_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		
		self.layoutviewer = LayoutViewer(self, self.splitter1)
		
		self.splitter1.addWidget(self.splitter2)
		self.splitter1.addWidget(self.layoutviewer)
		self.splitter1.addWidget(paramviewer_scroll)
		self.splitter1.setStretchFactor(0, 0)
		self.splitter1.setStretchFactor(1, 1)
		self.splitter1.setStretchFactor(2, 0)
		
		# load everything
		self.layerviewer.load_json("layerstacks/4_layer.alterstack.json")
		#self.layoutviewer.load_json("testshapes.json")
		
		# show window
		self.showMaximized()

class HelpDialog(QDialog):
	def __init__(self, shortcuts):
		QDialog.__init__(self)
		self.setWindowTitle("Help")
		self.shortcuts = shortcuts
		
		self.html_about = " <!DOCTYPE html><html><body><center><h1>Hotkeys</h1>"
		self.html_about += " <table>"
		self.html_about += "<tr><td></td><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td><td></td></tr>"
		for i in range(len(self.shortcuts)):
			self.html_about += "<tr><td>"+str(self.shortcuts[i][0])+"</td><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td><td>"+str(self.shortcuts[i][1])+"</td></tr>"
		self.html_about += "</table> "
		self.html_about += "</center></body></html> "
		

		self.textbrowser = QTextBrowser();
		self.textbrowser.setHtml(self.html_about);
		self.textbrowser.setMinimumSize(500, 700);

		layout = QVBoxLayout();
		layout.setSpacing(0)
		layout.setContentsMargins(0,0,0,0)
		
		layout.addWidget(self.textbrowser);
		self.setLayout(layout)



app = QApplication(sys.argv)
window = MainWindow()
app.exec_()

# Delete the libraries. This is necessary to prevent problems with freetype fonts being unloaded too late.
# Not doing this will in some cases result in SIGSEGV when closing the program. This might be caused by Qt, I'm not sure.
del window.layoutviewer.library
#del window
