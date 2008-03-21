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

from tekkaConfig import tekkaConfig

class addServerDialog(tekkaConfig):
	def __init__(self):
		tekkaConfig.__init__(self)
		self.widgets = None
		self.RESPONSE_ADD = 1

	def run(self):
		data = None
		
		self.widgets = gtk.glade.XML(self.gladefile, "serverAdd")
		dialog = self.widgets.get_widget("serverAdd")
	
		servername_input = self.widgets.get_widget("serverAdd_Servername")
		serveradress_input = self.widgets.get_widget("serverAdd_Serveradress")
		serverport_input = self.widgets.get_widget("serverAdd_Serverport")

		serverport_input.set_text("6667")

		result = dialog.run()
		if result == self.RESPONSE_ADD:
			data = {}
			data["name"] = servername_input.get_text()
			data["adress"] = serveradress_input.get_text()
			data["port"] = serveradress_input.get_text()
		dialog.destroy()

		return result,data

class serverDialog(tekkaConfig):
	def __init__(self, tekkaComInterface):
		tekkaConfig.__init__(self)
		self.serverView = None
		self.serverList = None
		self.tekkaComInt = tekkaComInterface
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
		column = gtk.TreeViewColumn("Server",gtk.CellRendererText(), text=0)
		column.set_resizable(False)
		column.set_sort_column_id(0)
		self.serverView.append_column(column)
	
		# setup the serverList
		self.serverList = gtk.ListStore(str)
		self.serverView.set_model(self.serverList)

		self.addServer({"name":"Placeholder","adress":"foo","port":"54"},1)

		server = None # the server we want to connect to
		result = dialog.run()

		while result not in (gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT, self.RESPONSE_CONNECT):
			result = dialog.run()
		else:
			if result == self.RESPONSE_CONNECT:
				id = self.serverView.get_cursor()[0]
				if id:
					if len(id) > 1:
						print "too much servers selected. Multiple connect not supported yet."
					else:
						server = self.serverList[id[0]][0]
			dialog.destroy()

		return result,server

	def addServer(self, newServer, noDBus=0):
		if not newServer.has_key("name") or not newServer.has_key("adress") or not newServer.has_key("port"):
			print "Wrong data to addServer."
			return
		if self.serverList:
			self.serverList.append([newServer["name"]])
			if not noDBus:
				self.tekkaComInt.newServer(newServer)


	def listselect(self, widget):
		print "selected!"
		print widget

	def openAddDialog(self, widget):
		dialog = addServerDialog()
		result,newServer = dialog.run()
		if result == dialog.RESPONSE_ADD:
			print "User added a new server"
			self.addServer(newServer)

	def openEditDialog(self, widget):
		print "would open edit dialog"

	def openDeleteDialog(self, widget):
		print "rly delete? :]"

	def setActiveRow(self, widget):
		print "setting active row"
