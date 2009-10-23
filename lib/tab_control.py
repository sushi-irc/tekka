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
import logging

import com
import config

import lib.gui_control
from lib.input_history import InputHistory
from lib.tab import TekkaTab, TekkaChannel, TekkaQuery, TekkaServer
from lib.output_textview import OutputTextView
from lib.nick_list_store import NickListStore

from typecheck import types

"""
TODO:  In the long run get rid of multiple
TODO:: columns in the server tree. There
TODO:: should be only one column with the
TODO:: tab object inside.
"""

class TabControl(gobject.GObject):
	"""
	Add/remove/replace tabs.
	Tabs are objects defined in tab.py.
	They're stored in the TreeModel set
	to serverTree TreeView widget.
	"""

	def __init__(self):
		gobject.GObject.__init__(self)
		self.currentPath = ()
		self.prefix_cache = {}
		self._callbacks = {}

		""" valid callbacks are, at the moment:

			TekkaTab:
			- new_message
			- new_name
			- new_path
			- connected
			- new_markup

			TekkaChannel:
			- joined
			- topic

			TekkaServer:
			- away
			- new_nick
		"""

	@types (d = dict)
	def add_callbacks(self, d):
		""" get dict with {<str>:<function>,...}
			and apply the values to the internal
			callback dict as a list, resulting in:
			{<str>:[<function0>,<function1>...],...}
		"""
		for (key, value) in d.items():
			if self._callbacks.has_key(key):
				self._callbacks[key].append(value)
			else:
				self._callbacks[key] = [value]

	@types (key = basestring)
	def get_callbacks(self, key):
		""" return all callback functions stored
			under the given key as a list.
		"""
		try:
			return self._callbacks[key]
		except KeyError:
			raise ValueError, "No such signal handler: %s." % (key)

	@types (callbacks = tuple)
	def connect_callbacks(self, obj, callbacks):
		""" connect the object with all the callbacks
			identified by a string in the callbacks
			tuple.
		"""
		for cb in callbacks:
			cbFunctions = self.get_callbacks(cb)

			for fun in cbFunctions:
				try:
					obj.connect(cb, fun)
				except TypeError, e:
					# invalid signal
					continue

	@types (tab = TekkaTab, switch = bool)
	def set_useable(self, tab, switch):
		""" switch the destinated tab from/to
			useable state
			((de)activate sensitive widgets)
		"""
		if not tab is self.get_current_tab():
			return

		widgetList = [lib.gui_control.get_widget('nickList')]

		for widget in widgetList:
			widget.set_sensitive (switch)

	def _create_tab(self, tabtype, name, *args, **kwargs):
		""" instance class of type tabtype, connect signals,
			create textview and setup input history.

			Returns a new child of TekkaTab.
		"""
		tab = tabtype(name, *args, **kwargs)

		tab.textview = OutputTextView()
		tab.textview.show()
		lib.gui_control.set_font(tab.textview, lib.gui_control.get_font())

		self.connect_callbacks(tab, ("new_message","new_name",
			"new_path","connected","new_markup"))

		tab.input_history = InputHistory(
			text_callback = lib.gui_control.get_widget("inputBar").get_text)

		return tab

	@types (server = TekkaServer, name = basestring)
	def create_channel(self, server, name):
		""" create TekkaChannel object and associated a NickListStore
			with it.

			Returns the newly created Tab object.
		"""
		ns = NickListStore()

		ns.set_modes(server.support_prefix[1])

		tab = self._create_tab(TekkaChannel, name, server,
			nicklist = ns)

		self.connect_callbacks(tab, ("joined","topic"))

		return tab

	@types(server = TekkaServer, name = basestring)
	def create_query(self, server, name):
		tab = self._create_tab(TekkaQuery, name, server)
		return tab

	@types (server = basestring)
	def create_server(self, server):
		tab = self._create_tab(TekkaServer, server)

		self.update_server(tab)

		self.connect_callbacks(tab, ("away","new_nick"))

		return tab

	@types (tab = TekkaServer)
	def update_server(self, tab):
		""" fetch server info from sushi and apply them
			to the given serverTab
		"""
		server = tab.name

		if com.sushi.user_away(server, com.get_own_nick(server)):
			# FIXME
			tab.away = "OHAI"

		tab.nick = com.parse_from(com.sushi.user_from(server, ""))[0]
		tab.support_prefix = com.sushi.support_prefix(server)
		tab.support_chantypes = com.sushi.support_chantypes(server)

	@types(server = basestring, child = basestring)
	def search_tab(self, server, child = ""):
		store = lib.gui_control.get_widget("serverTree").get_model()

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
	def search_tabs(self, server, name=""):
		"""	Searches for a pair of tabs.
			name can be empty, in that case
			only the server string is used
			for the search.

			Possible return values:
			(<serverTab>,<channelTab>)
			(<serverTab>,None)
			(None,None)
		"""
		store = lib.gui_control.get_widget("serverTree").get_model()
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
	def add_tab(self, server, object, update_shortcuts=True):
		"""	Adds a tab object into the server tree.
			server can be a string identifying a
			server acting as parent for the tab or
			None.

			On succes the method returns the path
			to the new tab, otherwise None.
		"""
		store = lib.gui_control.get_widget("serverTree").get_model()

		serverIter = None

		if server:
			for row in store:
				if row[0] == server:
					serverIter = row.iter

		iter = store.append(serverIter, row=(object,))
		object.path = store.get_path(iter)

		if server and config.get("tekka", "auto_expand"):
			# expand the whole server tab
			path = store.get_path(serverIter)
			lib.gui_control.get_widget("serverTree").expand_row(
				store.get_path(store.iter_parent(iter)), True)

		if update_shortcuts:
			lib.gui_control.updateServerTreeShortcuts()

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

	@types (tab = TekkaTab, update_shortcuts = bool)
	def remove_tab(self, tab, update_shortcuts=True):
		"""	Removes the tab from the server tree.
			There's no need for giving a parent due
			to to the unique identifying path stored
			inner the tekkaTab.
		"""
		store = lib.gui_control.get_widget("serverTree").get_model()

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

		callbacks = self.get_callbacks("remove")

		for cb in callbacks:
			cb(tab)

		store.remove(row.iter)

		# hack because the signal rows-reordered
		# does not work yet. Update all rows under
		# the deleted to the new path.
		#
		# XXX: is this still necessary?
		self.__updateLowerRows(store,nextIter)

		if update_shortcuts:
			lib.gui_control.updateServerTreeShortcuts()

		return True

	@types (old = TekkaTab, new = TekkaTab)
	def replace_tab(self, old, new):
		"""	Replaces the tab `old` with the tab `new`. """
		store = lib.gui_control.get_widget("serverTree").get_model()

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

	@types (servers = list, excludes = list)
	def get_all_tabs(self, servers=[], excludes=[]):
		"""
			Returns all registered tabs.
			If server is given, only the servers
			and it's children are returned.
			If exclude is given, the given servers
			will be ignored.

			Note:  if there's a newly row inserted, the
			Note:: tab-column can be None.
		"""
		store = lib.gui_control.get_widget("serverTree").get_model()

		tabs = []

		def lower(l):
			return [n.lower() for n in l if n]

		def iterate_store(model, path, iter):
			tab = model[path][0]
			if (None == tab
			or (tab.is_server() and tab.name.lower() in lower(excludes))
			or (not tab.is_server() and tab.server.name.lower() in lower(excludes))):
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

	def get_current_tab(self):
		"""
			Returns the current tab.
		"""
		store = lib.gui_control.get_widget("serverTree").get_model()
		try:
			return store[self.currentPath][0]
		except (IndexError,TypeError):
			return None

	def get_current_tabs(self):
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
		store = lib.gui_control.get_widget("serverTree").get_model()

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
			return store.get_value(iter, 0), None
		else:
			return store.get_value(pIter, 0), store.get_value(iter, 0)

		return None, None

	@types (tab = TekkaTab)
	def is_active(self, tab):
		"""
			Checks if the given tab is currently
			activated in the serverTree.
			Returns True if the tab is active,
			otherwise False.
		"""
		serverTab, channelTab = self.get_current_tabs()

		if not serverTab or (not channelTab and tab.is_channel()):
			return False

		if (tab.is_server()
			and tab.name.lower() == serverTab.name.lower()
			and not channelTab):
			return True

		if (( tab.is_channel() or tab.is_query() )
			and channelTab
			and tab.name.lower() == channelTab.name.lower()
			and tab.server.name.lower() == serverTab.name.lower()):
			return True

		return False

	def get_next_server(self, current):
		store = lib.gui_control.get_widget("serverTree").get_model()
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
	def get_next_tab(self, tab):
		""" get the next left tab near to tab.

			This function doesn't consider the
			type of the tab.
		"""
		if not tab or not tab.path:
			return None

		tablist = self.get_all_tabs()

		if not tablist or len(tablist) == 1:
			return None

		try:
			i = tablist.index(tab)
		except ValueError:
			return None

		return tablist[i-1]

	@types (path = tuple)
	def switch_to_path(self, path):
		""" Switch the server tree cursor
			to the row pointed to by path.

			This function returns None.
		"""
		if not lib.gui_control.gui_is_useable:
			return

		serverTree = lib.gui_control.get_widget("serverTree")
		store = serverTree.get_model()

		if not path:
			logging.error("switchToPath(): empty path given, aborting.")
			return

		try:
			tab = store[path][0]
		except IndexError:
			logging.error(
				"switchToPath(): tab not found in store, aborting.")
			return

		old_tab = self.get_current_tab()

		serverTree.set_cursor(path)
		self.currentPath = path

		lib.gui_control.replace_output_textview(tab.textview)

		self.emit("tab_switched", old_tab, tab)

		if tab.is_channel():
			"""
				show up topicbar and nicklist (in case
				they were hidden) and fill them with tab
				specific data.
			"""
			self.set_useable(tab, tab.joined)

			lib.gui_control.set_user_count(
				len(tab.nickList),
				tab.nickList.get_operator_count())

			if config.get_bool("tekka", "show_topicbar"):
				lib.gui_control.set_topic(
					lib.gui_control.markup_escape(tab.topic))
				lib.gui_control.get_widget("topicBar").show()

			lib.gui_control.get_widget("VBox_nickList").show_all()
			lib.gui_control.get_widget("nickList").set_model(tab.nickList)

		elif tab.is_query() or tab.is_server():
			# queries and server tabs don't have topics or nicklists
			self.set_useable(tab, tab.connected)

			lib.gui_control.get_widget("topicBar").hide()
			lib.gui_control.get_widget("VBox_nickList").hide()

		# reset message notification
		tab.setNewMessage(None)

		lib.gui_control.set_window_title(tab.name)

		if not tab.is_server():
			lib.gui_control.set_nick(com.get_own_nick(tab.server.name))
		else:
			lib.gui_control.set_nick(com.get_own_nick(tab.name))

	def switch_to_tab(self, tab):
		if not tab or not tab.path:
			return
		self.switch_to_path(tab.path)

	def switch_to_previous(self):
		tabs = self.get_all_tabs()
		tab = self.get_current_tab()

		try:
			i = tabs.index(tab)
		except ValueError:
			return

		try:
			self.switch_to_tab(tabs[i-1])
		except IndexError:
			return

	def switch_to_next(self):
		tabs = self.get_all_tabs()
		tab = self.get_current_tab()

		try:
			i = tabs.index(tab)
		except ValueError:
			return

		try:
			i = i+1
			if (i) == len(tabs):
				i = 0
			self.switch_to_tab(tabs[i])
		except IndexError:
			return


gobject.signal_new("tab_switched", TabControl, gobject.SIGNAL_ACTION,
	None, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))

