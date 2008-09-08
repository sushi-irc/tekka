import gtk
import gtk.glade

com = None
dialogs = None
widgets = None

RESPONSE_CONNECT = 3

def setup(_dialogs):
	global widgets, com, dialogs

	widgets = gtk.glade.XML(_dialogs.config.get("gladefiles","dialogs"), "serverDialog")
	com = _dialogs.com
	dialogs = _dialogs

	sigdic = { "serverDialog_Add_clicked_cb" : openAddDialog,
				"serverDialog_Edit_clicked_cb" : openEditDialog,
				"serverDialog_Delete_clicked_cb" : openDeleteDialog
			}

	widgets.signal_autoconnect(sigdic)

def addServer(newServer):
	"""
		Add server from maki to the Serverlist.get_model() 
		(ListStore)
	"""
	if not newServer.has_key("servername") \
		or not newServer.has_key("address") \
		or not newServer.has_key("port") \
		or not newServer.has_key("autoconnect") \
		or not newServer.has_key("nick") \
		or not newServer.has_key("name"):

		print "Wrong data to addServer."
		return

	serverList = widgets.get_widget("serverDialog_Serverlist").get_model()
	serverList.append([newServer["servername"]])

def retrieveServerlist():
	"""
		Fetch server list from maki and get
		infos about every server.
	"""
	store = widgets.get_widget("serverDialog_Serverlist").get_model()
	store.clear()

	servers = com.fetchServerList()
	for server in servers:
		addServer(com.fetchServerInfo(server))

def run():
	dialog = widgets.get_widget("serverDialog")

	# get the treeview
	serverView = widgets.get_widget("serverDialog_Serverlist")

	# add servercolumn
	renderer = gtk.CellRendererText()
	renderer.set_property("editable",True)
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

	while result not in (gtk.RESPONSE_CANCEL,
						gtk.RESPONSE_DELETE_EVENT,
						RESPONSE_CONNECT):
			result = dialog.run()
	else:
		if result == RESPONSE_CONNECT:
			# look for servername
			id = serverView.get_cursor()[0]
			if id:
				server = serverList[id][0]
		dialog.destroy()

	return (result == RESPONSE_CONNECT) and server or None

def serverNameEdit(cellrenderertext, path, newText):
	"""
	User edited column in serverView
	"""

	try:
		oldText = widgets.get_widget("serverDialog_Serverlist").get_model()[path][0]
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
	serverList = widgets.get_widget("serverDialog_Serverlist").get_model()

	for row in serverList:
		if row[0] == servername:
			serverList.remove(row.iter)
			com.deleteServer(servername)

def openAddDialog(widget):
	data = dialogs.showAddServerDialog()

	if data:
		# TODO: these methods check input twice at all.
		addServer(data) # append to local list
		createServer(data) # add server in maki

def openEditDialog(widget):
	view = widgets.get_widget("serverDialog_Serverlist")
	serverList = view.get_model()

	path = view.get_cursor()[0]

	servername = None

	if not path:
		print "No server selected."
		return

	else:
		servername = serverList[path][0]

	data = dialogs.showEditServerDialog(servername)
	
	if not servername:
		print "Error in retrieving the servername"
		return

	if data:
		print "User edited server"
		com.createServer(data)
		retrieveServerlist()

def openDeleteDialog(widget):
	view = widgets.get_widget("serverDialog_Serverlist")

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

	result = dialogs.showDeleteServerDialog()
	# result = True if answer = Yes

	if result:
		print "Deleting server %s" % servername
		deleteServer(servername)

