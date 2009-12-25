"""
Copyright (c) 2009 Marian Tietz
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHORS AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
"""

import gtk
import re

from .. import config
from .. import gui
from ..helper import color
from ..lib import contrast

builder = gtk.Builder()

def dialog_responce_cb(dialog, id):
	dialog.destroy()

def run():

	output_bg = gui.widgets.get_widget("output")\
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

		ccolor = color.COLOR_TABLE[i]

		box.modify_bg(gtk.STATE_NORMAL,
			contrast.contrast_render_foreground_color(output_bg,
				ccolor))


	builder.get_object("colorTable").show_all()


def setup():
	path = config.get("gladefiles","dialogs") + "colorTable.ui"

	builder.add_from_file(path)

	dialog = builder.get_object("colorTable")
	dialog.connect("response", dialog_responce_cb)
