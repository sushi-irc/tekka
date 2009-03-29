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
from dbus import String

# local modules
import config
import com
from typecheck import types

from helper.shortcuts import addShortcut, removeShortcut
from helper.url import URLToTag
from helper import URLHandler

import __main__

widgets = None
statusIcon = None
accelGroup = None

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

	import lib.tab as tab
	from lib.htmlbuffer import HTMLBuffer
	from lib.nickListStore import nickListStore

	def __init__(self):
		self.currentPath = ()

	@types(tab=(
		tab.tekkaTab,
		tab.tekkaChannel,
		tab.tekkaServer,
		tab.tekkaQuery), switch=bool)
	def setUseable(self, tab, switch):
		if not tab is self.getCurrentTab():
			return
		widgetList = [
			widgets.get_widget('nickList'),
			widgets.get_widget('topicBar')]
		for widget in widgetList:
			widget.set_sensitive (switch)

	def getNewBuffer(self):
		"""
		Returns a HTMLBuffer with assigned URL handler.
		"""
		buffer = self.HTMLBuffer(handler = URLHandler.URLHandler)
		return buffer

	def createChannel(self, server, name):
		ns = self.nickListStore()

		# TODO: cache prefixes
		ns.set_modes(list(com.sushi.support_prefix(server)[1]))

		obj = self.tab.tekkaChannel(
			name,
			server,
			nicklist=ns,
			buffer=self.getNewBuffer())

		if not obj:
			raise Exception, "Failed to create channel."

		obj.connect("new_message", __main__.tekka_tab_new_message)
		obj.connect("new_name", __main__.tekka_tab_new_name)
		obj.connect("new_path", __main__.tekka_tab_new_path)
		obj.connect("connected", __main__.tekka_tab_connected)
		obj.connect("joined", __main__.tekka_channel_joined)

		return obj

	def createQuery(self, server, name):
		obj = self.tab.tekkaQuery(
			name,
			server,
			buffer=self.getNewBuffer())

		if not obj:
			raise Exception, "Failed to create Query."

		obj.connect("new_message", __main__.tekka_tab_new_message)
		obj.connect("new_name", __main__.tekka_tab_new_name)
		obj.connect("new_path", __main__.tekka_tab_new_path)
		obj.connect("connected", __main__.tekka_tab_connected)

		return obj

	def createServer(self, server):
		obj = self.tab.tekkaServer(
			server,
			buffer=self.getNewBuffer())

		if not obj:
			raise Exception, "Failed to create Server."

		obj.connect("new_message", __main__.tekka_tab_new_message)
		obj.connect("new_name", __main__.tekka_tab_new_name)
		obj.connect("away", __main__.tekka_server_away)
		obj.connect("new_path", __main__.tekka_tab_new_path)
		obj.connect("connected", __main__.tekka_tab_connected)

		return obj

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

	def addTab(self, server, object, update_shortcuts=True):
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
			widgets.get_widget("serverTree").expand_row(
				store.get_path(store.iter_parent(iter)),
				True)

		if update_shortcuts:
			updateServerTreeShortcuts()

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


	def removeTab(self, tab, update_shortcuts=True):
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

		if update_shortcuts:
			updateServerTreeShortcuts()

		return True

	@types(server=str, object=str)
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

		if (tab.is_server()
			and tab.name.lower() == serverTab.name.lower()
			and not channelTab):
			return True

		if (( tab.is_channel() or tab.is_query() )
			and channelTab
			and tab.name.lower() == channelTab.name.lower()
			and tab.server.lower() == serverTab.name.lower()):
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
			self.setUseable(tab, tab.joined)

			setUserCount(
				len(tab.nickList),
				tab.nickList.get_operator_count())

			widgets.get_widget("topicBar").show()
			widgets.get_widget("topicBar").set_text(tab.topic)

			widgets.get_widget("VBox_nickList").show_all()
			widgets.get_widget("nickList").set_model(tab.nickList)

		elif tab.is_query() or tab.is_server():
			# queries and server tabs don't have topics or nicklists
			self.setUseable(tab, tab.connected)

			widgets.get_widget("topicBar").hide()
			widgets.get_widget("VBox_nickList").hide()

		tab.setNewMessage(None)
		updateServerTreeMarkup(tab.path)

		adj = widgets.get_widget("scrolledWindow_output").get_vadjustment()

		#print "position before switch: %s" % (tab.buffer.scrollPosition)

		if tab.buffer.scrollPosition != None and not tab.autoScroll:
			idle_add(adj.set_value,tab.buffer.scrollPosition)
		else:
			scrollOutput()

			def narf(tab):
				tab.autoScroll=True
				return False

			idle_add(narf,tab)

		# NOTE:  to avoid race conditions the idle_add() method is used.
		# NOTE:: If it wouldn't be used the scrolling would not work due
		# NOTE:: to modifications of the scroll position by the base class.

		setWindowTitle(tab.name)

		if not tab.is_server():
			setNick(com.getOwnNick(tab.server))
		else:
			setNick(com.getOwnNick(tab.name))



tabs = TabClass()

def setup_statusIcon():
	"""
	Sets up the status icon.
	"""
	if config.get_bool("tekka", "rgba"):
		gtk.widget_push_colormap(
			widgets.get_widget("mainWindow")\
			.get_screen()\
			.get_rgb_colormap())

	global statusIcon
	statusIcon = gtk.StatusIcon()

	if config.get_bool("tekka", "rgba"):
		gtk.widget_pop_colormap()

	statusIcon.set_tooltip("tekka IRC client")

	statusIcon.connect(
		"popup-menu",
		__main__.statusIcon_popup_menu_cb)

	try:
		statusIcon.set_from_file(
			config.get("tekka","status_icon"))
	except BaseException,e:
		# unknown, print it
		print e
		return

	statusIcon.connect(
		"activate",
		__main__.statusIcon_activate_cb)

@types(switch=bool)
def setUseable(switch):
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

@types(switch=bool)
def setStatusIcon(switch):
	""" enables / disables status icon """
	if switch:
		if not statusIcon:
			setup_statusIcon()
		statusIcon.set_visible(True)

	else:
		if not statusIcon:
			return
		statusIcon.set_visible(False)

@types(switch=bool)
def setUrgent(switch):
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

	if statusIcon:
		statusIcon.set_blinking(switch)

@types(title=(str,String,unicode))
def setWindowTitle(title):
	"""
		Sets the window title to the main
		window.
	"""
	widgets.get_widget("mainWindow").set_title(title)

@types(nick=(str, String, unicode))
def setNick(nick):
	"""
		Sets nick as label text of nickLabel.
	"""
	widgets.get_widget("nickLabel").set_text(nick)

@types(normal=int, ops=int)
def setUserCount(normal, ops):
	"""
	sets the amount of users in the current channel.
	"""
	m_users = gettext.ngettext(
		"%d User", "%d Users", normal) % (normal)
	m_ops = gettext.ngettext(
		"%d Operator", "%d Operators", ops) % (ops)

	widgets.get_widget("nickList_label").set_text(
		"%(users)s – %(ops)s" % {
			"users": m_users, "ops": m_ops })

def setFont(textView, font):
	"""
		Sets the font of the textView to
		the font identified by fontFamily
	"""
	fd = pango.FontDescription(font)

	if not fd:
		print "Font _not_ modified (previous error)"
		return

	textView.modify_font(fd)

@types(string=(str, String, unicode))
def setTopic(string):
	"""
		Sets the given string as text in
		the topic bar.
	"""
	tb = widgets.get_widget("topicBar")
	tb.set_text(string)
	tb.set_position(len(string))

def updateServerTreeShortcuts():
	"""
		Iterates through the TreeModel
		of the server tree and sets 9
		shortcuts to tabs for switching.
	"""
	global accelGroup

	tabList = tabs.getAllTabs()
	st = widgets.get_widget("serverTree")

	for i in range(1,10):
		removeShortcut(accelGroup, st, "<alt>%d" % (i))

	c = 1
	for tab in tabList:
		if c == 10:
			break

		if (tab.is_server()
			and not config.get("tekka","server_shortcuts")):
			continue

		addShortcut(accelGroup, st, "<alt>%d" % (c),
			lambda w,s,p: tabs.switchToPath(p), tab.path)

		c+=1

@types(path=tuple)
def updateServerTreeMarkup(path):
	"""
		Updates the first column of the row in
		gtk.TreeModel of serverTree identified by path.
	"""
	store = widgets.get_widget("serverTree").get_model()
	iter = store.get_iter(path)
	try:
		store.set_value(iter, 0, store[path][2].markup())
	except IndexError:
		print "updateServerTreeMarkup(%s): IndexError" % (
			repr(path))
		return

def scrollGeneralOutput():
	"""
		Scrolls the general output text view to it's end.
	"""
	tv = widgets.get_widget("generalOutput")
	tb = tv.get_buffer()

	mark = tb.create_mark("end", tb.get_end_iter(), False)
	tv.scroll_to_mark(mark, 0.05, True, 0.0, 1.0)
	tb.delete_mark(mark)

def scrollOutput():
	"""
		Scrolls the output text view to it's end.
	"""
	tv = widgets.get_widget("output")
	tb = tv.get_buffer()

	mark = tb.create_mark("end", tb.get_end_iter(), False)
	tv.scroll_to_mark(mark, 0.05, True, 0.0, 1.0)
	tb.delete_mark(mark)

def escape(msg):
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

def channelPrint(timestamp, server, channel, message, type="message"):
	"""
		Inserts a string formatted like "[H:M] <message>\n"
		into the htmlbuffer of the channel `channel` on server
		`server`.
	"""
	timestring = time.strftime(config.get("tekka", "time_format", "%H:%M"), time.localtime(timestamp))

	message = URLToTag(message)

	if not config.get_bool("tekka","color_text"):
		colorHack = ""
	else:
		colorHack = "foreground='%s'" % (
			config.get("colors", "text_%s" % type, "#000000"))

	outputString = "[%s] <font %s>%s</font>" % (
		timestring,
		colorHack,
		message)

	channelTab = tabs.searchTab(server, channel)

	if not channelTab:
		print "No such channel %s:%s" % (server,channel)
		return

	buffer = channelTab.buffer

	if not buffer:
		print "channelPrint(): Channel %s on %s "\
			"has no buffer." % (channel, server)
		return

	buffer.insertHTML(buffer.get_end_iter(), outputString)

	if config.get_bool("tekka","show_general_output"):
		# write it to the general output, also

		goBuffer = widgets.get_widget("generalOutput").get_buffer()
		goBuffer.insertHTML(goBuffer.get_end_iter(),
				"[%s] &lt;%s:%s&gt; %s" % (
					timestring, server, channel, message
				))

		scrollGeneralOutput()

	# notification in server/channel list
	if tabs.isActive(channelTab):
		if channelTab.autoScroll:
			scrollOutput()

	else:
		if type in channelTab.newMessage:
			return

		channelTab.setNewMessage(type)
		updateServerTreeMarkup(channelTab.path)

def serverPrint(timestamp, server, string, type="message"):
	"""
		prints 'string' with "%H:%M' formatted 'timestamp' to the server-output
		identified by 'server'
	"""
	serverTab = tabs.searchTab(server)

	if not serverTab:
		print "Server %s does not exist." % server
		return

	buffer = serverTab.buffer

	if not buffer:
		print "serverPrint(): No output buffer for "\
			"server %s." % server
		return

	timestr = time.strftime(config.get("tekka", "time_format", "%H:%M"), time.localtime(timestamp))

	buffer.insertHTML(buffer.get_end_iter(), "[%s] %s" % (
		timestr,string))

	if config.get_bool("tekka","show_general_output"):
		goBuffer = widgets.get_widget("generalOutput").get_buffer()
		goBuffer.insertHTML(goBuffer.get_end_iter(), \
				"[%s] &lt;%s&gt; %s" % (timestr, server, string))

		scrollGeneralOutput()

	if tabs.isActive(serverTab):
		if serverTab.autoScroll:
			print "scrolling in serverPrint"
			scrollOutput()

	else:
		if type in serverTab.newMessage:
			# don't need to repeat setting
			return
		serverTab.setNewMessage(type)
		updateServerTreeMarkup(serverTab.path)

def currentServerPrint(timestamp, server, string, type="message"):
	"""
		Prints the string on the current tab of server (if any).
		Otherwise it prints directly in the server tab.
	"""
	serverTab,channelTab = tabs.getCurrentTabs()

	if (serverTab
		and serverTab.name.lower() == server.lower()
		and channelTab):
		# print in current channel
		channelPrint(
			timestamp, server,
			channelTab.name, string, type)
	else:
		# print to server tab
		serverPrint(timestamp, server, string, type)

@types(string=(str,unicode), html=bool)
def myPrint(string, html=False):
	"""
		prints the string `string` in the current output
		buffer. If html is true the string would be inserted via
		the insertHTML-method falling back to normal insert
		if it's not possible to insert via insertHTML.
	"""
	output = widgets.get_widget("output").get_buffer()

	if not output:
		print "No output buffer here!"
		return

	if not html:
		output.insert(output.get_end_iter(), "\n"+string)

	else:
		try:
			output.insertHTML(output.get_end_iter(), string)
		except AttributeError:
			print "No HTML buffer, printing normal."
			output.insert(output.get_end_iter(), "\n"+string)

	scrollOutput()

@types(string=str, force_dialog=bool)
def errorMessage(string, force_dialog=False):
	""" if GUI is initialized, and the output widget
		has an buffer, print the error there,
		else raise an error dialog with the given message.
		You can force the usage of an dialog
		with the force_dialog parameter.
	"""
	output = widgets.get_widget("output")
	if output.get_buffer() and not force_dialog:
		myPrint(
			gettext.gettext(
				"<font foreground='%(color)s'>Error: %(message)s</font>" % {
					"color": config.get("colors","error","#FF0000"),
					"message": string}),
			html=True)
	else:
		err = gtk.MessageDialog(
			type=gtk.MESSAGE_ERROR,
			buttons=gtk.BUTTONS_CLOSE,
			message_format=gettext.gettext("Error: %s" % string))
		err.run()
		err.destroy()

