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

import sys
try:
	import pygtk
	pygtk.require("2.0")
except:
	pass

try:
	import gtk
	import gtk.glade
except:
	print "GTK load failed."
	sys.exit(1)

gui = None
com = None
config = None

def setup(_config, _gui, _com):
	"""
		Look, I don't have to tell you what a
		setup method does, don't I?
	"""
	global config, gui, com

	config = _config
	gui = _gui
	com = _com

def loadDialog(name):
	importName = "dialogs."+name
	try:
		dialog = __import__(importName)
	except ImportError,e:
		print "ImportError: ",e
		return None
	# get the sub-module (name)
	components = importName.split('.')
	for comp in components[1:]:
		dialog = getattr(dialog, comp)
	if not dialog:
		return None
	dialog.setup(sys.modules["dialog"])#, gtk, gtk.glade)
	return dialog

def showEditServerDialog(server):
	d = loadDialog("editServer")

	return d.run(server)

def showAddServerDialog():
	d = loadDialog("addServer")

	return d.run()

def showDeleteServerDialog():
	d = loadDialog("deleteServer")

	return d.run()

def showServerDialog():
	"""
		Shows up the server dialog.
	"""
	d = loadDialog("serverDialog")

	return d.run()

def showChannelListDialog(server):
	"""
		Shows up the channel list dialog
		(GUI representation of /list)
	"""
	d = loadDialog("channelList")

	return d.run(server)