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

# 40G V 607G zf -> fold ; zc -> close

import pygtk
pygtk.require("2.0")

import sys

try:
	import gtk
except:
	print "Are you sure X is running?"
	sys.exit(1)

import dbus
import time

import gtk.glade
from gobject import TYPE_STRING, TYPE_PYOBJECT, idle_add,GError
import pango

import locale
import gettext
from gettext import gettext as _

from helper.shortcuts import addShortcut, removeShortcut
from helper import tabcompletion

import gui_control
import config
import com

import dialog
import signals
import commands
import menus

# plugin interface
import tekka as plugins

gui = None

# TODO:  if a tab is closed the widgets remain the same.
# TODO:: it would be nice if the tab would be switched
# TODO:: to an active on (for error prevention too).


"""
Glade signals
"""

def menu_tekka_Connect_activate_cb(menuItem):
	"""
		menuBar -> tekka -> connect was clicked,
		show up server dialog and connect to the
		returned server (if any).
	"""
	if not com.getConnected():
		err = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE,
			message_format="There is no connection to maki!")
		err.run()
		err.destroy()
		return

	serverList = dialog.showServerDialog()

	if serverList:
		for server in serverList:
			com.connectServer(server)

def menu_View_showGeneralOutput_toggled_cb(menuItem):
	"""
		Deactivate or enable (hide/show) the general output
		widget.
	"""
	sw = gui.getWidgets().get_widget("scrolledWindow_generalOutput")

	if menuItem.get_active():
		sw.show_all()
		config.set("tekka","show_general_output","True")
	else:
		sw.hide()
		config.set("tekka","show_general_output","False")

def menu_View_showStatusBar_toggled_cb(menuItem):
	"""
		hide or show the status bar.
	"""
	bar = gui.getWidgets().get_widget("statusBar")
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
		gui.setStatusIcon(False)

	else:
		config.set("tekka", "show_status_icon", "True")
		gui.setStatusIcon(True)


def menu_Dialogs_channelList_activate_cb(menuItem):
	"""
		show channel list dialog.
	"""
	if not com.getConnected():
		err = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE,
			message_format="There is no connection to maki!")
		err.run()
		err.destroy()
		return

	sTab,cTab = gui.tabs.getCurrentTabs()
	if not sTab: return
	dialog.showChannelListDialog(sTab.name)

def menu_Dialogs_plugins_activate_cb(menuItem):
	"""
	show plugin load/unload/list dialog.
	"""
	dialog.showPluginsDialog()

def menu_Dialogs_debug_activate_cb(menuItem):
	dialog.showDebugDialog()

def menu_Dialogs_preferences_activate_cb(menuItem):
	dialog.showPreferencesDialog()

def menu_Help_about_activate_cb(menuItem):
	"""
		Show the about dialog!
	"""
	widgets = gtk.glade.XML(config.get("gladefiles","dialogs") + "about.glade")
	d = widgets.get_widget("aboutDialog")
	d.run()
	d.destroy()

def mainWindow_delete_event_cb(mainWindow, event):
	"""
		The user want's to close the main window.
		If the status icon is enabled and the
		"hideOnClose" option is set the window
		will be hidden, otherwise the main looped
		will be stopped.
	"""
	if config.get("tekka", "hide_on_close") and gui.statusIcon and gui.statusIcon.get_visible():
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
	gui.setUrgent(False)
	return False

def mainWindow_size_allocate_cb(mainWindow, alloc):
	"""
		Main window was resized.
		Store the new size in the config.

		Due to resizing the scrollbar dimensions
		of the scrolled window arround the output
		changed. In conclusion the autoscroll is
		disabled because the scrollbar is not
		at bottom anymore. So if the current tab
		has auto scroll = True, scroll to bottom.
	"""
	if not mainWindow.window.get_state() & gtk.gdk.WINDOW_STATE_MAXIMIZED:
		config.set("tekka","window_width",alloc.width)
		config.set("tekka","window_height",alloc.height)

	tab = gui.tabs.getCurrentTab()
	if tab and tab.autoScroll:
		idle_add(lambda: gui.scrollOutput())

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

	tab = gui.tabs.getCurrentTab()

	commands.parseInput(text)

	if tab:
		tab.insertHistory(text)

	inputBar.set_text("")

def inputBar_key_press_event_cb(inputBar, event):
	"""
		Key pressed in inputBar.
		Implements tab and command completion.
	"""
	key =  gtk.gdk.keyval_name(event.keyval)
	tab =  gui.tabs.getCurrentTab()

	text = inputBar.get_text()

	if key == "Up":
		# get next input history item
		if not tab: return

		if tab.historyPosition == -1:
			tab.setCurrentHistory(inputBar.get_text())

		hist = tab.getNextHistory()

		if tab.historyPosition == -1:
			return

		inputBar.set_text(hist)
		inputBar.set_position(len(hist))

	elif key == "Down":
		# get previous input history item
		if not tab: return

		if tab.historyPosition == -1:
			return

		hist = tab.getPrevHistory()

		if tab.historyPosition == -1:
			hist = tab.getCurrentHistory()

		inputBar.set_text(hist)
		inputBar.set_position(len(hist))


	elif key == "Tab":
		# tab completion comes here.

		tabcompletion.complete(tab, text)
		return True

	if key != "Tab":
		tabcompletion.stopIteration()


def topicBar_activate_cb(topicBar):
	"""
		Receives if the topicBar gtk.Entry
		widget was activated (Enter was hit).
		Set the topic of the current channel
		to the text in the topicBar
	"""
	sTab,cTab = gui.tabs.getCurrentTabs()

	if not cTab:
		# no channel, no topic
		return

	text = topicBar.get_text()

	com.setTopic(sTab.name, cTab.name, text)

	widgets.get_widget("inputBar").grab_focus()

def serverTree_misc_menu_reset_activate_cb(menuItem):
	"""
	reset the markup of all tabs
	"""
	for tab in gui.tabs.getAllTabs():
		tab.setNewMessage(None)
		gui.updateServerTreeMarkup(tab.path)

def serverTree_button_press_event_cb(serverTree, event):
	"""
		A row in the server tree was activated.
		The main function of this method is to
		cache the current activated row as path.
	"""

	try:
		path = serverTree.get_path_at_pos(int(event.x),int(event.y))[0]
		tab = serverTree.get_model()[path][2]
	except Exception,e:
		print e
		tab = None

	if event.button == 1:
		# activate the tab

		if not tab:
			return False

		gui.tabs.switchToPath(path)

	elif event.button == 3:
		# popup tab menu

		if tab:

			menu = menus.getServerTreeMenu(tab)

			if not menu:
				print "error in creating server tree tab menu."
				return False

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


def nickList_row_activated_cb(nickList, path, column):
	"""
		The user activated a nick in the list.

		If there's a nick in the row a query
		for the nick on the current server will be opened.
	"""
	serverTab,channelTab = gui.tabs.getCurrentTabs()

	try:
		name = nickList.get_model()[path][nickList.get_model().COLUMN_NICK]
	except TypeError:
		# nickList has no model
		return
	except IndexError:
		# path is invalid
		return

	if gui.tabs.searchTab(serverTab.name, name):
		# already a query open
		return

	query = gui.tabs.createQuery(serverTab.name, name)
	query.connected = True

	gui.tabs.addTab(serverTab.name, query)
	gui.updateServerTreeShortcuts()

	output = query.buffer

	for line in com.fetchLog(serverTab.name, name, dbus.UInt64(config.get("chatting", "last_log_lines", "10"))):
		output.insertHTML(output.get_end_iter(), "<font foreground='#DDDDDD'>%s</font>" % gui.escape(line))

	gui.tabs.switchToPath(query.path)

def nickList_menu_leftSide_toggled_cb(menuItem):
	"""
	move the nick list widget to the left hbox if menuItem
	is toggled or move it to the vpaned
	"""

	if menuItem.get_active():
		gui.moveNickList(left=True)

	else:
		gui.moveNickList(left=False)


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

			nick = nick[nickList.get_model().COLUMN_NICK]

			menu = menus.getNickListMenu(nick)

			if not menu:
				return False

			# finaly popup the menu
			menu.popup(None, None, None, event.button, event.time)

		else:
			# display nick list menu

			menu = gtk.Menu()
			leftSide = gtk.CheckMenuItem(label="Show on _left side")
			menu.append(leftSide)
			leftSide.show()

			if config.get_bool("tekka", "nick_list_left"):
				leftSide.set_active(True)

			leftSide.connect("toggled", nickList_menu_leftSide_toggled_cb)

			menu.popup(None, None, None, event.button, event.time)

	return False


def scrolledWindow_output_vscrollbar_valueChanged_cb(range):
	"""
		The vertical scrollbar of the surrounding scrolled window
		of the output text view was moved.
		Disable the autoscroll if the scroll bar is not at the
		bottom.
		Also the method sets the current scroll position
		to the buffer in the tab.
	"""
	tab = gui.tabs.getCurrentTab()

	if not tab:
		# no tab to (dis|en)able auto scrolling
		return

	adjust = range.get_property("adjustment")

	if (adjust.upper - adjust.page_size) == range.get_value():
		# bottom reached
		tab.autoScroll = True
		#print "autoscroll for %s = True" % (tab.name)
	else:
		tab.autoScroll = False
		#print "autoScroll for %s = False" % (tab.name)

	# cache the last position to set after switch
	tab.buffer.scrollPosition=range.get_value()

	#print "scrollPosition is now %d" % (tab.buffer.scrollPosition)

def statusIcon_activate_cb(statusIcon):
	"""
		Click on status icon
	"""
	mw = widgets.get_widget("mainWindow")
	if mw.get_property("visible"):
		mw.hide()
	else:
		mw.show()

def statusIcon_popup_menu_cb(statusIcon, button, time):
	"""
	User wants to see the menu
	"""
	m = gtk.Menu()

	hide = gtk.MenuItem(label="Show/Hide main window")
	m.append(hide)
	hide.connect("activate", statusIcon_menu_hide_activate_cb)

	sep = gtk.SeparatorMenuItem()
	m.append(sep)

	quit = gtk.ImageMenuItem(stock_id=gtk.STOCK_QUIT)
	m.append(quit)
	quit.connect("activate", lambda *x: gtk.main_quit())

	m.show_all()

	m.popup(None, None, gtk.status_icon_position_menu, button, time, statusIcon)

def statusIcon_menu_hide_activate_cb(menuItem):
	"""
	Show main window if hidden, else hide.
	"""
	mw = widgets.get_widget("mainWindow")
	if mw.get_property("visible"):
		mw.hide()
	else:
		mw.show()


"""
	Shortcut callbacks
"""

def inputBar_shortcut_ctrl_u(inputBar, shortcut):
	"""
		Ctrl + U was hit, clear the inputBar
	"""
	widgets.get_widget("inputBar").set_text("")

def output_shortcut_ctrl_l(output, shortcut):
	"""
		Ctrl+L was hit, clear the output.
	"""
	buf = output.get_buffer()
	if buf: buf.set_text("")
	buf = widgets.get_widget("generalOutput").get_buffer()
	if buf: buf.set_text("")

def serverTree_shortcut_ctrl_Page_Up(serverTree, shortcut):
	"""
		Ctrl+Page_Up was hit, go up in server tree
	"""
	tabs = gui.tabs.getAllTabs()
	tab = gui.tabs.getCurrentTab()

	try:
		i = tabs.index(tab)
	except ValueError:
		return

	try:
		gui.tabs.switchToPath(tabs[i-1].path)
	except IndexError:
		return

def serverTree_shortcut_ctrl_Page_Down(serverTree, shortcut):
	"""
		Ctrl+Page_Down was hit, go down in server tree
	"""
	tabs = gui.tabs.getAllTabs()
	tab = gui.tabs.getCurrentTab()

	try:
		i = tabs.index(tab)
	except ValueError:
		return

	try:
		i = i+1
		if (i) == len(tabs):
			i = 0
		gui.tabs.switchToPath(tabs[i].path)
	except IndexError:
		return

def serverTree_shortcut_ctrl_w(serverTree, shortcut):
	"""
		Ctrl+W was hit, close the current tab (if any)
	"""
	tab = gui.tabs.getCurrentTab()
	if not tab:
		return

	if tab.is_channel():
		message = _(u"Do you really want to close channel “%(name)s”?")
	elif tab.is_query():
		message = _(u"Do you really want to close query “%(name)s”?")
	elif tab.is_server():
		message = _(u"Do you really want to close server “%(name)s”?")

	dialog = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO,
		message_format=message % { "name": tab.name })
	res = dialog.run()
	dialog.destroy()

	if res != gtk.RESPONSE_YES:
		return

	# FIXME:  if you close a tab no part message will be shown up
	# FIXME:: because the tab which contains the output buffer is
	# FIXME:: removed before the signal execution.
	if tab.is_channel():
		com.part(tab.server,tab.name, config.get("chatting", "part_message", ""))

	elif tab.is_server():
		com.quitServer(tab.name, config.get("chatting", "quit_message", ""))

	gui.tabs.removeTab(tab)
	gui.updateServerTreeShortcuts()

	# TODO:  automagically switch to the next active tab
	# TODO:: around the old tab.

def output_shortcut_Page_Up(output, shortcut):
	"""
		Page_Up was hit, scroll up in output
	"""
	vadj = widgets.get_widget("scrolledWindow_output").get_vadjustment()

	if vadj.get_value() == 0.0:
		return # at top already

	n = vadj.get_value()-vadj.page_size
	if n < 0: n = 0
	idle_add(vadj.set_value,n)

def output_shortcut_Page_Down(output, shortcut):
	"""
		Page_Down was hit, scroll down in output
	"""
	vadj = widgets.get_widget("scrolledWindow_output").get_vadjustment()

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
	buffer = widgets.get_widget("output").get_buffer()
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
		topicBar.copy_clipboard()


def nickListRenderNicks(column, renderer, model, iter):
	""" Renderer func for column "Nicks" in NickList """

	if not com.getConnected():
		# do not render if no connection exists
		return

	# highlight own nick
	serverTab = gui.tabs.getCurrentTabs()[0]

	if not serverTab:
		return

	nick = model.get(iter, 1)

	if not nick:
		return

	nick = nick[0]

	# highlight own nick
	if com.getOwnNick(serverTab.name) == nick:
		renderer.set_property("weight", pango.WEIGHT_BOLD)
	else:
		renderer.set_property("weight", pango.WEIGHT_NORMAL)

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
				gtk.gdk.pixbuf_new_from_file_at_size(
					iconPath,
					64,
					64),
				gtk.gdk.pixbuf_new_from_file(iconPath))

		except GError:
			# file not found
			pass

	width = config.get("tekka","window_width")
	height = config.get("tekka","window_height")

	if width and height:
		win.resize(int(width),int(height))

	if config.get_bool("tekka","window_maximized"):
		win.maximize()

	win.show_all()

def setup_serverTree():
	"""
		Sets up a treemodel with three columns.
		The first column is a pango markup language
		description, the second is the identifying
		channel or server name and the third is a
		tab object.
	"""
	tm = gtk.TreeStore(TYPE_STRING, TYPE_STRING, TYPE_PYOBJECT)

	"""
	# Sorting
	def cmpl(m,i1,i2):
		" compare columns lower case "
		a = m.get_value(i1, 1)
		b = m.get_value(i2, 1)
		c,d=None,None
		if a: c=a.lower()
		if b: d=b.lower()
		return cmp(c,d)

	tm.set_sort_func(1,
		lambda m,i1,i2,*x: cmpl(m,i1,i2))
	tm.set_sort_column_id(1, gtk.SORT_ASCENDING)
	"""

	# further stuff (set model to treeview, add columns)

	widget = widgets.get_widget("serverTree")

	widget.set_model(tm)

	renderer = gtk.CellRendererText()
	column = gtk.TreeViewColumn("Server", renderer, markup=0)

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
	column.set_cell_data_func(renderer, nickListRenderNicks)
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
	"""
	gui.accelGroup = gtk.AccelGroup()
	widgets.get_widget("mainWindow").add_accel_group(gui.accelGroup)

	addShortcut(gui.accelGroup, widgets.get_widget("inputBar"), "<ctrl>u",
		inputBar_shortcut_ctrl_u)
	addShortcut(gui.accelGroup, widgets.get_widget("output"), "<ctrl>l",
		output_shortcut_ctrl_l)

	addShortcut(gui.accelGroup, widgets.get_widget("serverTree"),
		"<ctrl>Page_Up", serverTree_shortcut_ctrl_Page_Up)
	addShortcut(gui.accelGroup, widgets.get_widget("serverTree"),
		"<ctrl>Page_Down", serverTree_shortcut_ctrl_Page_Down)
	addShortcut(gui.accelGroup, widgets.get_widget("serverTree"),
		"<ctrl>w", serverTree_shortcut_ctrl_w)

	addShortcut(gui.accelGroup, widgets.get_widget("output"),
		"Page_Up", output_shortcut_Page_Up)
	addShortcut(gui.accelGroup, widgets.get_widget("output"),
		"Page_Down", output_shortcut_Page_Down)

	addShortcut(gui.accelGroup, widgets.get_widget("inputBar"),
		"<ctrl>c", inputBar_shortcut_ctrl_c)

def connectMaki():
	"""
		Tries to connect to maki over DBus.
		If succesful, the GUI is enabled (gui.setUseable(True))
		and signals, dialogs, menus as well as the commands module
		were set up.
	"""
	gui.setUseable(False)

	if com.connect():
		# init modules

		signals.setup()
		commands.setup()
		dialog.setup()
		menus.setup()

		gui.setUseable(True)

		plugins.setup()

	# TODO: print error message


def setupGTK():
	"""
		Set locale, parse glade files.
		Connects gobject widget signals to code.
		Setup widgets.
	"""
	global commands, signals
	global gui, widgets

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
	widgets = gui_control.load_widgets(
		gladefiles["mainwindow"], "mainWindow")

	setup_mainWindow()

	# connect main window signals:
	sigdic = {
		# tekka menu
		"menu_tekka_Connect_activate_cb":
			menu_tekka_Connect_activate_cb,
		"menu_tekka_Quit_activate_cb":
			gtk.main_quit,

		# maki menu
		"menu_maki_Connect_activate_cb":
			lambda w: connectMaki(),
		"menu_maki_Shutdown_activate_cb":
			lambda w: com.shutdown(
				config.get(
					"chatting",
					"quit_message",
					"")),

		# view menu
		"menu_View_showGeneralOutput_toggled_cb":
			menu_View_showGeneralOutput_toggled_cb,
		"menu_View_showStatusBar_toggled_cb":
			menu_View_showStatusBar_toggled_cb,
		"menu_View_showStatusIcon_toggled_cb":
			menu_View_showStatusIcon_toggled_cb,

		# dialogs menu
		"menu_Dialogs_channelList_activate_cb":
			menu_Dialogs_channelList_activate_cb,
		"menu_Dialogs_plugins_activate_cb" :
			menu_Dialogs_plugins_activate_cb,
		"menu_Dialogs_debug_activate_cb" :
			menu_Dialogs_debug_activate_cb,
		"menu_Dialogs_preferences_activate_cb" :
			menu_Dialogs_preferences_activate_cb,

		# help menu
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

		# input signals
		"inputBar_activate_cb":
			inputBar_activate_cb,
		"inputBar_key_press_event_cb":
			inputBar_key_press_event_cb,
		"topicBar_activate_cb":
			topicBar_activate_cb,

		# server tree signals
		"serverTree_realize_cb":
			lambda w: w.expand_all(),
		"serverTree_button_press_event_cb" :
			serverTree_button_press_event_cb,

		# nick list signals
		"nickList_row_activated_cb":
			nickList_row_activated_cb,
		"nickList_button_press_event_cb":
			nickList_button_press_event_cb,
	}

	widgets.signal_autoconnect(sigdic)

	vbar = widgets.get_widget(
		"scrolledWindow_output").get_vscrollbar()
	vbar.connect(
		"value-changed",
		scrolledWindow_output_vscrollbar_valueChanged_cb)

	setup_serverTree()
	setup_nickList()

	# create instance of wrapper class for easy
	# accessing of frequently used widget magic
	gui = gui_control.GUIWrapper()

	if not gui:
		raise Exception("GUIWrapper not successfully initialized!")

	# set output font
	gui.setFont(widgets.get_widget("output"),
		config.get("tekka","output_font"))

	# set general output font
	gui.setFont(widgets.get_widget("generalOutput"),
		config.get("tekka","general_output_font"))

	# set input font
	gui.setFont(widgets.get_widget("inputBar"),
		config.get("tekka","input_font"))

	# setup general output
	buffer = gui.tabs.getNewBuffer()
	widgets.get_widget("generalOutput").set_buffer(buffer)

	# setup menu bar stuff
	btn = widgets.get_widget("menu_View_showGeneralOutput")

	if config.get_bool("tekka","show_general_output"):
		btn.set_active(True)
	btn.toggled()

	btn = widgets.get_widget("menu_View_showStatusBar")

	if config.get_bool("tekka","show_status_bar"):
		btn.set_active(True)
	btn.toggled()

	btn = widgets.get_widget("menu_View_showStatusIcon")

	if config.get_bool("tekka","show_status_icon"):
		gui.setup_statusIcon()
		btn.set_active(True)
	btn.toggled()

	if config.get_bool("tekka", "nick_list_left"):
		gui.moveNickList(left=True)

	setup_shortcuts()

	# disable the GUI and wait for commands :-)
	gui.setUseable(False)

def main():
	"""
	Entry point. The program starts here.
	"""

	# load config file, apply defaults
	config.setup()

	# build graphical interface
	setupGTK()

	# connect to maki daemon
	connectMaki()

	# start main loop
	gtk.main()

	# after main loop break, write config
	config.write_config_file()

	# At last, close maki if requested
	if config.get_bool("tekka", "close_maki_on_close"):
		com.shutdown(config.get("chatting", "quit_message", ""))

if __name__ == "__main__":

	main()

"""
	The best thing while coding is that anything seems to be working
	and some piece of code silently drops your data to /dev/null. :]
"""
