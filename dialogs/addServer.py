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

widgets = None
com = None

RESPONSE_ADD = 1

def setup(dialogs):
	global widgets, com
	com = dialogs.com
	widgets = gtk.glade.XML(dialogs.config.get("gladefiles","dialogs"), "serverAdd")

def run():
	data = None

	dialog = widgets.get_widget("serverAdd")

	servernameInput = widgets.get_widget("serverAdd_Servername")
	serveraddressInput = widgets.get_widget("serverAdd_Serveradress")
	serverportInput = widgets.get_widget("serverAdd_Serverport")
	serverautoconnectInput = widgets.get_widget("serverAdd_Autoconnect")
	nicknameInput = widgets.get_widget("serverAdd_Nick")
	realnameInput = widgets.get_widget("serverAdd_Realname")
	nickservInput = widgets.get_widget("serverAdd_Nickserv")

	result = dialog.run()
	if result == RESPONSE_ADD:
		data = {}
		data["servername"] = servernameInput.get_text()
		data["address"] = serveraddressInput.get_text()
		data["port"] = serverportInput.get_text()
		data["nick"] = nicknameInput.get_text()
		data["name"] = realnameInput.get_text()
		data["nickserv"] = nickservInput.get_text()
		if serverautoconnectInput.get_active():
			data["autoconnect"] = "true"
		else:
			data["autoconnect"] = "false"
	dialog.destroy()

	return data


