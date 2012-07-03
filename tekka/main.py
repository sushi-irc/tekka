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
import dbus
import webbrowser
import locale
import types as ptypes
import logging

import gettext
from gettext import gettext as _

import gui
import gui.tabs

# local modules
from . import config
from . import com
from . import signals
from . import commands
from . import plugins

from .typecheck import types


from .helper import markup

from .menus import *

import gui.builder
import gui.shortcuts



class Tekka (object):

	class PartContainer(dict):
		def __setattr__(self, name, value):
			self[name] = value

		def __getattr__(self, name):
			return self[name]

	from parts import generaloutput
	from parts import inputbar
	from parts import nicklist
	from parts import outputshell
	from parts import tabtree
	from parts import window

	parts	= property(lambda s: s._parts)
	widgets	= property(lambda s: s._widgets)


	def __init__(self):
		self._parts = self.PartContainer()

		from gui import _builder
		self._widgets = _builder.widgets


	def setup(self):
		self._parts.generalOutput = self.generaloutput.setup(self)
		self._parts.tabTree = self.tabtree.setup(self)
		self._parts.inputBar = self.inputbar.setup(self)
		#self._parts.topicBar = self.setup_topic_bar(self)
		#self._parts.toolBar = self.setup_tool_bar(self)
		self._parts.nickList = self.nicklist.setup(self)
		self._parts.outputShell = self.outputshell.setup(self)
		self._parts.window = self.window.setup(self)

		gui.shortcuts.setup_shortcuts()

		com.sushi.g_connect("maki-connected",
			lambda *x: self.set_useable(True))

		com.sushi.g_connect("maki-disconnected",
			lambda *x: self.set_useable(False))

		com.sushi.g_connect("sushi-error",
			self.sushi_error_cb)


	def test(self):
		"a rough functionality test, passed down to the parts of tekka."
		assert self.parts.tabTree != None
		assert self.parts.inputBar != None
		assert self.parts.nickList != None
		assert self.parts.outputShell != None
		assert self.parts.window != None

		assert self.parts.tabTree.test()
		assert self.parts.inputBar.test()
		assert self.parts.nickList.test()
		assert self.parts.outputShell.test()

		return True


	def set_useable(self, flag):
		gui.mgmt.set_useable(flag)


	def show_inline_dialog(self, dialog):
		gui.mgmt.show_inline_dialog(d)


	def show_dialog(self, name):
		pass



	def sushi_error_cb(self, sushi, title, message):
		""" Error in sushi interface occured. """

		def response_cb(d, i):
			gui.status.unset(title)
			d.destroy()

		from .lib.inline_dialog import InlineMessageDialog

		d = InlineMessageDialog(title, message)
		d.connect("response", response_cb)

		self.show_inline_dialog(d)

		gui.status.set_visible(title, title)



def notificationWidget_remove_cb(area, widget):
	""" restore the focus if a inline dialog is closed """
	gui.widgets.get_object("input_entry").grab_focus()









""" Shortcut callbacks """

def changeTopic_shortcut(inputBar, shortcut):
	""" The user wants to change the topic for the current tab.
	"""
	channel = gui.tabs.get_current_tab()
	if not channel or not channel.is_channel():
		return

	menu = servertree_menu.ServerTreeMenu()
	menu.get_menu(channel)
	menu.widgets.get_object("setTopicItem").activate()



""" Fixes """

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
		# TODO: report error
		pass


def setup_topic_label():
	""" tooltip style box arround topic label """

	def expose_event_cb(box, event):
		a = box.get_allocation()

		box.style.paint_flat_box(
			box.window,
			gtk.STATE_NORMAL,
			gtk.SHADOW_ETCHED_IN,
			None,
			box,
			"tooltip",
			a.x,
			a.y,
			a.width,
			a.height - 1
		)
		return False
	gui.widgets.get_object("topic_label").connect(
		"expose-event", expose_event_cb)



def setup_locale():
	try:
		locale.setlocale(locale.LC_ALL, '')
		locale.bindtextdomain("tekka", config.get("tekka","locale_dir"))
		locale.textdomain("tekka")
	except:
		# TODO: What is ignored here?
		pass

	# Fire gettext up with our locale directory
	gettext.bindtextdomain("tekka", config.get("tekka","locale_dir"))
	gettext.textdomain("tekka")


def setupGTK(tekka):
	""" Set locale, load UI file, connect signals, setup widgets. """

	# Fix about dialog URLs
	def about_dialog_url_hook (dialog, link, data):
		if gtk.gtk_version >= (2, 16, 0): return
		webbrowser.open(link)
	gtk.about_dialog_set_url_hook(about_dialog_url_hook, None)

	setup_locale()

	mmc = gui.widgets.get_object("main_menu_context")

	# tell the searchbar where it can get it's input
	gui.widgets.get_object("output_searchbar").textview_callback =\
		lambda: gui.widgets.get_object("output")


	# connect main window signals:
	sigdic = {
		# Notification VBox
		"notification_vbox_remove":
			notificationWidget_remove_cb,

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

	for part in tekka.parts:
		sigdic.update(tekka.parts[part].widget_signals())

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

	# setup more complex widgets
	setup_topic_label()

	# apply visibility to widgets from config
	mmc.view.apply_visibility_settings()

	gui.mgmt.visibility.apply_visibility_from_config()

	setup_fonts()

	gui.shortcuts.add_handlers({
		"change_topic": changeTopic_shortcut,
		"show_sidepane": lambda w,s: w.set_active(not w.get_active()),
	})


	gui.mgmt.visibility.show_welcome_screen(True)

	# disable the GUI and wait for commands :-)
	gui.mgmt.set_useable(False)

	gobject.idle_add(setup_paneds)


def tekka_excepthook(extype, exobj, extb):
	""" we got an exception, print it in a dialog box and,
		if possible, to the standard output.
	"""

	message = "%s\n%s: %s\n" % (
		"".join(traceback.format_tb(extb)),
		extype.__name__,
		str(exobj))

	try:
		print >> sys.stderr, message
	except:
		pass

	self = tekka_excepthook

	def dialog_response_cb(dialog, rid):
		del self.dialog
		dialog.destroy()

	if not hasattr(self, "dialog"):
		from .lib.error_dialog import ErrorDialog

		self.dialog = ErrorDialog(message)
		self.dialog.connect("response", dialog_response_cb)
		self.dialog.show_all()
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

		logging.basicConfig(
			filename = logfile,
			level = logging.DEBUG,
			filemode="w"
		)

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
	signals.setup()


	# parse ui file for main window
	uifiles = config.get("uifiles", default={})
	gui.builder.load_main_window(uifiles["mainwindow"])

	tekka = Tekka()

	tekka.setup()

	# build graphical interface
	setupGTK(tekka)

	tekka.test()

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

