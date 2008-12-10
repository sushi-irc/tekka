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

from helper.expandingList import expandingList

widgets = None
commandList = None

def createCommandList(glade, function_name, widget_name, *x):
	global commandList

	print widget_name
	if widget_name != "commandList":
		print "wrong widget"
		return

	commandList = expandingList(gtk.Entry)

	sw = gtk.ScrolledWindow()
	sw.add_with_viewport(commandList)
	sw.show_all()

	return sw

def setup():
	global widgets
	path = config.get("gladefiles","dialogs") + "serverEdit.glade"
	gtk.glade.set_custom_handler(createCommandList)
	widgets = gtk.glade.XML(path)

def run(server):
	serverdata = com.fetchServerInfo(server)

	addressInput = widgets.get_widget("addressEntry")
	addressInput.set_text(serverdata["address"])

	portInput = widgets.get_widget("portEntry")
	portInput.set_text(serverdata["port"])

	nameInput = widgets.get_widget("realNameEntry")
	nameInput.set_text(serverdata["name"])

	nickInput = widgets.get_widget("nickEntry")
	nickInput.set_text(serverdata["nick"])

	nickservInput = widgets.get_widget("nickServEntry")
	nickservInput.set_text(serverdata["nickserv"])

	# TODO: implement nickserv ghost flag
	autoconnectInput = widgets.get_widget("autoConnectCheckButton")

	if serverdata["autoconnect"] == "true":
		autoconnectInput.set_active(True)
	else:
		autoconnectInput.set_active(False)

	i = 0
	for command in com.sushi.server_get_list(server, "server", "commands"):
		commandList.get_widget_matrix()[i][0].set_text(command)
		commandList.add_row()
		i += 1

	dialog = widgets.get_widget("serverEdit")
	result = dialog.run()

	newServer = {}

	if result == gtk.RESPONSE_OK:
		# apply the data
		for key in ("address","port","name","nick","nickserv"):
			exec ("value = %sInput.get_text()" % key)
			com.sushi.server_set(server, "server", key, value)

		com.sushi.server_set(server, "server", "autoconnect",
				str(autoconnectInput.get_active()))

		# apply commands
		list = [i[0].get_text() for i in commandList.get_widget_matrix() if i[0].get_text()]
		com.sushi.server_set_list(server, "server", "commands", list)

	dialog.destroy()


