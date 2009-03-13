# coding: utf-8
"""
The "core": the gui wrapper class.
"""

# global modules
import gtk
import gtk.glade
import time
import pango
import gettext
from gobject import idle_add

# local modules
import config
import com
from typecheck import types

from helper.shortcuts import addShortcut, removeShortcut
from helper.url import URLToTag
from helper import URLHandler

import __main__

widgets = None

@types(gladeFile=str, section=str)
def load_widgets(gladeFile, section):
	""" load the given section from gladeFile
		into widgets and return them.
		This method is ususally called from main.py
		to initialize the GUI
	"""
	global widgets
	widgets = gtk.glade.XML(gladeFile, section)
	return widgets




class TabClass(object):
	"""
	Add/remove/replace tabs.
	Tabs are objects defined in tab.py.
	They're stored in the TreeModel set
	to serverTree TreeView widget.
	"""

	import tab
	from htmlbuffer import HTMLBuffer
	from nickListStore import nickListStore

	def __init__(self, gui):
		self.currentPath = ()
		self.gui = gui

	def getNewBuffer(self):
		"""
		Returns a HTMLBuffer with assigned URL handler.
		XXX: for what is this?
		"""
		buffer = self.HTMLBuffer(handler = URLHandler.URLHandler)
		return buffer

	def createChannel(self, server, name):
		ns = self.nickListStore()

		# TODO: cache prefixes
		ns.set_modes(list(com.sushi.support_prefix(server)[1]))

		return self.tab.tekkaChannel(
			name,
			server,
			nicklist=ns,
			buffer=self.getNewBuffer())

	def createQuery(self, server, name):
		return self.tab.tekkaQuery(
			name,
			server,
			buffer=self.getNewBuffer())

	def createServer(self, server):
		return self.tab.tekkaServer(
			server,
			buffer=self.getNewBuffer())

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

		iter = store.append(serverIter, row=(object.markup,object.name,object))

		object.path = store.get_path(iter)
		store.set(iter, 0, object.markup(), 1, object.name, 2, object)

		if server and config.get("tekka", "auto_expand"):
			# expand the whole server tab
			widgets.get_widget("serverTree").expand_row(store.get_path(store.iter_parent(iter)),True)

		return object.path

	def __updateLowerRows(self, store, iter):
		"""
			iter points to the row after the deleted row.
			path is the path of the deleted row.
			This hack is UGLY! Would someone please fix
			the crappy rows-reordered signal? KTHXBYE
		"""

		if not iter:
			# no work, phew.
			return

		newLastPath = None
		nextIter = iter

		while True:
			if not nextIter:
				break

			tab = store.get(nextIter, 2)
			try:
				tab=tab[0]
			except:
				print "OHMENOODLESKARPOTT"
				break

			tab.path = store.get_path(nextIter)

			oIter = nextIter
			nextIter = store.iter_next(oIter)
			if not nextIter:
				if store.iter_has_child(oIter):
					# oIter is a server
					nextIter = store.iter_children(oIter)
				else:
					# oIter is a channel and the next is (maybe)
					# a further server
					temp = store.iter_parent(oIter)
					nextIter = store.iter_next(temp)


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

		# part of hack:
		nextIter = store.iter_next(row.iter)
		if not nextIter:
			temp = store.iter_parent(row.iter)
			if temp:
				nextIter = store.iter_parent(temp)
			else:
				nextIter = None
		path = tab.path

		store.remove(row.iter)

		# hack because the signal rows-reordered
		# does not work yet. Update all rows under
		# the deleted to the new path.
		self.__updateLowerRows(store,nextIter)

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
		new.path = store.get_path(row.iter)

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
			store.foreach(lambda model,path,iter: tabs.append(model[path][2]))
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
		except (IndexError,TypeError):
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

		# iter could be server or channel
		try:
			iter = store.get_iter(self.currentPath)
		except ValueError:
			# tab is already closed
			return None, None

		if not iter:
			return None, None

		pIter = store.iter_parent(iter)
		if not pIter:
			# no parent, iter is a server
			return store.get_value(iter, 2), None
		else:
			return store.get_value(pIter, 2), store.get_value(iter, 2)

		return None, None

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
		and channelTab \
		and tab.name.lower() == channelTab.name.lower() \
		and tab.server.lower() == serverTab.name.lower():
			return True

		return False

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
			self.gui.setUserCount(
				len(tab.nickList),
				tab.nickList.get_operator_count())

			widgets.get_widget("topicBar").show()
			widgets.get_widget("topicBar").set_text(tab.topic)

			widgets.get_widget("VBox_nickList").show_all()
			widgets.get_widget("nickList").set_model(tab.nickList)

		elif tab.is_query() or tab.is_server():
			# queries and server tabs don't have topics or nicklists
			widgets.get_widget("topicBar").hide()
			widgets.get_widget("VBox_nickList").hide()

		tab.setNewMessage(None)
		self.gui.updateServerTreeMarkup(tab.path)

		adj = widgets.get_widget("scrolledWindow_output").get_vadjustment()

		#print "position before switch: %s" % (tab.buffer.scrollPosition)

		if tab.buffer.scrollPosition != None and not tab.autoScroll:
			print "scrolling in switchToPath(%s) to %f" % (tab.name,tab.buffer.scrollPosition)
			idle_add(adj.set_value,tab.buffer.scrollPosition)
		else:
			print "scrolling with narf(tab) in switchToPath(%s)" % tab.name
			self.gui.scrollOutput()
			def narf(tab):
				tab.autoScroll=True
				return False
			idle_add(narf,tab)

		# NOTE:  to avoid race conditions the idle_add() method is used.
		# NOTE:: If it wouldn't be used the scrolling would not work due
		# NOTE:: to modifications of the scroll position by the base class.

		self.gui.setWindowTitle(tab.name)

		if not tab.is_server():
			self.gui.setNick(com.getOwnNick(tab.server))
		else:
			self.gui.setNick(com.getOwnNick(tab.name))







class GUIWrapper(object):
	"""
		The gui wrapper class is instanced one time
		and acts as interface to the gtk widgets
		for modules like the signals-module.

		gui = wrapper class
		gui.tabs = tab management (channels and servers)
	"""

	def __init__(self):
		self.statusIcon = None
		self.accelGroup = None
		self.tabs = TabClass(self)

	def getWidgets(self):
		return widgets

	def setup_statusIcon(self):
		"""
		Sets up the status icon.
		"""
		if config.getBool("tekka", "rgba"):
			gtk.widget_push_colormap(
				widgets.get_widget("mainWindow")\
				.get_screen()\
				.get_rgb_colormap())

		self.statusIcon = gtk.StatusIcon()

		if config.getBool("tekka", "rgba"):
			gtk.widget_pop_colormap()

		self.statusIcon.set_tooltip("tekka IRC client")

		self.statusIcon.connect(
			"popup-menu",
			__main__.statusIcon_popup_menu_cb)

		try:
			self.statusIcon.set_from_file(
				config.get("tekka","status_icon"))
		except BaseException,e:
			# unknown, print it
			print e
			return

		self.statusIcon.connect(
			"activate",
			__main__.statusIcon_activate_cb)

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

		if switch: widgets.get_widget("inputBar").grab_focus()

	def setStatusIcon(self, switch):
		""" enables / disables status icon """
		if switch:
			if not self.statusIcon:
				self.setup_statusIcon()
			self.statusIcon.set_visible(True)

		else:
			if not self.statusIcon:
				return
			self.statusIcon.set_visible(False)

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

	def setNick(self, nick):
		"""
			Sets nick as label text of nickLabel.
		"""
		widgets.get_widget("nickLabel").set_text(nick)

	def setUserCount(self, normal, ops):
		"""
		sets the amount of users in the current channel.
		"""
		m_users = gettext.ngettext("%d User", "%d Users", normal) % (normal)
		m_ops = gettext.ngettext("%d Operator", "%d Operators", ops) % (ops)

		widgets.get_widget("nickList_label").set_text(
			"%(users)s – %(ops)s" % { "users": m_users, "ops": m_ops })


	def setFont(self, textView, font):
		"""
			Sets the font of the textView to
			the font identified by fontFamily
		"""
		fd = pango.FontDescription(font)

		if not fd:
			print "Font _not_ modified (previous error)"
			return

		textView.modify_font(fd)

	def setTopic(self, string):
		"""
			Sets the given string as text in
			the topic bar.
		"""
		tb = widgets.get_widget("topicBar")
		tb.set_text(string)
		tb.set_position(len(string))

	def updateServerTreeShortcuts(self):
		"""
			Iterates through the TreeModel
			of the server tree and sets 9
			shortcuts to tabs for switching.
		"""
		tabs = self.tabs.getAllTabs()
		st = widgets.get_widget("serverTree")

		for i in range(1,10):
			removeShortcut(self.accelGroup, st, "<alt>%d" % (i))

		c = 1
		for tab in tabs:
			if c == 10:
				break

			if tab.is_server() and not config.get("tekka","server_shortcuts"):
				continue

			addShortcut(self.accelGroup, st, "<alt>%d" % (c),
				lambda w,s,p: self.tabs.switchToPath(p), tab.path)

			c+=1

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

		if not config.getBool("tekka","color_text"):
			colorHack = ""
		else:
			colorHack = "foreground='%s'" % config.get("colors", "text_%s" % type, "#000000")

		outputString = "[%s] <font %s>%s</font>" % \
			(timestring, colorHack, message)

		channelTab = self.tabs.searchTab(server, channel)

		if not channelTab:
			print "No such channel %s:%s" % (server,channel)
			return

		buffer = channelTab.buffer

		if not buffer:
			print "channelPrint(): Channel %s on %s has no buffer." % (channel, server)
			return

		buffer.insertHTML(buffer.get_end_iter(), outputString)

		if config.getBool("tekka","show_general_output"):
			# write it to the general output, also

			goBuffer = widgets.get_widget("generalOutput").get_buffer()
			goBuffer.insertHTML(goBuffer.get_end_iter(),
					"[%s] &lt;%s:%s&gt; %s" % (
						timestring, server, channel, message
					))

			self.scrollGeneralOutput()

		# notification in server/channel list
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

		if config.getBool("tekka","show_general_output"):
			goBuffer = widgets.get_widget("generalOutput").get_buffer()
			goBuffer.insertHTML(goBuffer.get_end_iter(), \
					"[%s] &lt;%s&gt; %s" % (timestr, server, string))

			self.scrollGeneralOutput()

		if self.tabs.isActive(serverTab):
			if serverTab.autoScroll:
				print "scrolling in serverPrint"
				#idle_add(lambda: self.scrollOutput())
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

		if serverTab and serverTab.name.lower() == server.lower() and channelTab:
			# print in current channel
			self.channelPrint(timestamp, server, channelTab.name, string, type)
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

		self.scrollOutput()


	def moveNickList(self, left):
		"""
		Moves the nick list to the left side of the window if left is True
		otherwise to the right bottom vpaned.
		"""

		# XXX: no move to the already set position (will crash....)

		nl = widgets.get_widget("VBox_nickList")

		vpaned = widgets.get_widget("listVPaned")
		hbox = widgets.get_widget("mainHBox")
		vbox = widgets.get_widget("mainVBox")

		if left:
			"""
			remove the nick list packet from the vpaned on the right side,
			remove the mainHBox (containing GO,output,input,vpaned from servertree,...)
			from the mainVBox (containing all window stuff) and create
			a hpaned.
			Position one (left side) is filled with the nick list stuff
			with new border (6px) and the right side is the main hbox.
			After this, apply the new hpaned to the main vbox.
			"""

			vpaned.remove(nl)
			vbox.remove(hbox)

			nlHpaned = gtk.HPaned()
			nlHpaned.pack1(nl)
			nlHpaned.pack2(hbox)
			nlHpaned.show()

			nl.set_property("border-width", 6)

			vbox.pack_start(nlHpaned)

			# set to the middle (above status bar, under menu bar)
			vbox.reorder_child(nlHpaned, 1)

			widgets.get_widget("inputBar").grab_focus()

			config.set("tekka", "nick_list_left", "True")

		else:
			nl.set_property("border-width", 0)

			nlHpaned = vbox.get_children()[1]

			nl = nlHpaned.get_child1()
			nlHpaned.remove(nl)

			# move nl box to the right vpaned
			vpaned.pack2(nl, resize=True, shrink=False)

			main = nlHpaned.get_child2()
			nlHpaned.remove(main)

			vbox.remove(nlHpaned)

			vbox.pack_start(main)
			vbox.reorder_child(main, 1)

			config.set("tekka", "nick_list_left", "False")

