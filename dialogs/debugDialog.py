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
import gui_control as gui
import __main__

error_textview = gtk.TextView()

def button_clicked_cb(button, textView):
	"""
		compile statement and run it.
	"""
	print "compile and run!"
	exec(textView.get_buffer().get_property("text"))

def error_log(s):
	buf = error_textview.get_buffer()
	buf.insert(buf.get_end_iter(), s)

def connect_error_pipe():
	global error_textview
	error_textview.get_buffer().set_text(__main__.get_error_history())
	__main__.add_error_handler(error_log)

def destroy_dialog(dialog, rid):
	__main__.remove_error_handler(error_log)
	dialog.destroy()

def run():
	ag = gtk.AccelGroup()

	dialog = gtk.Dialog(
		title="Debug dialog",
		parent=gui.widgets.get_widget("mainWindow"),
		flags=gtk.DIALOG_DESTROY_WITH_PARENT,
		buttons=( (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL) ))

	dialog.resize(300,400)

	if not dialog:
		print "Dialog creation failed!"
		return

	hpaned = gtk.HPaned()
	error_sw = gtk.ScrolledWindow()
	error_sw.add(error_textview)

	code_vbox = gtk.VBox()
	textView = gtk.TextView()
	button = gtk.Button(label=_("C_ompile and run"))

	code_vbox.pack_start(textView)
	code_vbox.pack_end(button)
	code_vbox.set_child_packing(button, False, True, 0L, gtk.PACK_END)

	hpaned.add1(code_vbox)
	hpaned.add2(error_sw)

	dialog.vbox.pack_start(hpaned)
	dialog.vbox.show_all()

	button.connect("clicked", button_clicked_cb, textView)

	# close on cancel
	dialog.connect("response", destroy_dialog)

	dialog.show_all()

	connect_error_pipe()

def setup():
	pass
