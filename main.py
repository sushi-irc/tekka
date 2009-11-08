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

"""
Coding style

Classes: MyClass
Methods: my_method
Variables: my_var OR myVar (that does not matter to me)

Line length: 80 characters
Indentation: Lines split up but with same context should
			 stick together:

			 if (myLongCondition != otherLongThing
			 and thatIsAll):
				 pass

			 or

			 my_string_function(
				 firstParam,
				 "This should be filled with %(vars)s." % {
					 "vars": testVar},
				 anotherParam)
"""

# TODO:  would be nice to be notified (in a visual way?) if there's
# TODO:: a new markup in the server tree for a hidden tab (not in the
# TODO:: current view scope due to scrolling). It would be cool if the
# TODO:: top or bottom (in order which direction the tab with the new
# TODO:: markup is) of the server tree smoothly flashes or something
# TODO:: like that.

import pygtk
pygtk.require("2.0")

import sys
import traceback

try:
	import gtk
except:
	print "Are you sure X is running?"
	sys.exit(1)

import os
from gobject import TYPE_STRING, TYPE_PYOBJECT, idle_add,GError
import pango
import dbus
import webbrowser
import locale
import types as ptypes
import logging
import gettext
_ = gettext.gettext

# local modules
import config
import com
import signals
import commands
from typecheck import types

import lib.gui_control as gui

from lib import dialog_control
from lib.inline_dialog import InlineMessageDialog
from lib import plugin_control
import lib.output_textview
import lib.nick_list_store

from helper.shortcuts import addShortcut, removeShortcut
from helper import tabcompletion

from menus import *

widgets = None

"""
Tekka intern signals
"""

def maki_connect_callback(sushi):
	""" connection to maki etablished """
	signals.handle_maki_connect_cb()
	gui.set_useable(True)

def maki_disconnect_callback():
	""" connection to maki lost """
	# FIXME:  after disconnecting and reconnecting,
	# FIXME:: the current tab's textview
	# FIXME:: is still insensitive
	signals.handle_maki_disconnect_cb()
	gui.set_useable(False)

def tekka_server_away_cb(tab, msg):
	pass

def tekka_server_new_nick_cb(tab, nick):
	activeTabs = gui.tabs.get_current_tabs()

	if (tab in activeTabs
	or (not tab.is_server() and tab.server in activeTabs)):
		gui.set_nick(nick)

def tekka_tab_new_markup_cb(tab):
	# FIXME: is there a better solution than _this_?
	if tab.path:
		store = gui.widgets.get_widget("serverTree").get_model()
		store.set_value(store.get_iter(tab.path), 0, tab)

def tekka_tab_new_message_cb(tab, mtype):
	""" a new message of the given type was received """
	if gui.tabs.is_active(tab):
		# FIXME: this won't reset urgent window hint and so on...
		tab.newMessage = [] # already read

		print "%s: auto_scroll = %s, mtype = %s" % (tab, tab.window.auto_scroll, mtype)

		if tab.window.auto_scroll and mtype:
			tab.window.textview.scroll_to_bottom()

	else:
		pass

def tekka_tab_new_name_cb(tab, name):
	tekka_tab_new_markup_cb(tab)

def tekka_tab_connected_cb(tab, connected):
	""" tab received a change on connected attribute """
	gui.tabs.set_useable(tab, connected)

def tekka_channel_joined_cb(tab, switch):
	""" channel received a change on joined attribute """
	gui.tabs.set_useable(tab, switch)

def tekka_channel_topic_cb(tab, topic):
	""" topic set """
	pass

def tekka_tab_new_path_cb(tab, new_path):
	""" a new path is set to the path """
	pass

def tekka_tab_switched_cb(tabclass, old, new):
	""" switched from tab old to tab new """
	inputBar = widgets.get_widget("inputBar")

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
			new.window.textview.scroll_to_bottom( no_smooth = True )

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
			gui.set_useable(False)
		else:
			gui.tabs.switch_to_tab(nextTab)

	elif (tab.is_server()
	and len(gui.get_widget("serverTree").get_model()) == 1):
		gui.set_useable(False)

"""
Glade signals
"""

def menu_tekka_Connect_activate_cb(menuItem):
	"""
		menuBar -> tekka -> connect was clicked,
		show up server dialog and connect to the
		returned server (if any).
	"""

	def server_dialog_callback(server_list):
		if server_list:
			for server in server_list:
				com.sushi.connect(server)

	if not com.sushi.connected:
		d = InlineMessageDialog(_("tekka could not connect to maki."),
			_("Please check whether maki is running."))
		gui.showInlineDialog(d)
		d.connect("response", lambda d,id: d.destroy())

	else:
		dialog_control.showServerDialog(server_dialog_callback)

def menu_View_showGeneralOutput_toggled_cb(menuItem):
	"""
		Deactivate or enable (hide/show) the general output
		widget.
	"""
	sw = gui.widgets.get_widget("scrolledWindow_generalOutput")

	if menuItem.get_active():
		sw.show_all()
		config.set("tekka","show_general_output","True")
	else:
		sw.hide()
		config.set("tekka","show_general_output","False")

def menu_View_showSidePane_toggled_cb(menuItem):
	""" Toggle side pane (listVPaned) """
	p = gui.widgets.get_widget("listVPaned")

	if menuItem.get_active():
		p.show()
		config.set("tekka","show_side_pane", "True")
	else:
		p.hide()
		config.set("tekka","show_side_pane", "False")


def menu_View_showStatusBar_toggled_cb(menuItem):
	"""
		hide or show the status bar.
	"""
	bar = gui.widgets.get_widget("statusBar")
	if menuItem.get_active():
		bar.show()
		config.set("tekka","show_status_bar","True")
	else:
		bar.hide()
		config.set("tekka","show_status_bar","False")

def menu_View_showStatusIcon_toggled_cb(menuItem):
	"""
	hide or show the status icon
	"""
	if not menuItem.get_active():
		config.set("tekka", "show_status_icon", "False")
		gui.switch_status_icon(False)

	else:
		config.set("tekka", "show_status_icon", "True")
		gui.switch_status_icon(True)

def menu_View_showTopicBar_toggled_cb(menuItem):
	""" hide or show topic bar """
	if not menuItem.get_active():
		config.set("tekka", "show_topicbar", str(False))
		gui.widgets.get_widget("topicBar").hide()
	else:
		config.set("tekka", "show_topicbar", str(True))
		tb = gui.widgets.get_widget("topicBar")

		cTab = gui.tabs.get_current_tab()

		if cTab and cTab.is_channel():
			tb.set_text(cTab.topic)

		tb.show()

def menu_Dialogs_channelList_activate_cb(menuItem):
	""" show channel list dialog. """
	if not com.sushi.connected:
		d = InlineMessageDialog(
			_("tekka could not connect to maki."),
			_("Please check whether maki is running."))

		gui.showInlineDialog(d)
		d.connect("response", lambda d,i: d.destroy())

	else:

		sTab,cTab = gui.tabs.get_current_tabs()

		if not sTab:
			d = InlineMessageDialog(_("tekka could not determine server."),
				_("There is no active server. Click on a server tab or a "
				"child of a server tab to activate the server."))
			d.connect("response", lambda w,i: w.destroy())
			gui.showInlineDialog(d)

		else:
			dialog_control.showChannelListDialog(sTab.name)

def menu_Dialogs_dcc_activate_cb(menuItem):
	""" show file transfers dialog """
	dialog_control.showDCCDialog()

def menu_Dialogs_plugins_activate_cb(menuItem):
	"""
	show plugin load/unload/list dialog.
	"""
	dialog_control.showPluginsDialog()

def menu_Dialogs_debug_activate_cb(menuItem):
	dialog_control.showDebugDialog()

def menu_Dialogs_preferences_activate_cb(menuItem):
	dialog_control.showPreferencesDialog()

def menu_Help_Colors_activate_cb(menuItem):
	dialog_control.showColorTableDialog()

def menu_Help_about_activate_cb(menuItem):
	"""
		Show the about dialog!
	"""
	def about_response_cb(dialog, response_id):
		dialog.destroy()

	widgets = gtk.glade.XML(config.get("gladefiles","dialogs") + "about.glade")
	d = widgets.get_widget("aboutDialog")
	d.connect("response", about_response_cb)
	d.show_all()

def mainWindow_scroll_event_cb(mainWindow, event):
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
	if (config.get_bool("tekka", "hide_on_close")
		and gui.statusIcon
		and gui.statusIcon.get_visible()):

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
	gui.set_urgent(False)
	return False

def mainWindow_size_allocate_cb(mainWindow, alloc):
	"""
		Main window was resized.
		Store the new size in the config.
	"""
	if not mainWindow.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED:
		config.set("sizes","window_width",alloc.width)
		config.set("sizes","window_height",alloc.height)

def mainWindow_window_state_event_cb(mainWindow, event):
	"""
		Window state was changed.
		Track maximifoo and save it.
	"""

	if event.new_window_state & gtk.gdk.WINDOW_STATE_MAXIMIZED:
		config.set("tekka","window_maximized","True")
	else:
		config.set("tekka","window_maximized","False")

def inputBar_activate_cb(inputBar):
	"""
		Receives if a message in the input bar
		was entered and sent.
		The entered message will be passed
		to the commands module (parseInput(text))
		and the input bar will be cleared.
	"""
	text = inputBar.get_text()

	tab = gui.tabs.get_current_tab()

	commands.parseInput(text)

	if tab:
		tab.input_history.add_entry(text)
		tab.input_history.reset()

	inputBar.set_text("")

def inputBar_key_press_event_cb(inputBar, event):
	"""
		Key pressed in inputBar.
		Implements tab and command completion.
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

def outputShell_widget_changed_cb(shell, old_widget, new_widget):
	""" old_widget: OutputWindow
		new_widget: OutputWindow
	"""
	print "widgets changed: %s to %s" % (old_widget, new_widget)

	new_widget.set_property("name", "outputWindow")
	new_widget.textview.set_property("name", "output")

	gui.widgets.remove_widget(old_widget)
	gui.widgets.add_widget(new_widget)

	gui.widgets.remove_widget(old_widget.textview)
	gui.widgets.add_widget(new_widget.textview)

def serverTree_misc_menu_reset_activate_cb(menuItem):
	"""
	reset the markup of all tabs
	"""
	for tab in gui.tabs.get_all_tabs():
		tab.setNewMessage(None)

def serverTree_button_press_event_cb(serverTree, event):
	"""
		A row in the server tree was activated.
		The main function of this method is to
		cache the current activated row as path.
	"""

	try:
		path = serverTree.get_path_at_pos(int(event.x),int(event.y))[0]
		tab = serverTree.get_model()[path][0]
	except Exception,e:
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

	dialog_control.showHistoryDialog(tab)

def nickList_row_activated_cb(nickList, path, column):
	"""
		The user activated a nick in the list.

		If there's a nick in the row a query
		for the nick on the current server will be opened.
	"""
	serverTab,channelTab = gui.tabs.get_current_tabs()

	try:
		name = nickList.get_model()[path][lib.nick_list_store.COLUMN_NICK]
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

	gui.print_last_log("", "", tab = query)
	gui.tabs.switch_to_tab(query)

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

			nick = nick[lib.nick_list_store.COLUMN_NICK]

			menu = nicklist_menu.NickListMenu().get_menu(nick)

			if not menu:
				return False

			# finaly popup the menu
			menu.popup(None, None, None, event.button, event.time)

	return False

def outputVBox_size_allocate_cb(outputVBox, alloc):
	widget = gui.widgets.get_widget("topicBar")
	widget.set_size_request(alloc.width, -1)

"""
	Shortcut callbacks
"""

def inputBar_shortcut_ctrl_u(inputBar, shortcut):
	"""
		Ctrl + U was hit, clear the inputBar
	"""
	widgets.get_widget("inputBar").set_text("")

def output_shortcut_ctrl_l(inputBar, shortcut):
	"""
		Ctrl+L was hit, clear the outputs.
	"""
	current_tab = gui.tabs.get_current_tab()

	if current_tab:
		output = current_tab.window.textview

		buf = output.get_buffer()
		if buf:
			buf.set_text("")

	buf = widgets.get_widget("generalOutput").get_buffer()
	if buf:
		buf.set_text("")

def output_shortcut_ctrl_f(inputBar, shortcut):
	""" show/hide the search toolbar """
	if gui.searchToolbar.get_property("visible"):
		gui.searchToolbar.hide()
		return

	gui.searchToolbar.show_all()
	gui.searchToolbar.grab_focus()

def output_shortcut_ctrl_g(inputBar, shortcut):
	""" search further """
	gui.searchToolbar.search_further()

def serverTree_shortcut_ctrl_Page_Up(serverTree, shortcut):
	"""
		Ctrl+Page_Up was hit, go up in server tree
	"""
	gui.tabs.switch_to_previous()

def serverTree_shortcut_ctrl_Page_Down(serverTree, shortcut):
	"""
		Ctrl+Page_Down was hit, go down in server tree
	"""
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

	gui.showInlineDialog(dialog)

def serverTree_shortcut_ctrl_w(serverTree, shortcut):
	"""
		Ctrl+W was hit, close the current tab (if any)
	"""

	tab = gui.tabs.get_current_tab()

	if not tab:
		return

	askToRemoveTab(tab)

def output_shortcut_Page_Up(inputBar, shortcut):
	"""
		Page_Up was hit, scroll up in output
	"""
	vadj = widgets.get_widget("outputWindow").get_vadjustment()

	if vadj.get_value() == 0.0:
		return # at top already

	n = vadj.get_value()-vadj.page_size
	if n < 0: n = 0
	idle_add(vadj.set_value,n)

def output_shortcut_Page_Down(inputBar, shortcut):
	"""
		Page_Down was hit, scroll down in output
	"""
	vadj = widgets.get_widget("outputWindow").get_vadjustment()

	if (vadj.upper - vadj.page_size) == vadj.get_value():
		return # we are already at bottom

	n = vadj.get_value()+vadj.page_size
	if n > (vadj.upper - vadj.page_size): n = vadj.upper - vadj.page_size
	idle_add(vadj.set_value,n)

def inputBar_shortcut_ctrl_c(inputBar, shortcut):
	"""
		Ctrl + C was hit.
		Check every text input widget for selection
		and copy the selection to clipboard.
		FIXME: this solution sucks ass.
	"""
	buffer = gui.get_current_output_textview().get_buffer()
	goBuffer = widgets.get_widget("generalOutput").get_buffer()
	topicBar = widgets.get_widget("topicBar")
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
	""" show tooltips for treeview rows """

	def limit(s):
		limit = int(config.get("tekka","popup_line_limit"))
		if len(s) > limit:
			return gui.escape(s[:limit-3]+u"...")
		return gui.escape(s)

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
		s = "<b>" + _("Nickname: ") + "</b>" +  gui.escape(tab.nick)

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

	if not nick:
		return

	nick = nick[0]

	# highlight own nick
	if com.get_own_nick(serverTab.name) == nick:
		renderer.set_property("weight", pango.WEIGHT_BOLD)
	else:
		renderer.set_property("weight", pango.WEIGHT_NORMAL)

	# TODO: highlighing of users which are away

"""
Initial setup routines
"""

def setup_mainWindow():
	"""
		- set window title
		- set window icon
		- set window size
		- set window state
	"""
	win = widgets.get_widget("mainWindow")

	if config.get_bool("tekka", "rgba"):
		colormap = win.get_screen().get_rgba_colormap()
		if colormap:
			gtk.widget_set_default_colormap(colormap)

	iconPath = config.get("tekka","status_icon")
	if iconPath:
		try:
			# Explicitly add a 64x64 icon to work around
			# a Compiz bug (LP: #312317)
			gtk.window_set_default_icon_list(
				gtk.gdk.pixbuf_new_from_file(iconPath),
				gtk.gdk.pixbuf_new_from_file_at_size(
					iconPath,
					64,
					64))

		except GError:
			# file not found
			pass

	width = config.get("sizes","window_width")
	height = config.get("sizes","window_height")

	if width and height:
		win.resize(int(width),int(height))

	if config.get_bool("tekka","window_maximized"):
		win.maximize()

	# enable scrolling through server tree by scroll wheel
	def kill_mod1_scroll(w,e):
		if e.state & gtk.gdk.MOD1_MASK:
			w.emit_stop_by_name("scroll-event")

	for widget in ("scrolledWindow_generalOutput",
				"scrolledWindow_serverTree","scrolledWindow_nickList"):
		widgets.get_widget(widget).connect("scroll-event",
			kill_mod1_scroll)

	win.connect("scroll-event", mainWindow_scroll_event_cb)

	win.show_all()

def treemodel_rows_reordered_cb(treemodel, path, iter, new_order):
	""" new_order is not accessible, so hack arround it... """
	updated = False
	for row in treemodel:
		if not row[0]:
			continue

		if gui.tabs.currentPath == row[0].path and not updated:
			gui.tabs.currentPath = row.path
			updated = True

		row[0].path = row.path

		for child in row.iterchildren():
			if not child[0]:
				continue

			if gui.tabs.currentPath == child[0].path and not updated:
				gui.tabs.currentPath = child.path
				updated = True

			child[0].path = child.path

def setup_serverTree():
	"""
		Sets up a treemodel with three columns.
		The first column is a pango markup language
		description, the second is the identifying
		channel or server name and the third is a
		tab object.
	"""
	tm = gtk.TreeStore(TYPE_PYOBJECT)

	# Sorting
	def cmpl(m,i1,i2):
		" compare columns lower case "
		a = m.get_value(i1, 0)
		b = m.get_value(i2, 0)
		c,d=None,None
		if a: c=a.name.lower()
		if b: d=b.name.lower()
		return cmp(c,d)

	tm.set_sort_func(1,
		lambda m,i1,i2,*x: cmpl(m,i1,i2))
	tm.set_sort_column_id(1, gtk.SORT_ASCENDING)
	tm.connect("rows-reordered", treemodel_rows_reordered_cb)

	# further stuff (set model to treeview, add columns)

	widget = widgets.get_widget("serverTree")

	widget.set_model(tm)
	widget.set_property("has-tooltip", True)
	widget.connect("query-tooltip", serverTree_query_tooltip_cb)

	renderer = gtk.CellRendererText()
	column = gtk.TreeViewColumn("Server", renderer)
	column.set_cell_data_func(renderer, serverTree_render_server_cb)

	widget.append_column(column)
	widget.set_headers_visible(False)

def setup_nickList():
	"""
		Sets up a empty nickList widget.
		Two columns (both rendered) were set up.
		The first is the prefix and the second
		the nick name.
	"""
	widget = widgets.get_widget("nickList")
	widget.set_model(None)

	renderer = gtk.CellRendererText()
	column = gtk.TreeViewColumn("Prefix", renderer, text=0)
	widget.append_column(column)

	renderer = gtk.CellRendererText()
	column = gtk.TreeViewColumn("Nicks", renderer, text=1)
	column.set_cell_data_func(renderer, nickList_render_nicks_cb)
	widget.append_column(column)

	widget.set_headers_visible(False)

def setup_shortcuts():
	"""
		Set shortcuts to widgets.

		- ctrl + page_up -> scroll to prev tab in server tree
		- ctrl + page_down -> scroll to next tab in server tree
		- ctrl + w -> close the current tab
		- ctrl + l -> clear the output buffer
		- ctrl + u -> clear the input entry
		- ctrl + s -> hide/show the side pane
	"""
	gui.accelGroup = gtk.AccelGroup()
	widgets.get_widget("mainWindow").add_accel_group(gui.accelGroup)

	addShortcut(gui.accelGroup, widgets.get_widget("inputBar"), "<ctrl>u",
		inputBar_shortcut_ctrl_u)
	addShortcut(gui.accelGroup, widgets.get_widget("inputBar"), "<ctrl>l",
		output_shortcut_ctrl_l)
	addShortcut(gui.accelGroup, widgets.get_widget("inputBar"), "<ctrl>f",
		output_shortcut_ctrl_f)
	addShortcut(gui.accelGroup, widgets.get_widget("inputBar"), "<ctrl>g",
		output_shortcut_ctrl_g)

	addShortcut(gui.accelGroup, widgets.get_widget("serverTree"),
		"<ctrl>Page_Up", serverTree_shortcut_ctrl_Page_Up)
	addShortcut(gui.accelGroup, widgets.get_widget("serverTree"),
		"<ctrl>Page_Down", serverTree_shortcut_ctrl_Page_Down)
	addShortcut(gui.accelGroup, widgets.get_widget("serverTree"),
		"<ctrl>w", serverTree_shortcut_ctrl_w)

	addShortcut(gui.accelGroup, widgets.get_widget("inputBar"),
		"Page_Up", output_shortcut_Page_Up)
	addShortcut(gui.accelGroup, widgets.get_widget("inputBar"),
		"Page_Down", output_shortcut_Page_Down)

	addShortcut(gui.accelGroup, widgets.get_widget("inputBar"),
		"<ctrl>c", inputBar_shortcut_ctrl_c)

	addShortcut(gui.accelGroup,
		widgets.get_widget("menu_View_showSidePane"), "<ctrl>s",
		lambda w,s: w.set_active(not w.get_active()))


def connect_maki():
	"""
		Tries to connect to maki over DBus.
		If succesful, the GUI is enabled (gui.setUseable(True))
		and signals, dialogs, menus as well as the commands module
		were set up.

		See also: maki_connect_callback
	"""
	com.connect()

def paned_notify_cb(paned, gparam):
	""" watch every property set for
		paned. If the property equals
		position, save the new value
		to the config.
	"""
	if gparam.name == "position":
		config.set("sizes", paned.name, paned.get_property("position"))

def load_paned_positions():
	""" restore the positions of the
		paned dividers for the list,
		main and output paneds.
	"""
	paneds = [
		widgets.get_widget("listVPaned"),
		widgets.get_widget("mainHPaned"),
		widgets.get_widget("outputVPaned")]

	for paned in paneds:
		paned.set_property("position-set", True)
		position = config.get("sizes", paned.name, None)

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

	sigdic = {
		# watch for position change of paneds
		"listVPaned_notify_cb":
			paned_notify_cb,
		"mainHPaned_notify_cb":
			paned_notify_cb,
		"outputVPaned_notify_cb":
			paned_notify_cb,
		}
	widgets.signal_autoconnect(sigdic)

	return False

def setup_fonts():
	""" add default font callback """
	try:
		import gconf

		def default_font_cb (client, id, entry, data):
			if not config.get_bool("tekka", "use_default_font"):
				return

			gui.apply_new_font()

		c = gconf.client_get_default()

		c.add_dir("/desktop/gnome/interface", gconf.CLIENT_PRELOAD_NONE)
		c.notify_add("/desktop/gnome/interface/monospace_font_name",
			default_font_cb)

	except:
		# ImportError or gconf reported a missing dir.
		pass

def setupGTK():
	"""
		Set locale, parse glade files.
		Connects gobject widget signals to code.
		Setup widgets.
	"""
	global commands, signals
	global widgets

	gladefiles = config.get("gladefiles", default={})

	# setup locale stuff
	try:
		locale.setlocale(locale.LC_ALL, '')
	except:
		pass

	gettext.bindtextdomain("tekka", config.get("tekka","locale_dir"))
	gettext.textdomain("tekka")

	gtk.glade.bindtextdomain("tekka", config.get("tekka","locale_dir"))
	gtk.glade.textdomain("tekka")

	# parse glade file for main window
	widgets = gui.load_widgets(
		gladefiles["mainwindow"], "mainWindow")

	def about_dialog_url_hook (dialog, link, data):
		if gtk.gtk_version >= (2, 16, 0):
			return

		webbrowser.open(link)

	gtk.about_dialog_set_url_hook(about_dialog_url_hook, None)

	setup_mainWindow()

	# to some setup on the search toolbar
	gui.searchToolbar.hide()
	gui.searchToolbar.textview = gui.widgets.get_widget("output")

	# connect tab control signals
	gui.tabs.add_callbacks({
		"new_message": tekka_tab_new_message_cb,
		"new_name": tekka_tab_new_name_cb,
		"new_path": tekka_tab_new_path_cb,
		"remove": tekka_tab_remove_cb,
		"new_markup": tekka_tab_new_markup_cb,
		"connected": tekka_tab_connected_cb,
		"joined": tekka_channel_joined_cb,
		"away": tekka_server_away_cb,
		"topic": tekka_channel_topic_cb,
		"new_nick": tekka_server_new_nick_cb })

	gui.tabs.connect("tab_switched", tekka_tab_switched_cb)

	# connect main window signals:
	sigdic = {
		# tekka menu
		"menu_tekka_Connect_activate_cb":
			menu_tekka_Connect_activate_cb,
		"menu_tekka_Quit_activate_cb":
			gtk.main_quit,

		# maki menu
		"menu_maki_Connect_activate_cb":
			lambda w: connect_maki(),
		"menu_maki_Disconnect_activate_cb":
			lambda w: com.disconnect(),
		"menu_maki_Shutdown_activate_cb":
			lambda w: com.sushi.shutdown(
				config.get("chatting", "quit_message", "")),

		# view menu
		"menu_View_showGeneralOutput_toggled_cb":
			menu_View_showGeneralOutput_toggled_cb,
		"menu_View_showSidePane_toggled_cb":
			menu_View_showSidePane_toggled_cb,
		"menu_View_showStatusBar_toggled_cb":
			menu_View_showStatusBar_toggled_cb,
		"menu_View_showStatusIcon_toggled_cb":
			menu_View_showStatusIcon_toggled_cb,
		"menu_View_showTopicBar_toggled_cb":
			menu_View_showTopicBar_toggled_cb,

		# dialogs menu
		"menu_Dialogs_channelList_activate_cb":
			menu_Dialogs_channelList_activate_cb,
		"menu_Dialogs_dcc_activate_cb" :
			menu_Dialogs_dcc_activate_cb,
		"menu_Dialogs_plugins_activate_cb" :
			menu_Dialogs_plugins_activate_cb,
		"menu_Dialogs_debug_activate_cb" :
			menu_Dialogs_debug_activate_cb,
		"menu_Dialogs_preferences_activate_cb" :
			menu_Dialogs_preferences_activate_cb,

		# help menu
		"menu_Help_Colors_activate_cb":
			menu_Help_Colors_activate_cb,
		"menu_Help_about_activate_cb":
			menu_Help_about_activate_cb,

		# main window signals
		"mainWindow_delete_event_cb":
			mainWindow_delete_event_cb,
		"mainWindow_focus_in_event_cb":
			mainWindow_focus_in_event_cb,
		"mainWindow_size_allocate_cb":
			mainWindow_size_allocate_cb,
		"mainWindow_window_state_event_cb":
			mainWindow_window_state_event_cb,

		# server tree signals
		"serverTree_realize_cb":
			lambda w: w.expand_all(),
		"serverTree_button_press_event_cb" :
			serverTree_button_press_event_cb,
		"serverTree_row_activated_cb":
			serverTree_row_activated_cb,

		# nick list signals
		"nickList_row_activated_cb":
			nickList_row_activated_cb,
		"nickList_button_press_event_cb":
			nickList_button_press_event_cb,

		# output vbox signals
		"outputVBox_size_allocate_cb":
			outputVBox_size_allocate_cb,
	}

	widgets.signal_autoconnect(sigdic)

	# setup manual signals

	bar = widgets.get_widget("inputBar")
	bar.connect("key-press-event", inputBar_key_press_event_cb)
	bar.connect("activate", inputBar_activate_cb)

	shell = widgets.get_widget("outputShell")
	shell.connect("widget-changed", outputShell_widget_changed_cb)
	shell.reset()

	# setup more complex widgets

	setup_serverTree()

	setup_nickList()

	setup_fonts()

	# set input font
	gui.set_font(widgets.get_widget("inputBar"), gui.get_font())

	# set general output font
	gui.set_font(widgets.get_widget("generalOutput"), gui.get_font())

	# setup general output
	buffer = gui.get_new_buffer()
	widgets.get_widget("generalOutput").set_buffer(buffer)

	# setup menu bar stuff
	@types( user = ptypes.FunctionType )
	def apply_visibility(wname, cvalue, user=None):
		button = widgets.get_widget(wname)
		if config.get_bool("tekka", cvalue):
			if user: user()
			button.set_active(True)
		button.toggled()

	apply_visibility("menu_View_showGeneralOutput", "show_general_output")
	apply_visibility("menu_View_showSidePane", "show_side_pane")
	apply_visibility("menu_View_showStatusBar", "show_status_bar")
	apply_visibility("menu_View_showStatusIcon", "show_status_icon",
		lambda: gui.setup_statusIcon())
	apply_visibility("menu_View_showTopicBar", "show_topicbar")

	setup_shortcuts()

	# disable the GUI and wait for commands :-)
	gui.set_useable(False)

	idle_add(setup_paneds)

def tekka_excepthook(extype, exobj, extb):
	""" we got an exception, print it in a dialog box """

	def dialog_response_cb(dialog, rid):
		del tekka_excepthook.dialog
		dialog.destroy()

	class ErrorDialog(gtk.Dialog):
		def __init__(self, message):
			gtk.Dialog.__init__(self,
				parent = widgets.get_widget("mainWindow"),
				title = _("Error occured"),
				buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

			self.set_default_size(400,300)

			self.tv = gtk.TextView()
			self.tv.get_buffer().set_text(message)
			self.sw = gtk.ScrolledWindow()
			self.sw.add(self.tv)
			self.vbox.pack_start(self.sw)
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

	except BaseException, e:
		print >> sys.stderr, "Logging init error: %s" % (e)

def main():
	"""
	Entry point. The program starts here.
	"""

	# load config file, apply defaults
	config.setup()

	# create logfile, setup logging module
	setup_logging()

	# setup callbacks
	com.setup( [maki_connect_callback], [maki_disconnect_callback])

	# build graphical interface
	setupGTK()

	# setup exception handler
	sys.excepthook = tekka_excepthook

	# connect to maki daemon
	connect_maki()

	plugin_control.load_autoloads()

	# initialize threading, needed by dcc dialog
	gtk.gdk.threads_init()

	# start main loop
	gtk.main()

	# after main loop break, write config
	config.write_config_file()

	# At last, close maki if requested
	if config.get_bool("tekka", "close_maki_on_close"):
		com.sushi.shutdown(config.get("chatting", "quit_message", ""))

if __name__ == "__main__":

	main()

"""
	The best thing while coding is that anything seems to be working
	and some piece of code silently drops your data to /dev/null. :]
"""
