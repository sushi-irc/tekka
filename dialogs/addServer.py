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

import gtk.glade
import com
from com import sushi
import config
import gui_control

from lib.expanding_list import ExpandingList

widgets = None
commandList = None

RESPONSE_ADD = 1

def createCommandList(glade, fun_name, widget_name, *x):
	"""
	create the command list widget.
	this function is called by glade
	"""
	global commandList

	if widget_name != "commandList":
		print "wrong widget"
		return None

	commandList = ExpandingList(gtk.Entry)

	sw = gtk.ScrolledWindow()
	sw.add_with_viewport(commandList)

	sw.show_all()

	return sw

def setup():
	global widgets

	path = config.get("gladefiles","dialogs") + "serverAdd.glade"
	gtk.glade.set_custom_handler(createCommandList)
	widgets = gtk.glade.XML(path)


def dialog_response_cb(dialog, response_id, callback):
	if response_id == RESPONSE_ADD:

		server = widgets.get_widget("servernameEntry").get_text()

		if not server:
			gui_control.errorMessage("No server name given.", force_dialog=True)
			return

		# set text values
		for key in ("address","port","nick","name","nickserv"):
			exec ("value = widgets.get_widget('%sEntry').get_text()" % key)
			if value:
				sushi.server_set(server, "server", key, value)

		# set autoconnect bool
		sushi.server_set(server, "server", "autoconnect",
			str (widgets.get_widget("autoConnectCheckButton").get_active()).lower())

		# set up commands
		list = [i[0].get_text() for i in commandList.get_widget_matrix() if i[0].get_text()]
		sushi.server_set_list(server, "server", "commands", list)
		callback()

	dialog.destroy()


def run(callback):
	data = None

	dialog = widgets.get_widget("serverAdd")

	dialog.connect("response", dialog_response_cb, callback)
	dialog.show_all()

