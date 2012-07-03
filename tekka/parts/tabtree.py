# coding:utf-8

import gtk
import gobject

from gettext import gettext as _

from .. import gui
from .. import signals
from ..lib.inline_dialog import InlineMessageDialog


class TabTree(object):

	def __init__(self, tekka):
		self.current_tab = None

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

		setup_tabs_view(tekka)

	def test(self):
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


	def find_tab_by_name(self, server, name):
		pass


	def sushi_nick_change(self, time, server, fromStr, newNick):
		""" rename queries on nick change """
		nick = sushi.parse_from(from_str)[0]
		tab = self.find_tab_by_name(server, nick)

		if tab and tab.isQuery:
			tab.name = newNick



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