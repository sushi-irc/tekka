# coding: UTF-8
"""
Copyright (c) 2008 Marian Tietz
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
from gettext import gettext as _
from .. import gui
import logging

error_textview = gtk.TextView()

def button_clicked_cb(button, textView):
	"""
		compile statement and run it.
	"""
	logging.info("debugDialog: Compile and run!")
	exec(textView.get_buffer().get_property("text"))

def destroy_dialog(dialog, rid):
	dialog.destroy()

def run():
	ag = gtk.AccelGroup()

	dialog = gtk.Dialog(
		title="Debug dialog",
		parent=gui.widgets.get_object("mainWindow"),
		flags=gtk.DIALOG_DESTROY_WITH_PARENT,
		buttons=( (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL) ))

	dialog.resize(300,400)

	if not dialog:
		logging.error("DebugDialog creation failed!")
		return

	code_vbox = gtk.VBox()
	textView = gtk.TextView()
	button = gtk.Button(label=_("C_ompile and run"))

	dialog.vbox.pack_start(textView)
	dialog.vbox.pack_end(button)
	dialog.vbox.set_child_packing(button, False, True, 0L, gtk.PACK_END)
	dialog.vbox.show_all()

	button.connect("clicked", button_clicked_cb, textView)

	# close on cancel
	dialog.connect("response", destroy_dialog)

	dialog.show_all()

def setup():
	pass
