#!/usr/bin/env python
# coding: UTF-8
"""
Copyright (c) 2008 Marian Tietz
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


""" Purpose:
	setup and usage of submodules,
	main window signal handling,
	tekka internal signal handling,
	glue of all submodules
"""

import pygtk
pygtk.require("2.0")

import sys
import traceback

import gtk # TODO: catch gtk.Warning after init with warnings module

import os
import gobject
import pango
import dbus
import webbrowser
import locale
import types as ptypes
import logging

import gettext
from gettext import gettext as _

# TODO: point out why this has to be an direct adressed import...
import tekka.gui as gui
import tekka.gui.tabs

# local modules
from . import config
from . import com
from . import signals
from . import commands
from . import plugins

from .typecheck import types

from .lib import nick_list_store
from .lib.inline_dialog import InlineMessageDialog
from .lib.welcome_window import WelcomeWindow
from .lib.general_output_buffer import GOHTMLBuffer

from .helper import tabcompletion
from .helper import markup
from .helper.URLHandler import URLHandler

from .menus import *

import gui.builder
import gui.shortcuts

"""
Tekka intern signals
"""

def sushi_error_cb(sushi, title, message):
	""" Error in sushi interface occured. """

	def response_cb(d, i):
		gui.status.unset(title)
		d.destroy()

	d = InlineMessageDialog(title, message)
	d.connect("response", response_cb)
	gui.mgmt.show_inline_dialog(d)

	gui.status.set_visible(title, title)


def maki_connect_callback(sushi):
	""" connection to maki etablished """

	gui.mgmt.set_useable(True)


def maki_disconnect_callback(sushi):
	""" connection to maki lost """

	# FIXME:  after disconnecting and reconnecting,
	# FIXME:: the current tab's textview
	# FIXME:: is still insensitive - is this good or bad?
	gui.mgmt.set_useable(False)


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
			# FIXME:  on high load, the whole application
			# FIXME:: hangs. High load means, you insert a
			# FIXME:: text with around 2000 characters.
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

	if type(gui.widgets.get_object("output_window")) == WelcomeWindow:
		# FIXME: this is called often if the tab is not changed
		hide_welcome_screen()


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


def mainWindow_scroll_event_cb(mainWindow, event):
	""" MOD1 + SCROLL_DOWN -> Next tab
		MOD1 + SCROLL_UP -> Prev. tab
	"""

	if (event.state & gtk.gdk.MOD1_MASK
	and event.direction == gtk.gdk.SCROLL_DOWN):
		gui.tabs.switch_to_next()

	elif (event.state & gtk.gdk.MOD1_MASK
	and event.direction == gtk.gdk.SCROLL_UP):
		gui.tabs.switch_to_previous()


def mainWindow_delete_event_cb(mainWindow, event):
	"""
		The user want's to close the main window.
		If the status icon is enabled and the
		"hideOnClose" option is set the window
		will be hidden, otherwise the main looped
		will be stopped.
		On hide there is an read-line inserted
		in every tab so the user does not have to
		search were he was reading last time.
	"""

	statusIcon = gui.widgets.get_object("status_icon")

	if (config.get_bool("tekka", "hide_on_close")
	and statusIcon and statusIcon.get_visible()):

		for tab in gui.tabs.get_all_tabs():
			tab.window.textview.set_read_line()

		mainWindow.hide()

		return True

	else:
		gtk.main_quit()


def mainWindow_focus_in_event_cb(mainWindow, event):
	"""
		User re-focused the main window.
		If we were in urgent status, the user
		recognized it now so disable the urgent thing.
	"""

	gui.mgmt.set_urgent(False)
	return False


def mainWindow_size_allocate_cb(mainWindow, alloc):
	""" Main window was resized, store the new size in the config. """

	if not mainWindow.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED:
		config.set("sizes","window_width",alloc.width)
		config.set("sizes","window_height",alloc.height)


def mainWindow_window_state_event_cb(mainWindow, event):
	""" Window state was changed.
		If it's maximized or unmaximized, save that state.
	"""

	if event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED:
		config.set("tekka","window_maximized","True")
	else:
		config.set("tekka","window_maximized","False")


def inputBar_activate_cb(inputBar):
	""" Enter hit, pass the inputBar text over to the
		commands.parseInput method and add the text
		to the input history (if there's one).

		The inputBar is cleared after that.
	"""

	text = inputBar.get_text()

	tab = gui.tabs.get_current_tab()

	commands.parseInput(text)

	if tab:
		tab.input_history.add_entry(text)
		tab.input_history.reset()

	inputBar.set_text("")


def inputBar_key_press_event_cb(inputBar, event):
	""" Up -> Input history previous entry
		Down -> Input history next entry
		Tab -> Completion of the current word

		Everything else than tab ->
			No further completion wished, tell that.
	"""

	key =  gtk.gdk.keyval_name(event.keyval)
	tab =  gui.tabs.get_current_tab()

	text = unicode(inputBar.get_text(), "UTF-8")

	if key == "Up":
		# get next input history item
		if not tab:
			return

		hist = tab.input_history.get_previous()

		if hist != None:
			inputBar.set_text(hist)
			inputBar.set_position(len(hist))

	elif key == "Down":
		# get previous input history item
		if not tab:
			return

		hist = tab.input_history.get_next()

		if hist == None:
			return

		inputBar.set_text(hist)
		inputBar.set_position(len(hist))

	elif key == "Tab":
		# tab completion comes here.

		tabcompletion.complete(tab, inputBar, text)
		return True

	if key != "Tab":
		tabcompletion.stopIteration()


def notificationWidget_remove_cb(area, widget):
	""" restore the focus if a inline dialog is closed """
	gui.widgets.get_object("input_entry").grab_focus()


def outputShell_widget_changed_cb(shell, old_widget, new_widget):
	""" old_widget: OutputWindow
		new_widget: OutputWindow

		Set the current content of the output_shell in widgets store.
		- output_window <- new_widget
		- output        <- new_widget.textview
	"""
	if (type(old_widget) == WelcomeWindow
	and type(new_widget) != WelcomeWindow):
		hide_welcome_screen()

	gui.widgets.remove_object("output_window")
	gui.widgets.add_object(new_widget, "output_window")

	gui.widgets.remove_object("output")
	gui.widgets.add_object(new_widget.textview, "output")


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



""" Shortcut callbacks """

def inputBar_shortcut_ctrl_u(inputBar, shortcut):
	""" Ctrl + U was hit, clear the inputBar """

	gui.widgets.get_object("input_entry").set_text("")


def output_shortcut_ctrl_l(inputBar, shortcut):
	"""
		Ctrl+L was hit, clear the outputs.
	"""
	gui.mgmt.clear_all_outputs()


def output_shortcut_ctrl_f(inputBar, shortcut):
	""" show/hide the search toolbar """
	sb = gui.widgets.get_object("output_searchbar")

	if sb.get_property("visible"):
		sb.hide()
	else:
		sb.show_all()
		sb.grab_focus()


def output_shortcut_ctrl_g(inputBar, shortcut):
	""" search further """

	gui.widgets.get_object("output_searchbar").search_further()


def serverTree_shortcut_ctrl_Page_Up(serverTree, shortcut):
	""" Ctrl+Page_Up was hit, go up in server tree """

	gui.tabs.switch_to_previous()


def serverTree_shortcut_ctrl_Page_Down(serverTree, shortcut):
	""" Ctrl+Page_Down was hit, go down in server tree """

	gui.tabs.switch_to_next()


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


def serverTree_shortcut_ctrl_w(serverTree, shortcut):
	""" Ctrl+W was hit, close the current tab (if any) """

	tab = gui.tabs.get_current_tab()

	if not tab:
		return

	askToRemoveTab(tab)


def output_shortcut_Page_Up(inputBar, shortcut):
	"""
		Page_Up was hit, scroll up in output
	"""
	vadj = gui.widgets.get_object("output_window").get_vadjustment()

	if vadj.get_value() == 0.0:
		return # at top already

	n = vadj.get_value()-vadj.page_size
	if n < 0: n = 0
	gobject.idle_add(vadj.set_value,n)


def output_shortcut_Page_Down(inputBar, shortcut):
	""" Page_Down was hit, scroll down in output """

	vadj = gui.widgets.get_object("output_window").get_vadjustment()

	if (vadj.upper - vadj.page_size) == vadj.get_value():
		return # we are already at bottom

	n = vadj.get_value()+vadj.page_size

	if n > (vadj.upper - vadj.page_size):
		n = vadj.upper - vadj.page_size

	gobject.idle_add(vadj.set_value,n)


def inputBar_shortcut_ctrl_c(inputBar, shortcut):
	"""
		Ctrl + C was hit.
		Check every text input widget for selection
		and copy the selection to clipboard.
		FIXME: this solution sucks ass.
	"""
	buffer = gui.widgets.get_object("output").get_buffer()
	goBuffer = gui.widgets.get_object("general_output").get_buffer()
	topicBar = gui.widgets.get_object("topic_label")
	cb = gtk.Clipboard()

	if buffer.get_property("has-selection"):
		buffer.copy_clipboard(cb)
	elif inputBar.get_selection_bounds():
		inputBar.copy_clipboard()
	elif goBuffer.get_property("has-selection"):
		goBuffer.copy_clipboard(cb)
	elif topicBar.get_selection_bounds():
		bounds = topicBar.get_selection_bounds()
		text = unicode(topicBar.get_text(), "UTF-8")
		text = text[bounds[0]:bounds[1]]
		cb.set_text(text)


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



def treemodel_rows_reordered_cb(treemodel, path, iter, new_order):
	""" new_order is not accessible, so hack arround it... """
	updated = False
	for row in treemodel:
		if not row[0]:
			continue

		if gui.tabs._currentPath == row[0].path and not updated:
			# update the currentPath cache
			gui.tabs._currentPath = row.path
			updated = True

		# update the tab's path cache
		row[0].path = row.path

		for child in row.iterchildren():
			if not child[0]:
				continue

			if gui.tabs._currentPath == child[0].path and not updated:
				gui.tabs._currentPath = child.path
				updated = True

			# update path's tab cache
			child[0].path = child.path


def paned_notify_cb(paned, gparam):
	if not paned_notify_cb.init_done:
		return

	if gparam.name == "position":

		# only save if there are no inline dialogs displayed
		ids = gui.widgets.get_object("notification_vbox").get_children()
		if len(ids) == 0:
			config.set("sizes", gtk.Buildable.get_name(paned),
						paned.get_property("position"))

paned_notify_cb.init_done = False


""" Initial setup routines """

def setup_main_window():
	"""
		- set window title
		- set window icon
		- set window size
		- set window state
	"""
	win = gui.widgets.get_object("main_window")

	win.set_title("tekka IRC client")

	if config.get_bool("tekka", "rgba"):
		colormap = win.get_screen().get_rgba_colormap()
		if colormap:
			gtk.widget_set_default_colormap(colormap)

	try:
		img = gtk.icon_theme_get_default().load_icon("tekka",64,0)

		win.set_icon(img)
		""" 20.06.10
			Don't know if this is still needed.
		# Explicitly add a 128x128 icon to work around
		# a Compiz bug (LP: #312317)
		gtk.window_set_default_icon_list(
			gtk.gdk.pixbuf_new_from_file(iconPath),
			gtk.gdk.pixbuf_new_from_file_at_size(
				iconPath,
				128,
				128))
		"""
	except gobject.GError:
		# file not found
		pass

	# Restore sizes from last start
	width = config.get("sizes","window_width")
	height = config.get("sizes","window_height")

	if width and height:
		win.resize(int(width),int(height))


	# Restore window state from last start
	if config.get_bool("tekka","window_maximized"):
		win.maximize()

	# enable scrolling through server tree by scroll wheel
	def kill_mod1_scroll(w,e):
		if e.state & gtk.gdk.MOD1_MASK:
			w.emit_stop_by_name("scroll-event")

	for widget in ("general_output_window",
				   "tabs_window",
				   "nicks_window"):
		gui.widgets.get_object(widget).connect("scroll-event",
											   kill_mod1_scroll)

	win.show()


def setup_tabs_view():
	""" Setup tab sorting, setup tab rendering """
	model = gui.widgets.get_object("tab_store")

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


def setup_general_ouptut():
	""" set the textview's buffer to a GOHTMLBuffer and add
		the textview as general_output to the widgets store
	"""
	w = gui.widgets.get_object("general_output_window")
	w.textview.set_buffer(GOHTMLBuffer(handler=URLHandler))
	gui.widgets.add_object(w.textview, "general_output")


def setup_nicks_view():
	""" setup custom rendering of nick column """
	column = gui.widgets.get_object("nicks_store_nick_column")
	column.set_cell_data_func(
			gui.widgets.get_object("nicks_store_nick_renderer"),
			nickList_render_nicks_cb)


def load_paned_positions():
	""" restore the positions of the
		paned dividers for the list,
		main and output paneds.
	"""

	paneds = [
		"list_vpaned",
		"main_hpaned",
		"output_vpaned"]

	for paned_name in paneds:
		paned = gui.widgets.get_object(paned_name)

		position = config.get("sizes", paned_name, None)
		paned.set_property("position-set", True)

		if position == None:
			continue

		try:
			paned.set_position(int(position))
		except ValueError:
			logging.error("Failed to set position for paned %s" % (
				paned.name))
			continue


def setup_paneds():
	load_paned_positions()
	paned_notify_cb.init_done = True
	return False


def setup_fonts():
	""" add default font callback """
	try:
		import gconf

		def default_font_cb (client, id, entry, data):
			if not config.get_bool("tekka", "use_default_font"):
				return

			gui.mgmt.apply_new_font()

		c = gconf.client_get_default()

		c.add_dir("/desktop/gnome/interface", gconf.CLIENT_PRELOAD_NONE)
		c.notify_add("/desktop/gnome/interface/monospace_font_name",
			default_font_cb)

	except:
		# ImportError or gconf reported a missing dir.
		pass


def show_welcome_screen():
	""" hide the general_output_window and the list_vpaned
		and display the welcome window in the output shell.
	"""
	self = show_welcome_screen
	self.hides = ("general_output_window", "list_vpaned")

	for w in self.hides:
		gui.widgets.get_object(w).hide()

	s = gui.widgets.get_object("output_shell")

	w = WelcomeWindow()

	s.set(w)
	s.show_all()

	com.sushi.g_connect("maki-disconnected",
		lambda sushi: s.set_sensitive(True))


def hide_welcome_screen():
	""" undo the hiding from show_welcome_screen """

	hides = show_welcome_screen.hides

	for w in hides:
		gui.widgets.get_object(w).show()


def setupGTK():
	""" Set locale, load UI file, connect signals, setup widgets. """

	uifiles = config.get("uifiles", default={})

	# setup locale stuff
	try:
		locale.setlocale(locale.LC_ALL, '')
		locale.bindtextdomain("tekka", config.get("tekka","locale_dir"))
		locale.textdomain("tekka")
	except:
		pass

	# Fix about dialog URLs
	def about_dialog_url_hook (dialog, link, data):
		if gtk.gtk_version >= (2, 16, 0): return
		webbrowser.open(link)
	gtk.about_dialog_set_url_hook(about_dialog_url_hook, None)

	# Fire gettext up with our locale directory
	gettext.bindtextdomain("tekka", config.get("tekka","locale_dir"))
	gettext.textdomain("tekka")

	# parse ui file for main window
	gui.builder.load_main_window(uifiles["mainwindow"])

	setup_main_window()


	mmc = gui.widgets.get_object("main_menu_context")

	# tell the searchbar where it can get it's input
	gui.widgets.get_object("output_searchbar").textview_callback =\
		lambda: gui.widgets.get_object("output")

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
		"tab_switched": tekka_tab_switched_cb })

	# connect main window signals:
	sigdic = {
		# main window signals
		"main_window_delete_event":
			mainWindow_delete_event_cb,
		"main_window_focus_in_event":
			mainWindow_focus_in_event_cb,
		"main_window_size_allocate":
			mainWindow_size_allocate_cb,
		"main_window_window_state_event":
			mainWindow_window_state_event_cb,
		"main_window_scroll_event":
			mainWindow_scroll_event_cb,

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

		# Input entry...
		"input_entry_activate":
			inputBar_activate_cb,
		"input_entry_key_press_event":
			inputBar_key_press_event_cb,

		# Notification VBox
		"notification_vbox_remove":
			notificationWidget_remove_cb,

		"output_shell_widget_changed":
			outputShell_widget_changed_cb,

		# nick list signals
		"nicks_view_row_activated":
			nickList_row_activated_cb,
		"nicks_view_button_press_event":
			nickList_button_press_event_cb,
		"nicks_view_query_tooltip":
			nicks_view_query_tooltip_cb,

		# watch for position change of paneds
		"list_vpaned_notify":
			paned_notify_cb,
		"main_hpaned_notify":
			paned_notify_cb,
		"output_vpaned_notify":
			paned_notify_cb,


	# tekka menu context
		"tekka_server_list_item_activate":
			mmc.tekka.connect_activate_cb,
		"tekka_quit_item_activate":
			mmc.tekka.quit_activate_cb,
	# maki menu context
		"maki_connect_item_activate":
			mmc.maki.connect_activate_cb,
		"maki_disconnect_item_activate":
			mmc.maki.disconnect_activate_cb,
		"maki_shutdown_item_activate":
			mmc.maki.shutdown_activate_cb,
	# view menu context
		"view_general_output_item_toggled":
			mmc.view.showGeneralOutput_toggled_cb,
		"view_side_pane_item_toggled":
			mmc.view.showSidePane_toggled_cb,
		"view_status_bar_item_toggled":
			mmc.view.showStatusBar_toggled_cb,
		"view_status_icon_item_toggled":
			mmc.view.showStatusIcon_toggled_cb,
		"view_topic_bar_item_toggled":
			mmc.view.showTopicBar_toggled_cb,
	# tools menu context
		"tools_channel_list_item_activate":
			mmc.tools.channelList_activate_cb,
		"tools_file_transfers_item_activate" :
			mmc.tools.dcc_activate_cb,
		"tools_plugins_item_activate" :
			mmc.tools.plugins_activate_cb,
		"tools_debug_item_activate" :
			mmc.tools.debug_activate_cb,
		"tools_preferences_item_activate" :
			mmc.tools.preferences_activate_cb,
	# help menu context
		"help_irc_colors_item_activate":
			mmc.help.colors_activate_cb,
		"help_about_item_activate":
			mmc.help.about_activate_cb,
	}

	gui.widgets.connect_signals(sigdic)

	# push status messages directly in the status bar
	gui.status.connect("set-visible-status",
		lambda w,s,m: gui.widgets.get_object("statusbar")\
		.push(gui.status.id(s), m))

	# pop status message if they're unset
	gui.status.connect("unset-status",
		lambda w,s: gui.widgets.get_object("statusbar")\
		.pop(gui.status.id(s)))

	# initialize output_shell again (signals are connected now)
	gui.widgets.get_object("output_shell").reset()

	# apply visibility to widgets from config
	mmc.view.apply_visibilty_settings()

	# setup more complex widgets
	setup_tabs_view()
	setup_nicks_view()
	setup_general_ouptut()

	setup_fonts()

	# set input font
	gui.mgmt.set_font(gui.widgets.get_object("input_entry"),
					  gui.mgmt.get_font())

	# set general output font
	gui.mgmt.set_font(gui.widgets.get_object("general_output"),
					  gui.mgmt.get_font())

	gui.shortcuts.add_handlers({
			"clear_outputs": output_shortcut_ctrl_l,
			"output_page_up": output_shortcut_Page_Up,
			"output_page_down": output_shortcut_Page_Down,
			"input_clear_line": inputBar_shortcut_ctrl_u,
			"input_search": output_shortcut_ctrl_f,
			"input_search_further": output_shortcut_ctrl_g,
			"input_copy": inputBar_shortcut_ctrl_c,
			"servertree_previous": serverTree_shortcut_ctrl_Page_Up,
			"servertree_next": serverTree_shortcut_ctrl_Page_Down,
			"servertree_close": serverTree_shortcut_ctrl_w,
			"show_sidepane": lambda w,s: w.set_active(not w.get_active()),
		})
	gui.shortcuts.setup_shortcuts()

	# disable the GUI and wait for commands :-)
	gui.mgmt.set_useable(False)

	show_welcome_screen()

	gobject.idle_add(setup_paneds)


def tekka_excepthook(extype, exobj, extb):
	""" we got an exception, print it in a dialog box and,
		if possible, to the standard output.
	"""

	def dialog_response_cb(dialog, rid):
		del tekka_excepthook.dialog
		dialog.destroy()

	class ErrorDialog(gtk.Dialog):

		def __init__(self, message):

			gtk.Dialog.__init__(self,
				parent = gui.widgets.get_object("main_window"),
				title = _("Error occured"),
				buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

			self.set_default_size(400,300)

			self.error_label = gtk.Label()
			self.error_label.set_properties(width_chars=50,
											wrap=True,
											xalign=0.0)
			self.error_label.set_markup(_(
				"<span size='larger' weight='bold'>Error</span>\n\n"
				"An error occured – we apologize for that. "
				"Feel free to submit a bug report at "
				"<a href=\"https://bugs.launchpad.net/sushi\">https://bugs.launchpad.net/sushi</a>."))

			self.tv = gtk.TextView()
			self.tv.get_buffer().set_text(message)

			self.sw = gtk.ScrolledWindow()
			self.sw.set_properties(
				shadow_type = gtk.SHADOW_ETCHED_IN,
				hscrollbar_policy = gtk.POLICY_AUTOMATIC,
				vscrollbar_policy = gtk.POLICY_AUTOMATIC)
			self.sw.add(self.tv)

			self.vbox_inner = gtk.VBox()
			self.vbox_inner.set_property("border-width", 6)

			self.vbox_inner.pack_start(self.error_label)
			self.vbox_inner.pack_end(self.sw)

			self.vbox.pack_start(self.vbox_inner)
			self.vbox.show_all()


		def set_message(self, msg):
			self.tv.get_buffer().set_text(msg)


	message = "%s\n%s: %s\n" % (
		"".join(traceback.format_tb(extb)),
		extype.__name__,
		str(exobj))

	try:
		print >> sys.stderr, message
	except:
		pass

	self = tekka_excepthook
	try:
		dialog = self.dialog
	except AttributeError:
		dialog = self.dialog = ErrorDialog(message)
		dialog.connect("response", dialog_response_cb)
		dialog.show_all()
	else:
		self.dialog.set_message(message)

	sys.__excepthook__(extype, exobj, extb)


def setup_logging():
	""" set the path of the logfile to tekka.logfile config
		value and create it (including path) if needed.
		After that, add a logging handler for exceptions
		which reports exceptions catched by the logger
		to the tekka_excepthook. (DBus uses this)
	"""
	try:
		class ExceptionHandler(logging.Handler):
			""" handler for exceptions caught with logging.error.
				dump those exceptions to the exception handler.
			"""
			def emit(self, record):
				if record.exc_info:
					tekka_excepthook(*record.exc_info)

		logfile = config.get("tekka","logfile")
		logdir = os.path.dirname(logfile)

		if not os.path.exists(logdir):
			os.makedirs(logdir)

		logging.basicConfig(filename = logfile, level = logging.DEBUG,
			filemode="w")

		logging.getLogger("").addHandler(ExceptionHandler())

	except BaseException as e:
		print >> sys.stderr, "Logging init error: %s" % (e)


def setup():
	""" Setup the UI """

	# load config file, apply defaults
	config.setup()

	# create logfile, setup logging module
	setup_logging()

	# setup callbacks
	com.sushi.g_connect("sushi-error", sushi_error_cb)
	com.sushi.g_connect("maki-connected", maki_connect_callback)
	com.sushi.g_connect("maki-disconnected", maki_disconnect_callback)
	signals.setup()

	# build graphical interface
	setupGTK()

	# setup exception handler
	sys.excepthook = tekka_excepthook


def main():
	""" Fire up the UI """

	# connect to maki daemon
	com.connect()

	plugins.load_autoloads()

	# start main loop
	gtk.main()

	# after main loop break, write config
	config.write_config_file()

	# At last, close maki if requested
	if config.get_bool("tekka", "close_maki_on_close"):
		com.sushi.shutdown(config.get("chatting", "quit_message", ""))

