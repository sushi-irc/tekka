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

from .. import memdebug

memdebug.c("before loading builder")

from ._builder import widgets

memdebug.c("after loading builder.widgets")

from .. import config
from ..typecheck import types

from ..lib.htmlbuffer import HTMLBuffer
from ..lib.status_icon import TekkaStatusIcon
from ..lib.output_window import OutputWindow
memdebug.c("before middle of loading builder mods")
from ..lib.output_shell import OutputShell # FIXME produces up to 5MB RSS
memdebug.c("in middle of loading builder mods")
from ..lib.search_toolbar import SearchBar
from ..lib.expanding_list import ExpandingList
from ..lib.contrast_color_table import ContrastColorTable
from ..lib.custom_color_button import CustomColorButton

memdebug.c("after loading modules")

from ..helper import URLHandler


def get_new_buffer():
	""" Returns a HTMLBuffer with assigned URL handler. """
	buffer = HTMLBuffer(handler = URLHandler.URLHandler)
	return buffer


def get_new_output_window():
	w = OutputWindow()
	return w


def information_dialog(title="", message=""):
	""" create a dialog with an info icon, a title and a message.
		This dialog has one button (OK) and does not handle it's response.
	"""
	d = gtk.MessageDialog(
		   		  type = gtk.MESSAGE_INFO,
			   buttons = gtk.BUTTONS_OK,
		message_format = message)

	d.set_title(title)

	return d


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


def build_status_icon():
	"""
	Sets up the status icon.
	"""
	if config.get_bool("tekka", "rgba"):
		gtk.widget_push_colormap(
			widgets.get_object("main_window")\
			.get_screen().get_rgb_colormap()
		)

	statusIcon = TekkaStatusIcon()
	widgets.add_object(statusIcon, "status_icon")

	if config.get_bool("tekka", "rgba"):
		gtk.widget_pop_colormap()

	statusIcon.set_visible(True)


@types(ui_file=basestring, section=basestring)
def load_main_window(ui_file):
	""" Load the widgets from the UI file, do simple setup on them,
		setup the widgets wrapper and return it.
		After succesful setup, load-finished is emitted.
	"""

	widgets.add_from_file(ui_file)

	def setup_mainmenu_context():
		from ..menus.mainmenu_context import MainMenuContext
		return MainMenuContext(name="menubar", widgets=widgets)

	mainmenu = setup_mainmenu_context()
	widgets.add_object(mainmenu, "main_menu_context")

	return widgets


def load_menu(name):
	# menus are gtkbuilder
	path = os.path.join(
					config.get("uifiles", "menus"),
					name + ".ui")

	builder = gtk.Builder()

	builder.add_from_file(path)

	return builder


def load_dialog(name):
	path = os.path.join(
		config.get("uifiles", "dialogs"),
		name + ".ui"
	)

	builder = gtk.Builder()
	builder.add_from_file(path)

	return builder


class Builder(gtk.Builder):

	def load_dialog(self, name):
		path = os.path.join(config.get("uifiles", "dialogs"),
							name + ".ui")
		self.add_from_file(path)

	def load_menu(self, name):
		path = os.path.join(config.get("uifiles", "menus"),
							name + ".ui")
		self.add_from_file(path)

