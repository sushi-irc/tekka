# coding:utf-8

import gtk
import gobject
import pango

from .. import config

from ._widgets import widgets

from ..helper import color
from ..helper import code
from ..typecheck import types

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

	for row in widgets.get_widget("serverTree").get_model():
		for child in row.iterchildren():
			set_font(child[0].window.textview, font)
		set_font(row[0].window.textview, font)

	set_font(widgets.get_widget("output"), font)
	set_font(widgets.get_widget("inputBar"), font)
	set_font(widgets.get_widget("generalOutput"), font)


@types(switch=bool)
def set_useable(switch):
	"""
		Dis- or enable the widgets
		which emit or receive signals
		to/from maki.
	"""
	global gui_is_useable

	widgetList = [
		widgets.get_widget("inputBar"),
		widgets.get_widget("serverTree"),
		widgets.get_widget("nickList"),
		widgets.get_widget("outputShell"),
		widgets.get_widget("output"),
		widgets.get_widget("generalOutput")
	]

	for widget in widgetList:
		widget.set_sensitive(switch)

	if switch: widgets.get_widget("inputBar").grab_focus()

	gui_is_useable = switch


@types(switch=bool)
def switch_status_icon(switch):
	""" enables / disables status icon """

	statusIcon = widgets.get_widget("statusIcon")

	if switch:

		if not statusIcon:
			setup_statusIcon()

		statusIcon.set_visible(True)

	else:

		if not statusIcon:
			return

		statusIcon.set_visible(False)


def has_focus():
	""" return wether the mainwindow has focus or not """

	win = widgets.get_widget("mainWindow")

	return win.has_toplevel_focus()


@types(switch=bool)
def set_urgent(switch):
	""" Sets or unsets the urgent status to the main window.
		If the status icon is enabled it will be set flashing.
	"""
	win = widgets.get_widget("mainWindow")

	if has_focus():
		# don't urgent if we have already the focus
		return

	win.set_urgency_hint(switch)

	statusIcon = widgets.get_widget("statusIcon")

	if statusIcon:
		statusIcon.set_blinking(switch)


@types(title=basestring)
def set_window_title(title):
	""" Sets the window title to the main window. """
	widgets.get_widget("mainWindow").set_title(title)


@types(nick=basestring)
def set_nick(nick):
	""" Sets nick as label text of nickLabel. """
	widgets.get_widget("nickLabel").set_text(nick)


@types(normal=int, ops=int)
def set_user_count(normal, ops):
	""" sets the amount of users in the current channel. """

	m_users = gettext.ngettext(
		"%d User", "%d Users", normal) % (normal)
	m_ops = gettext.ngettext(
		"%d Operator", "%d Operators", ops) % (ops)

	widgets.get_widget("nickList_label").set_text(
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
	tb = widgets.get_widget("topicBar")
	tb.set_markup(string)


def clear_all_outputs():

	from . import tabs

	def clear(buf):
		if buf: buf.set_text("")

	current_tab = tabs.get_current_tab()

	if current_tab:
		output = current_tab.window.textview

		buf = output.get_buffer()

		clear(buf)

	buf = widgets.get_widget("generalOutput").get_buffer()

	clear(buf)


@types(string=basestring, html=bool)
def myPrint(string, html=False):
	"""
		prints the string `string` in the current output
		buffer. If html is true the string would be inserted via
		the insertHTML-method falling back to normal insert
		if it's not possible to insert via insertHTML.
	"""
	textview = widgets.get_widget("output")
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

			output.insertHTML(output.get_end_iter(), string)

		except AttributeError:

			logging.info("myPrint: No HTML buffer, printing normal.")
			output.insert(output.get_end_iter(), "\n"+string)

	textview.scroll_to_bottom()


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


def show_inline_dialog(dialog):
	""" show an InlineDialog in the notificationWidget """

	# Purpose: auto removing messages (depends on config)
	self = code.init_function_attrs(
										show_inline_dialog,
										timeouts = [])

	area = widgets.get_widget("notificationWidget")

	if dialog:

		area.set_no_show_all(False)
		area.add(dialog)
		area.show_all()
		area.set_no_show_all(True)

		if config.get_bool("tekka", "idialog_timeout"):

			def dialog_timeout_cb():
				area.remove(dialog)
				self.timeouts.remove(dialog_timeout_cb.timer)

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
