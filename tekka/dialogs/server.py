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
import logging
from gettext import gettext as _

from .. import com
from ..lib import dialog_control
from .. import gui

widgets = None
serverSelection = None

RESPONSE_CONNECT = 3

def setup():
	global widgets, serverSelection

	widgets = gui.builder.load_dialog("server")

	sigdic = { "addButton_clicked_cb" : openAddDialog,
				"editButton_clicked_cb" : openEditDialog,
				"deleteButton_clicked_cb" : openDeleteDialog
			}

	widgets.signal_autoconnect(sigdic)

	# enable multiple selection
	serverSelection = widgets.get_object("serverList").get_selection()
	serverSelection.set_mode(gtk.SELECTION_MULTIPLE)

def addServer(name):
	"""
	Add server from maki to the Serverlist.get_model()
	(ListStore)
	"""
	serverList = widgets.get_object("serverList").get_model()
	serverList.append([name])

def retrieveServerlist():
	"""
		Fetch server list from maki and get
		infos about every server.
	"""
	store = widgets.get_object("serverList").get_model()
	store.clear()

	servers = com.sushi.server_list("","")

	if servers:
		for server in servers:
			addServer(server)

def dialog_response_cb(dialog, response_id, callback):
	if response_id == RESPONSE_CONNECT:
		# get the selected server(s)

		serverList = widgets.get_object("serverList").get_model()
		paths = serverSelection.get_selected_rows()[1]

		if not paths:
			return

		toConnect = []
		for path in paths:
			toConnect.append(serverList[path][0])

		callback(toConnect)

	else:
		callback(None)

	dialog.destroy()

def run(callback):
	dialog = widgets.get_object("serverDialog")

	# get the treeview
	serverView = widgets.get_object("serverList")

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
		oldText = widgets.get_object("serverList").get_model()[path][0]
	except IndexError:
		return

	com.sushi.server_rename(oldText, newText)

	# at least, update the list from maki (caching would be better..)
	retrieveServerlist()

def createServer(serverName, data):
	""" Create a server in maki. """
	for (k,v) in data.items():
		com.sushi.server_set(serverName, "server", k, v)

def deleteServer(servername):
	""" Remove server from Serverlist widget
		and delete server in maki.
	"""
	serverList = widgets.get_object("serverList").get_model()

	for row in serverList:
		if row[0] == servername:
			serverList.remove(row.iter)
			com.sushi.server_remove(servername, "", "")

def add_dialog_cb():
	""" indicates, server was added """
	retrieveServerlist()

def openAddDialog(widget):
	dialog_control.show_dialog("addServer", add_dialog_cb)

def openEditDialog(widget):
	view = widgets.get_object("serverList")
	serverList = view.get_model()

	path = view.get_cursor()[0]

	servername = None

	if not path:
		# TODO:  dialog to inform the user that there's no
		# TODO:: server selected?
		return

	else:
		servername = serverList[path][0]

	data = dialog_control.show_dialog("editServer", servername)

	if not servername:
		logging.error("openEditDialog: Error in retrieving the servername")
		return

	if data:
		retrieveServerlist()

def delete_dialog_cb(servername):
	""" indicates that the server can be deleted """
	deleteServer(servername)

def openDeleteDialog(widget):
	view = widgets.get_object("serverList")

	path = view.get_cursor()[0]
	servername = None

	if not path:
		# TODO: see openEditDialog-todo
		return

	else:
		servername = view.get_model()[path][0]

	if not servername:
		gui.mgmt.show_error_dialog(
			title = _("Error while retrieving server name."),
			message = _("There was an error while retrieving the server name.\n"
						"Are you connected to maki?"))
		return

	dialog_control.show_dialog("deleteServer", servername, delete_dialog_cb)
