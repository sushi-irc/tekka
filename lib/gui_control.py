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
import re
import gtk
import gtk.glade
import time
import pango
import gettext
import gobject
import logging

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

import lib.tab_control
from lib.search_toolbar import SearchBar
from lib.input_history import InputHistory
from lib.output_textview import OutputTextView
from lib.htmlbuffer import HTMLBuffer
from lib.status_icon import TekkaStatusIcon

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

def green(s,f={0:0}):
	f[0]+=1
	return chr(27)+"[31m"+str(f[0])+": "+chr(27)+"[32m"+s+chr(27)+"[0m"

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
					self.textview.scroll_to_bottom(no_smooth = True)

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
					self.auto_scroll = True
					print green("smooth scrolling => auto_scroll = True")
				elif (adjust.upper - adjust.page_size) == sbar.get_value():
					self.auto_scroll = True
					print green("At end => auto_scroll = True")
				else:
					self.auto_scroll = False
					print green("Neither end nor smooth_scrolling => auto_scroll = False")
				return False

			gobject.idle_add(idle_handler_cb)

		self.get_vscrollbar().connect("value-changed", value_changed_cb)

		def at_end_cb(widget):
			""" scrolled to end """
			# FIXME: check if this whole signal is necessary
			self.auto_scroll = True
			print green("set auto_scroll = True, at end")

		self.textview.connect("at-end", at_end_cb)

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

widgets = None
accelGroup = None
searchToolbar = None
tabs = lib.tab_control.TabControl()

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
		if widget_name == "searchToolbar":
			return setup_searchToolbar()

		elif widget_name == "outputShell":
			return OutputShell(OutputWindow())

		elif widget_name == "generalOutput":
			return OutputTextView()

		elif widget_name == "inputBar":
			try:
				bar = SpellEntry()
			except NameError:
				bar = gtk.Entry()
			bar.grab_focus()

			return bar

		elif widget_name == "notificationWidget":
			align = gtk.VBox()
			align.set_no_show_all(True)
			align.set_property("visible", False)
			return align

		return None

	gtk.glade.set_custom_handler(custom_handler)

	widgets = WidgetsWrapper(gtk.glade.XML(gladeFile, section))

	return widgets

def setup_searchToolbar():
	global searchToolbar
	searchToolbar = SearchBar(None)
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
	goBuffer = widgets.get_widget("generalOutput").get_buffer()

	filter = config.get_list("general_output", "filter", [])
	logging.debug("filter: %s" % (filter))

	for rule in filter:
		try:
			if not eval(rule):
				return
		except BaseException as e:
			errorMessage("Error in general output filter "
				"rule '%s': '%s'." % (rule, e))

	if channel:
		# channel print
		goBuffer.insertHTML(goBuffer.get_end_iter(),
			"[%s] &lt;%s:%s&gt; %s" % (
				timestring, server, channel, message))
	else:
		# server print
		goBuffer.insertHTML(goBuffer.get_end_iter(),
			"[%s] &lt;%s&gt; %s" % (timestring, server, message))

	widgets.get_widget("generalOutput").scroll_to_bottom()

def colorize_message(msgtype, message):
	if not config.get_bool("tekka", "color_text"):
		return message
	else:
		return "<font foreground='%s'>%s</font>" % (
			config.get("colors", "text_%s" % msgtype, "#000000"),
			message)

def channelPrint(timestamp, server, channel, message, msgtype="message"):
	"""
		Inserts a string formatted like "[H:M] <message>\n"
		into the htmlbuffer of the channel `channel` on server
		`server`.
	"""
	timestring = time.strftime(
		config.get("tekka", "time_format", "%H:%M"),
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
		if config.get_bool("tekka", "show_general_output"):
			# write it to the general output, also
			write_to_general_output(msgtype, timestring, server, channel, message)

	channelTab.setNewMessage(msgtype)

def serverPrint(timestamp, server, string, msgtype="message"):
	"""
		prints 'string' with "%H:%M' formatted 'timestamp' to the server-output
		identified by 'server'
	"""
	serverTab = tabs.search_tab(server)

	if not serverTab:
		logging.error("Server %s does not exist." % (server))
		return

	buffer = serverTab.window.textview.get_buffer()

	timestr = time.strftime(config.get("tekka", "time_format", "%H:%M"),
		time.localtime(timestamp))

	buffer.insertHTML(buffer.get_end_iter(), "[%s] %s" % (timestr, string))

	if not tabs.is_active(serverTab):
		if config.get_bool("tekka", "show_general_output"):
			write_to_general_output(msgtype, timestr, server, "", string)

	serverTab.setNewMessage(msgtype)

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

@types(string=basestring, force_dialog=bool)
def errorMessage(string, force_dialog=False):
	# TODO: get rid of this
	""" if GUI is initialized, and the output widget
		has an buffer, print the error there,
		else raise an error dialog with the given message.
		You can force the usage of an dialog
		with the force_dialog parameter.
	"""
	output = get_current_output_textview()

	message = gettext.gettext("Error: %(message)s")

	if output.get_buffer() and not force_dialog:
		message = "<font foreground='%(color)s'>" + message + "</font>"
		myPrint(message % {
				"color": config.get("colors", "error", "#FF0000"),
				"message": string},
			html=True)
	else:
		err = gtk.MessageDialog(
			type=gtk.MESSAGE_ERROR,
			buttons=gtk.BUTTONS_CLOSE,
			message_format=message % { "message": string })
		err.run()
		err.destroy()

######################################################
# new style error reporting sticking to the guidelines

def showInlineDialog(dialog):
	area = widgets.get_widget("notificationWidget")

	if dialog:
		area.set_no_show_all(False)
		area.add(dialog)
		area.show_all()
		area.set_no_show_all(True)
	else:
		area.set_property("visible", False)
