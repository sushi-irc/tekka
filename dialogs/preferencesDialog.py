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

# UHF = ultra high frequency :]

import config
import gtk
import gtk.glade
from gobject import idle_add
import re

import gui_control as gui
import dialog_control

from helper.expandingList import expandingList

widgets = None
nickColorsList = None
highlightList = None

def generalOutputFilterList_instanced_widget_cb(elist, row, column, obj):
	if column == 0:
		obj.set_property("label", "Negate")

def customHandler(glade, function_name, widget_name, *x):
	if widget_name == "nickColorsList":
		global nickColorsList

		nickColorsList = expandingList(gtk.ColorButton)
		sw = gtk.ScrolledWindow()
		sw.add_with_viewport(nickColorsList)
		sw.show_all()

		return sw

	elif widget_name == "highlightList":
		global highlightList

		highlightList = expandingList(gtk.Entry)
		sw = gtk.ScrolledWindow()
		sw.add_with_viewport(highlightList)
		sw.show_all()

		return sw

	elif widget_name == "generalOutputFilterList":
		global generalOutputFilterList

		# negate, type, server, channel
		generalOutputFilterList = expandingList(
			gtk.ToggleButton, gtk.Entry,
			gtk.Entry, gtk.Entry,
			no_firstrow=True)

		generalOutputFilterList.connect("instanced_widget",
			generalOutputFilterList_instanced_widget_cb)

		generalOutputFilterList._add_row(0)

		sw = gtk.ScrolledWindow()
		sw.add_with_viewport(generalOutputFilterList)
		sw.show_all()

		return sw

	return None

def fillTekka():
	table = widgets.get_widget("tekkaTable")

	# set checkbuttons
	for child in table.get_children():

		if type(child) != gtk.CheckButton:
			continue

		name = child.get_property("name")
		bval = config.get_bool("tekka", name)

		child.set_active(bval)

	# set font labels
	font = config.get("tekka", "font")
	widgets.get_widget("fontSelectButton").set_font_name(font)

def fillColors():
	for key in ("own_nick", "own_text", "notification",
				"text_message", "text_action", "nick",
				"text_highlightmessage", "text_highlightaction",
				"last_log"):
		val = config.get("colors", key)

		try:
			color = gtk.gdk.Color(val)
		except:
			color = gtk.gdk.Color()

		widgets.get_widget(key).set_color(color)

def fillChatting():
	for key in ("quit_message", "part_message"):
		val = config.get("chatting", key)
		widgets.get_widget(key).set_text(val)

	i = 0
	for highlight in config.get_list("chatting", "highlight_words"):
		highlightList.get_widget_matrix()[i][0].set_text(highlight)
		highlightList.add_row()
		i+=1

	highlightList.remove_row(i)

	val = config.get("chatting", "last_log_lines", default=0)
	widgets.get_widget("last_log_lines").set_value(float(val))

def fillNickColors():
	colors = config.get_list("colors", "nick_colors")

	if not colors:
		return

	i = 0

	for color in colors:
		try:
			c = gtk.gdk.Color(color)
		except:
			c = gtk.gdk.Color()

		nickColorsList.get_widget_matrix()[i][0].set_color(c)
		nickColorsList.add_row()
		i+=1

	nickColorsList.remove_row(i)

def fillGeneralOutputFilters():
	filter = config.get_list("general_output", "filter")
	pattern = re.compile("^not \((.+)\)")

	if not filter:
		return

	i=0
	for filter_rule in filter:

		if not filter_rule:
			continue

		match = pattern.match(filter_rule)

		if match:
			filter_rule = match.groups()[0]
			generalOutputFilterList.get_widget_matrix()[i][0].set_active(True)

		vars = dict([ pair.split(" == ") for pair in filter_rule.split(" and ") ])

		for (key,value) in vars.items():
			value = value.strip('"')
			if key == "type":
				generalOutputFilterList.get_widget_matrix()[i][1].set_text(value)

			elif key == "server":
				generalOutputFilterList.get_widget_matrix()[i][2].set_text(value)

			elif key == "channel":
				generalOutputFilterList.get_widget_matrix()[i][3].set_text(value)

			else:
				raise ValueError, "Invalid key '%s'" % (key)

		generalOutputFilterList.add_row()
		i+=1
	generalOutputFilterList.remove_row(i)


def applyNickColors():
	config.set_list("colors","nick_colors", [n[0].get_color().to_string() for n in nickColorsList.get_widget_matrix() if n and len(n) >= 1])

def applyChatting():
	config.set_list("chatting", "highlight_words", [n[0].get_text() for n in highlightList.get_widget_matrix() if n])

def applyGeneralOutputFilter():
	filter_list = []
	header = ("type", "server", "channel")

	for row in generalOutputFilterList.get_widget_matrix():
		n_c = 0
		rule = ""
		c_l = len(row[1:len(header)])

		if not row:
			continue

		for col in row[1:len(header)]:
			if not col.get_text():
				continue

			# XXX: yep, this is a hole.
			rule += "%s == \"\"\"%s\"\"\"" % (header[n_c],col.get_text())
			n_c += 1

			if n_c != c_l:
				rule += " and "

		if row[0].get_active():
			rule = "not (%s)" % (rule)

		filter_list.append(rule)

		print filter_list
		config.set_list("general_output", "filter", filter_list)


""" tekka page signals """

def tekka_show_status_icon_toggled(button):
	config.set("tekka", "show_status_icon",
			str(button.get_active()))
	gui.setStatusIcon(button.get_active())

def tekka_hide_on_close_toggled(button):
	config.set("tekka", "hide_on_close",
			str(button.get_active()))

def tekka_font_clicked(button):
	font = button.get_font_name()

	if font:
		config.set("tekka", "font", font)

		for row in gui.widgets.get_widget("serverTree").get_model():
			for child in row.iterchildren():
				gui.setFont(child[2].textview, gui.get_font())
			gui.setFont(row[2].textview, gui.get_font())

		gui.setFont(gui.widgets.get_widget("output"), gui.get_font())
		gui.setFont(gui.widgets.get_widget("inputBar"), gui.get_font())
		gui.setFont(gui.widgets.get_widget("generalOutput"), gui.get_font())

def tekka_use_default_font_toggled(button):
	config.set("tekka", "use_default_font",
			str(button.get_active()))

	gui.setFont(gui.widgets.get_widget("output"), gui.get_font())
	gui.setFont(gui.widgets.get_widget("inputBar"), gui.get_font())
	gui.setFont(gui.widgets.get_widget("generalOutput"), gui.get_font())

def tekka_auto_expand_toggled(button):
	config.set("tekka", "auto_expand",
			str(button.get_active()))

def tekka_rgba_toggled(button):
	config.set("tekka", "rgba",
			str(button.get_active()))

def tekka_close_maki_on_close_toggled(button):
	config.set("tekka", "close_maki_on_close",
			str(button.get_active()))

""" colors page signals """

def colors_set_color_from_button(button, key):
	color = button.get_color()

	config.set("colors", key, color.to_string())

def colors_own_text_written(button):
	colors_set_color_from_button(button, "own_text")

def colors_own_nick_written(button):
	colors_set_color_from_button(button, "own_nick")

def colors_notification_written(button):
	colors_set_color_from_button(button, "notification")

def colors_messages_written(button):
	colors_set_color_from_button(button, "text_message")

def colors_actions_written(button):
	colors_set_color_from_button(button, "text_action")

def colors_highlighted_messages_written(button):
	colors_set_color_from_button(button, "text_highlightmessage")

def colors_highlighted_actions_written(button):
	colors_set_color_from_button(button, "text_highlightaction")

def colors_default_nick_written(button):
	colors_set_color_from_button(button, "nick")

def colors_last_log_written(button):
	colors_set_color_from_button(button, "last_log")

""" chatting page signals """

def chatting_quit_message_written(entry, event):
	text = entry.get_text()
	config.set("chatting", "quit_message", text)

def chatting_part_message_written(entry, event):
	text = entry.get_text()
	config.set("chatting", "part_message", text)

def chatting_log_lines_changed(button):
	value = int(button.get_value())

	if value < 0:
		return

	config.set("chatting", "last_log_lines", str(value))

""" advanced page signals """

def advanced_advancedSettingsClicked(button):
	d = dialog_control.loadDialog("advancedPreferences")
	if not d:
		print "dialog setup failed"
		return
	d.run()

""" setup/run/maintenace methods """

def setup():
	"""
	read glade stuff
	"""
	global widgets

	path = config.get("gladefiles","dialogs") + "preferences.glade"

	gtk.glade.set_custom_handler(customHandler)
	widgets = gtk.glade.XML(path)

	sigdic = {
	# tekka page
		"tekka_show_status_icon_toggled": tekka_show_status_icon_toggled,
		"tekka_hide_on_close_toggled": tekka_hide_on_close_toggled,
		"tekka_font_clicked": tekka_font_clicked,
		"tekka_use_default_font_toggled": tekka_use_default_font_toggled,
		"tekka_auto_expand_toggled": tekka_auto_expand_toggled,
		"tekka_rgba_toggled": tekka_rgba_toggled,
		"tekka_close_maki_on_close_toggled": tekka_close_maki_on_close_toggled,
	# colors page
		"colors_own_text_written": colors_own_text_written,
		"colors_own_nick_written": colors_own_nick_written,
		"colors_notification_written": colors_notification_written,
		"colors_messages_written": colors_messages_written,
		"colors_actions_written": colors_actions_written,
		"colors_highlighted_messages_written":
				colors_highlighted_messages_written,
		"colors_highlighted_actions_written":
				colors_highlighted_actions_written,
		"colors_default_nick_written": colors_default_nick_written,
		"colors_last_log_written": colors_last_log_written,
	# chatting page
		"chatting_quit_message_written": chatting_quit_message_written,
		"chatting_part_message_written": chatting_part_message_written,
		"chatting_log_lines_changed": chatting_log_lines_changed,
	# advanced page
		"advanced_advancedSettingsClicked": advanced_advancedSettingsClicked
	}

	widgets.signal_autoconnect(sigdic)

def dialog_response_cb(dialog, response_id):
	applyNickColors()
	applyGeneralOutputFilter()
	applyChatting()

	dialog.destroy()

def run():
	dialog = widgets.get_widget("preferencesDialog")

	fillTekka()
	fillColors()
	fillChatting()
	fillNickColors()
	fillGeneralOutputFilters()

	dialog.connect("response", dialog_response_cb)
	dialog.show_all()


