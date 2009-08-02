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

import gobject

import com
import config

import lib.gui_control
from lib.input_history import InputHistory
from lib.tab import TekkaTab, TekkaChannel, TekkaQuery, TekkaServer
from lib.output_textview import OutputTextView
from lib.nickListStore import nickListStore

from typecheck import types

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

	@types (d = dict)
	def set_callbacks(self, d):
		self._callbacks = d

	@types (key = basestring)
	def get_callback(self, key):
		try:
			return self._callbacks[key]
		except KeyError:
			raise ValueError, "No such signal handler: %s." % (key)

	@types (server = basestring, channel = basestring)
	def get_channel_prefix(self, server, channel):
		if not self.prefix_cache.has_key(server):
			self.prefix_cache[server] = {}

		if self.prefix_cache[server].has_key(channel):
			return self.prefix_cache[server][channel]
		else:
			self.prefix_cache[server][channel] = list(
				com.sushi.support_prefix(server)[1])
			return self.prefix_cache[server][channel]

	@types (tab = TekkaTab, switch = bool)
	def setUseable(self, tab, switch):
		""" switch the destinated tab from/to
			useable state
			((de)activate sensitive widgets)
		"""
		if not tab is self.get_current_tab():
			return

		widgetList = [lib.gui_control.get_widget('nickList')]

		for widget in widgetList:
			widget.set_sensitive (switch)

	def _createTab(self, tabtype, name, *args, **kwargs):
		""" instance class of type tabtype, connect signals,
			create textview and setup input history.
			
			Returns a new child of TekkaTab.
		"""
		tab = tabtype(name, *args, **kwargs)

		tab.textview = OutputTextView()
		tab.textview.show()
		lib.gui_control.set_font(tab.textview, lib.gui_control.get_font())

		tab.connect("new_message", self.get_callback("new_message"))
		tab.connect("new_name", self.get_callback("new_name"))
		tab.connect("new_path", self.get_callback("new_path"))
		tab.connect("connected", self.get_callback("connected"))

		tab.input_history = InputHistory(
			text_callback = lib.gui_control.get_widget("inputBar").get_text)

		return tab

	@types (server = basestring, name = basestring)
	def create_channel(self, server, name):
		""" create TekkaChannel object and associated a nickListStore
			with it.
			
			Returns the newly created Tab object.
		"""
		ns = nickListStore()

		ns.set_modes(self.get_channel_prefix(server, name))

		tab = self._createTab(TekkaChannel, name, server,
			nicklist = ns)
		tab.connect("joined", self.get_callback("joined"))

		return tab

	def create_query(self, server, name):
		tab = self._createTab(TekkaQuery, name, server)
		return tab

	def create_server(self, server):
		tab = self._createTab(TekkaServer, server)

		tab.connect("away", self.get_callback("away"))
		return tab

	@types (server = basestring, name = basestring)
	def search_tab(self, server, name=""):
		"""	Searches for server (and if name is given,
			for a tab identified by name).
			The method returns the tab object or None.
		"""
		store = lib.gui_control.get_widget("serverTree").get_model()

		for row in store:
			if row[1].lower() == server.lower():
				if not name:
					return row[2]
				else:
					for channel in row.iterchildren():
						if channel[1].lower() == name.lower():
							return channel[2]
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
			if row[1].lower() == server.lower():
				if not name:
					return (row[2], None)
				else:
					for channel in row.iterchildren():
						if channel[1].lower() == name.lower():
							return (row[2], channel[2])
		return (None, None)

	@types (server = (type(None), basestring), object = TekkaTab, update_shortcuts = bool)
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
				if row[1].lower() == server.lower():
					serverIter = row.iter

		iter = store.append(serverIter,
			row=(object.markup(),object.name,object))
		object.path = store.get_path(iter)

		if server and config.get("tekka", "auto_expand"):
			# expand the whole server tab
			lib.gui_control.get_widget("serverTree").expand_row(
				store.get_path(store.iter_parent(iter)),
				True)

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

			tab = store.get(nextIter, 2)
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

		store.remove(row.iter)

		# hack because the signal rows-reordered
		# does not work yet. Update all rows under
		# the deleted to the new path.
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

		store.set(row.iter, 0, new.markup(), 1, new.name, 2, new)
		new.path = store.get_path(row.iter)

		# apply new server name to childs
		if old.is_server():
			for row in store.iter_children(iter):
				row[2].server = new.name

	@types (server = basestring)
	def get_all_tabs(self, server=""):
		"""
			Returns all registered tabs.
			If server is given, only the server
			and it's childs are returned.
			
			Note:  if there's a newly row inserted, the
			Note:: tab-column can be None.
		"""
		store = lib.gui_control.get_widget("serverTree").get_model()

		tabs = []

		def iterate_store(model, path, iter):
			tab = model[path][2]
			if None == tab:
				return
			tabs.append(tab)

		if not server:
			store.foreach(iterate_store)
		else:
			for row in store:
				if row[1].lower() == server.lower():
					tabs.append(row[2])
					for child in row.iterchildren():
						tabs.append(child[2])
					break

		return tabs

	def get_current_tab(self):
		"""
			Returns the current tab.
		"""
		store = lib.gui_control.get_widget("serverTree").get_model()
		try:
			return store[self.currentPath][2]
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
			return store.get_value(iter, 2), None
		else:
			return store.get_value(pIter, 2), store.get_value(iter, 2)

		return None, None

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
			and tab.server.lower() == serverTab.name.lower()):
			return True

		return False

	def get_next_tab(self, tab):
		""" get the next left tab near to tab. 
		
			This function doesn't make a difference
			between the type of tab.
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
			print "switchToPath(): empty path given, aborting."
			return

		try:
			tab = store[path][2]
		except IndexError:
			print "switchToPath(): tab not found in store, aborting."
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
			self.setUseable(tab, tab.joined)

			lib.gui_control.set_user_count(
				len(tab.nickList),
				tab.nickList.get_operator_count())

			if config.get_bool("tekka", "show_topicbar"):
				lib.gui_control.get_widget("topicBar").set_text(tab.topic)
				lib.gui_control.get_widget("topicBar").show()

			lib.gui_control.get_widget("VBox_nickList").show_all()
			lib.gui_control.get_widget("nickList").set_model(tab.nickList)

		elif tab.is_query() or tab.is_server():
			# queries and server tabs don't have topics or nicklists
			self.setUseable(tab, tab.connected)

			lib.gui_control.get_widget("topicBar").hide()
			lib.gui_control.get_widget("VBox_nickList").hide()

		tab.setNewMessage(None)

		lib.gui_control.updateServerTreeMarkup(tab.path)
		lib.gui_control.set_window_title(tab.name)

		if not tab.is_server():
			lib.gui_control.set_nick(com.get_own_nick(tab.server))
		else:
			lib.gui_control.set_nick(com.get_own_nick(tab.name))

	def switch_to_tab(self, tab):
		if not tab or not tab.path:
			return
		self.switch_to_path(tab.path)

gobject.signal_new("tab_switched", TabControl, gobject.SIGNAL_ACTION,
	None, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))

