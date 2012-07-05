# coding:utf-8

import gtk
import gobject

from time import time as current_time
from gettext import gettext as _

from .. import com
from .. import config
from .. import gui
from .. import signals

from ..typecheck import types
from ..helper.static import static

from ..gui.tabs.channel import TekkaChannel
from ..gui.tabs.server import TekkaServer
from ..gui.tabs.query import TekkaQuery
from ..gui.tabs.tab import TekkaTab

from ..lib.nick_list_store import NickListStore
from ..lib.inline_dialog import InlineMessageDialog
from ..lib.input_history import InputHistory

class TabTree(gobject.GObject):

	def __init__(self, tekka):
		self.tekka = tekka
		self.current_path = ()

		signals.connect_signal("nick", self.sushi_nick_change)

		gui.shortcuts.add_handlers({
			"servertree_previous": serverTree_shortcut_ctrl_Page_Up,
			"servertree_next": serverTree_shortcut_ctrl_Page_Down,
			"servertree_close": serverTree_shortcut_ctrl_w,
		})

		# connect tab control signals
		gui.tabs.add_callbacks({
			"new_message": tekka_tab_new_message_cb,
			"new_name": tekka_tab_new_name_cb,
			"add": tekka_tab_add_cb,
			"remove": tekka_tab_remove_cb,
			"new_markup": tekka_tab_new_markup_cb,
			"server_connected": tekka_tab_server_connected_cb,
			"joined": tekka_channel_joined_cb,
			"new_nick": tekka_server_new_nick_cb,
			"tab_switched": tekka_tab_switched_cb,
			"topic": tekka_channel_topic_changed_cb,
			})

		com.sushi.g_connect("maki-connected", self.maki_connected_cb)

		signals.connect_signal("connect", self.sushi_server_connect_cb)
		signals.connect_signal("connected", self.sushi_server_connected_cb)

		setup_tabs_view(tekka)


	def test(self):
		self._set_current_path((1,2))
		assert self.get_current_path() == (1,2)
		self._set_current_path(())

		return True


	def widget_signals(self):
		return {
			# server tree signals
			"tabs_view_button_press_event" :
				serverTree_button_press_event_cb,
			"tabs_view_row_activated":
				serverTree_row_activated_cb,
			"tabs_view_query_tooltip":
				serverTree_query_tooltip_cb,

			# Store of the tabs view
			"tab_store_rows_reordered":
				treemodel_rows_reordered_cb,
		}


	""" sushi signal handlers """

	def maki_connected_cb(self, sushi):
		self._add_existing_servers()


	def sushi_server_connect_cb(self, time, server):
		" connected to a server, add it if it didn't exist yet "
		self.tekka.set_useable(True)

		if not self.search_tab(server):
			tab = self._setup_new_server_tab(server)
			tab.sushi_server_connect_cb(time, server)


	def sushi_server_connected_cb(self, time, server):
		" maki connected successfuly to a server. "

		if not self.search_tab(server):
			tab = _setup_server(server)
			tab.sushi_server_connected_cb(time, server)


	@static(first_time={})
	def sushi_server_motd_cb(self, time, server, message):
		""" Server is sending a MOTD.
			Setup the server tab if it doesn't exist yet.
		"""
		first_time = sushi_server_motd_cb.first_time

		if not first_time.has_key(server):
			tab = gui.tabs.search_tab(server)

			if not tab:
				tab = _setup_server(server)
				tab.sushi_server_motd_cb(time, server, message)

		if not message:
			del first_time[server]


	""" further normal methods """


	@types (server = basestring)
	def _setup_new_server_tab(self, serverName):
		tab = self.create_server(serverName)

		self.add_tab(None, tab,
			update_shortcuts = config.get_bool("tekka","server_shortcuts"))

		return tab

	def _add_existing_servers(self):
		""" Adds all servers to tekka which are reported by maki. """
		# in case we're reconnecting, clear all stuff
		self.tekka.widgets.get_object("tab_store").clear()

		for server in com.sushi.servers():
			tab = self._setup_new_server_tab(server)
			tab.connected = True
			self._add_existing_channels(tab)

		try:
			toSwitch = gui.tabs.get_all_tabs()[1]
		except IndexError:
			return
		else:
			self.switch_to_path(toSwitch.path)


	def _add_existing_channels(self, server_tab):
		""" Adds all channels to tekka wich are reported by maki. """
		channels = com.sushi.channels(server_tab.name)

		for channel in channels:
			add = False
			tab = self.search_tab(server_tab.name, channel)

			if not tab:
				tab = self.create_channel(server_tab, channel)
				add = True

			tab.server = server_tab
			tab.refresh()

			if add:
				self.add_tab(server_tab, tab, update_shortcuts=False)
				tab.print_last_log()

			topic = com.sushi.channel_topic(server_tab.name, channel)
			tab.report_topic(current_time(), server_tab.name, channel, topic)

		self.tekka.shortcuts.assign_numeric_tab_shortcuts(gui.tabs.get_all_tabs())


	def _set_current_path(self, path):
		" called by the parent module on a tab switch "
		self.current_path = path


	def get_current_path(self):
		return self.current_path


	def get_current_tab(self):
		""" Returns the current tab """
		store = widgets.get_object("tab_store")

		try:
			return store[self.current_path][0]
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
		current_path = self.current_path
		store = self.tekka.widgets.get_object("tab_store")

		if not current_path:
			return None,None

		# iter could be server or channel
		try:
			iter = store.get_iter(current_path)
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


	def sushi_nick_change(self, time, server, fromStr, newNick):
		""" rename queries on nick change """
		nick = com.sushi.parse_from(from_str)[0]
		tab = self.find_tab_by_name(server, nick)

		if tab and tab.isQuery:
			tab.name = newNick


	@types(tabtype = TekkaTab)
	def _create_tab(self, tabtype, name, *args, **kwargs):
		""" instance class of type tabtype, connect signals,
			create output window and setup input history.

			Returns a new child of TekkaTab.
		"""
		tab = tabtype(self.tekka, name, *args, **kwargs)

		tab.window = gui.builder.get_new_output_window()
		tab.window.show_all()

		gui.mgmt.set_font(tab.window.textview, gui.mgmt.get_font())

		gui.tabs.connect_tab_callbacks(tab, ("new_message","new_name",
			"server_connected","new_markup"))

		tab.input_history = InputHistory(
			text_callback = self.tekka.widgets.get_object("input_entry").get_text)

		return tab


	@types (server = TekkaServer, name = basestring)
	def create_channel(self, server, name):
		""" Create TekkaChannel object and associated a NickListStore with it.
			Returns the newly created Tab object.
		"""
		ns = NickListStore()

		ns.set_modes(server.support_prefix[1])

		tab = self._create_tab(TekkaChannel, name, server, nicklist = ns)

		gui.tabs.connect_tab_callbacks(tab, ("joined","topic"))

		return tab


	@types(server = TekkaServer, name = basestring)
	def create_query(self, server, name):
		tab = self._create_tab(TekkaQuery, name, server)
		return tab


	@types (server = basestring)
	def create_server(self, server):
		tab = self._create_tab(TekkaServer, server)

		tab.update()

		gui.tabs.connect_tab_callbacks(tab, ("new_nick",))

		return tab


	@types(server = basestring, child = basestring)
	def search_tab(self, server, child = ""):
		store = self.tekka.widgets.get_object("tab_store")

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
		store = self.tekka.widgets.get_object("tab_store")
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
		store = self.tekka.widgets.get_object("tab_store")

		serverIter = None

		if server:
			for row in store:
				if row[0] == server:
					serverIter = row.iter

		iter = store.append(serverIter, row=(object,))
		object.path = store.get_path(iter)

		callbacks = gui.tabs.get_callbacks("add")

		for cb in callbacks:
			cb(object)

		if server and config.get("tekka", "auto_expand"):
			# expand the whole server tab
			path = store.get_path(serverIter)
			self.tekka.widgets.get_object("tabs_view").expand_row(
				store.get_path(store.iter_parent(iter)), True)

		if update_shortcuts:
			gui.shortcuts.assign_numeric_tab_shortcuts(get_all_tabs())

		return object.path


	@types (tab = TekkaTab, update_shortcuts = bool)
	def remove_tab(self, tab, update_shortcuts=True):
		"""	Removes the tab from the server tree.
			There's no need for giving a parent due
			to to the unique identifying path stored
			inner the tekkaTab.
		"""
		store =self.tekka.widgets.get_object("tab_store")

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

		callbacks = gui.tabs.get_callbacks("remove")

		for cb in callbacks:
			cb(tab)

		store.remove(row.iter)
		__updateLowerRows(store, nextIter)

		if update_shortcuts:
			gui.shortcuts.assign_numeric_tab_shortcuts(get_all_tabs())

		return True


	def get_tab_by_path(self, path):
		if not path:
			return

		store = self.tekka.widgets.get_object("tab_store")

		try:
			return store[path][0]
		except (KeyError, IndexError):
			return None


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
		store = self.tekka.widgets.get_object("tab_store")

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


	def get_next_server(self, current):
		" Get the server next to the given server or None "
		store = self.tekka.widgets.get_object("tab_store")
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


	@types(path=tuple)
	def switch_to_path(self, path):
		""" Switch the server tree cursor
			to the row pointed to by path.

			This function returns None.
		"""
		if not gui.mgmt.gui_is_useable:
			return

		tabs_view = self.tekka.widgets.get_object("tabs_view")
		store = self.tekka.widgets.get_object("tab_store")

		try:
			tab = store[path][0]
		except IndexError:
			logging.error("switch_to_path(): tab not found in store, aborting.")
			return

		old_tab = self.get_current_tab()

		tabs_view.set_cursor(path)

		# explicit import to not make it accesible to the public
		from gui.tabs.current import _set_current_path
		current._set_current_path(path)

		self.tekka.widgets.get_object("output_shell").set(tab.window)

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

				if (tab.topic
				or not config.get_bool("tekka","hide_topic_if_empty")):
					mgmt.visibility.show_topic_bar(True)
				else:
					mgmt.visibility.show_topic_bar(False)

			mgmt.visibility.show_nicks(True)
			widgets.get_object("nicks_view").set_model(tab.nickList)

		elif tab.is_query() or tab.is_server():
			# queries and server tabs don't have topics or nicklists
			if not status.get("connecting"):
				tab.set_useable(tab.connected)

			if config.get_bool("tekka","show_topic_bar"):
				# hide topic bar in queries if enabled
				mgmt.visibility.show_topic_bar(False)

			# hide nick list in queries
			mgmt.visibility.show_nicks(False)

		# reset message notification
		tab.set_new_message(None)

		mgmt.set_window_title(tab.name)

		if not tab.is_server():
			mgmt.set_nick(tab.server.nick)
		else:
			mgmt.set_nick(tab.nick)

		call_callback("tab_switched", old_tab, tab)


	def switch_to_previous(self):
		tabs = self.get_all_tabs()
		tab = self.get_current_tab()

		try:
			i = tabs.index(tab)
		except ValueError:
			return

		try:
			tabs[i-1].switch_to()
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
			tabs[i].switch_to()
		except IndexError:
			return





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



def setup(tekka):
	return TabTree(tekka)



def askToRemoveTab(tab):
	def response_handler(dialog, response_id):

		if response_id == gtk.RESPONSE_YES:

			if tab.is_channel():
				com.sushi.part(tab.server.name, tab.name,
					config.get("chatting", "part_message", ""))

			elif tab.is_server():
				com.sushi.quit(tab.name,
					config.get("chatting", "quit_message", ""))

			gui.tabs.remove_tab(tab)

		dialog.destroy()

	if tab.is_channel():
		message = _(u"Do you really want to close channel “%(name)s”?")
	elif tab.is_query():
		message = _(u"Do you really want to close query “%(name)s”?")
	elif tab.is_server():
		message = _(u"Do you really want to close server “%(name)s”?")

	dialog = InlineMessageDialog(
		message % { "name": tab.name },
		icon=gtk.STOCK_DIALOG_QUESTION,
		buttons=gtk.BUTTONS_YES_NO
	)
	dialog.connect("response", response_handler)

	gui.mgmt.show_inline_dialog(dialog)


def setup_tabs_view(tekka):
	""" Setup tab sorting, setup tab rendering """
	model = tekka.widgets.get_object("tab_store")

	# Sorting
	def cmpl(m,i1,i2):
		" compare columns lower case "

		a = m.get_value(i1, 0)
		b = m.get_value(i2, 0)

		c, d = None, None

		if a: c=a.name.lower()
		if b: d=b.name.lower()
		return cmp(c,d)

	model.set_sort_func(1, lambda m,i1,i2,*x: cmpl(m,i1,i2))
	model.set_sort_column_id(1, gtk.SORT_ASCENDING)

	# Setup the renderer
	column = gui.widgets.get_object("tabs_view_name_column")
	column.set_cell_data_func(
				gui.widgets.get_object("tabs_view_name_renderer"),
				serverTree_render_server_cb)



def serverTree_misc_menu_reset_activate_cb(menuItem):
	""" reset the markup of all tabs """

	for tab in gui.tabs.get_all_tabs():
		tab.set_new_message(None)


def serverTree_button_press_event_cb(serverTree, event):
	"""
		A row in the server tree was activated.
		The main function of this method is to
		cache the current activated row as path.
	"""

	try:
		path = serverTree.get_path_at_pos(int(event.x),int(event.y))[0]
		tab = serverTree.get_model()[path][0]
	except Exception as e:
		tab = None

	if event.button == 1:
		# activate the tab

		if tab:
			gui.tabs.switch_to_path(path)

	elif event.button == 2:
		# if there's a tab, ask to close
		if tab:
			askToRemoveTab(tab)

	elif event.button == 3:
		# popup tab menu

		if tab:
			menu = servertree_menu.ServerTreeMenu().get_menu(tab)

			if not menu:
				logging.error("error in creating server tree tab menu.")
				return False

			else:
				menu.popup(None, None, None, event.button, event.time)
				return True

		else:
			# display misc. menu
			menu = gtk.Menu()
			reset = gtk.MenuItem(label=_(u"Reset markup"))
			reset.connect("activate",
				serverTree_misc_menu_reset_activate_cb)
			menu.append(reset)
			reset.show()
			menu.popup(None,None,None,event.button,event.time)

	return False


def serverTree_row_activated_cb(serverTree, path, column):
	""" open the history dialog for the pointed tab """
	model = serverTree.get_model()
	tab = model[path][0]

	# don't show the history dialog for server tabs, they don't
	# have a history.
	if type(tab) != gui.tabs.TekkaServer:
		gui.dialogs.show_dialog("history", tab)



def tekka_server_new_nick_cb(tab, nick):
	""" New nick for the given tab. Apply the new nick in
		the GUI if the tab or a tab with the same server is active.
	"""

	activeTabs = gui.tabs.get_current_tabs()

	if (tab in activeTabs
	or (not tab.is_server() and tab.server in activeTabs)):
		gui.mgmt.set_nick(nick)



def tekka_tab_new_markup_cb(tab):
	""" Push the CellRenderer to re-render the serverTree """

	if not tab.path:
		return

	store = gui.widgets.get_object("tab_store")
	store[tab.path][0] = tab


def tekka_tab_new_message_cb(tab, mtype):
	""" A new message of the given type was received.
		If the tab is active, reset the message buffer
		and scroll the tab's textview to bottom if
		auto scrolling is enabled for this window.
	"""

	if tab.is_active():
		tab.set_new_message(None)

		if tab.window.auto_scroll and mtype:
			if tab.window.textview.is_smooth_scrolling():
				tab.window.textview.stop_scrolling()
				tab.window.textview.scroll_to_bottom(no_smooth = True)
			else:
				tab.window.textview.scroll_to_bottom()

	else:
		pass


def tekka_tab_new_name_cb(tab, name):
	tekka_tab_new_markup_cb(tab)


def tekka_tab_server_connected_cb(tab, connected):
	""" the server of the tab connected/disconnected """

	if tab.is_active():
		tab.set_useable(connected)


def tekka_channel_joined_cb(tab, switch):
	""" channel received a change on joined attribute """

	if tab.is_active():
		tab.set_useable(switch)


def tekka_tab_switched_cb(old, new):
	""" switched from tab old to tab new """

	inputBar = gui.widgets.get_object("input_entry")

	if old:
		itext = inputBar.get_text()
		old.set_input_text(itext)
		old.window.textview.set_read_line()

	inputBar.set_text("")
	inputBar.set_position(1)

	if new:
		inputBar.set_text(new.get_input_text())
		inputBar.set_position(len(inputBar.get_text()))

		if new.window.auto_scroll:
			# XXX: Needs testing!
			def check_for_scrolling():
				sw = new.window
				adj = sw.get_vadjustment()

				if adj.get_value() != (adj.upper - adj.page_size):
					sw.textview.scroll_to_bottom( no_smooth = True )
				else:
					print "No need for scrolling!"
				return False

			gobject.idle_add(check_for_scrolling)


def tekka_tab_add_cb(tab):
	""" a tab is added """

	if gui.mgmt.is_welcome_screen():
		# FIXME: this is called often if the tab is not changed
		gui.mgmt.visibility.show_welcome_screen(False)


def tekka_tab_remove_cb(tab):
	""" a tab is about to be removed """

	if gui.tabs.get_current_tab() == tab:
		# switch to another tab

		if tab.is_server():
			# server and children are removed, choose
			# another server
			server = gui.tabs.get_next_server(tab)

			if server:
				tabs = gui.tabs.get_all_tabs(servers = [server.name])
				nextTab = tabs[0]
			else:
				nextTab = None
		else:
			nextTab = gui.tabs.get_next_tab(tab)

		if None == nextTab:
			# lock interface
			# XXX:  maybe the inputBar should
			# XXX:: useable, though.
			gui.mgmt.set_useable(False)
		else:
			nextTab.switch_to()

	elif (tab.is_server()
	and len(gui.widgets.get_object("tab_store")) == 1):
		gui.mgmt.set_useable(False)


def tekka_channel_topic_changed_cb(tab, topic):
	if not tab.is_active(): return

	if (config.get_bool("tekka","hide_topic_if_empty")
	and config.get_bool("tekka", "show_topic_bar")):
		if topic:
			gui.mgmt.visibility.show_topic_bar(True)
		else:
			gui.mgmt.visibility.show_topic_bar(False)




def serverTree_query_tooltip_cb(widget, x, y, kbdmode, tooltip):
	""" show tooltips for treeview rows.

		Server tabs:
			Nick: <nickname>

		Channel tabs:
			Users: <count>
			Topic: <topic>
			Last Sentence: <last sentence>

		Query tabs:
			Last Sentence: <last sentence>
	"""

	def limit(s):
		limit = int(config.get("tekka","popup_line_limit"))
		if len(s) > limit:
			return markup.escape(s[:limit-3]+u"...")
		return markup.escape(s)

	path = widget.get_path_at_pos(x,y)

	if not path:
		return

	path = path[0]

	try:
		tab = widget.get_model()[path][0]
	except IndexError:
		return

	if tab.is_server():
		# TODO: away status
		s = "<b>" + _("Nickname: ") + "</b>" +  markup.escape(tab.nick)

	elif tab.is_channel():
		s = "<b>" +_("User: ") + "</b>" + str(len(tab.nickList)) +\
			"\n<b>" + _("Topic: ") + "</b>" +\
				limit(tab.topic) +\
			"\n<b>" + _("Last sentence: ") + "</b>" +\
				limit(tab.window.textview.get_last_line())

	elif tab.is_query():
		s = "<b>" + _("Last sentence: ") + "</b>" +\
			limit(tab.window.textview.get_last_line())

	tooltip.set_markup(s)

	return True


def serverTree_render_server_cb(column, renderer, model, iter):
	""" Renderer func for column "Server" in servertree """

	tab = model.get(iter, 0)

	if not tab or not tab[0]:
		return

	renderer.set_property("markup",tab[0].markup())




def treemodel_rows_reordered_cb(treemodel, path, iter, new_order):
	""" new_order is not accessible, so hack arround it... """

	# explicit import because what we do is bad.
	# there should be no one writing on current_path
	from ..gui.tabs.current import _set_current_path

	updated = False
	for row in treemodel:
		if not row[0]:
			continue

		if gui.tabs.get_current_path() == row[0].path and not updated:
			# update the currentPath cache
			_set_current_path(row.path)
			updated = True

		# update the tab's path cache
		row[0].path = row.path

		for child in row.iterchildren():
			if not child[0]:
				continue

			if (gui.tabs.get_current_path() == child[0].path
			and not updated):
				_set_current_path(child.path)
				updated = True

			# update path's tab cache
			child[0].path = child.path



def serverTree_shortcut_ctrl_w(serverTree, shortcut):
	""" Ctrl+W was hit, close the current tab (if any) """

	tab = gui.tabs.get_current_tab()

	if not tab:
		return

	askToRemoveTab(tab)

def serverTree_shortcut_ctrl_Page_Up(serverTree, shortcut):
	""" Ctrl+Page_Up was hit, go up in server tree """

	gui.tabs.switch_to_previous()


def serverTree_shortcut_ctrl_Page_Down(serverTree, shortcut):
	""" Ctrl+Page_Down was hit, go down in server tree """

	gui.tabs.switch_to_next()