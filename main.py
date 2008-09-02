#!/usr/bin/env python
# 40G V 607G zf -> fold ; zc -> close

import pygtk
pygtk.require("2.0")

import sys

try:
	import gtk
except:
	print "Are you sure X is running?"
	sys.exit(1)

import time

import gtk.glade
from gobject import TYPE_STRING, TYPE_PYOBJECT, idle_add,GError
from pango import FontDescription
import webbrowser

import locale
import gettext

from helper.url import URLToTag

import config
import com

import dialogs
import signals
import commands
import menus

widgets = None
gui = None

"""
	The "core": the gui wrapper class.
"""

class guiWrapper(object):
	"""
		The gui wrapper class is instanced one time
		and acts as interface to the gtk widgets 
		for modules like the signals-module.

		gui = wrapper class
		gui.tabs = tab management (channels and servers)
	"""

	def __init__(self):
		self.statusIcon = None

	def getWidgets(self):
		return widgets

	def setUseable(self, switch):
		"""
			Dis- or enable the widgets
			which emit or receive signals
			to/from maki.
		"""
		widgetList = [
			widgets.get_widget("topicBar"),
			widgets.get_widget("inputBar"),
			widgets.get_widget("serverTree"),
			widgets.get_widget("nickList"),
			widgets.get_widget("output"),
			widgets.get_widget("generalOutput")
		]

		for widget in widgetList:
			widget.set_sensitive(switch)

	def setUrgent(self, switch):
		"""
			Sets or unsets the urgent
			status to the main window.
			If the status icon is enabled
			it will be set flashing (or 
			if switch is False the flashing
			will stop)
		"""
		win = widgets.get_widget("mainWindow")
		
		if win.has_toplevel_focus():
			# urgent toplevel windows suck ass
			return

		win.set_urgency_hint(switch)

		if self.statusIcon:
			self.statusIcon.set_blinking(switch)

	def setWindowTitle(self, title):
		"""
			Sets the window title to the main
			window.
		"""
		widgets.get_widget("mainWindow").set_title(title)

	def setFont(self, textView, fontFamily):
		"""
			Sets the font of the textView to
			the font identified by fontFamily
		"""
		fd = FontDescription()
		fd.set_family(fontFamily)

		textView.modify_font(fd)

	def setTopic(self, string):
		"""
			Sets the given string as text in
			the topic bar.
		"""
		tb = widgets.get_widget("topicBar")
		tb.set_text(string)
		tb.set_position(len(string))

	def updateServerTreeMarkup(self, path):
		"""
			Updates the first column of the row in
			gtk.TreeModel of serverTree identified by path.
		"""
		store = widgets.get_widget("serverTree").get_model()
		iter = store.get_iter(path)
		try:
			store.set_value(iter, 0, store[path][2].markup())
		except IndexError:
			print "updateServerTreeMarkup(%s): IndexError" % (repr(path))
			return

	def scrollGeneralOutput(self):
		"""
			Scrolls the general output text view to it's end.
		"""
		tv = widgets.get_widget("generalOutput")
		tb = tv.get_buffer()

		mark = tb.create_mark("end", tb.get_end_iter(), False)
		tv.scroll_to_mark(mark, 0.05, True, 0.0, 1.0)
		tb.delete_mark(mark)

	def scrollOutput(self):
		"""
			Scrolls the output text view to it's end.
		"""
		tv = widgets.get_widget("output")
		tb = tv.get_buffer()

		mark = tb.create_mark("end", tb.get_end_iter(), False)
		tv.scroll_to_mark(mark, 0.05, True, 0.0, 1.0)
		tb.delete_mark(mark)

	def escape(self, msg):
		"""
			Converts special characters in msg in-place.
		"""
		msg = msg.replace("&","&amp;")
		msg = msg.replace("<","&lt;")
		msg = msg.replace(">","&gt;")
		msg = msg.replace(chr(2), "<sb/>") # bold-char
		msg = msg.replace(chr(31), "<su/>") # underline-char
		msg = msg.replace(chr(1), "")
		return msg

	def channelPrint(self, timestamp, server, channel, message, type="message"):
		"""
			Inserts a string formatted like "[H:M] <message>\n"
			into the htmlbuffer of the channel `channel` on server
			`server`.
		"""
		timestring = time.strftime("%H:%M", time.localtime(timestamp))

		message = URLToTag(message)
		outputString = "[%s] %s" % (timestring, message)

		channelTab = self.tabs.searchTab(server, channel)

		if not channelTab:
			print "No such channel %s:%s\n" % (server,channel)
			return

		buffer = channelTab.buffer

		if not buffer:
			print "channelPrint(): Channel %s on %s has no buffer." % (channel, server)
			return

		buffer.insertHTML(buffer.get_end_iter(), outputString)

		if config.get("tekka","showGeneralOutput"):
			goBuffer = widgets.get_widget("generalOutput").get_buffer()
			goBuffer.insertHTML(goBuffer.get_end_iter(), \
					"[%s] &lt;%s:%s&gt; %s" % (timestring, server, channel, message))

			self.scrollGeneralOutput()

		if self.tabs.isActive(channelTab):
			if channelTab.autoScroll:
				self.scrollOutput()

		else:
			if type in channelTab.newMessage:
				return

			channelTab.setNewMessage(type)
			self.updateServerTreeMarkup(channelTab.path)

	def serverPrint(self, timestamp, server, string, type="message"):
		"""
			prints 'string' with "%H:%M' formatted 'timestamp' to the server-output
			identified by 'server'
		"""
		serverTab = self.tabs.searchTab(server)

		if not serverTab:
			print "Server %s does not exist." % server
			return

		buffer = serverTab.buffer

		if not buffer:
			print "serverPrint(): No output buffer for server %s." % server
			return

		timestr = time.strftime("%H:%M", time.localtime(timestamp))

		buffer.insertHTML(buffer.get_end_iter(), "[%s] %s" % (timestr,string))

		if self.tabs.isActive(serverTab):
			if serverTab.autoScroll:
				self.scrollOutput()

		else:
			if type in serverTab.newMessage: 
				# don't need to repeat setting
				return
			serverTab.setNewMessage(type)
			self.updateServerTreeMarkup(serverTab.path)

	def currentServerPrint(self, timestamp, server, string, type="message"):
		"""
			Prints the string on the current tab of server (if any).
			Otherwise it prints directly in the server tab.
		"""
		serverTab,channelTab = self.tabs.getCurrentTabs()

		if serverTab.name.lower() == server.lower() and channelTab:
			# print in current channel
			self.channelPrint(timestamp, server, cchannel, string, type)
		else:
			# print to server tab
			self.serverPrint(timestamp, server, string, type)

	def myPrint(self, string, html=False):
		"""
			prints the string `string` in the current output
			buffer. If html is true the string would be inserted via
			the insertHTML-method.
		"""
		output = widgets.get_widget("output").get_buffer()

		if not output:
			print "No output buffer here!"
			return

		if not html:
			output.insert(output.get_end_iter(), "\n"+string)

		else:
			output.insertHTML(output.get_end_iter(), string)

		tab = gui.tabs.getCurrentTab()
		if tab.autoScroll:
			self.scrollOutput()

	def urlHandler(self, texttag, widget, event, iter, url):
		if event.type == gtk.gdk.MOTION_NOTIFY:
			pass

		if event.type == gtk.gdk.BUTTON_PRESS:
			if event.button == 1:
				webbrowser.open(url)

			elif event.button == 3:
				menu = gtk.Menu()
				openitem = gtk.MenuItem(label="Open")
				openitem.connect("activate", lambda w: webbrowser.open(url))
				menu.append(openitem)
				copyitem = gtk.MenuItem(label="Copy URL")
				copyitem.connect("activate", self.copyUrlToClipboard, url)
				menu.append(copyitem)

				menu.show_all()
				menu.popup(None, None, None, button=event.button, activate_time=event.time)

	class tabClass(object):
		"""
			Add/remove/replace tabs.
			Tabs are objects defined in tab.py.
			They're stored in the TreeModel set
			to serverTree TreeView widget.
		"""

		import tab
		from htmlbuffer import htmlbuffer
		from nickListStore import nickListStore

		def __init__(self):
			self.currentPath = ()

		def getBuffer(self):
			"""
				Returns a HTMLBuffer with assigned URL handler.
			"""
			buffer = self.htmlbuffer()
			buffer.urlHandler = gui.urlHandler
			return buffer

		def createChannel(self, server, name):
			return self.tab.tekkaChannel(name, server, nicklist=self.nickListStore(), 
				buffer=self.getBuffer())

		def createQuery(self, server, name):
			return self.tab.tekkaChannel(name, server, buffer=self.getBuffer())

		def createServer(self, server):
			return self.tab.tekkaServer(server, buffer=self.getBuffer())

		def searchTab(self, server, name=""):
			"""
				Searches for server (and if name is given, 
				for a tab identified by name).
				The method returns the tab object or None.
			"""
			store = widgets.get_widget("serverTree").get_model()

			for row in store:
				if row[1].lower() == server.lower():
					if not name:
						return row[2]
					else:
						for channel in row.iterchildren():
							if channel[1].lower() == name.lower():
								return channel[2]
			return None



		def searchTabs(self, server, name=""):
			"""
				server: string
				name: string

				Searches for the given server and 
				if not "" the method searches for
				a child identified by name.
				They would be returned in a tuple:
				(<serverTab>,<channelTab>)

				Possible return values:
				(<serverTab>,<channelTab)
				(<serverTab>,None)
				(None,None)
			"""
			store = widgets.get_widget("serverTree").get_model()
			for row in store:
				if row[1].lower() == server.lower():
					if not name:
						return (row[2], None)
					else:
						for channel in row.iterchildren():
							if channel[1].lower() == name.lower():
								return (row[2], channel[2])
			return (None, None)

		def addTab(self, server, object):
			"""
				server: string
				object: tekkaTab

				Adds a tab object into the server tree.
				server can be a string identifying a 
				server acting as parent for the tab or 
				None.

				On succes the method returns the path
				to the new tab, otherwise None.
			"""
			store = widgets.get_widget("serverTree").get_model()

			serverIter = None

			if server:
				for row in store:
					if row[1].lower() == server.lower():
						serverIter = row.iter

			iter = store.append(serverIter)

			store.set(iter, 0, object.markup(), 1, object.name, 2, object)
			object.path = store.get_path(iter)

			if config.get("serverTree", "autoExpand"):
				widgets.get_widget("serverTree").expand_row(object.path, True)

			return object.path

		def removeTab(self, tab):
			"""
				tab: tekkaTab

				Removes the tab from the server tree.
				There's no need for giving a parent due
				to to the unique identifying path stored 
				inner the tekkaTab.
			"""
			store = widgets.get_widget("serverTree").get_model()

			try:
				row = store[tab.path]
			except IndexError:
				# no tab in server tree at this path
				return False

			store.remove(row.iter)
			return True

		def removeTabByString(self, server, object):
			"""
				server: string
				object: string
				
				Removes a tab from the server tree.
				
				server and object are strings identifying
				the server and the child tab.

				server can be None/"" so there only
				a search on the top of the tree is performed.
				
				On success this method returns True
				otherwise False.
			"""
			store = widgets.get_widget("serverTree").get_model()

			if server:
				for row in store:
					if row[1].lower() == server.lower():
						for child in row.iterchildren():
							if child[1].lower() == object.lower():
								store.remove(child.iter)
								return True
			else:
				for row in store:
					if row[1].lower() == object.lower():
						store.remove(row.iter)
						return True

			return False

		def replaceTab(self, old, new):
			"""
				old: tekkaTab
				new: tekkaTab

				Replaces the tab `old` with the tab `new`.
			"""
			store = widgets.get_widget("serverTree").get_model()

			try:
				row = store[old.path]
			except IndexError:
				# no such tab at path
				return False

			store.set(row.iter, 0, new.markup(), 1, new.name, 2, new)
			new.path = store.get_path(iter)

			# apply new server name to childs
			if old.is_server():
				for row in store.iter_children(iter):
					row[2].server = new.name

		def getAllTabs(self, server=""):
			"""
				Returns all registered tabs.
				If server is given this method
				returns only the tabs registered
				to the server identified by server.
				In the case of a given server, the
				server tab is included in the returned list.
			"""
			store = widgets.get_widget("serverTree").get_model()

			tabs = []

			if not server:
				store.foreach(lambda model,path,iter: tabs.append(model[path]))
			else:
				for row in store:
					if row[1].lower() == server.lower():
						tabs.append(row[2])
						for child in row.iterchildren():
							tabs.append(child[2])
						break

			return tabs

		def getCurrentTab(self):
			"""
				Returns the current tab.
			"""
			store = widgets.get_widget("serverTree").get_model()
			try:
				return store[self.currentPath][2]
			except IndexError:
				return None

		def getCurrentTabs(self):
			"""
				Returns a tuple with the server
				as parent tab and the active channel tab.
				If only a server is active a tuple
				with <server>,None is returned.

				Possible return values:
				(<serverTab>,<channelTab>)
				(<serverTab>,None)
				(None,None)
			"""
			store = widgets.get_widget("serverTree").get_model()

			if not self.currentPath:
				return None,None
			
			serverPath = self.currentPath[0]
			channelPath = self.currentPath

			try:
				serverTab = store[serverPath][2]
			except IndexError:
				return None,None

			try:
				channelTab = store[channelPath][2]
			except IndexError:
				channelTab = None

			return serverTab,channelTab

		def isActive(self, tab):
			"""
				Checks if the given tab is currently
				activated in the serverTree.
				Returns True if the tab is active,
				otherwise False.
			"""
			serverTab,channelTab = self.getCurrentTabs()

			if not serverTab or (not channelTab and tab.is_channel()):
				return False

			if tab.is_server() \
			and tab.name.lower() == serverTab.name.lower() \
			and not channelTab:
				return True

			if ( tab.is_channel() or tab.is_query() ) \
			and tab.name.lower() == channelTab.name.lower() \
			and tab.server.lower() == serverTab.name.lower():
				return True

			return False

		def __help(self, tab):
			"""
				ugly scrolling helper but.. *sigh*
				well it's needed until someone has
				a better solution (which works)
			"""
			tab.autoScroll=True
			gui.scrollOutput()

		def switchToPath(self, path):
			"""
				path: tuple

				Switches in TreeModel of serverTree to the
				tab identified by path.
			"""
			serverTree = widgets.get_widget("serverTree")
			store = serverTree.get_model()

			if not path:
				print "switchToPath(): empty path given, aborting."
				return

			try:
				tab = store[path][2]
			except IndexError:
				print "switchToPath(): tab not found in store, aborting."
				return

			serverTree.set_cursor(path)
			self.currentPath = path
		
			widgets.get_widget("output").set_buffer(tab.buffer)

			if tab.is_channel():
				"""
					show up topicbar and nicklist (in case
					they were hidden) and fill them with tab
					specific data.
				"""
				widgets.get_widget("topicBar").show()
				widgets.get_widget("topicBar").set_text(tab.topic)

				widgets.get_widget("scrolledWindow_nickList").show_all()
				widgets.get_widget("nickList").set_model(tab.nickList)

			elif tab.is_query() or tab.is_server():
				# queries and server tabs don't have topics or nicklists
				widgets.get_widget("topicBar").hide()
				widgets.get_widget("scrolledWindow_nickList").hide()

			tab.setNewMessage(None)
			gui.updateServerTreeMarkup(tab.path)

			adj = widgets.get_widget("scrolledWindow_output").get_vadjustment()

			if tab.buffer.scrollPosition != None:
				print "set adjustment"
				adj.set_value(tab.buffer.scrollPosition)
			else:
				idle_add(lambda s,tab: s.__help(tab), self,tab)

			# NOTE:  to avoid race conditions the idle_add() method is used.
			# NOTE:: If it wouldn't be used the scrolling would not work due
			# NOTE:: to resets of the base class.

			gui.setWindowTitle(tab.name)

	tabs = tabClass()




"""
Glade signals
"""

def menu_tekka_Connect_activate_cb(menuItem):
	"""
		...
	"""
	res, server = dialogs.showServerDialog()

	if server:
		com.connectServer(server)

def menu_View_showGeneralOutput_toggled_cb(menuItem):
	"""
		Deactivate or enable (hide/show) the general output
		widget.
	"""
	sw = gui.getWidgets().get_widget("scrolledWindow_generalOutput")

	if menuItem.get_active():
		sw.show_all()
		config.set("tekka","showGeneralOutput","True")
	else:
		sw.hide()
		config.unset("tekka","showGeneralOutput")

def menu_View_showStatusBar_toggled_cb(menuItem):
	"""
		hide or show the status bar.
	"""
	bar = gui.getWidgets().get_widget("statusBar")
	if menuItem.get_active():
		bar.show()
		config.set("tekka","showStatusBar","True")
	else:
		bar.hide()
		config.unset("tekka","showStatusBar")

def mainWindow_delete_event_cb(mainWindow, event):
	"""
		The user want's to close the main window.
		If the status icon is enabled and the 
		"hideOnClose" option is set the window
		will be hidden, otherwise the main looped
		will be stopped.
	"""
	if config.get("hideOnClose") and gui.statusIcon:
		mainWindow.hide()
		return True
	else:
		gtk.main_quit()

def mainWindow_focus_in_event_cb(mainWindow, event):
	"""
		User re-focused the main window.
		If we were in urgent status, the user
		recognized it now so disable the urgent thing.
	"""
	gui.setUrgent(False)
	return False

def mainWindow_size_allocate_cb(mainWindow, alloc):
	"""
		Main window was resized.
		Store the new size in the config.
	"""
	config.set("tekka","window_width",alloc.width)
	config.set("tekka","window_height",alloc.height)

def inputBar_activate_cb(inputBar):
	"""
		Receives if a message in the input bar
		was entered and sent.
		The entered message will be passed
		to the commands module (parseInput(text))
		and the input bar will be cleared.
	"""
	text = inputBar.get_text()

	commands.parseInput(text)

	inputBar.set_text("")

def topicBar_activate_cb(topicBar):
	"""
		Receives if the topicBar gtk.Entry
		widget was activated (Enter was hit).
		Set the topic of the current channel
		to the text in the topicBar
	"""
	sTab,cTab = gui.tabs.getCurrentTabs()

	if not cTab:
		# no channel, no topic
		return

	text = topicBar.get_text()

	com.setTopic(sTab.name, cTab.name, text)

	topicBar.set_text("")

def serverTree_button_press_event_cb(serverTree, event):
	"""
		A row in the server tree was activated.
		The main function of this method is to
		cache the current activated row as path.
	"""

	try:
		path = serverTree.get_path_at_pos(int(event.x),int(event.y))[0]
		tab = serverTree.get_model()[path][2]
	except Exception,e:
		print e
		return False

	if event.button == 1:
		# activate the tab

		gui.tabs.switchToPath(path)

	elif event.button == 3:
		# popup tab menu

		menu = menus.getServerTreeMenu(tab)

		if not menu:
			print "error in creating server tree tab menu."
			return False

		menu.popup(None, None, None, event.button, event.time)

		return True

	return False


def nickList_row_activated_cb(nickList, path, column):
	"""
		The user activated a nick in the list.

		If there's a nick in the row a query
		for the nick on the current server will be opened.
	"""
	server,channel = gui.tabs.getCurrentTabs()

	try:
		name = nickList.get_model()[path][nickList.get_model().COLUMN_NICK]
	except TypeError:
		# nickList has no model
		return
	except IndexError:
		# path is invalid
		return
	gui.tabs.createQuery(server, name)

def nickList_button_press_event_cb(nickList, event):
	"""
		A button pressed inner nickList.

		If it's the right mouse button and there
		is a nick at the coordinates, pop up a menu
		for setting nick options.
	"""
	if event.button == 3:
		# right mouse button pressed.
		
		path = nickList.get_path_at_pos(int(event.x), int(event.y))

		# get marked nick
		try:
			nick = nickList.get_model()[path[0]]
		except TypeError:
			# no model
			return False
		except IndexError:
			# path is "invalid"
			return False

		nick = nick[nickList.get_model().COLUMN_NICK]

		menu = menus.getNickListMenu(nick)

		if not menu:
			return False

		# finaly popup the menu
		menu.popup(None, None, None, event.button, event.time)
	return False


def scrolledWindow_output_vscrollbar_valueChanged_cb(range):
	"""
		The vertical scrollbar of the surrounding scrolled window
		of the output text view was moved.
		Disable the autoscroll if the scroll bar is not at the
		bottom.
		Also the method sets the current scroll position 
		to the buffer in the tab.
	"""
	tab = gui.tabs.getCurrentTab()

	if not tab:
		# no tab to (dis|en)able auto scrolling
		return

	adjust = range.get_property("adjustment")

	if (adjust.upper - adjust.page_size) == range.get_value():
		# bottom reached
		print "autoscroll to %s true" % tab.name
		tab.autoScroll = True
	else:
		print "setting %s to autoscroll false." % (tab.name)
		tab.autoScroll = False

	# cache the last position to set after switch
	tab.buffer.scrollPosition=range.get_value()
	print "current value: ",range.get_value()

"""
Initial setup routines
"""

def setup_mainWindow():
	"""
		- set window title
		- set window icon
		- set window size
	"""
	win = widgets.get_widget("mainWindow")

	win.set_title("tekka")

	iconPath = config.get("tekka","statusIcon")
	if iconPath:
		try:
			win.set_icon_from_file(iconPath)
		except GError:
			# file not found
			pass

	width = config.get("tekka","window_width")
	height = config.get("tekka","window_height")

	if not width or not height:
		return

	win.resize(int(width),int(height))

def setup_serverTree():
	"""
		Sets up a treemodel with three columns.
		The first column is a pango markup language
		description, the second is the identifying
		channel or server name and the third is a
		tab object.
	"""
	tm = gtk.TreeStore(TYPE_STRING, TYPE_STRING, TYPE_PYOBJECT)
	widget = widgets.get_widget("serverTree")
	
	widget.set_model(tm)

	renderer = gtk.CellRendererText()
	column = gtk.TreeViewColumn("Server", renderer, markup=0)

	widget.append_column(column)
	widget.set_headers_visible(False)

def setup_nickList():
	"""
		Sets up a empty nickList widget.
		Two columns (both rendered) were set up.
		The first is the prefix and the second
		the nick name.
	"""
	widget = widgets.get_widget("nickList")
	widget.set_model(None)

	renderer = gtk.CellRendererText()
	column = gtk.TreeViewColumn("Prefix", renderer, text=0)
	widget.append_column(column)

	renderer = gtk.CellRendererText()
	column = gtk.TreeViewColumn("Nicks", renderer, text=1)
	widget.append_column(column)

	widget.set_headers_visible(False)

def setup_statusIcon():
	"""
		Sets up the status icon.
	"""
	gui.statusIcon = gtk.StatusIcon()
	try:
		gui.statusIcon.set_from_file(config.get("tekka","statusIcon"))
	except Exception,e:
		print e
		return

def connectMaki():
	"""
		Tries to connect to maki over DBus.
		If succesful, the GUI is enabled (gui.setUseable(True))
		and signals, dialogs, menus as well as the commands module 
		were set up.
	"""
	gui.setUseable(False)
	
	if com.connect():
		signals.setup(config, gui, com)
		commands.setup(config, gui, com)
		dialogs.setup(config, gui, com)
		menus.setup(config, gui, com, gtk, gtk.glade)

		gui.setUseable(True)

def setupGTK():
	"""
		Set locale, parse glade files.
		Connects gobject widget signals to code.
	"""
	global commands, signals, gui
	global widgets

	gladefiles = config.get("gladefiles", default={})

	# setup locale stuff
	locale.setlocale(locale.LC_ALL, '')

	gettext.bindtextdomain("tekka", config.get("tekka","localeDir"))
	gettext.textdomain("tekka")

	gtk.glade.bindtextdomain("tekka", config.get("tekka","localeDir"))
	gtk.glade.textdomain("tekka")

	# parse glade file for main window
	widgets = gtk.glade.XML(gladefiles["mainwindow"], "mainWindow")

	# connect main window signals:
	sigdic = {
	# tekka menu
		"menu_tekka_Connect_activate_cb" : menu_tekka_Connect_activate_cb,
		"menu_tekka_Quit_activate_cb" : gtk.main_quit,
	# maki menu
		"menu_maki_Connect_activate_cb" : lambda w: connectMaki(),
		"menu_maki_Shutdown_activate_cb" : lambda w: com.shutdown(),
	# view menu
		"menu_View_showGeneralOutput_toggled_cb" : menu_View_showGeneralOutput_toggled_cb,
		"menu_View_showStatusBar_toggled_cb" : menu_View_showStatusBar_toggled_cb,
	# help menu
		# TODO: about dialog
	# main window signals
		"mainWindow_delete_event_cb" : mainWindow_delete_event_cb,
		"mainWindow_focus_in_event_cb" : mainWindow_focus_in_event_cb,
		"mainWindow_size_allocate_cb" : mainWindow_size_allocate_cb,
		# TODO: catch window state change for restoring through tray hide
	# input signals
		"inputBar_activate_cb" : inputBar_activate_cb,
		"topicBar_activate_cb" : topicBar_activate_cb,
	# server tree signals
		"serverTree_realize_cb" : lambda w: w.expand_all(),
		"serverTree_button_press_event_cb" : serverTree_button_press_event_cb,
	# nick list signals
		"nickList_row_activated_cb" : nickList_row_activated_cb,
		"nickList_button_press_event_cb" : nickList_button_press_event_cb,
	}

	widgets.signal_autoconnect(sigdic)

	vbar = widgets.get_widget("scrolledWindow_output").get_vscrollbar()
	vbar.connect("value-changed", scrolledWindow_output_vscrollbar_valueChanged_cb)

	setup_mainWindow()
	setup_serverTree()
	setup_nickList()

	gui = guiWrapper()

	if not gui:
		raise Exception("guiWrapper not successfully initialized!")

	# set output font
	gui.setFont(widgets.get_widget("output"),config.get("tekka","outputFont"))

	# setup general output
	buffer = gui.tabs.getBuffer()
	widgets.get_widget("generalOutput").set_buffer(buffer)

	# setup menu bar stuff
	btn = widgets.get_widget("menu_View_showGeneralOutput")

	if config.get("tekka","showGeneralOutput"):
		btn.set_active(True)
	btn.toggled()

	btn = widgets.get_widget("menu_View_showStatusBar")

	if config.get("tekka","showStatusBar"):
		btn.set_active(True)
	btn.toggled()

	if config.get("tekka","showStatusIcon"):
		setup_statusIcon()

	# disable the GUI and wait for commands :-)
	gui.setUseable(False)

def main():
	"""
		Entry point. The program starts here.
	"""

	config.setup()

	setupGTK()

	connectMaki()

	gtk.main()

	config.writeConfigFile()

if __name__ == "__main__":

	main()

"""
	The best thing while coding is that anything seems to be working
	and some piece of code silently drops your data to /dev/null. :]
"""
