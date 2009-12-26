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

import gtk
import gobject
import time
import logging
from dbus import UInt64

from . import builder
from . import mgmt
from . import shortcuts
from . import _widgets
widgets = _widgets.widgets

from . import _status_manager
status = _status_manager.status

from .. import com
from .. import config

from ..lib.input_history import InputHistory
from ..lib.nick_list_store import NickListStore

from ..helper import color
from ..helper import markup

from ..typecheck import types


def __write_to_general_output(msgtype, timestring, tab, message):
	""" channel can be empty """
	goBuffer = widgets.get_widget("generalOutput").get_buffer()

	filter = config.get_list("general_output", "filter", [])
	logging.debug("filter: %s" % (filter))

	for tuple_str in filter:

		try:
			r_tuple = eval(tuple_str)

		except BaseException as e:
			logging.error("Error in filter tuple '%s': %s" % (
							tuple_str, e))
			continue

		# if the rule matches, abort execution
		if r_tuple[0] == msgtype and r_tuple[-1] in (server, channel):
			return

	if (tab.is_channel() or tab.is_query()):
		# channel print
		goBuffer.go_insert(
						goBuffer.get_end_iter(),
						"[%s] &lt;%s:%s&gt; %s" % (
						   timestring,
						   tab.server.name,
						   tab.name,
						   message),
						tab,
						msgtype)
	else:
		# server print
		goBuffer.go_insert(
						goBuffer.get_end_iter(),
						"[%s] &lt;%s&gt; %s" % (
						   timestring,
						   tab.name,
						   message),
						tab,
						msgtype)

	widgets.get_widget("generalOutput").scroll_to_bottom()


def colorize_message(msgtype, message):
	if not config.get_bool("tekka", "color_text"):
		return message

	else:
		return "<font foreground='%s'>%s</font>" % (
					config.get("colors", "text_%s" % msgtype, "#000000"),
					message)


class TekkaTab(gobject.GObject):
	"""
		Provides basic attributes like the output textview,
		the name of the tab and a flag if a new message is received.

		Attributes:
		textview: the textview bound to this tag
		path: the identifying path in gtk.TreeModel
		name: the identifying name
		newMessage: a list containing message "flags"
		connected: is the tab active or not
	"""

	@types(switch=bool)
	def _set_connected(self, switch):
		self._connected=switch
		self.emit ("server_connected", switch)
		self.emit ("new_markup")
	connected = property(lambda x: x._connected, _set_connected)


	@types(path=tuple)
	def _set_path(self, path):
		self._path = path
		self.emit ("new_path", path)
	path = property(lambda x: x._path, _set_path)


	@types(name=basestring)
	def _set_name(self, name):
		self._name = name
		self.emit ("new_name", name)
	name = property(lambda x: x._name, _set_name)


	def __init__(self, name, window = None):
		gobject.GObject.__init__(self)

		self.window = window
		self.path = ()
		self.name = name
		self.newMessage = []
		self.connected = False
		self.input_text = ""

		self.input_history = None


	def __repr__(self):
		return "<tab '%s', path: '%s'>" % (self.name, self.path)


	def is_server(self):
		return False


	def is_query(self):
		return False


	def is_channel(self):
		return False


	@types(text = str)
	def set_input_text(self, text):
		self.input_text = text


	def get_input_text(self):
		return self.input_text


	@types(status = (str, type(None)))
	def set_new_message(self, status):
		""" A message is unique set and represents
			the status of the tab. The message stack
			can be reset by using None as status.

			The following message states are implemented:
			- "action" and "highlightaction"
			- "message" and "highlightmessage"
		"""
		if not status:
			self.newMessage = []
			self.emit ("reset_message")
		else:
			try:
				self.newMessage.index(status)
			except ValueError:
				self.newMessage.append(status)
			self.emit ("new_message", status)
		self.emit("new_markup")


	def markup(self):
		if self.newMessage:
			return "<b>"+self.name+"</b>"
		return self.name


	def write(self, *x):
		raise NotImplementedError


	def write_raw(self, msg, type="message"):
		buf = self.window.textview.buffer
		end = buf.get_end_iter()

		buf.insert_at_iter(end, msg)

		def notify():
			self.set_new_message(type)
			return False

		gobject.idle_add(notify)


	def print_last_log(self, lines=0):
		"""	Fetch the given amount of lines of history for
			the channel on the given server and print it to the
			channel's textview.
		"""

		# XXX: instead of catching this, cancel new()
		if type(self) == TekkaTab:
			raise NotImplementedError

		buffer = self.window.textview.get_buffer()

		lines = UInt64(lines or config.get(
			"chatting",
			"last_log_lines",
			"0"))

		if type(self) == TekkaServer:
			server = self.name
			channel = ""
		else:
			server = self.server.name
			channel = self.name

		for line in com.sushi.log(server, channel, lines):

			line = color.strip_color_codes(line)

			buffer.insertHTML(buffer.get_end_iter(),
				"<font foreground='%s'>%s</font>" % (
					config.get("colors","last_log","#DDDDDD"),
					markup.escape(line)))


	def set_useable(self, switch):
		widgetList = [
			widgets.get_widget('nickList'),
			widgets.get_widget("output")]

		for widget in widgetList:
			if widget.get_property("sensitive") == switch:
				continue
			widget.set_sensitive (switch)


	def is_active(self):
		serverTab, channelTab = get_current_tabs()

		if not serverTab or (not channelTab and self.is_channel()):
			return False

		if (self.is_server()
			and self.name.lower() == serverTab.name.lower()
			and not channelTab):
			return True

		if (( self.is_channel() or self.is_query() )
			and channelTab
			and self.name.lower() == channelTab.name.lower()
			and self.server.name.lower() == serverTab.name.lower()):
			return True

		return False

	def switch_to(self):
		switch_to_path(self.path)

gobject.signal_new(
	"server_connected",
	TekkaTab,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	(gobject.TYPE_BOOLEAN,))

gobject.signal_new(
	"new_markup",
	TekkaTab,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,())

gobject.signal_new(
	"new_message",
	TekkaTab,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	(gobject.TYPE_PYOBJECT,))

gobject.signal_new(
	"reset_message",
	TekkaTab,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	())

gobject.signal_new(
	"new_path",
	TekkaTab,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	(gobject.TYPE_PYOBJECT,))

gobject.signal_new(
	"new_name",
	TekkaTab,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	(gobject.TYPE_STRING,))


class TekkaServer(TekkaTab):

	@types(msg=basestring)
	def _set_away(self, msg):
		self._away = msg
		self.emit("away", msg)
		self.emit("new_markup")


	@types(prefix = (tuple, list))
	def _set_sprefix(self, prefix):
		self._sprefix = prefix
		self.emit("prefix_set", prefix)


	@types(ctypes = (tuple, list, basestring))
	def _set_ctypes(self, ctypes):
		self._ctypes = ctypes
		self.emit("channeltypes_set", ctypes)


	@types(nick = basestring)
	def _set_nick(self, nick):
		self._nick = nick
		self.emit("new_nick", nick)


	support_prefix = property(lambda x: x._sprefix, _set_sprefix)
	support_chantypes = property(lambda x: x._ctypes, _set_ctypes)
	away = property(lambda x: x._away, _set_away)
	nick = property(lambda x: x._nick, _set_nick)


	def __init__(self, name, textview=None):
		TekkaTab.__init__(self, name, textview)

		self.nick = ""
		self.away = ""
		self.support_prefix = ()
		self.support_chantypes = ()


	def is_server(self):
		return True


	def markup(self):
		base = self.name

		if not self.connected:
			base = "<span strikethrough='true'>"+base+"</span>"

		if self.newMessage:
			base = "<b>"+base+"</b>"

		if self.away:
			base = "<i>"+base+"</i>"

		return base


	def write(self, timestamp, message, msgtype="message",
		no_general_output=False):
		""" write [<timestamp>] <message> to this tab's buffer """

		buffer = self.window.textview.get_buffer()

		timestr = time.strftime(
						config.get("chatting", "time_format", "%H:%M"),
						time.localtime(timestamp))

		buffer.insertHTML(
			buffer.get_end_iter(),
			"[%s] %s" % (timestr, string))

		if not self.is_active():

			if (config.get_bool("tekka", "show_general_output")
			and not no_general_output):

				_write_to_general_output(
					msgtype,
					timestr,
					self,
					string)

		def notify():
			self.set_new_message(msgtype)
			return False

		gobject.idle_add(notify)

	def current_write(self, timestamp, message, msgtype="message",
	no_general_output=False):
		""" write a string to the current active tab of
			this server or, if no tab is active, to the
			this tab
		"""

		cServerTab, cChannelTab = gui.tabs.get_current_tabs()

		if (cServerTab and cServerTab.name.lower() == self.name.lower()
		and cChannelTab):

			cChannelTab.write(
				timestamp,
				message,
				msgtype,
				no_general_output)
		else:

			self.write(
				timestamp,
				message,
				msgtype,
				no_general_output)


	def update(self):
		""" fetch server info from sushi and apply them
			to this tab
		"""
		server = self.name

		if com.sushi.user_away(server, com.get_own_nick(server)):
			# TODO: better query management @ LP
			tab.away = "-- Not implemented yet --"

		self.nick = com.parse_from(com.sushi.user_from(server, ""))[0]
		self.support_prefix = com.sushi.support_prefix(server)
		self.support_chantypes = com.sushi.support_chantypes(server)

gobject.signal_new(
	"away",
	TekkaServer, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_STRING,))

gobject.signal_new(
	"channeltypes_set",
	TekkaServer, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))

gobject.signal_new(
	"prefix_set",
	TekkaServer, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))

gobject.signal_new(
	"new_nick",
	TekkaServer, gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE, (gobject.TYPE_STRING,))


class TekkaQuery(TekkaTab):
	""" Class for typical query-tabs """

	def __init__(self, name, server, textview=None):
		TekkaTab.__init__(self, name, textview)

		self.server = server

	def is_query(self):
		return True

	def markup(self):
		italic = False
		bold = False
		foreground = None

		base = self.name

		if not self.connected:
			base = "<span strikethrough='true'>"+base+"</span>"

		if "action" in self.newMessage:
			italic = True

		if "message" in self.newMessage:
			bold = True

		if ("highlightmessage" in self.newMessage
			and "highlightaction" in self.newMessage):
			foreground = "#DDDD00"
		elif "highlightmessage" in self.newMessage:
			foreground = "#DD0000"
		elif "highlightaction" in self.newMessage:
			foreground = "#00DD00"

		markup = "<span "
		if italic:
			markup += "style='italic' "

		if bold:
			markup += "weight='bold' "

		if foreground:
			markup += "foreground='%s'" % foreground

		markup += ">%s</span>" % base

		return markup


	def write(self, timestamp, message, msgtype="message",
	no_general_output = False):
		""" write [<timestamp>] <message> to this tab's buffer """

		timestring = time.strftime(
					config.get("chatting", "time_format", "%H:%M"),
					time.localtime(timestamp))

		cString = colorize_message(msgtype, message)

		outputString = "[%s] %s" % (timestring, cString)

		buffer = self.window.textview.get_buffer()
		buffer.insertHTML(buffer.get_end_iter(), outputString)

		if not self.is_active():

			if (config.get_bool("tekka", "show_general_output")
			and not no_general_output):

				# write it to the general output, also
				_write_to_general_output(
					msgtype,
					timestring,
					self,
					message)

		def notify():
			self.set_new_message(msgtype)
			return False

		gobject.idle_add(notify)



class TekkaChannel(TekkaTab):
	"""
		A typically channel tab.
	"""

	@types(switch=bool)
	def _set_joined(self, switch):
		self._joined = switch
		self.emit("joined", switch)
		self.emit("new_markup")


	@types(topic=basestring)
	def _set_topic(self, topic):
		self._topic = topic
		self.emit("topic", topic)


	joined = property(lambda x: x._joined, _set_joined)
	topic = property(lambda x: x._topic, _set_topic)


	def __init__(self, name, server, textview=None,
		nicklist=None, topic="", topicsetter=""):
		TekkaTab.__init__(self, name, textview)

		self.nickList = nicklist
		self.topic = topic
		self.topicSetter = topicsetter
		self.joined = False

		self.server = server


	def is_channel(self):
		return True


	def markup(self):
		italic = False
		bold = False
		foreground = None

		base = self.name

		if not self.joined:
			base = "<span strikethrough='true'>"+base+"</span>"

		if "action" in self.newMessage:
			italic = True

		if "message" in self.newMessage:
			bold = True

		if ("highlightmessage" in self.newMessage
		and "highlightaction" in self.newMessage):
			foreground = "#DDDD00"
		elif "highlightmessage" in self.newMessage:
			foreground = "#DD0000"
		elif "highlightaction" in self.newMessage:
			foreground = "#00DD00"

		markup = "<span "
		if italic:
			markup += "style='italic' "

		if bold:
			markup += "weight='bold' "

		if foreground:
			markup += "foreground='%s'" % foreground

		markup += ">%s</span>" % base

		return markup


	def write(self, timestamp, message, msgtype="message",
	no_general_output=False):
		""" write [<timestamp>] <message> to this tab's buffer """

		timestring = time.strftime(
					config.get("chatting", "time_format", "%H:%M"),
					time.localtime(timestamp))

		cString = colorize_message(msgtype, message)

		outputString = "[%s] %s" % (timestring, cString)

		buffer = self.window.textview.get_buffer()
		buffer.insertHTML(buffer.get_end_iter(), outputString)

		if not self.is_active():

			if (config.get_bool("tekka", "show_general_output")
			and not no_general_output):

				# write it to the general output, also
				_write_to_general_output(
					msgtype,
					timestring,
					self,
					message)

		def notify():
			self.set_new_message(msgtype)
			return False

		gobject.idle_add(notify)

gobject.signal_new(
	"joined",
	TekkaChannel,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	(gobject.TYPE_BOOLEAN,))

gobject.signal_new(
	"topic",
	TekkaChannel,
	gobject.SIGNAL_ACTION,
	gobject.TYPE_NONE,
	(gobject.TYPE_STRING,))


_currentPath = ()
_callbacks = {}


"""
List of valid callbacks:
- XXX
  XXX
  XXX
"""
@types (d = dict)
def add_callbacks(d):
	""" get dict with {<str>:<function>,...}
		and apply the values to the internal
		callback dict as a list, resulting in:
		{<str>:[<function0>,<function1>...],...}
	"""
	global _callbacks
	for (key, value) in d.items():
		if _callbacks.has_key(key):
			_callbacks[key].append(value)
		else:
			_callbacks[key] = [value]


@types (key = basestring)
def get_callbacks(key):
	""" return all callback functions stored
		under the given key as a list.
	"""
	global _callbacks
	try:
		return _callbacks[key]
	except KeyError:
		raise ValueError, "No such signal handler: %s." % (key)


@types (callbacks = tuple)
def connect_tab_callbacks(obj, callbacks, *args):
	""" connect the object with all the callbacks
		identified by a string in the callbacks
		tuple.
	"""
	for cb in callbacks:
		cbFunctions = get_callbacks(cb)

		for fun in cbFunctions:
			try:
				obj.connect(cb, fun, *args)
			except TypeError as e:
				# invalid signal
				continue


def call_callback(name, *args):
	for cb in get_callbacks(name):
		try:
			cb(*args)
		except BaseException as e:
			logging.error(e, exc_info = True)
			continue

@types(tabtype = TekkaTab)
def _create_tab(tabtype, name, *args, **kwargs):
	""" instance class of type tabtype, connect signals,
		create output window and setup input history.

		Returns a new child of TekkaTab.
	"""
	tab = tabtype(name, *args, **kwargs)

	tab.window = builder.get_new_output_window()
	tab.window.show_all()

	mgmt.set_font(tab.window.textview, mgmt.get_font())

	connect_tab_callbacks(tab, ("new_message","new_name",
		"new_path","server_connected","new_markup", "reset_message"))

	tab.input_history = InputHistory(
		text_callback = widgets.get_widget("inputBar").get_text)

	return tab


@types (server = TekkaServer, name = basestring)
def create_channel(server, name):
	""" create TekkaChannel object and associated a NickListStore
		with it.

		Returns the newly created Tab object.
	"""
	ns = NickListStore()

	ns.set_modes(server.support_prefix[1])

	tab = _create_tab(TekkaChannel, name, server, nicklist = ns)

	connect_tab_callbacks(tab, ("joined","topic"))

	return tab


@types(server = TekkaServer, name = basestring)
def create_query(server, name):
	tab = _create_tab(TekkaQuery, name, server)
	return tab


@types (server = basestring)
def create_server(server):
	print TekkaServer, type(TekkaServer)
	tab = _create_tab(TekkaServer, server)

	tab.update()

	connect_tab_callbacks(tab, ("away","new_nick"))

	return tab


@types(server = basestring, child = basestring)
def search_tab(server, child = ""):
	store = widgets.get_widget("serverTree").get_model()

	for row in store:
		if row[0].name.lower() == server.lower():
			if child:
				for crow in row.iterchildren():
					if crow[0].name.lower() == child.lower():
						return crow[0]
			else:
				return row[0]

	return None


@types (server = basestring, name = basestring)
def search_tabs(server, name=""):
	"""	Searches for a pair of tabs.
		name can be empty, in that case
		only the server string is used
		for the search.

		Possible return values:
		(<serverTab>,<channelTab>)
		(<serverTab>,None)
		(None,None)
	"""
	store = widgets.get_widget("serverTree").get_model()
	for row in store:
		if row[0].name.lower() == server.lower():
			if not name:
				return (row[0], None)
			else:
				for channel in row.iterchildren():
					if channel[0].name.lower() == name.lower():
						return (row[0], channel[0])
				return (row[0], None)
	return (None, None)


@types (server = (type(None), TekkaServer), object = TekkaTab, update_shortcuts = bool)
def add_tab(server, object, update_shortcuts=True):
	"""	Adds a tab object into the server tree.
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
			if row[0] == server:
				serverIter = row.iter

	iter = store.append(serverIter, row=(object,))
	object.path = store.get_path(iter)

	callbacks = get_callbacks("add")

	for cb in callbacks:
		cb(object)

	if server and config.get("tekka", "auto_expand"):
		# expand the whole server tab
		path = store.get_path(serverIter)
		widgets.get_widget("serverTree").expand_row(
			store.get_path(store.iter_parent(iter)), True)

	if update_shortcuts:
		shortcuts.update_servertree_shortcuts()

	return object.path


@types (tab = TekkaTab, update_shortcuts = bool)
def remove_tab(tab, update_shortcuts=True):
	"""	Removes the tab from the server tree.
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

	callbacks = get_callbacks("remove")

	for cb in callbacks:
		cb(tab)

	store.remove(row.iter)
	__updateLowerRows(store, nextIter)

	if update_shortcuts:
		shortcuts.update_servertree_shortcuts()

	return True

def __updateLowerRows(store, iter):
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

		tab = store.get(nextIter, 0)
		try:
			tab=tab[0]
		except:
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


@types (old = TekkaTab, new = TekkaTab)
def replace_tab(old, new):
	"""	Replaces the tab `old` with the tab `new`. """
	store = widgets.get_widget("serverTree").get_model()

	try:
		row = store[old.path]
	except IndexError:
		# no such tab at path
		return False

	store.set(row.iter, 0, new)
	new.path = store.get_path(row.iter)

	# apply new server to childs
	if old.is_server():
		for row in store.iter_children(iter):
			row[0].server = new


def get_tab_by_path(path):
	if not path:
		return

	store = widgets.get_widget("serverTree").get_model()

	try:
		return store[path][0]
	except:
		return None


@types (servers = list, excludes = list)
def get_all_tabs(servers=[], excludes=[]):
	"""
		Returns all registered tabs.
		If server is given, only the servers
		and it's children are returned.
		If exclude is given, the given servers
		will be ignored.

		Note:  if there's a newly row inserted, the
		Note:: tab-column can be None.
	"""
	store = widgets.get_widget("serverTree").get_model()

	tabs = []

	def lower(l):
		return [n.lower() for n in l if n]

	def iterate_store(model, path, iter):
		tab = model[path][0]
		if (None == tab
		or (tab.is_server() and tab.name.lower() in lower(excludes))
		or (
		  not tab.is_server()
		  and tab.server.name.lower() in lower(excludes))):
			return
		tabs.append(tab)


	if not servers:
		store.foreach(iterate_store)
	else:
		for row in store:
			if row[0].name.lower() in lower(servers):
				tabs.append(row[0])
				for child in row.iterchildren():
					tabs.append(child[0])
				break

	return tabs


def get_current_tab():
	""" Returns the current tab """
	global _currentPath

	store = widgets.get_widget("serverTree").get_model()

	try:
		return store[_currentPath][0]
	except (IndexError,TypeError):
		return None


def get_current_tabs():
	"""
		Returns a tuple with the server
		as parent tab and the active channel tab.

		If only a server is active, the
		second field of the tuple is None.

		Possible return values:
		(<serverTab>,<channelTab>)
		(<serverTab>,None)
		(None,None)
	"""
	global _currentPath

	store = widgets.get_widget("serverTree").get_model()

	if not _currentPath:
		return None,None

	# iter could be server or channel
	try:
		iter = store.get_iter(_currentPath)
	except ValueError:
		# tab is already closed
		return None, None

	if not iter:
		return None, None

	pIter = store.iter_parent(iter)
	if not pIter:
		# no parent, iter is a server
		return store.get_value(iter, 0), None
	else:
		return store.get_value(pIter, 0), store.get_value(iter, 0)

	return None, None


def get_next_server(current):
	store = widgets.get_widget("serverTree").get_model()
	useNext = False

	for row in store:
		if useNext:
			return row[0]

		if row[0] == current:
			useNext = True

	if len(store) >= 2:
		# current was the last item, wrap to the first
		return store[0][0]

	return None


@types (tab = TekkaTab)
def get_next_tab(tab):
	""" get the next left tab near to tab.

		This function doesn't consider the
		type of the tab.
	"""
	if not tab or not tab.path:
		return None

	tablist = get_all_tabs()

	if not tablist or len(tablist) == 1:
		return None

	try:
		i = tablist.index(tab)
	except ValueError:
		return None

	return tablist[i-1]


@types(path=tuple)
def switch_to_path(path):
	""" Switch the server tree cursor
		to the row pointed to by path.

		This function returns None.
	"""
	if not mgmt.gui_is_useable:
		return

	serverTree = widgets.get_widget("serverTree")
	store = serverTree.get_model()

	if not path:
		logging.error("switch_to_path(): empty path given, aborting.")
		return

	try:
		tab = store[path][0]
	except IndexError:
		logging.error(
			"switch_to_path(): tab not found in store, aborting.")
		return

	old_tab = get_current_tab()

	serverTree.set_cursor(path)

	global _currentPath
	_currentPath = path

	widgets.get_widget("outputShell").set(tab.window)

	if tab.is_channel():
		"""
			show up topicbar and nicklist (in case
			they were hidden) and fill them with tab
			specific data.
		"""
		tab.set_useable(tab.joined)

		mgmt.set_user_count(
			len(tab.nickList),
			tab.nickList.get_operator_count())

		mgmt.set_topic(markup.markup_escape(tab.topic))

		if config.get_bool("tekka","show_topic_bar"):
			widgets.get_widget("topicBar").show()

		widgets.get_widget("VBox_nickList").show()
		widgets.get_widget("nickList").set_model(tab.nickList)

	elif tab.is_query() or tab.is_server():
		# queries and server tabs don't have topics or nicklists
		if not status.get("connecting"):
			tab.set_useable(tab.connected)

		if config.get_bool("tekka","show_topic_bar"):
			widgets.get_widget("topicBar").hide()

		widgets.get_widget("VBox_nickList").hide()

	# reset message notification
	tab.set_new_message(None)

	mgmt.set_window_title(tab.name)

	if not tab.is_server():
		mgmt.set_nick(tab.server.nick)
	else:
		mgmt.set_nick(tab.nick)

	call_callback("tab_switched", old_tab, tab)


def switch_to_previous():
	tabs = get_all_tabs()
	tab = get_current_tab()

	try:
		i = tabs.index(tab)
	except ValueError:
		return

	try:
		tabs[i-1].switch_to()
	except IndexError:
		return


def switch_to_next():
	tabs = get_all_tabs()
	tab = get_current_tab()

	try:
		i = tabs.index(tab)
	except ValueError:
		return

	try:
		i = i+1
		if (i) == len(tabs):
			i = 0
		tabs[i].switch_to()
	except IndexError:
		return


#gobject.signal_new("tab_switched", TabControl, gobject.SIGNAL_ACTION,
#	None, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))
