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
import com
import dialog_control
import config

widgets = None
serverSelection = None

RESPONSE_CONNECT = 3

def setup():
	global widgets, serverSelection

	path = config.get("gladefiles","dialogs") + "server.glade"
	widgets = gtk.glade.XML(path)

	sigdic = { "addButton_clicked_cb" : openAddDialog,
				"editButton_clicked_cb" : openEditDialog,
				"deleteButton_clicked_cb" : openDeleteDialog
			}

	widgets.signal_autoconnect(sigdic)

	# enable multiple selection
	serverSelection = widgets.get_widget("serverList").get_selection()
	serverSelection.set_mode(gtk.SELECTION_MULTIPLE)

def addServer(name):
	"""
	Add server from maki to the Serverlist.get_model()
	(ListStore)
	"""
	serverList = widgets.get_widget("serverList").get_model()
	serverList.append([name])

def retrieveServerlist():
	"""
		Fetch server list from maki and get
		infos about every server.
	"""
	store = widgets.get_widget("serverList").get_model()
	store.clear()

	servers = com.fetchServerList()
	for server in servers:
		addServer(server)

def run():
	dialog = widgets.get_widget("serverDialog")

	# get the treeview
	serverView = widgets.get_widget("serverList")

	# add servercolumn
	renderer = gtk.CellRendererText()
	renderer.set_property("editable", True)
	renderer.connect("edited", serverNameEdit)

	column = gtk.TreeViewColumn("Server", renderer, text=0)
	column.set_resizable(False)
	column.set_sort_column_id(0)

	serverView.append_column(column)

	# setup the serverList
	serverList = gtk.ListStore(str)
	serverView.set_model(serverList)

	retrieveServerlist()

	result = dialog.run()

	server = None

	if result == RESPONSE_CONNECT:
		# get the selected server(s)

		paths = serverSelection.get_selected_rows()[1]

		if not paths:
			print "no server(s) selected"
			return

		toConnect = []
		for path in paths:
			toConnect.append(serverList[path][0])

		dialog.destroy()

		return toConnect

	else:
		dialog.destroy()
		return []

def serverNameEdit(cellrenderertext, path, newText):
	"""
	User edited column in serverView
	"""

	try:
		oldText = widgets.get_widget("serverList").get_model()[path][0]
	except IndexError:
		return

	com.renameServer(oldText, newText)

	# at least, update the list from maki (caching would be better..)
	retrieveServerlist()

def createServer(newServer):
	"""
		Create a server in maki.
	"""
	if not newServer.has_key("servername") \
		or not newServer.has_key("address") \
		or not newServer.has_key("port") \
		or not newServer.has_key("autoconnect") \
		or not newServer.has_key("nick") \
		or not newServer.has_key("name"):

		print "wrong data to createserver"
		return

	com.createServer(newServer)

def deleteServer(servername):
	"""
	Remove server from Serverlist widget
	and delete server in maki.
	"""
	serverList = widgets.get_widget("serverList").get_model()

	for row in serverList:
		if row[0] == servername:
			serverList.remove(row.iter)
			com.deleteServer(servername)

def openAddDialog(widget):
	dialog_control.showAddServerDialog()
	retrieveServerlist()

def openEditDialog(widget):
	view = widgets.get_widget("serverList")
	serverList = view.get_model()

	path = view.get_cursor()[0]

	servername = None

	if not path:
		print "No server selected."
		return

	else:
		servername = serverList[path][0]

	data = dialog_control.showEditServerDialog(servername)

	if not servername:
		print "Error in retrieving the servername"
		return

	if data:
		print "User edited server"
		retrieveServerlist()

def openDeleteDialog(widget):
	view = widgets.get_widget("serverList")

	path = view.get_cursor()[0]
	servername = None

	if not path:
		print "No server selected."
		return

	else:
		servername = view.get_model()[path][0]

	if not servername:
		print "Error in retrieving the servername"
		return

	result = dialog_control.showDeleteServerDialog()
	# result = True if answer = Yes

	if result:
		print "Deleting server %s" % servername
		deleteServer(servername)

