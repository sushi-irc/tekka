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

import logging

def loadDialog(name):
	importName = "dialogs."+name
	try:
		dialog = __import__(importName)
	except ImportError,e:
		logging.error("loadDialog: ImportError: %s" % (e))
		return None
	# get the sub-module (name)
	components = importName.split('.')
	for comp in components[1:]:
		dialog = getattr(dialog, comp)
	if not dialog:
		return None

	dialog.setup()
	return dialog

def show_dialog(name, *param):
	d = loadDialog(name)

	if not d:
		raise Exception, "Dialog with name '%s' not found." % (name)

	return d.run(*param)

def showEditServerDialog(server):
	d = loadDialog("editServer")

	return d.run(server)

def showAddServerDialog(callback):
	d = loadDialog("addServer")

	return d.run(callback)

def showDeleteServerDialog(servername, callback):
	d = loadDialog("deleteServer")

	return d.run(servername, callback)

def showServerDialog(callback):
	"""
		Shows up the server dialog.
	"""
	d = loadDialog("server")

	return d.run(callback)

def showChannelListDialog(server):
	"""
		Shows up the channel list dialog
		(GUI representation of /list)
	"""
	d = loadDialog("channelList")

	return d.run(server)

def showDCCDialog():
	d = loadDialog("dcc")
	return d.run()

def showPluginsDialog():
	"""
	"""
	d = loadDialog("plugins")

	return d.run()

def showHistoryDialog(tab):
	"""
		Shows up the history dialog for the current tab.
	"""
	d = loadDialog("history")

	return d.run(tab)

def showDebugDialog():
	d = loadDialog("debug")

	return d.run()

def showPreferencesDialog():
	d = loadDialog("preferences")

	return d.run()

def showWhoisDialog(server, nick):
	d = loadDialog("whois")
	return d.run(server, nick)

def showColorTableDialog():
	d = loadDialog("colorTable")
	return d.run()
