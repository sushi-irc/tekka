# coding:utf-8
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
import gobject
import pango
import gettext
from gettext import gettext as _
from threading import Timer

from ... import config

from ..builder import build_status_icon, error_dialog
from .._builder import widgets

from ...helper import color
from ...helper import code
from ...typecheck import types

from ...lib.inline_dialog import InlineMessageDialog

from . import visibility

def get_font():

	if not config.get_bool("tekka", "use_default_font"):
		return config.get("tekka", "font")

	try:
		import gconf

		client = gconf.client_get_default()

		font = client.get_string(
			"/desktop/gnome/interface/monospace_font_name")

		return font

	except:
		return config.get("tekka", "font")


def apply_new_font():
	""" iterate over all widgets which use fonts and change them """

	font = get_font()

	for row in widgets.get_object("tabs_view").get_model():
		for child in row.iterchildren():
			set_font(child[0].window.textview, font)
		set_font(row[0].window.textview, font)

	set_font(widgets.get_object("output"), font)
	set_font(widgets.get_object("input_entry"), font)
	set_font(widgets.get_object("general_output"), font)


@types(switch=bool)
def set_useable(switch):
	"""
		Dis- or enable the widgets
		which emit or receive signals
		to/from maki.
	"""
	global gui_is_useable

	widgetList = [
		widgets.get_object("input_entry"),
		widgets.get_object("tabs_view"),
		widgets.get_object("nicks_view"),
		widgets.get_object("output_shell"),
		widgets.get_object("output"),
		widgets.get_object("general_output_window")
	]

	for widget in widgetList:
		widget.set_sensitive(switch)

	if switch: widgets.get_object("input_entry").grab_focus()

	gui_is_useable = switch


def has_focus():
	""" return wether the mainwindow has focus or not """

	win = widgets.get_object("main_window")

	return win.has_toplevel_focus()


@types(switch=bool)
def set_urgent(switch):
	""" Sets or unsets the urgent status to the main window.
		If the status icon is enabled it will be set flashing.
	"""
	win = widgets.get_object("main_window")

	if has_focus():
		# don't urgent if we have already the focus
		return

	win.set_urgency_hint(switch)

	statusIcon = widgets.get_object("status_icon")

	if statusIcon:
		statusIcon.set_blinking(switch)


@types(title=basestring)
def set_window_title(title):
	""" Sets the window title to the main window. """
	widgets.get_object("main_window").set_title(title)


@types(nick=basestring)
def set_nick(nick):
	""" Sets nick as label text of nick_label. """
	widgets.get_object("nick_label").set_text(nick)


@types(normal=int, ops=int)
def set_user_count(normal, ops):
	""" sets the amount of users in the current channel. """

	m_users = gettext.ngettext(
		"%d User", "%d Users", normal) % (normal)
	m_ops = gettext.ngettext(
		"%d Operator", "%d Operators", ops) % (ops)

	widgets.get_object("nick_stats_label").set_text(
		"%(users)s – %(ops)s" % {
			"users": m_users, "ops": m_ops })


def set_font(textView, font):
	"""	Sets the font of the textView to
		the font identified by fontFamily
	"""
	fd = pango.FontDescription(font)

	if not fd:
		logging.error("set_font: Font _not_ modified (previous error)")

	else:
		textView.modify_font(fd)


@types(string=basestring)
def set_topic(string):
	""" Sets the given string as text in
		the topic bar.
	"""
	tb = widgets.get_object("topic_label")
	tb.set_markup(string)
	tb.set_tooltip_markup(string)


def clear_all_outputs():

	from . import tabs

	def clear(buf):
		if buf: buf.set_text("")

	current_tab = tabs.get_current_tab()

	if current_tab:
		output = current_tab.window.textview

		buf = output.get_buffer()

		clear(buf)

	buf = widgets.get_object("general_output").get_buffer()

	clear(buf)


@types(string=basestring, html=bool)
def myPrint(string, html=False):
	"""
		prints the string `string` in the current output
		buffer. If html is true the string would be inserted via
		the insert_html-method falling back to normal insert
		if it's not possible to insert via insert_html.
	"""
	textview = widgets.get_object("output")
	output = textview.get_buffer()

	if not output:
		logging.error("myPrint: No output buffer.")
		return

	if not html:

		if output.get_char_count() > 0:

			string = "\n" + string

		output.insert(output.get_end_iter(), string)

	else:

		try:

			output.insert_html(output.get_end_iter(), string)

		except AttributeError:

			logging.info("myPrint: No HTML buffer, printing normal.")
			output.insert(output.get_end_iter(), "\n"+string)

	textview.scroll_to_bottom()


def show_error_dialog(title = "", message = ""):
	""" create a dialog with error_dialog() and show  it up.
		The dialog closes on every action.
	"""
	d = error_dialog(title, message)

	d.connect("response", lambda d,i: d.destroy())
	d.show()

	return d


def show_maki_connection_error(title, message):
	d = InlineMessageDialog(
		_("tekka could not connect to maki."),
		_("Please check whether maki is running."))

	d.connect("response", lambda d,id: d.destroy())

	show_inline_dialog(d)


def show_inline_message(title, message, dtype="info"):
	""" title, the title of the dialog
		message, the message
		dtype, the type. Values can be "error","info" or "warning"
	"""
	if dtype == "error":
		icon = gtk.STOCK_DIALOG_ERROR
	elif dtype == "info":
		icon = gtk.STOCK_DIALOG_INFO
	elif dtype == "warning":
		icon = gtk.STOCK_DIALOG_WARNING

	d = InlineMessageDialog(title, message, icon=icon)
	d.connect("response", lambda d,id: d.destroy())

	show_inline_dialog(d)

	return d


def show_inline_dialog(dialog):
	""" show an InlineDialog in the notification_vbox"""

	# Purpose: auto removing messages (depends on config)
	self = code.init_function_attrs(
										show_inline_dialog,
										timeouts = [])

	area = widgets.get_object("notification_vbox")

	if dialog:

		area.set_no_show_all(False)
		area.add(dialog)
		area.show_all()
		area.set_no_show_all(True)

		if config.get_bool("tekka", "idialog_timeout"):

			def dialog_timeout_cb():
				area.remove(dialog)
				self.timeouts.remove(dialog_timeout_cb.timer)

			if isinstance(dialog, InlineMessageDialog):
				# let only messages disappear
				t = Timer(
					int(config.get("tekka", "idialog_timeout_seconds")),
					dialog_timeout_cb)

				dialog_timeout_cb.timer = t
				self.timeouts.append(t)

				t.start()

	else:
		area.set_property("visible", False)

		for timer in self.timeouts:
			t.cancel()
