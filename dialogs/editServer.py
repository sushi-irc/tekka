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
import gtk.glade
import config
import com
from com import sushi

from lib.expanding_list import ExpandingList

widgets = None
commandList = None

def createCommandList(glade, function_name, widget_name, *x):
	global commandList

	if widget_name != "commandList":
		return

	commandList = ExpandingList(gtk.Entry)

	sw = gtk.ScrolledWindow()
	sw.add_with_viewport(commandList)
	sw.show_all()

	return sw

def setup():
	global widgets
	path = config.get("gladefiles","dialogs") + "serverEdit.glade"
	gtk.glade.set_custom_handler(createCommandList)
	widgets = gtk.glade.XML(path)

def dialog_response_cb(dialog, response_id, server):
	newServer = {}

	if response_id == gtk.RESPONSE_OK:
		# apply the data
		for key in ("address","port","name","nick","nickserv"):
			exec ("value = widgets.get_widget('%sEntry').get_text()" % key)
			sushi.server_set(server, "server", key, value)

		sushi.server_set(server, "server", "autoconnect",
				str(widgets.get_widget("autoConnectCheckButton").get_active()).lower())

		# apply commands
		list = [i[0].get_text() for i in commandList.get_widget_matrix() if i[0].get_text()]
		sushi.server_set_list(server, "server", "commands", list)

	dialog.destroy()


def run(server):
	serverdata = com.fetchServerInfo(server)

	autoconnectInput = widgets.get_widget("autoConnectCheckButton")
	# TODO: implement nickserv ghost flag

	# Fill entries with given data.
	for key in ("address","port","name","nick","nickserv"):
		widgets.get_widget("%sEntry" % key).set_text(serverdata[key])

	if serverdata["autoconnect"].lower() == "true":
		autoconnectInput.set_active(True)
	else:
		autoconnectInput.set_active(False)

	i = 0
	for command in sushi.server_get_list(server, "server", "commands"):
		commandList.get_widget_matrix()[i][0].set_text(command)
		commandList.add_row()
		i += 1

	dialog = widgets.get_widget("serverEdit")
	dialog.connect("response", dialog_response_cb, server)
	dialog.show_all()

