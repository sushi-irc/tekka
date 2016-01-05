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
from ..com import sushi
from .. import gui


def setup():
	pass


def get_configurator(ctype, key, server):

	def bool_configurator(key, server):

		def apply_value(*arg):
			state = str(arg[0].get_active())
			sushi.server_set(server, "server", key, state.lower())

		return apply_value

	def text_configurator(key, server):

		def apply_value(*arg):
			s = arg[0].get_text()
			sushi.server_set(server, "server", key, s)

		return apply_value

	if ctype == "bool":
		return bool_configurator(key, server)
	elif ctype == "text":
		return text_configurator(key, server)
	return None


def run(server):

	def dialog_response_cb(dialog, response_id):
		dialog.destroy()

	def update_commandList(widget, server):
		list = [i[0].get_text() for i in widget.get_widget_matrix()
				if i[0].get_text()]
		sushi.server_set_list(server, "server", "commands", list)

	widgets =  gui.builder.load_dialog("serverEdit")


	types = {"address":"text", "port":"text", "nick":"text",
		"name":"text", "nickserv":"text", "autoconnect":"bool",
                "nickserv_ghost":"bool", "ssl":"bool"}

	signals = {
		"addressEntry": {
			"key":"address",
			"signals":("focus-out-event", "activate")},
		"portEntry": {
			"key":"port",
			"signals":("focus-out-event", "activate")},
		"nickEntry": {
			"key":"nick",
			"signals":("focus-out-event", "activate")},
		"nameEntry": {
			"key":"name",
			"signals":("focus-out-event", "activate")},
		"nickservEntry": {
			"key":"nickserv",
			"signals": ("focus-out-event", "activate")},
		"autoConnectCheckButton": {
			"key":"autoconnect",
			"signals":("toggled",),
                },
		"nickservGhostCheckButton": {
			"key":"nickserv_ghost",
			"signals":("toggled",)
		},
		"sslCheckButton": {
			"key":"ssl",
		    	"signals":("toggled",)
		},
	}

	for key in signals:
		c_type = types[signals[key]["key"]]
		widget = widgets.get_object(key)

		configurator = get_configurator(c_type, signals[key]["key"], server)

		for signal in signals[key]["signals"]:
			widget.connect(signal, configurator)

		value = sushi.server_get(server, "server", signals[key]["key"])

		if c_type == "text":
			widget.set_text(value)
		elif c_type == "bool":
			widget.set_active(value == "true")


	bsignals = {"commandList_row_added_cb":
					lambda w,*x: update_commandList(w, server),
				"commandList_row_removed_cb":
					lambda w,*x: update_commandList(w, server)
			   }
	widgets.connect_signals(bsignals)

	# fill the command list with the existing commands
	commandList = widgets.get_object("commandList")
	i = 0
	for command in sushi.server_get_list(server, "server", "commands"):
		commandList.get_widget_matrix()[i][0].set_text(command)
		commandList.add_row()
		i += 1

	dialog = widgets.get_object("serverEdit")
	dialog.connect("response", dialog_response_cb)
	dialog.show_all()




