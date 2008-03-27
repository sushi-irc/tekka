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

"""
maybe it's not good that all small dialogs inherit tekkaConfig.
if in tekkaConfig config parsing is implemented it would parse
the config for every dialog. it's better to initalize the config
class in tekkaMain and pass it to the dialogs.
"""

class addServerDialog(object):
	def __init__(self,tekkaMainobject):
		self.gladefile = tekkaMainobject.gladefiles["dialogs"]
		self.widgets = None
		self.servername = None
		self.RESPONSE_ADD = 1

	def run(self):
		data = None
		
		self.widgets = gtk.glade.XML(self.gladefile, "serverAdd")
		dialog = self.widgets.get_widget("serverAdd")
	
		servername_input = self.widgets.get_widget("serverAdd_Servername")
		serveradress_input = self.widgets.get_widget("serverAdd_Serveradress")
		serverport_input = self.widgets.get_widget("serverAdd_Serverport")
		serverautoconnect_input = self.widgets.get_widget("serverAdd_Autoconnect")

		serverport_input.set_text("6667")

		result = dialog.run()
		if result == self.RESPONSE_ADD:
			data = {"autoconnect":0}
			data["name"] = servername_input.get_text()
			data["adress"] = serveradress_input.get_text()
			data["port"] = serveradress_input.get_text()
			if serverautoconnect_input.toggled():
				data["autoconnect"] = 1
		dialog.destroy()

		return result,data

class editServerDialog(object):
	def __init__(self, servername, tekkaMainobject):
		self.gladefile = tekkaMainobject.gladefiles["dialogs"]
		self.widgets = None
		self.servername = servername
		self.tekkaMainobject = tekkaMainobject
		
	def run(self):
		newServer = None
		self.widgets = gtk.glade.XML(self.gladefile, "serverEdit")

		if not self.widgets:
			return 0,None

		servername_input = self.widgets.get_widget("serverEdit_Servername")
		servername_input.set_text(self.servername)
		
		# TODO: retrieve options from server and load fields with data.
		
		dialog = self.widgets.get_widget("serverEdit")
		result = dialog.run()

		dialog.destroy()

		return result,newServer

class deleteServerDialog(object):
	def __init__(self,tekkaMainobject):
		self.gladefile = tekkaMainobject.gladefiles["dialogs"]
	
	def run(self):
		widgets = gtk.glade.XML(self.gladefile, "serverDelete")
		dialog = widgets.get_widget("serverDelete")
		result = dialog.run()
		dialog.destroy()
		return result

class serverDialog(object):
	def __init__(self, tekkaMainobject):
		self.gladefile = tekkaMainobject.gladefiles["dialogs"]
		self.serverView = None
		self.serverList = None
		self.tekkaMainobject = tekkaMainobject
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

		self.addServer({"name":"Placeholder","adress":"foo","port":"54","autoconnect":0},1)

		server = None # the server we want to connect to
		result = dialog.run()

		while result not in (gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT, self.RESPONSE_CONNECT):
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

	def addServer(self, newServer, noDBus=0):
		if not newServer.has_key("name") or not newServer.has_key("adress") or not newServer.has_key("port") or not newServer.has_key("autoconnect"):
			print "Wrong data to addServer."
			return
		if self.serverList:
			self.serverList.append([newServer["name"]])
			if not noDBus:
				self.tekkaMainobject.newServer(newServer)

	def deleteServer(self, servername):
		for server in self.serverList:
			if server[0] == servername:
				self.serverList.remove(server.iter)


	def openAddDialog(self, widget):
		dialog = addServerDialog(self.tekkaMainobject)
		result,newServer = dialog.run()
		if result == dialog.RESPONSE_ADD:
			print "User added a new server"
			self.addServer(newServer)

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

		dialog = editServerDialog(servername, self.tekkaMainobject)
		result,newServer = dialog.run()
		if result == gtk.RESPONSE_OK:
			print "User edited server"
			# TODO: send changes over tekkaCom to server

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

		dialog = deleteServerDialog(self.tekkaMainobject)
		result = dialog.run()
		if result == gtk.RESPONSE_YES:
			print "Deleting server %s" % servername
			self.deleteServer(servername)
			# TODO: send a delete of the server to maki

	def setActiveRow(self, widget):
		print "setting active row"
