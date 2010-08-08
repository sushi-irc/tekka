"""
Copyright (c) 2009-2010 Marian Tietz
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

from .. import config
from .. import com
from .. import gui

builder = gtk.Builder()

def reset_values():
	builder.get_object("autoJoinCheckButton").set_active(False)
	builder.get_object("nameEntry").set_text("#")

def dialog_response_cb(dialog, id):
	global _current_server, builder

	if id == gtk.RESPONSE_OK:
		channel = builder.get_object("nameEntry").get_text()

		com.sushi.join(_current_server, channel, "")

		if builder.get_object("autoJoinCheckButton").get_active():
			com.sushi.server_set(
					_current_server,
					channel,
					"autojoin",
					"true")
	dialog.hide()
	reset_values()

def run(current_server):
	if not current_server:
		gui.show_inline_message(
			_("Could not determine server."),
			_("tekka could not figure out on which server to join."),
			dtype="error")

	else:
		global _current_server
		_current_server = current_server

		dialog = builder.get_object("joinDialog")

		dialog.set_title(_("Join a channel on %(server)s") % {
							"server": current_server})
		dialog.show_all()

def setup():

	if builder.get_object("joinDialog") != None:
		return

	path = config.get("uifiles","dialogs") + "join.ui"

	builder.add_from_file(path)

	dialog = builder.get_object("joinDialog")
	dialog.connect("response", dialog_response_cb)

	# enter on entry -> join channel
	builder.get_object("nameEntry").connect("activate",
		lambda w: dialog_response_cb(dialog, gtk.RESPONE_OK))
