# coding: UTF-8
"""
Copyright (c) 2009 Marian Tietz
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

""" The "core": the gui wrapper class. """

# global modules
import os
import re
import gtk
import gtk.glade
import time
import pango
import gettext
import gobject
import logging
from math import ceil

from threading import Timer
from gobject import idle_add
from dbus import String, UInt64

import lib.contrast
import helper.color
import helper.escape

try:
	from sexy import SpellEntry
except ImportError:
	logging.info("Spell checking disabled.")

# local modules
import config
import com
from typecheck import types

from helper.shortcuts import addShortcut, removeShortcut
from helper import URLHandler
import helper.code

import lib.tab_control
from lib.search_toolbar import SearchBar
from lib.input_history import InputHistory
from lib.output_textview import OutputTextView
from lib.htmlbuffer import HTMLBuffer
from lib.status_icon import TekkaStatusIcon
from lib.general_output_buffer import GOHTMLBuffer
from lib.status_manager import StatusManager

"""
What about a concept like retrieving a object
from glade/gtkbuilder and build a proxy object around
it so the signals in main.py can be handled in the proxy
and the proxy object can replace the origin object
in the glade object store.

Code example:
obj = gui.widgets.get_widget("serverTree")

class ServerTree(object):
	def __init__(self, w):
		self.widget = w

		w.connect("serverTree_realize_cb", self.realize_cb)

	def realize_cb(self, *x):
		pass

	def __getattr__(self, attr):
		return getattr(self.w, attr)

gui.widgets.set_widget("serverTree", ServerTree(obj))

That would clean up the namespace massively.
A possible contra would be that the signal autoconnect won't
work anymore.
A pro would be, that one could easily define new context objects,
like "ChatContext" which is a meta object holding input entry,
output window and general output. This context can handle signals
which are needed by all that components.
"""

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

class BuilderWrapper(object):

	def __init__(self):
		pass

	def set_glade_custom_handler(self, handler):
		if handler:
			gtk.glade.set_custom_handler(handler)

	def load_menu(self, name):
		# menus are gtkbuilder
		path = os.path.join(config.get("gladefiles", "menus"), name + ".ui")

		builder = gtk.Builder()
		builder.add_from_file(path)

		return builder

	def load_dialog(self, name, custom_handler = None):
		path = os.path.join(config.get("gladefiles", "dialogs"), name + ".glade")

		self.set_glade_custom_handler(custom_handler)

		return GladeWrapper(gtk.glade.XML(path))

class WidgetsWrapper(object):

	""" Wrap a glade XML widget object
		so one can manually add own widgets
		and access them as if they lie in
		the XML object.

		Every unknown method call will be
		forwarded to the glade object.
	"""

	def __init__(self, glade_widgets):
		self.glade_widgets = glade_widgets
		self.own_widgets = {}

	def _add_local(self, obj, name):
		""" add an object to the local dict. Checks
			if a object with the same name does already
			exist and raises a ValueError if that's the
			case.
		"""
		if not self.glade_widgets.get_widget(name):
			self.own_widgets[name] = obj
		else:
			raise ValueError, "Widgets '%s' already in widgets dict." % (
				name)

	@types (widget = gobject.GObject)
	def add_gobject(self, obj, name):
		self._add_local(obj, name)

	@types (widget = gtk.Widget)
	def add_widget(self, widget):
		""" Add a widget to the dictionary.

			Throws ValueError if the widget's name
			exists in the glade object.
		"""
		name = widget.get_property("name")

		try:
			self._add_local(widget, name)
		except ValueError:
			raise
		else:
			# XXX: does that make sense?
			widget.connect("destroy", lambda x: self.remove_widget(x))

	@types (widget = (basestring, gtk.Widget))
	def remove_widget(self, widget):
		""" Remove our widget by name or by object """
		def remove_by_name(name):
			if self.own_widgets.has_key(name):
				del self.own_widgets[name]

		if isinstance(widget, basestring):
			remove_by_name(widget)
		else:
			remove_by_name(widget.get_property("name"))

	@types (name = basestring)
	def get_widget(self, name):
		""" Return our own widget if found, else look in glade.
			Returns None if no widget is found.
		"""
		try:
			return self.own_widgets[name]
		except KeyError:
			pass

		w = self.glade_widgets.get_widget(name)
		if w:
			return w
		return None

	def __getattr__(self, attr):
		try:
			return object.__getattr__(self, attr)
		except AttributeError:
			return getattr(self.glade_widgets, attr)

class OutputWindow(gtk.ScrolledWindow):

	""" A gtk.ScrolledWindow with a TextView inside of it.

		This widget watches for autoscrolling and
		adjusts the scrollbar on size-allocations.

		This widget is supposed to be hold by a OutputShell.
	"""

	def __init__(self):
		gtk.ScrolledWindow.__init__(self)

		self.set_properties( hscrollbar_policy=gtk.POLICY_NEVER,
			vscrollbar_policy = gtk.POLICY_AUTOMATIC,
			shadow_type=gtk.SHADOW_ETCHED_IN )

		self.textview = OutputTextView()
		self.auto_scroll = True

		self.add(self.textview)

		self.old_allocation = self.get_allocation()

		# XXX: redundant code, see main.py::setup_mainWindow
		def kill_mod1_scroll_cb(w,e):
			if e.state & gtk.gdk.MOD1_MASK:
				w.emit_stop_by_name("scroll-event")

		self.connect("scroll-event", kill_mod1_scroll_cb)

		def size_allocate_cb(win, alloc):
			adj = win.get_vscrollbar().get_adjustment()

			if alloc.height != self.old_allocation.height:
				if self.auto_scroll:
					def doit():
						self.textview.scroll_to_bottom(no_smooth = True)
						return False
					gobject.idle_add(doit)

			self.old_allocation = alloc

		self.connect("size-allocate", size_allocate_cb)

		def value_changed_cb(sbar):
			def idle_handler_cb():
				adjust = sbar.get_property("adjustment")

				"""
				print "%d - %d (%d) == %d" % (adjust.upper,
					adjust.page_size, (adjust.upper-adjust.page_size),
					sbar.get_value())
				"""

				if (self.auto_scroll
				and self.textview.is_smooth_scrolling()):
					# XXX: instead of setting, ignore this completely.
					self.auto_scroll = True
				elif ceil(adjust.upper - adjust.page_size) == ceil(sbar.get_value()):
					self.auto_scroll = True
				else:
					self.auto_scroll = False
				return False

			gobject.idle_add(idle_handler_cb)

		self.get_vscrollbar().connect("value-changed", value_changed_cb)

class OutputShell(gtk.VBox):

	""" A shell for one OutputWindow with
		methods to display another OutputWindow.
	"""

	@types (widget = OutputWindow)
	def __init__(self, window):
		""" Takes a default window which is shown if reset() is
			called (which is the default).
		"""
		gtk.VBox.__init__(self)

		self.init_window = window
		self.output_window = None

		self.reset()

	@types (new_window = OutputWindow)
	def set(self, new_window):
		""" Set a new OutputWindow which replaces
			the current.

			Emits widget-changed with the old and the
			new widget.
		"""
		old_window = self.output_window

		if old_window:
			self.remove(old_window)

		self.pack_start(new_window)
		self.output_window = new_window

		self.emit("widget-changed", old_window, new_window)

	def reset(self):
		""" Reset to the default window. """
		self.set(self.init_window)

	def get(self):
		""" Return the current OutputWindow """
		return self.output_window

gobject.signal_new(
	"widget-changed", OutputShell,
	gobject.SIGNAL_ACTION, gobject.TYPE_NONE,
	(gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT))

# TODO: replace widgets with a GladeWrapper
widgets = None
builder = BuilderWrapper()
accelGroup = gtk.AccelGroup()
tabs = lib.tab_control.TabControl()
status = StatusManager()

# TODO: get rid of this in favor of widgets as a wrapper
def get_widget(name):
	try:
		return widgets.get_widget(name)
	except AttributeError:
		# unitialized widgets
		return None

def get_new_buffer():
	"""
	Returns a HTMLBuffer with assigned URL handler.
	"""
	buffer = HTMLBuffer(handler = URLHandler.URLHandler)
	return buffer

def get_new_output_window():
	w = OutputWindow()
	return w

def get_font ():
	if not config.get_bool("tekka", "use_default_font"):
		return config.get("tekka", "font")

	try:
		import gconf

		client = gconf.client_get_default()

		font = client.get_string("/desktop/gnome/interface/monospace_font_name")

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

	widgets = WidgetsWrapper(gtk.glade.XML(gladeFile, section))

	def setup_mainmenu_context():
		from menus.mainmenu_context import MainMenuContext
		return MainMenuContext(name = "mainMenuBar", widgets = widgets)

	mainmenu = setup_mainmenu_context()
	widgets.add_gobject(mainmenu, "mainMenuContext")

	return widgets

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
			widgets.get_widget("mainWindow")\
			.get_screen()\
			.get_rgb_colormap())

	statusIcon = TekkaStatusIcon()
	widgets.add_gobject(statusIcon, "statusIcon")

	if config.get_bool("tekka", "rgba"):
		gtk.widget_pop_colormap()

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
	win = widgets.get_widget("mainWindow")

	return win.has_toplevel_focus()

@types(switch=bool)
def set_urgent(switch):
	"""
		Sets or unsets the urgent
		status to the main window.
		If the status icon is enabled
		it will be set flashing (or
		if switch is False the flashing
		will stop)
	"""
	win = widgets.get_widget("mainWindow")

	if has_focus():
		# urgent toplevel windows suck ass
		return

	win.set_urgency_hint(switch)

	statusIcon = widgets.get_widget("statusIcon")
	if statusIcon:
		statusIcon.set_blinking(switch)

@types(title=basestring)
def set_window_title(title):
	"""
		Sets the window title to the main
		window.
	"""
	widgets.get_widget("mainWindow").set_title(title)

@types(nick=basestring)
def set_nick(nick):
	"""
		Sets nick as label text of nickLabel.
	"""
	widgets.get_widget("nickLabel").set_text(nick)

@types(normal=int, ops=int)
def set_user_count(normal, ops):
	"""
	sets the amount of users in the current channel.
	"""
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
	current_tab = tabs.get_current_tab()

	if current_tab:
		output = current_tab.window.textview

		buf = output.get_buffer()
		if buf:
			buf.set_text("")

	buf = widgets.get_widget("generalOutput").get_buffer()
	if buf:
		buf.set_text("")

def updateServerTreeShortcuts():
	"""	Iterates through the TreeModel
		of the server tree and sets 9
		shortcuts to tabs for switching.
	"""
	global accelGroup

	tabList = tabs.get_all_tabs()
	st = widgets.get_widget("serverTree")

	for i in range(1, 10):
		removeShortcut(accelGroup, st, "<alt>%d" % (i))

	c = 1
	for tab in tabList:
		if c == 10:
			break

		if (tab.is_server()
			and not config.get("tekka", "server_shortcuts")):
			continue

		addShortcut(accelGroup, st, "<alt>%d" % (c),
			lambda w, s, p: tabs.switch_to_path(p), tab.path)

		c+=1

def _escape_ml(msg):
	""" escape every invalid character via gobject.markup_escape_text
		from the given string but leave the irc color/bold characters:
		- chr(2)
		- chr(3)
		- chr(31)
	"""

	msg = msg.replace("%","%%") # escape %
	msg = msg.replace(chr(2), "%2")
	msg = msg.replace(chr(31), "%31")
	msg = msg.replace(chr(3), "%3")

	msg = gobject.markup_escape_text(msg)

	l = helper.escape.unescape_split("%2", msg, escape_char="%")
	msg = chr(2).join(l)

	l = helper.escape.unescape_split("%3", msg, escape_char="%")
	msg = chr(3).join(l)

	l = helper.escape.unescape_split("%31", msg, escape_char="%")
	msg = chr(31).join(l)

	return msg.replace("%%","%")

def markup_escape(msg):
	""" escape for pango markup language """
	msg = _escape_ml(msg)

	# don't want bold/underline, can't use it
	msg = msg.replace(chr(2), "")
	msg = msg.replace(chr(31), "")

	msg = helper.color.parse_color_codes_to_tags(msg)

	return msg

def escape(msg):
	"""	Converts special characters in msg and returns
		the new string. This function should only
		be used in combination with HTMLBuffer.
	"""
	msg = _escape_ml(msg)

	msg = msg.replace(chr(2), "<sb/>") # bold-char
	msg = msg.replace(chr(31), "<su/>") # underline-char

	msg = helper.color.parse_color_codes_to_tags(msg)

	return msg

@types (server = basestring, channel = basestring, lines = int,
	tab = (type(None), lib.tab.TekkaTab))
def print_last_log(server, channel, lines=0, tab = None):
	"""	Fetch the given amount of lines of history for
		the channel on the given server and print it to the
		channel's textview.
	"""
	if not tab:
		tab = tabs.search_tab(server, channel)

	if not tab:
		return

	buffer = tab.window.textview.get_buffer()

	if not buffer:
		logging.error("last_log('%s','%s'): no buffer" % (server,channel))
		return

	for line in com.sushi.log(
				server, channel,
				UInt64(lines or config.get(
					"chatting", "last_log_lines", default="0"))):

		line = helper.color.strip_color_codes(line)

		buffer.insertHTML(buffer.get_end_iter(),
			"<font foreground='%s'>%s</font>" % (
				config.get("colors","last_log","#DDDDDD"),
				escape(line)))

def write_to_general_output(msgtype, timestring, server, channel, message):
	""" channel can be empty """
	goBuffer = widgets.get_widget("generalOutput").get_buffer()

	filter = config.get_list("general_output", "filter", [])
	logging.debug("filter: %s" % (filter))

	for tuple_str in filter:
		try:
			r_tuple = eval(tuple_str)
		except BaseException as e:
			logging.error("Error in filter tuple '%s': %s" % (tuple_str, e))
			continue
		if r_tuple[0] == msgtype and r_tuple[-1] in (server, channel):
			return

	serverTab, channelTab = tabs.search_tabs(server, channel)

	if channel:
		# channel print
		goBuffer.go_insert(goBuffer.get_end_iter(),
			"[%s] &lt;%s:%s&gt; %s" % (
				timestring, server, channel, message),
				channelTab, msgtype)
	else:
		# server print
		goBuffer.go_insert(goBuffer.get_end_iter(),
			"[%s] &lt;%s&gt; %s" % (timestring, server, message),
			serverTab, msgtype)

	widgets.get_widget("generalOutput").scroll_to_bottom()

def colorize_message(msgtype, message):
	if not config.get_bool("tekka", "color_text"):
		return message
	else:
		return "<font foreground='%s'>%s</font>" % (
			config.get("colors", "text_%s" % msgtype, "#000000"),
			message)

def channelPrint(timestamp, server, channel, message, msgtype="message",
no_general_output = False):
	""" Inserts a string formatted like "[H:M] <message>\n"
		into the htmlbuffer of the channel `channel` on server
		`server`.
	"""
	timestring = time.strftime(
		config.get("chatting", "time_format", "%H:%M"),
		time.localtime(timestamp))

	cString = colorize_message(msgtype, message)

	outputString = "[%s] %s" % (timestring, cString)

	channelTab = tabs.search_tab(server, channel)

	if not channelTab:
		logging.error("No such channel %s:%s" % (server, channel))
		return

	buffer = channelTab.window.textview.get_buffer()
	buffer.insertHTML(buffer.get_end_iter(), outputString)

	if not tabs.is_active(channelTab):
		if (config.get_bool("tekka", "show_general_output")
		and not no_general_output):
			# write it to the general output, also
			write_to_general_output(msgtype, timestring, server,
				channel, message)

	def notify():
		channelTab.setNewMessage(msgtype)
		return False
	gobject.idle_add(notify)

def serverPrint(timestamp, server, string, msgtype="message",
no_general_output = False):
	""" prints 'string' with "%H:%M' formatted 'timestamp' to
		the server-output identified by 'server'
	"""
	serverTab = tabs.search_tab(server)

	if not serverTab:
		logging.error("Server %s does not exist." % (server))
		return

	buffer = serverTab.window.textview.get_buffer()

	timestr = time.strftime(config.get("chatting", "time_format", "%H:%M"),
		time.localtime(timestamp))

	buffer.insertHTML(buffer.get_end_iter(), "[%s] %s" % (timestr, string))

	if not tabs.is_active(serverTab):
		if (config.get_bool("tekka", "show_general_output")
		and not no_general_output):
			write_to_general_output(msgtype, timestr, server, "", string)

	# TODO: replace this with signal insert-text
	def notify():
		serverTab.setNewMessage(msgtype)
		return False
	gobject.idle_add(notify)

def currentServerPrint(timestamp, server, string, msgtype="message"):
	"""
		Prints the string on the current tab of server (if any).
		Otherwise it prints directly in the server tab.
	"""
	serverTab, channelTab = tabs.get_current_tabs()

	if (serverTab
	and serverTab.name.lower() == server.lower()
	and channelTab):
		# print in current channel
		channelPrint(
			timestamp, server,
			channelTab.name, string, msgtype)
	else:
		# print to server tab
		serverPrint(timestamp, server, string, msgtype)

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
	d = gtk.MessageDialog(
		type = gtk.MESSAGE_QUESTION,
		buttons = gtk.BUTTONS_YES_NO,
		message_format = message)
	d.set_title(title)
	return d

@types(string=basestring, force_dialog=bool)
def error_dialog(title = "", message = ""):
	err = gtk.MessageDialog(
		type = gtk.MESSAGE_ERROR,
		buttons = gtk.BUTTONS_CLOSE,
		message_format = message)
	err.set_title(title)
	return err

def show_error_dialog(title = "", message = ""):
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

	# Purpose: auto removing messages (depends on config)
	self = helper.code.init_function_attrs(
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
