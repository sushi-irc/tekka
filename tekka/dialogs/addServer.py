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

from gettext import gettext as _

from ..com import sushi
from .. import gui
from ..lib.expanding_list import ExpandingList

RESPONSE_ADD = 1

def setup():
	pass

def dialog_response_cb(dialog, response_id, callback, widgets):
	if response_id == RESPONSE_ADD:

		server = widgets.get_object('addressEntry').get_text()

		sushi.server_set(server, "server", "name", server)

		# set text values
		for key in ("address","port","nick","nickserv"):
			exec ("value = widgets.get_object('%sEntry').get_text()" % key)
			if value:
				sushi.server_set(server, "server", key, value)

		# set autoconnect bool
		sushi.server_set(server, "server", "autoconnect",
			str (widgets.get_object(
					"autoConnectCheckButton").get_active()).lower())

		# set SSL flag
		sushi.server_set(server, "server", "ssl",
			str (widgets.get_object(
					"sslCheckButton").get_active()).lower())

		# set custom SSL certificate path ("" if none set)
		sushi.server_set(server, "server", "ssl_cert",
			widgets.get_object("sslCertFileChooser").get_filename() or "")

		# set nickserv ghost flag
		sushi.server_set(server, "server", "nickserv_ghost",
			str (widgets.get_object(
					"nickservGhostCheckButton").get_active()).lower())

		# set up commands
		list = [i[0].get_text() for i in
			widgets.get_object("commandList").get_widget_matrix()
			if i[0].get_text()]

		if list:
			sushi.server_set_list(server, "server", "commands", list)
		callback()

	dialog.destroy()


def run(callback):
	widgets = gui.builder.load_dialog("server")

	dialog = widgets.get_object("server")

	signals = {
		"useCustomCertificateCheckButton_toggled_cb":
					lambda w,*x: widgets.get_object("sslCertFileChooser").set_sensitive(w.get_active()),
		"sslCheckButton_toggled_cb":
					lambda w,*x: widgets.get_object("useCustomCertificateCheckButton").set_sensitive(w.get_active()),
	}

	widgets.connect_signals(signals)

	dialog.connect("response", dialog_response_cb, callback, widgets)
	dialog.show_all()

