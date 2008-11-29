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

widgets = None

def setup():
	global widgets
	path = config.get("gladefiles","dialogs") + "serverEdit.glade"
	widgets = gtk.glade.XML(path)

def run(server):
	serverdata = com.fetchServerInfo(server)

	serveraddressInput = widgets.get_widget("addressEntry")
	serveraddressInput.set_text(serverdata["address"])

	serverportInput = widgets.get_widget("portEntry")
	serverportInput.set_text(serverdata["port"])

	servernameInput = widgets.get_widget("realNameEntry")
	servernameInput.set_text(serverdata["name"])

	servernickInput = widgets.get_widget("nickEntry")
	servernickInput.set_text(serverdata["nick"])

	servernickservInput = widgets.get_widget("nickServEntry")
	servernickservInput.set_text(serverdata["nickserv"])

	serverautoconnectInput = widgets.get_widget("autoConnectCheckButton")

	if serverdata["autoconnect"] == "true":
		serverautoconnectInput.set_active(True)
	else:
		serverautoconnectInput.set_active(False)

	dialog = widgets.get_widget("serverEdit")
	result = dialog.run()

	newServer = {}

	if result == gtk.RESPONSE_OK:

		newServer["servername"] = serverdata["servername"]
		for i in ("address","port","name","nick","nickserv"):
			newServer[i] = eval("server%sInput.get_text()" % (i))
		if serverautoconnectInput.get_active():
			newServer["autoconnect"] = "true"
		else:
			newServer["autoconnect"] = "false"

	dialog.destroy()

	return newServer

