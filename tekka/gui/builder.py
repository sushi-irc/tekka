"""
Copyright (c) 2009-2010 Marian Tietz
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
import os

from ._widgets import widgets, WidgetsWrapper
from .. import gui

from .. import config
from ..typecheck import types

from ..lib.htmlbuffer import HTMLBuffer
from ..lib.general_output_buffer import GOHTMLBuffer
from ..lib.status_icon import TekkaStatusIcon
from ..lib.search_toolbar import SearchBar
from ..lib.output_textview import OutputTextView
from ..lib.output_shell import OutputShell
from ..lib.output_window import OutputWindow
from ..helper import URLHandler

from ..helper.shortcuts import addShortcut

def get_new_buffer():
	""" Returns a HTMLBuffer with assigned URL handler. """
	buffer = HTMLBuffer(handler = URLHandler.URLHandler)
	return buffer


def get_new_output_window():
	w = OutputWindow()
	return w


def question_dialog(title = "", message = ""):
	""" create a dialog with a question mark, a title and a message.
		This dialog has two buttons (yes, no) and does not handle
		it's response.
	"""
	d = gtk.MessageDialog(
		   		  type = gtk.MESSAGE_QUESTION,
			   buttons = gtk.BUTTONS_YES_NO,
		message_format = message)

	d.set_title(title)

	return d


def error_dialog(title = "", message = ""):
	""" create a dialog with a exclamation mark, a title and a message.
		This dialog has one close button and does not handle it's
		response.
	"""
	err = gtk.MessageDialog(
				  type = gtk.MESSAGE_ERROR,
			   buttons = gtk.BUTTONS_CLOSE,
		message_format = message)

	err.set_title(title)

	return err


def setup_searchBar():
	searchToolbar = SearchBar(None)
	searchToolbar.set_property("name", "searchBar")

	return searchToolbar


def setup_statusIcon():
	"""
	Sets up the status icon.
	"""
	if config.get_bool("tekka", "rgba"):
		gtk.widget_push_colormap(
			widgets.get_widget("mainWindow") \
			.get_screen() \
			.get_rgb_colormap())

	statusIcon = TekkaStatusIcon()
	widgets.add_gobject(statusIcon, "statusIcon")

	if config.get_bool("tekka", "rgba"):
		gtk.widget_pop_colormap()

	statusIcon.set_visible(True)


@types(gladeFile=basestring, section=basestring)
def load_widgets(gladeFile, section):
	""" load the given section from gladeFile
		into widgets and return them.
		This method is ususally called from main.py
		to initialize the GUI
	"""
	global widgets

	def custom_handler(glade, function_name, widget_name, *x):
		if widget_name == "searchBar":
			return setup_searchBar()

		elif widget_name == "outputShell":
			return OutputShell(OutputWindow())

		elif widget_name == "generalOutput":
			t = OutputTextView()
			t.set_buffer(GOHTMLBuffer(handler = URLHandler.URLHandler))
			t.show()

			return t

		elif widget_name == "inputBar":
			try:
				bar = SpellEntry()
			except NameError:
				bar = gtk.Entry()

			bar.show()

			return bar

		elif widget_name == "notificationWidget":
			align = gtk.VBox()
			align.set_no_show_all(True)
			align.set_property("visible", False)

			return align

		return None

	gtk.glade.set_custom_handler(custom_handler)

	gladeObj = gtk.glade.XML(gladeFile, section)

	widgets.set_glade_widgets(gladeObj)

	def setup_mainmenu_context():
		from ..menus.mainmenu_context import MainMenuContext
		return MainMenuContext(name = "mainMenuBar", widgets = widgets)

	mainmenu = setup_mainmenu_context()
	widgets.add_gobject(mainmenu, "mainMenuContext")

	return gladeObj


class GladeWrapper(object):
	""" wrap glade to gtk.Builder """

	def __init__(self, glade):
		self.glade = glade

	def get_object(self, name):
		return self.glade.get_widget(name)

	def connect_signals(self, obj, user = None):
		if type(obj) == dict:
			self.glade.signal_autoconnect(obj)

	def __getattr__(self, attr):
		if attr in ("get_object","connect_signals"):
			return object.__getattr__(self, attr)
		return getattr(self.glade, attr)


def load_menu(name):
	# menus are gtkbuilder
	path = os.path.join(
					config.get("gladefiles", "menus"),
					name + ".ui")

	builder = gtk.Builder()
	builder.add_from_file(path)

	return builder


def load_dialog(name, custom_handler = None):
	path = os.path.join(
					config.get("gladefiles", "dialogs"),
					name + ".glade")

	if custom_handler:
		gtk.glade.set_custom_handler(custom_handler)

	return GladeWrapper(gtk.glade.XML(path))


