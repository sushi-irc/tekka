
from gobject import idle_add

"""
	References to modules loaded by main script
"""

gui = None
config = None
com = None
gtk = None
glade = None

def setup(_config, _gui, _com, _gtk, _glade):
	"""
		setup the module.
	"""
	global config, gui, com, gtk, glade

	config = _config
	gui = _gui
	com = _com
	gtk = _gtk
	glade = _glade

"""
	Server tree tab menu.
	Shows up if the context menu in server tree
	is called.
"""

serverTree_tabMenu_widgets = None
serverTree_tabMenu_currentTab = None
serverTree_tabMenu_headline = None

def serverTreeMenu_tabMenu_deactivate_cb(menu):
	"""
		The menu is closed.
	"""
	menu.remove(serverTree_tabMenu_headline)

def serverTreeMenu_connectItem_activate_cb(menuItem):
	"""
		connect on server tab hit.
		Connect to the server.
	"""
	if serverTree_tabMenu_currentTab and serverTree_tabMenu_currentTab.is_server():
		com.connectServer(serverTree_tabMenu_currentTab.name)

def serverTreeMenu_disconnectItem_activate_cb(menuItem):
	"""
		quit server with default quit message.
	"""
	if serverTree_tabMenu_currentTab and serverTree_tabMenu_currentTab.is_server():
		com.quitServer(serverTree_tabMenu_currentTab.name, config.get("quitMessage", default=""))

def serverTreeMenu_joinItem_activate_cb(menuItem):
	"""
		join channel without key
	"""
	if serverTree_tabMenu_currentTab and serverTree_tabMenu_currentTab.is_channel():
		com.join(serverTree_tabMenu_currentTab.server, serverTree_tabMenu_currentTab.name)

def serverTreeMenu_partItem_activate_cb(menuItem):
	"""
		part channel with default part message
	"""
	if serverTree_tabMenu_currentTab and serverTree_tabMenu_currentTab.is_channel():
		com.part(serverTree_tabMenu_currentTab.server, serverTree_tabMenu_currentTab.name, config.get("partMessage", default=""))

def serverTreeMenu_closeItem_activate_cb(menuItem):
	"""
		close tab. If the tab is a server emit a quit.
		If the tab is a channel, part the channel before.
	"""
	if not serverTree_tabMenu_currentTab:
		return

	if serverTree_tabMenu_currentTab.is_channel():
		com.part(serverTree_tabMenu_currentTab.server, serverTree_tabMenu_currentTab.name, config.get("partMessage", default=""))
	elif serverTree_tabMenu_currentTab.is_server():
		com.quitServer(serverTree_tabMenu_currentTab.name, config.get("quitMessage", default=""))		

def serverTreeMenu_autoJoinItem_toggled_cb(menuItem):
	"""
		set the auto join state of the tab to the state 
		of the menu item. (for channels)
	"""
	if not serverTree_tabMenu_currentTab or not serverTree_tabMenu_currentTab.is_channel():
		return

	com.setChannelAutoJoin(serverTree_tabMenu_currentTab.server,
			serverTree_tabMenu_currentTab.name,
			menuItem.get_active())

def serverTreeMenu_autoConnectItem_toggled_cb(menuItem):
	"""
		set the auto connect state of the tab to the state 
		of the menu item. (for servers)
	"""
	if not serverTree_tabMenu_currentTab or not serverTree_tabMenu_currentTab.is_server():
		return

	com.setServerAutoConnect(serverTree_tabMenu_currentTab.name,
			menuItem.get_active())


def initServerTreeMenu():
	"""
		TODO: document
	"""
	global serverTree_tabMenu_widgets

	serverTree_tabMenu_widgets = glade.XML(config.get("gladefiles", "mainwindow"), 
			"serverTree_tabMenu")

	if not serverTree_tabMenu_widgets:
		print "glade parsing for serverTree_tabMenu failed."
		return False

	sigdic = {
		"tabMenu_deactivate_cb" : serverTreeMenu_tabMenu_deactivate_cb,
		"connectItem_activate_cb" : serverTreeMenu_connectItem_activate_cb,
		"disconnectItem_activate_cb" : serverTreeMenu_disconnectItem_activate_cb,
		"joinItem_activate_cb" : serverTreeMenu_joinItem_activate_cb,
		"partItem_activate_cb" : serverTreeMenu_partItem_activate_cb,
		"closeItem_activate_cb" : serverTreeMenu_closeItem_activate_cb,
		"autoJoinItem_toggled_cb" : serverTreeMenu_autoJoinItem_toggled_cb,
		"autoConnectItem_toggled_cb" : serverTreeMenu_autoConnectItem_toggled_cb
	}

	serverTree_tabMenu_widgets.signal_autoconnect(sigdic)

	menu = serverTree_tabMenu_widgets.get_widget("serverTree_tabMenu")

	return True

def getServerTreeMenu(pointedTab):
	"""
		Returns the server tree context menu.
	"""
	global serverTree_tabMenu_currentTab, serverTree_tabMenu_headline

	if not serverTree_tabMenu_widgets:
		# no widgets? read glade file
		if not initServerTreeMenu():
			# no success, no menu.
			return None

	serverTree_tabMenu_currentTab = pointedTab

	serverTree_tabMenu_headline = gtk.MenuItem(pointedTab.name)

	headline = serverTree_tabMenu_headline

	menu = serverTree_tabMenu_widgets.get_widget("serverTree_tabMenu")
	menu.insert(headline,0)
	menu.show_all()

	connectItem = serverTree_tabMenu_widgets.get_widget("connectItem")
	disconnectItem = serverTree_tabMenu_widgets.get_widget("disconnectItem")
	joinItem = serverTree_tabMenu_widgets.get_widget("joinItem")
	partItem = serverTree_tabMenu_widgets.get_widget("partItem")
	autoConnectItem = serverTree_tabMenu_widgets.get_widget("autoConnectItem")		
	autoJoinItem = serverTree_tabMenu_widgets.get_widget("autoJoinItem")
	closeItem = serverTree_tabMenu_widgets.get_widget("closeItem")

	# set up visibilty of menu items for each case
	if pointedTab.is_server():
		joinItem.hide()
		partItem.hide()
		autoJoinItem.hide()

		if com.getServerAutoConnect(pointedTab.name) == "true":
			autoConnectItem.set_active(True)
		else:
			autoConnectItem.set_active(False)

		if pointedTab.connected:
			connectItem.hide()
		else:
			disconnectItem.hide()

	elif pointedTab.is_channel():
		connectItem.hide()
		disconnectItem.hide()
		autoConnectItem.hide()

		if com.getChannelAutoJoin(pointedTab.server, pointedTab.name) == "true":
			autoJoinItem.set_active(True)
		else:
			autoJoinItem.set_active(False)


		if pointedTab.joined:
			joinItem.hide()
		else:
			partItem.hide()
	
	elif pointedTab.is_query():
		autoConnectItem.hide()
		connectItem.hide()
		disconnectItem.hide()
		joinItem.hide()
		partItem.hide()

	return menu

"""
	Nick List Menu (context)
"""

nickListMenu_widgets = None
nickListMenu_currentNick = ""
nickListMenu_deactivateHandlers = []

def nickListMenu_deactivate_cb(menu):
	"""
		On deactivation call all handlers.
	"""
	global nickListMenu_deactivateHandlers

	for handler in nickListMenu_deactivateHandlers:
		if handler[1:]:
			handler[0](menu, *handler[1:])
		else:
			handler[0](menu)
	
	nickListMenu_deactivateHandlers = []

def kickItem_activate_cb(menuItem):
	sTab,cTab = gui.tabs.getCurrentTabs()

	if not cTab or not cTab.is_channel():
		return

	com.kick(sTab.name, cTab.name, nickListMenu_currentNick)

def banItem_activate_cb(menuItem):
	sTab,cTab = gui.tabs.getCurrentTabs()

	if not cTab or not cTab.is_channel():
		return

	com.mode(sTab.name, cTab.name, "+b %s*!*@*" % (nickListMenu_currentNick) )

def deVoiceItem_activate_cb(menuItem):
	sTab,cTab = gui.tabs.getCurrentTabs()

	if not cTab or not cTab.is_channel():
		return

	com.mode(sTab.name, cTab.name, "-v %s" % (nickListMenu_currentNick) )

def voiceItem_activate_cb(menuItem):
	sTab,cTab = gui.tabs.getCurrentTabs()

	if not cTab or not cTab.is_channel():
		return

	com.mode(sTab.name, cTab.name, "+v %s" % (nickListMenu_currentNick) )

def deHalfOpItem_activate_cb(menuItem):
	sTab,cTab = gui.tabs.getCurrentTabs()

	if not cTab or not cTab.is_channel():
		return

	com.mode(sTab.name, cTab.name, "-h %s" % (nickListMenu_currentNick) )

def halfOpItem_activate_cb(menuItem):
	sTab,cTab = gui.tabs.getCurrentTabs()

	if not cTab or not cTab.is_channel():
		return

	com.mode(sTab.name, cTab.name, "+h %s" % (nickListMenu_currentNick) )

def deOpItem_activate_cb(menuItem):
	sTab,cTab = gui.tabs.getCurrentTabs()

	if not cTab or not cTab.is_channel():
		return

	com.mode(sTab.name, cTab.name, "-o %s" % (nickListMenu_currentNick) )

def opItem_activate_cb(menuItem):
	sTab,cTab = gui.tabs.getCurrentTabs()

	if not cTab or not cTab.is_channel():
		return

	com.mode(sTab.name, cTab.name, "+o %s" % (nickListMenu_currentNick) )

def initNickListMenu():
	"""
		Parse nickListMenu widget from glade file and 
		connect signals.
		Returns True if successful, otherwise False.
	"""
	global nickListMenu_widgets

	nickListMenu_widgets = glade.XML(config.get("gladefiles", "mainwindow"), "nickListMenu")

	if not nickListMenu_widgets:
		return False

	sigdic = {
		"nickListMenu_deactivate_cb" : nickListMenu_deactivate_cb,
		"kickItem_activate_cb" : kickItem_activate_cb,
		"banItem_activate_cb" : banItem_activate_cb,
		# modes
		"deVoiceItem_activate_cb" : deVoiceItem_activate_cb,
		"voiceItem_activate_cb" : voiceItem_activate_cb,
		"deHalfOpItem_activate_cb" : deHalfOpItem_activate_cb,
		"halfOpItem_activate_cb" : halfOpItem_activate_cb,
		"deOpItem_activate_cb" : deOpItem_activate_cb,
		"opItem_activate_cb" : opItem_activate_cb
	}

	nickListMenu_widgets.signal_autoconnect(sigdic)

	return True

def getNickListMenu(currentNick):
	"""
	"""
	global nickListMenu_currentNick

	if not currentNick:
		return None

	if not nickListMenu_widgets:
		if not initNickListMenu():
			return None

	nickListMenu_currentNick = currentNick
	menu = nickListMenu_widgets.get_widget("nickListMenu")

	headerItem = gtk.MenuItem(label=currentNick)
	menu.insert(headerItem, 0)
	headerItem.show()

	ignoreItem = nickListMenu_widgets.get_widget("ignoreItem")
	ignoreItem.set_active(False)

	pattern = "%s!*" % (currentNick)
	sTab,cTab = gui.tabs.getCurrentTabs()

	if not sTab:
		return None

	ignores = com.fetchIgnores(sTab.name)

	if pattern in ignores:
		ignoreItem.set_active(True)
		ignoreHandler = ignoreItem.connect("toggled", 
			lambda w,n,p: com.unignore(n, p), sTab.name, pattern)

	else:
		ignoreItem.set_active(False)
		ignoreHandler = ignoreItem.connect_after("toggled", 
			lambda w,n,p: com.ignore(n, p), sTab.name, pattern)

	global nickListMenu_deactivateHandlers

	nickListMenu_deactivateHandlers.append(
		(lambda menu,header: menu.remove(header), headerItem))

	nickListMenu_deactivateHandlers.append(
		(lambda menu,item,handler: idle_add(item.disconnect, handler), ignoreItem, ignoreHandler))

	return menu

