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
"""
The "core": the gui wrapper class.
"""

# global modules
import gtk
import gtk.glade
import time
import pango
import gettext
import gobject
from gobject import idle_add
from dbus import String

# profiling imports
import os, sys
from xdg.BaseDirectory import xdg_cache_home
import cProfile

try:
	from sexy import SpellEntry
except ImportError:
	print "Spell checking disabled."

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

widgets = None
statusIcon = None
accelGroup = None
searchToolbar = None
tabs = lib.tab_control.TabControl()

def profileMe(file):
	def get_location(file):
		path = os.path.join(xdg_cache_home, "sushi", "tekka")
		if not os.path.exists(path):
			try:
				os.makedirs(path)
			except BaseException, e:
				print >> sys.stderr, "Profiling disabled: %s", e
				return None
		return os.path.join(path, file)

	def deco(fun):
		def new(*args, **kwargs):
			val = None
			file_path = get_location(file)

			if None == file:
				return fun(*args, **kwargs)

			cProfile.runctx("val = fun(*args,**kwargs)", {"fun":fun},
				locals(), file_path)
			return val

		if "-p" in sys.argv:
			return new
		return fun
	return deco

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

def custom_handler(glade, function_name, widget_name, *x):
	if widget_name == "searchToolbar":
		return setup_searchToolbar()

	elif widget_name in ("generalOutput", "output"):
		go = OutputTextView()

		return go

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

@types(gladeFile=basestring, section=basestring)
def load_widgets(gladeFile, section):
	""" load the given section from gladeFile
		into widgets and return them.
		This method is ususally called from main.py
		to initialize the GUI
	"""
	global widgets
	gtk.glade.set_custom_handler(custom_handler)
	widgets = gtk.glade.XML(gladeFile, section)

	return widgets

def replace_output_textview(textview):
	sw = widgets.get_widget("scrolledWindow_output")
	sw.remove(sw.get_children()[0])
	sw.add(textview)
	searchToolbar.textview = textview


def get_current_output_textview():
	tab = tabs.get_current_tab()

	if not tab:
		return widgets.get_widget("output")
	else:
		return tab.textview

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

	global statusIcon
	statusIcon = TekkaStatusIcon()

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
		widgets.get_widget("output"),
		widgets.get_widget("generalOutput")
	]

	current_textview = get_current_output_textview()
	if current_textview:
		widgetList.append(current_textview)

	for widget in widgetList:
		widget.set_sensitive(switch)

	if switch: widgets.get_widget("inputBar").grab_focus()

	gui_is_useable = switch

@types(switch=bool)
def switch_status_icon(switch):
	""" enables / disables status icon """
	if switch:
		if not statusIcon:
			setup_statusIcon()
		statusIcon.set_visible(True)

	else:
		if not statusIcon:
			return
		statusIcon.set_visible(False)

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

	if win.has_toplevel_focus():
		# urgent toplevel windows suck ass
		return

	win.set_urgency_hint(switch)

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
		print "Font _not_ modified (previous error)"
		return

	textView.modify_font(fd)

@types(string=basestring)
def set_topic(string):
	""" Sets the given string as text in
		the topic bar.
	"""
	tb = widgets.get_widget("topicBar")
	tb.set_text(string)

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

def escape(msg):
	"""	Converts special characters in msg and returns
		the new string.
	"""
	msg = msg.replace("&", "&amp;")
	msg = msg.replace("<", "&lt;")
	msg = msg.replace(">", "&gt;")
	msg = msg.replace(chr(2), "<sb/>") # bold-char
	msg = msg.replace(chr(31), "<su/>") # underline-char
	msg = msg.replace(chr(1), "")
	return msg

def write_to_general_output(msgtype, timestring, server, channel, message):
	goBuffer = widgets.get_widget("generalOutput").get_buffer()

	filter = config.get_list("general_output", "filter", default=[])
	print "filter: %s" % (filter)
	for rule in filter:
		try:
			if not eval(rule):
				return
		except BaseException, e:
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

def channelPrint(timestamp, server, channel, message, msgtype="message"):
	"""
		Inserts a string formatted like "[H:M] <message>\n"
		into the htmlbuffer of the channel `channel` on server
		`server`.
	"""
	timestring = time.strftime(config.get("tekka", "time_format", "%H:%M"),
		time.localtime(timestamp))

	if not config.get_bool("tekka", "color_text"):
		colorHack = ""
	else:
		colorHack = "foreground='%s'" % (
			config.get("colors", "text_%s" % msgtype, "#000000"))

	outputString = "[%s] <font %s>%s</font>" % (
		timestring,
		colorHack,
		message)

	channelTab = tabs.search_tab(server, channel)

	if not channelTab:
		print "No such channel %s:%s" % (server, channel)
		return

	buffer = channelTab.textview.get_buffer()
	buffer.insertHTML(buffer.get_end_iter(), outputString)

	# notification in server/channel list
	if tabs.is_active(channelTab):
		if channelTab.autoScroll:
			channelTab.textview.scroll_to_bottom()

	else:
		if config.get_bool("tekka", "show_general_output"):
			# write it to the general output, also
			write_to_general_output(msgtype, timestring, server, channel, message)

		if not msgtype in channelTab.newMessage:
			channelTab.setNewMessage(msgtype)

def serverPrint(timestamp, server, string, msgtype="message"):
	"""
		prints 'string' with "%H:%M' formatted 'timestamp' to the server-output
		identified by 'server'
	"""
	serverTab = tabs.search_tab(server)

	if not serverTab:
		print "Server %s does not exist." % server
		return

	buffer = serverTab.textview.get_buffer()

	timestr = time.strftime(config.get("tekka", "time_format", "%H:%M"),
		time.localtime(timestamp))

	buffer.insertHTML(buffer.get_end_iter(), "[%s] %s" % (timestr, string))


	if tabs.is_active(serverTab):
		if serverTab.autoScroll:
			serverTab.textview.scroll_to_bottom()

	else:
		if config.get_bool("tekka", "show_general_output"):
			write_to_general_output(msgtype, timestr, server, "", string)

		if not msgtype in serverTab.newMessage:
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
	textview = get_current_output_textview()
	output = textview.get_buffer()

	if not output:
		print "No output buffer here!"
		return

	if not html:
		if output.get_char_count() > 0:
			string = "\n" + string

		output.insert(output.get_end_iter(), string)

	else:
		try:
			output.insertHTML(output.get_end_iter(), string)
		except AttributeError:
			print "No HTML buffer, printing normal."
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
