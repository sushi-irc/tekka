import pango


from .. import com
from .. import gui

from ..lib import nick_list_store


class NickList(object):

	def __init__(self, tekka):
		pass


	def test(self):
		return True


	def widget_signals(self):
		return {
			# nick list signals
			"nicks_view_row_activated":
				nickList_row_activated_cb,
			"nicks_view_button_press_event":
				nickList_button_press_event_cb,
			"nicks_view_query_tooltip":
				nicks_view_query_tooltip_cb,
		}


def setup(tekka):
	setup_nicks_view()
	return NickList(tekka)



def setup_nicks_view():
	""" setup custom rendering of nick column """
	column = gui.widgets.get_object("nicks_store_nick_column")
	column.set_cell_data_func(
			gui.widgets.get_object("nicks_store_nick_renderer"),
			nickList_render_nicks_cb)


def nickList_row_activated_cb(nickList, path, column):
	"""
		The user activated a nick in the list.

		If there's a nick in the row a query
		for the nick on the current server will be opened.
	"""
	serverTab,channelTab = gui.tabs.get_current_tabs()

	try:
		name = nickList.get_model()[path][nick_list_store.COLUMN_NICK]
	except TypeError:
		# nickList has no model
		return
	except IndexError:
		# path is invalid
		return

	if gui.tabs.search_tab(serverTab.name, name):
		# already a query open
		return

	query = gui.tabs.create_query(serverTab, name)
	query.connected = True

	gui.tabs.add_tab(serverTab, query)

	query.print_last_log()
	query.switch_to()


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

		nick = None

		# get marked nick
		try:
			nick = nickList.get_model()[path[0]]
		except TypeError:
			# no model
			pass
		except IndexError:
			# path is "invalid"
			pass

		if nick:
			# display nick specific menu

			nick = nick[nick_list_store.COLUMN_NICK]

			menu = nicklist_menu.NickListMenu().get_menu(nick)

			if not menu:
				return False

			# finaly popup the menu
			menu.popup(None, None, None, event.button, event.time)

	return False


def nicks_view_query_tooltip_cb(view, x, y, kbdmode, tooltip):
	""" generate a tooltip with the awaymessage of the
		nick at the given x/y coordinates.
	"""

	# TODO: would be nice to have ident string of the nick here

	cursor = view.get_path_at_pos(x, y)

	if not cursor:
		return

	user_row = view.get_model()[cursor[0]]
	tip = ""

	# away message appendix
	if user_row[nick_list_store.COLUMN_AWAY]:
		# the user is away

		(server,_) = gui.tabs.get_current_tabs()


		if server:

			"""
			msg = com.sushi.awaymessage(server.name,
								user_row[nick_list_store.COLUMN_NICK])
			"""
			# TODO: retrieve awaymessage
			pass


def nickList_render_nicks_cb(column, renderer, model, iter):
	""" Renderer func for column "Nicks" in NickList """

	if not com.sushi.connected:
		# do not render if no connection exists
		return

	# highlight own nick
	serverTab = gui.tabs.get_current_tabs()[0]

	if not serverTab:
		return

	nick = model.get(iter, 1)
	away = model.get(iter, 2)

	if not nick:
		return

	nick = nick[0]
	away = away[0]

	# highlight own nick
	if com.get_own_nick(serverTab.name) == nick:
		renderer.set_property("weight", pango.WEIGHT_BOLD)
	else:
		renderer.set_property("weight", pango.WEIGHT_NORMAL)

	if away:
		renderer.set_property("style", pango.STYLE_ITALIC)
	else:
		renderer.set_property("style", pango.STYLE_NORMAL)
