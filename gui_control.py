# coding: UTF-8
"""
Copyright (c) 2009 Marian Tietz
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
"""
The "core": the gui wrapper class.
"""

# global modules
import gtk
import gtk.glade
import time
import pango
import gettext
import gobject
from gobject import idle_add
from dbus import String

import cProfile

try:
	from sexy import SpellEntry
except ImportError:
	print "Spell checking disabled."

# local modules
import config
import com
from typecheck import types

from helper.shortcuts import addShortcut, removeShortcut
from helper import URLHandler
from helper.searchToolbar import SearchBar
from helper.input_history import InputHistory

from lib.output_textview import OutputTextView
from lib.htmlbuffer import HTMLBuffer

import __main__

widgets = None
statusIcon = None
accelGroup = None
searchToolbar = None

def profileMe(file):
	def deco(fun):
		def new(*args, **kwargs):
			val = None
			cProfile.runctx("val = fun(*args,**kwargs)", {"fun":fun}, locals(), file)
			return val
		return new
	return deco

def getNewBuffer():
	"""
	Returns a HTMLBuffer with assigned URL handler.
	"""
	buffer = HTMLBuffer(handler = URLHandler.URLHandler)
	return buffer

def get_font ():
	if not config.get_bool("tekka", "use_default_font"):
		return config.get("tekka", "font")

	try:
		import gconf

		client = gconf.client_get_default()

		font = client.get_string("/desktop/gnome/interface/monospace_font_name")

		return font
	except:
		return config.get("tekka", "font")

def custom_handler(glade, function_name, widget_name, *x):
	if widget_name == "searchToolbar":
		return setup_searchToolbar()

	elif widget_name in ("generalOutput", "output"):
		go = OutputTextView()

		return go

	elif widget_name == "inputBar":
		try:
			bar = SpellEntry()
		except NameError:
			bar = gtk.Entry()
		bar.grab_focus()

		bar.connect("key-press-event", __main__.inputBar_key_press_event_cb)
		bar.connect("activate", __main__.inputBar_activate_cb)

		return bar

	elif widget_name == "notificationWidget":
		align = gtk.Alignment()
		align.set_property("visible",False)
		align.set_padding(6,6,6,6)
		return align

	elif widget_name == "topicBar":
		try:
			bar = SpellEntry()
		except NameError:
			bar = gtk.Entry()

		bar.connect("activate", __main__.topicBar_activate_cb)

		return bar

	return None

@types(gladeFile=basestring, section=basestring)
def load_widgets(gladeFile, section):
	""" load the given section from gladeFile
		into widgets and return them.
		This method is ususally called from main.py
		to initialize the GUI
	"""
	global widgets
	gtk.glade.set_custom_handler(custom_handler)
	widgets = gtk.glade.XML(gladeFile, section)

	return widgets

def replace_output_textview(textview):
	sw = widgets.get_widget("scrolledWindow_output")
	sw.remove(sw.get_children()[0])
	sw.add(textview)
	searchToolbar.textview = textview

class TabClass(gobject.GObject):
	"""
	Add/remove/replace tabs.
	Tabs are objects defined in tab.py.
	They're stored in the TreeModel set
	to serverTree TreeView widget.
	"""

	import lib.tab as tab
	from lib.nickListStore import nickListStore

	def __init__(self):
		gobject.GObject.__init__(self)
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

	def _createTab(self, tabtype, name, *args, **kwargs):
		tab = tabtype(name, *args, **kwargs)

		tab.textview = OutputTextView()
		tab.textview.show()
		setFont(tab.textview, get_font())

		tab.connect("new_message", __main__.tekka_tab_new_message)
		tab.connect("new_name", __main__.tekka_tab_new_name)
		tab.connect("new_path", __main__.tekka_tab_new_path)
		tab.connect("connected", __main__.tekka_tab_connected)

		tab.input_history = InputHistory(
			text_callback = widgets.get_widget("inputBar").get_text)

		return tab

	def createChannel(self, server, name):
		ns = self.nickListStore()

		# TODO: cache prefixes
		ns.set_modes(list(com.sushi.support_prefix(server)[1]))

		tab = self._createTab(self.tab.tekkaChannel, name, server, nicklist = ns)
		tab.connect("joined", __main__.tekka_channel_joined)

		return tab

	def createQuery(self, server, name):
		tab = self._createTab(self.tab.tekkaQuery, name, server)
		return tab

	def createServer(self, server):
		tab = self._createTab(self.tab.tekkaServer, server)

		tab.connect("away", __main__.tekka_server_away)
		return tab

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


	@profileMe("removeTab.pro")
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

	@types(server=basestring, object=basestring)
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

	def getNextTab(self, tab):
		""" get the next left tab near to tab. """
		if not tab or not tab.path:
			return None
		tablist = self.getAllTabs()
		if not tablist or len(tablist) == 1:
			return None
		try:
			i = tablist.index(tab)
		except ValueError:
			return None
		return tablist[i-1]

	@profileMe("switchToPath.pro")
	def switchToPath(self, path):
		"""
			path: tuple

			Switches in TreeModel of serverTree to the
			tab identified by path.
		"""
		if not gui_is_useable:
			return

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

		old_tab = self.getCurrentTab()

		serverTree.set_cursor(path)
		self.currentPath = path

		replace_output_textview(tab.textview)

		self.emit("tab_switched", old_tab, tab)

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

		setWindowTitle(tab.name)

		if not tab.is_server():
			setNick(com.getOwnNick(tab.server))
		else:
			setNick(com.getOwnNick(tab.name))

	def switchToTab(self, tab):
		if not tab or not tab.path:
			return
		self.switchToPath(tab.path)

gobject.signal_new("tab_switched", TabClass, gobject.SIGNAL_ACTION,
	None, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))

tabs = TabClass()

def get_current_output_textview():
	tab = tabs.getCurrentTab()

	if not tab:
		return widgets.get_widget("output")
	else:
		return tab.textview

def setup_searchToolbar():
	global searchToolbar
	searchToolbar = SearchBar(None)
	return searchToolbar

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
	global gui_is_useable

	widgetList = [
		widgets.get_widget("topicBar"),
		widgets.get_widget("inputBar"),
		widgets.get_widget("serverTree"),
		widgets.get_widget("nickList"),
		widgets.get_widget("output"),
		widgets.get_widget("generalOutput")
	]

	current_textview = get_current_output_textview()
	if current_textview:
		widgetList.append(current_textview)

	for widget in widgetList:
		widget.set_sensitive(switch)

	if switch: widgets.get_widget("inputBar").grab_focus()

	gui_is_useable = switch

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

@types(title=basestring)
def setWindowTitle(title):
	"""
		Sets the window title to the main
		window.
	"""
	widgets.get_widget("mainWindow").set_title(title)

@types(nick=basestring)
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

@types(string=basestring)
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

def write_to_general_output(msgtype, timestring, server, channel, message):
	goBuffer = widgets.get_widget("generalOutput").get_buffer()

	filter = config.get_list("general_output", "filter", default=[])
	print "filter: %s" % (filter)
	for rule in filter:
		try:
			if not eval(rule):
				return
		except BaseException,e:
			errorMessage("Error in general output filter rule '%s': '%s'." % (rule, e))
			return

	if channel:
		# channel print
		goBuffer.insertHTML(goBuffer.get_end_iter(),
			"[%s] &lt;%s:%s&gt; %s" % (
				timestring, server, channel, message))
	else:
		# server print
		goBuffer.insertHTML(goBuffer.get_end_iter(),
			"[%s] &lt;%s&gt; %s" % (timestring, server, message))


	widgets.get_widget("generalOutput").scroll_to_bottom()

def channelPrint(timestamp, server, channel, message, msgtype="message"):
	"""
		Inserts a string formatted like "[H:M] <message>\n"
		into the htmlbuffer of the channel `channel` on server
		`server`.
	"""
	timestring = time.strftime(config.get("tekka", "time_format", "%H:%M"),
		time.localtime(timestamp))

	if not config.get_bool("tekka","color_text"):
		colorHack = ""
	else:
		colorHack = "foreground='%s'" % (
			config.get("colors", "text_%s" % msgtype, "#000000"))

	outputString = "[%s] <font %s>%s</font>" % (
		timestring,
		colorHack,
		message)

	channelTab = tabs.searchTab(server, channel)

	if not channelTab:
		print "No such channel %s:%s" % (server,channel)
		return

	buffer = channelTab.textview.get_buffer()
	buffer.insertHTML(buffer.get_end_iter(), outputString)

	# notification in server/channel list
	if tabs.isActive(channelTab):
		if channelTab.autoScroll:
			channelTab.textview.scroll_to_bottom()

	else:
		if config.get_bool("tekka","show_general_output"):
			# write it to the general output, also
			write_to_general_output(msgtype, timestring, server, channel, message)

		if not msgtype in channelTab.newMessage:
			channelTab.setNewMessage(msgtype)
			updateServerTreeMarkup(channelTab.path)

def serverPrint(timestamp, server, string, msgtype="message"):
	"""
		prints 'string' with "%H:%M' formatted 'timestamp' to the server-output
		identified by 'server'
	"""
	serverTab = tabs.searchTab(server)

	if not serverTab:
		print "Server %s does not exist." % server
		return

	buffer = serverTab.textview.get_buffer()

	timestr = time.strftime(config.get("tekka", "time_format", "%H:%M"),
		time.localtime(timestamp))

	buffer.insertHTML(buffer.get_end_iter(), "[%s] %s" % (timestr,string))


	if tabs.isActive(serverTab):
		if serverTab.autoScroll:
			serverTab.textview.scroll_to_bottom()

	else:
		if config.get_bool("tekka","show_general_output"):
			write_to_general_output(msgtype, timestr, server, "", string)

		if not msgtype in serverTab.newMessage:
			serverTab.setNewMessage(msgtype)
			updateServerTreeMarkup(serverTab.path)

def currentServerPrint(timestamp, server, string, msgtype="message"):
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
			channelTab.name, string, msgtype)
	else:
		# print to server tab
		serverPrint(timestamp, server, string, msgtype)

@types(string=basestring, html=bool)
def myPrint(string, html=False):
	"""
		prints the string `string` in the current output
		buffer. If html is true the string would be inserted via
		the insertHTML-method falling back to normal insert
		if it's not possible to insert via insertHTML.
	"""
	textview = get_current_output_textview()
	output = textview.get_buffer()

	if not output:
		print "No output buffer here!"
		return

	if not html:
		if output.get_char_count() > 0:
			string = "\n" + string

		output.insert(output.get_end_iter(), string)

	else:
		try:
			output.insertHTML(output.get_end_iter(), string)
		except AttributeError:
			print "No HTML buffer, printing normal."
			output.insert(output.get_end_iter(), "\n"+string)

	textview.scroll_to_bottom()

@types(string=basestring, force_dialog=bool)
def errorMessage(string, force_dialog=False):
	""" if GUI is initialized, and the output widget
		has an buffer, print the error there,
		else raise an error dialog with the given message.
		You can force the usage of an dialog
		with the force_dialog parameter.
	"""
	output = get_current_output_textview()

	message = gettext.gettext("Error: %(message)s")

	if output.get_buffer() and not force_dialog:
		message = "<font foreground='%(color)s'>" + message + "</font>"
		myPrint(message % {
				"color": config.get("colors","error","#FF0000"),
				"message": string},
			html=True)
	else:
		err = gtk.MessageDialog(
			type=gtk.MESSAGE_ERROR,
			buttons=gtk.BUTTONS_CLOSE,
			message_format=message % { "message": string })
		err.run()
		err.destroy()

######################################################
# new style error reporting sticking to the guidelines

class InlineDialog(gtk.Alignment):

	def __init__(self, message, icon = gtk.STOCK_DIALOG_WARNING, buttons = gtk.BUTTONS_CLOSE):

		"""
		 /!\ I'm a warning!  [Close]

		 /!\ I'm a long warning  [Close]
		     which got no place
			 for buttons.

	     (?) Do you want?   [Yes] [No]

		 ICON <-> TEXT => 12 px
		 TEXT <-> BUTTONS => 24 px (XXX: better 12?)
		"""
		gtk.Alignment.__init__(self)

		self.hbox = gtk.HBox(homogeneous=True)

		self.icon = gtk.image_new_from_stock(icon, gtk.ICON_SIZE_DIALOG)
		self.hbox.pack_start(self.icon)

		self.label = gtk.Label()
		self.label.set_markup(message)
		self.hbox.add(self.label)

		self.buttonbox = gtk.VButtonBox()
		self.hbox.pack_end(self.buttonbox)

		if type(buttons) == gtk.ButtonsType:
			self.apply_buttons_type(buttons)
		else:
			self.add_buttons(*buttons)

		self.add(self.hbox)

	@types(btype = gtk.ButtonsType)
	def apply_buttons_type(self, btype):
		if btype == gtk.BUTTONS_NONE:
			pass

		elif btype == gtk.BUTTONS_OK:
			self.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK)

		elif btype == gtk.BUTTONS_CLOSE:
			self.add_buttons(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)

		elif btype == gtk.BUTTONS_YES_NO:
			self.add_buttons(gtk.STOCK_YES, gtk.RESPONSE_YES, gtk.STOCK_NO, gtk.RESPONSE_NO)

		elif btype == gtk.BUTTONS_OK_CANCEL:
			self.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

	def add_buttons(self, *args):
		""" add_buttons(Label0, ResponseID0, StockID1, ResponseID1, ...) """

		if len(args) % 2 != 0:
			raise ValueError, "Not enough arguments supplied, (Button, Response,...)"

		i = 0
		while i < len(args)-1:

			try:
				stock_info = gtk.stock_lookup(args[i])
			except TypeError:
				stock_info = None

			if stock_info != None:
				# Stock item
				button = gtk.Button(stock = args[i])

			else:
				# Label
				button = gtk.Button(label = args[i])

			button.connect("clicked", lambda w,id: self.activate(w, id), args[i+1])
			self.buttonbox.add(button)

			i += 2

	def activate(self, button, id):
		""" button was activated, react on id """
		print "ACTIVATE"
		self.emit("response", id)

gobject.signal_new("response", InlineDialog, gobject.SIGNAL_ACTION, None, (gobject.TYPE_INT,))

def showInlineDialog(dialog):
	area = widgets.get_widget("notificationWidget")
	for child in area.get_children():
		area.remove(child)

	if dialog:
		area.add(dialog)
		area.show_all()
