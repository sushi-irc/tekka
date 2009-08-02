import gobject

import gui_control
import com
import config

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

	@types(d = dict)
	def set_callbacks(self, d):
		self._callbacks = d

	def get_callback(self, key):
		try:
			return self._callbacks[key]
		except KeyError:
			raise ValueError, "No such signal handler: %s." % (key)

	@types(server = basestring, channel = basestring)
	def get_channel_prefix(self, server, channel):
		if not self.prefix_cache.has_key(server):
			self.prefix_cache[server] = {}

		if self.prefix_cache[server].has_key(channel):
			return self.prefix_cache[server][channel]
		else:
			self.prefix_cache[server][channel] = list(
				com.sushi.support_prefix(server)[1])
			return self.prefix_cache[server][channel]

	@types(tab = TekkaTab, switch = bool)
	def setUseable(self, tab, switch):
		""" switch the destinated tab from/to
			useable state
			((de)activate sensitive widgets)
		"""
		if not tab is self.getCurrentTab():
			return

		widgetList = [gui_control.get_widget('nickList')]

		for widget in widgetList:
			widget.set_sensitive (switch)

	def _createTab(self, tabtype, name, *args, **kwargs):
		tab = tabtype(name, *args, **kwargs)

		tab.textview = OutputTextView()
		tab.textview.show()
		gui_control.set_font(tab.textview, gui_control.get_font())

		tab.connect("new_message", self.get_callback("new_message"))
		tab.connect("new_name", self.get_callback("new_name"))
		tab.connect("new_path", self.get_callback("new_path"))
		tab.connect("connected", self.get_callback("connected"))

		tab.input_history = InputHistory(
			text_callback = gui_control.get_widget("inputBar").get_text)

		return tab

	def createChannel(self, server, name):
		ns = nickListStore()

		ns.set_modes(self.get_channel_prefix(server, name))

		tab = self._createTab(TekkaChannel, name, server,
			nicklist = ns)
		tab.connect("joined", self.get_callback("joined"))

		return tab

	def createQuery(self, server, name):
		tab = self._createTab(TekkaQuery, name, server)
		return tab

	def createServer(self, server):
		tab = self._createTab(TekkaServer, server)

		tab.connect("away", self.get_callback("away"))
		return tab

	def searchTab(self, server, name=""):
		"""
			Searches for server (and if name is given,
			for a tab identified by name).
			The method returns the tab object or None.
		"""
		store = gui_control.get_widget("serverTree").get_model()

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
		store = gui_control.get_widget("serverTree").get_model()
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
		store = gui_control.get_widget("serverTree").get_model()

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
			gui_control.get_widget("serverTree").expand_row(
				store.get_path(store.iter_parent(iter)),
				True)

		if update_shortcuts:
			gui_control.updateServerTreeShortcuts()

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


	def removeTab(self, tab, update_shortcuts=True):
		"""
			tab: tekkaTab

			Removes the tab from the server tree.
			There's no need for giving a parent due
			to to the unique identifying path stored
			inner the tekkaTab.
		"""
		store = gui_control.get_widget("serverTree").get_model()

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
			gui_control.updateServerTreeShortcuts()

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
		store = gui_control.get_widget("serverTree").get_model()

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
		store = gui_control.get_widget("serverTree").get_model()

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
			Note:  if there's a newly row inserted, the
			Note:: tab-column can be None.
		"""
		store = gui_control.get_widget("serverTree").get_model()

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

	def getCurrentTab(self):
		"""
			Returns the current tab.
		"""
		store = gui_control.get_widget("serverTree").get_model()
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
		store = gui_control.get_widget("serverTree").get_model()

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
		serverTab, channelTab = self.getCurrentTabs()

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

	def switchToPath(self, path):
		"""
			path: tuple

			Switches in TreeModel of serverTree to the
			tab identified by path.
		"""
		if not gui_control.gui_is_useable:
			return

		serverTree = gui_control.get_widget("serverTree")
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

		gui_control.replace_output_textview(tab.textview)

		self.emit("tab_switched", old_tab, tab)

		if tab.is_channel():
			"""
				show up topicbar and nicklist (in case
				they were hidden) and fill them with tab
				specific data.
			"""
			self.setUseable(tab, tab.joined)

			gui_control.setUserCount(
				len(tab.nickList),
				tab.nickList.get_operator_count())

			if config.get_bool("tekka", "show_topicbar"):
				gui_control.get_widget("topicBar").set_text(tab.topic)
				gui_control.get_widget("topicBar").show()

			gui_control.get_widget("VBox_nickList").show_all()
			gui_control.get_widget("nickList").set_model(tab.nickList)

		elif tab.is_query() or tab.is_server():
			# queries and server tabs don't have topics or nicklists
			self.setUseable(tab, tab.connected)

			gui_control.get_widget("topicBar").hide()
			gui_control.get_widget("VBox_nickList").hide()

		tab.setNewMessage(None)

		gui_control.updateServerTreeMarkup(tab.path)
		gui_control.setWindowTitle(tab.name)

		if not tab.is_server():
			gui_control.setNick(com.getOwnNick(tab.server))
		else:
			gui_control.setNick(com.getOwnNick(tab.name))

	def switchToTab(self, tab):
		if not tab or not tab.path:
			return
		self.switchToPath(tab.path)

gobject.signal_new("tab_switched", TabControl, gobject.SIGNAL_ACTION,
	None, (gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))

