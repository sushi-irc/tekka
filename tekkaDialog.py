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
	sys.exit(1)

class addServerDialog(object):
	def __init__(self,tekkaMainObject):
		self.gladefile = tekkaMainObject.getConfig().gladefiles["dialogs"]
		self.widgets = None
		self.servername = None
		self.RESPONSE_ADD = 1

	def run(self):
		data = None

		self.widgets = gtk.glade.XML(self.gladefile, "serverAdd")
		dialog = self.widgets.get_widget("serverAdd")

		servernameInput = self.widgets.get_widget("serverAdd_Servername")
		serveraddressInput = self.widgets.get_widget("serverAdd_Serveradress")
		serverportInput = self.widgets.get_widget("serverAdd_Serverport")
		serverautoconnectInput = self.widgets.get_widget("serverAdd_Autoconnect")
		nicknameInput = self.widgets.get_widget("serverAdd_Nick")
		realnameInput = self.widgets.get_widget("serverAdd_Realname")
		nickservInput = self.widgets.get_widget("serverAdd_Nickserv")

		serverportInput.set_text("6667")

		result = dialog.run()
		if result == self.RESPONSE_ADD:
			data = {}
			data["servername"] = servernameInput.get_text()
			data["address"] = serveraddressInput.get_text()
			data["port"] = serverportInput.get_text()
			data["nick"] = nicknameInput.get_text()
			data["name"] = realnameInput.get_text()
			data["nickserv"] = nickservInput.get_text()
			if serverautoconnectInput.toggled():
				data["autoconnect"] = 1
			else:
				data["autoconnect"] = 0
		dialog.destroy()

		return result,data

class editServerDialog(object):
	def __init__(self, serverdata, tekkaMainObject):
		self.gladefile = tekkaMainObject.getConfig().gladefiles["dialogs"]
		self.widgets = None
		self.serverdata = serverdata
		self.tekkaMainObject = tekkaMainObject
		self.deleteServer = 0 # if the server name is changed, delete the old

	def servernameChanged(self,widget):
		self.deleteServer = 1

	def run(self):
		newServer = None
		self.widgets = gtk.glade.XML(self.gladefile, "serverEdit")

		if not self.widgets:
			return 0,None

		serverservernameInput = self.widgets.get_widget("serverEdit_Servername")
		serverservernameInput.set_text(self.serverdata["servername"])
		serverservernameInput.connect("changed",self.servernameChanged)
		self.orgServername = self.serverdata["servername"]
		serveraddressInput = self.widgets.get_widget("serverEdit_Address")
		serveraddressInput.set_text(self.serverdata["address"])
		serverportInput = self.widgets.get_widget("serverEdit_Port")
		serverportInput.set_text(self.serverdata["port"])
		servernameInput = self.widgets.get_widget("serverEdit_Realname")
		servernameInput.set_text(self.serverdata["name"])
		servernickInput = self.widgets.get_widget("serverEdit_Nick")
		servernickInput.set_text(self.serverdata["nick"])
		servernickservInput = self.widgets.get_widget("serverEdit_Nickserv")
		servernickservInput.set_text(self.serverdata["nickserv"])
		serverautoconnectInput = self.widgets.get_widget("serverEdit_Autoconnect")
		if self.serverdata["autoconnect"]:
			connect = True
		else:
			connect = False
		serverautoconnectInput.set_active(connect)

		dialog = self.widgets.get_widget("serverEdit")
		result = dialog.run()

		if result == gtk.RESPONSE_OK:
			if self.deleteServer:
				self.tekkaMainObject.getCom().deleteServer(self.orgServername)
			newServer = {}
			for i in ("servername","address","port","name","nick","nickserv"):
				newServer[i] = eval("server%sInput.get_text()" % (i))

		dialog.destroy()

		return result,newServer

class deleteServerDialog(object):
	def __init__(self,tekkaMainObject):
		self.gladefile = tekkaMainObject.getConfig().gladefiles["dialogs"]

	def run(self):
		widgets = gtk.glade.XML(self.gladefile, "serverDelete")
		dialog = widgets.get_widget("serverDelete")
		result = dialog.run()
		dialog.destroy()
		return result

class serverDialog(object):
	def __init__(self, tekkaMainObject):
		self.gladefile = tekkaMainObject.getConfig().gladefiles["dialogs"]
		self.serverView = None
		self.serverList = None
		self.tekkaMainObject = tekkaMainObject
		self.RESPONSE_CONNECT = 3

	def run(self):
		sigdic = { "serverDialog_Add_clicked_cb" : self.openAddDialog,
		           "serverDialog_Edit_clicked_cb" : self.openEditDialog,
				   "serverDialog_Delete_clicked_cb" : self.openDeleteDialog }

		self.widgets = gtk.glade.XML(self.gladefile, "serverDialog")
		self.widgets.signal_autoconnect(sigdic)

		dialog = self.widgets.get_widget("serverDialog")

		# get the treeview
		self.serverView = self.widgets.get_widget("serverDialog_Serverlist")

		if not self.serverView:
			print "Failed to get serverView."
			return gtk.RESPONSE_CANCEL

		# add servercolumn
		renderer = gtk.CellRendererText()
		renderer.set_property("editable",True)
		renderer.connect("edited", self.serverNameEdit)

		column = gtk.TreeViewColumn("Server", renderer, text=0)
		column.set_resizable(False)
		column.set_sort_column_id(0)
		self.serverView.append_column(column)

		# setup the serverList
		self.serverList = gtk.ListStore(str)
		self.serverView.set_model(self.serverList)

		# a dict containing detailed data of servers
		self.serverDict = {}

		self._retrieveServerlist()

		server = None # the server we want to connect to
		result = dialog.run()

		while result not in (gtk.RESPONSE_CANCEL, \
			gtk.RESPONSE_DELETE_EVENT, self.RESPONSE_CONNECT):
			result = dialog.run()
		else:
			if result == self.RESPONSE_CONNECT:
				# look for servername
				id = self.serverView.get_cursor()[0]
				if id:
					if len(id) > 1:
						print "too much servers selected. Multiple connect not supported yet."
					else:
						server = self.serverList[id[0]][0]
			dialog.destroy()

		return result,server

	"""
	User edited column in serverView
	"""
	def serverNameEdit(self, cellrenderertext, path, newText):
		try:
			oldText = self.serverView.get_model()[path][0]
		except IndexError:
			return
		self.tekkaMainObject.getCom().renameServer(oldText, newText)
		self.serverView.get_model()[path][0] = newText

	def _retrieveServerlist(self):
		com = self.tekkaMainObject.getCom()

		self.serverView.get_model().clear()
		serverlist = com.fetchServerList()
		for s in serverlist:
			self.addServer(com.fetchServerInfo(s))


	def addServer(self, newServer):
		if not newServer.has_key("servername") \
			or not newServer.has_key("address") \
			or not newServer.has_key("port") \
			or not newServer.has_key("autoconnect") \
			or not newServer.has_key("nick") \
			or not newServer.has_key("name"):
			print "Wrong data to addServer."
			return
		if self.serverList:
			self.serverList.append([newServer["servername"]])
		self.serverDict[newServer["servername"]]=newServer

	def createServer(self, newServer):
		if not newServer.has_key("servername") \
			or not newServer.has_key("address") \
			or not newServer.has_key("port") \
			or not newServer.has_key("autoconnect") \
			or not newServer.has_key("nick") \
			or not newServer.has_key("name"):
			print "wrong data to createserver"
			return
		self.tekkaMainObject.getCom().createServer(newServer)

	def deleteServer(self, servername):
		for server in self.serverList:
			if server[0] == servername:
				self.serverList.remove(server.iter)
				self.tekkaMainObject.getCom().deleteServer(servername)


	def openAddDialog(self, widget):
		dialog = addServerDialog(self.tekkaMainObject)
		result,newServer = dialog.run()
		if result == dialog.RESPONSE_ADD:
			print "User added a new server"
			self.addServer(newServer)
			self.createServer(newServer)

	def openEditDialog(self, widget):
		if not self.serverView:
			return

		sID = self.serverView.get_cursor()[0]
		servername = None
		if not sID:
			print "No server selected."
			return
		else:
			servername = self.serverList[sID[0]][0]

		if not servername:
			print "Error in retrieving the servername"
			return

		dialog = editServerDialog(self.serverDict[servername], self.tekkaMainObject)
		result,newServer = dialog.run()
		if result == gtk.RESPONSE_OK:
			print "User edited server"
			#print newServer
			self.tekkaMainObject.getCom().createServer(newServer)
			self._retrieveServerlist()


	def openDeleteDialog(self, widget):
		if not self.serverView:
			return

		sID = self.serverView.get_cursor()[0]
		servername = None

		if not sID:
			print "No server selected."
			return
		else:
			servername = self.serverList[sID[0]][0]

		if not servername:
			print "Error in retrieving the servername"
			return

		dialog = deleteServerDialog(self.tekkaMainObject)
		result = dialog.run()
		if result == gtk.RESPONSE_YES:
			print "Deleting server %s" % servername
			self.deleteServer(servername)
