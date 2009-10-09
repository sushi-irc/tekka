import gtk
import re

import config
import helper.color
import lib.gui_control
import lib.contrast

builder = gtk.Builder()

def dialog_responce_cb(dialog, id):
	dialog.destroy()

def run():

	output_bg = lib.gui_control.widgets.get_widget("output")\
		.get_style().base[gtk.STATE_NORMAL]
	pattern = re.compile("eventbox([0-9]*)")
	table = builder.get_object("table1")
	boxes = [n for n in table.get_children() if type(n) == gtk.EventBox]

	for box in boxes:
		name = box.get_property("name")

		match = pattern.match(name)

		if not match:
			raise ValueError, "Invalid event box in table."

		i = int(match.groups()[0]) - 1

		ccolor = helper.color.COLOR_TABLE[i]

		box.modify_bg(gtk.STATE_NORMAL,
			lib.contrast.contrast_render_foreground_color(output_bg,
				ccolor))


	builder.get_object("colorTable").show_all()


def setup():
	path = config.get("gladefiles","dialogs") + "colorTable.ui"

	builder.add_from_file(path)

	dialog = builder.get_object("colorTable")
	dialog.connect("response", dialog_responce_cb)
