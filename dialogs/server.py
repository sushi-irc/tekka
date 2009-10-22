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
import config
import logging

from lib import dialog_control
import lib.gui_control as gui_control

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

	servers = com.sushi.server_list("","")
	for server in servers:
		addServer(server)

def dialog_response_cb(dialog, response_id, callback):
	if response_id == RESPONSE_CONNECT:
		# get the selected server(s)

		serverList = widgets.get_widget("serverList").get_model()
		paths = serverSelection.get_selected_rows()[1]

		if not paths:
			gui_control.errorMessage("No servers selected!", force_dialog=True)
			return

		toConnect = []
		for path in paths:
			toConnect.append(serverList[path][0])

		callback(toConnect)

	else:
		callback(None)

	dialog.destroy()

def run(callback):
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

	dialog.connect("response", dialog_response_cb, callback)
	dialog.show_all()


def serverNameEdit(cellrenderertext, path, newText):
	"""
	User edited column in serverView
	"""

	try:
		oldText = widgets.get_widget("serverList").get_model()[path][0]
	except IndexError:
		return

	com.sushi.server_rename(oldText, newText)

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

		logging.error("wrong data to createServer: %s" % (newServer))
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
			com.sushi.server_remove(servername, "", "")

def add_dialog_cb():
	""" indicates, server was added """
	retrieveServerlist()

def openAddDialog(widget):
	dialog_control.showAddServerDialog(add_dialog_cb)

def openEditDialog(widget):
	view = widgets.get_widget("serverList")
	serverList = view.get_model()

	path = view.get_cursor()[0]

	servername = None

	if not path:
		# TODO:  dialog to inform the user that there's no
		# TODO:: server selected?
		return

	else:
		servername = serverList[path][0]

	data = dialog_control.showEditServerDialog(servername)

	if not servername:
		logging.error("openEditDialog: Error in retrieving the servername")
		return

	if data:
		retrieveServerlist()

def delete_dialog_cb(servername):
	""" indicates that the server can be deleted """
	deleteServer(servername)

def openDeleteDialog(widget):
	view = widgets.get_widget("serverList")

	path = view.get_cursor()[0]
	servername = None

	if not path:
		# TODO: see openEditDialog-todo
		return

	else:
		servername = view.get_model()[path][0]

	if not servername:
		gui_control.errorMessage("Error while retrieving server name.",
			force_dialog = True)
		return

	dialog_control.showDeleteServerDialog(servername, delete_dialog_cb)
