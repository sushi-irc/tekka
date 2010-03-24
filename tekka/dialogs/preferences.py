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

import gtk
import gtk.glade
import logging
from gobject import idle_add

from .. import gui
from .. import config
from ..lib.expanding_list import ExpandingList

widgets = None
nickColorsList = None
highlightList = None
generalOutputFilterList = None

MESSAGE_TYPES=('message','action',
		'highlightmessage','highlightaction')

def generalOutputFilterList_instanced_widget_cb(elist, row, column, obj):
	if column == 0:
		model = gtk.ListStore(str)
		obj.set_model(model)

		renderer = gtk.CellRendererText()
		obj.pack_start(renderer, True)
		obj.add_attribute(renderer, "text", 0)

		for row in MESSAGE_TYPES:
			model.append((row,))

def customHandler(glade, function_name, widget_name, *x):
	def _nice_sw():
		sw = gtk.ScrolledWindow()
		sw.set_properties(
			hscrollbar_policy = gtk.POLICY_AUTOMATIC,
			vscrollbar_policy = gtk.POLICY_AUTOMATIC)
		return sw

	if widget_name == "nickColorsList":
		global nickColorsList

		nickColorsList = ExpandingList(gtk.ColorButton)

		sw = _nice_sw()
		sw.add_with_viewport(nickColorsList)
		sw.show_all()

		return sw

	elif widget_name == "highlightList":
		global highlightList

		highlightList = ExpandingList(gtk.Entry)

		sw = _nice_sw()
		sw.add_with_viewport(highlightList)
		sw.show_all()

		return sw

	elif widget_name == "generalOutputFilterList":
		global generalOutputFilterList

		# negate, type, server, channel
		generalOutputFilterList = ExpandingList(
			gtk.ComboBox, gtk.Entry, gtk.Entry,
			no_firstrow=True)

		generalOutputFilterList.connect("instanced_widget",
			generalOutputFilterList_instanced_widget_cb)

		generalOutputFilterList._add_row(0)

		sw = _nice_sw()
		sw.add_with_viewport(generalOutputFilterList)
		sw.show_all()

		return sw

	return None

def fillTekka():
	table = widgets.get_object("tekkaTable")

	# set checkbuttons
	for child in table.get_children():

		if type(child) != gtk.CheckButton:
			continue

		name = gtk.Buildable.get_name(child)
		bval = config.get_bool("tekka", name)

		child.set_active(bval)

	# set font labels
	font = config.get("tekka", "font")
	widgets.get_object("fontSelectButton").set_font_name(font)

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

		widgets.get_object(key).set_color(color)

		btn = widgets.get_widget("auto_rule_color")
		btn.set_active(config.get("colors","rules_color") == "auto")
		btn.toggled()

		btn = widgets.get_widget("rules_color_yesno")
		btn.set_active(config.get_bool("tekka","text_rules"))
		btn.toggled()


def fillChatting():
	for key in ("quit_message", "part_message", "time_format"):
		val = config.get("chatting", key)
		widgets.get_object(key).set_text(val)

	i = 0
	for highlight in config.get_list("chatting", "highlight_words", []):
		highlightList.get_widget_matrix()[i][0].set_text(highlight)
		highlightList.add_row()
		i+=1

	highlightList.remove_row(i)

	val = config.get("chatting", "last_log_lines", default=0)
	widgets.get_object("last_log_lines").set_value(float(val))

def fillNickColors():
	widgets.get_object("nick_contrast_colors").set_active(
		config.get_bool("colors", "nick_contrast_colors"))

	colors = config.get_list("colors", "nick_colors", [])

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
	# (type, server, channel), (type, server), ...
	filter = config.get_list("general_output", "filter", [])

	i=0
	for tuple in filter:
		try:
			e_tuple = eval(tuple)
		except BaseException as e:
			logging.error("Tuple '%s' in filter rule is malformed: %s" % (
				tuple, e))
			continue

		widget_row = generalOutputFilterList.get_widget_matrix()[i]
		combobox = widget_row[0]

		try:
			type_index = MESSAGE_TYPES.index(e_tuple[0])
		except ValueError:
			logging.error("Unknown message type '%s'." % (e_tuple[0]))
			continue
		else:
			combobox.set_active(type_index)

		if len(e_tuple) >= 2:
			widget_row[1].set_text(e_tuple[1])

		if len(e_tuple) == 3:
			widget_row[2].set_text(e_tuple[2])

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

	for widget_row in generalOutputFilterList.get_widget_matrix():
		cbox = widget_row[0]

		mtype = cbox.get_active_text()

		if not mtype:
			logging.error("No message type selected.")
			continue

		server = widget_row[1].get_text()
		channel = widget_row[2].get_text()

		f_tuple = (str(mtype), str(server), str(channel))

		filter_list.append(str(f_tuple))

	config.set_list("general_output", "filter", filter_list)

""" tekka page signals """

def tekka_show_status_icon_toggled(button):
	config.set("tekka", "show_status_icon",
			str(button.get_active()))
	gui.mgmt.switch_status_icon(button.get_active())

def tekka_hide_on_close_toggled(button):
	config.set("tekka", "hide_on_close",
			str(button.get_active()))

def tekka_font_clicked(button):
	font = button.get_font_name()

	if font:
		config.set("tekka", "font", font)
		gui.mgmt.apply_new_font()

def tekka_use_default_font_toggled(button):
	config.set("tekka", "use_default_font",
			str(button.get_active()))

	gui.mgmt.apply_new_font()

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

def colors_rules_color_written(button):
	colors_set_color_from_button(button, "rules_color")

def colors_rules_autodetect_toggled(button):
	if button.get_active():
		config.set("colors","rules_color","auto")
	widgets.get_widget("rules_color").set_sensitive(not button.get_active())

def colors_rules_color_yesno_toggled(button):
	flag = button.get_active()
	config.set("tekka", "text_rules", str(flag))
	widgets.get_widget("auto_rule_color").set_sensitive(flag)
	widgets.get_widget("rules_color").set_sensitive(flag)


""" chatting page signals """

def chatting_quit_message_written(entry, event):
	text = entry.get_text()
	config.set("chatting", "quit_message", text)

def chatting_part_message_written(entry, event):
	text = entry.get_text()
	config.set("chatting", "part_message", text)

def chatting_time_format_written(entry, *x):
	text = entry.get_text()
	config.set("chatting", "time_format", text)

def chatting_log_lines_changed(button):
	value = int(button.get_value())

	if value < 0:
		return

	config.set("chatting", "last_log_lines", str(value))

""" nick colors page signals """

def nick_contrast_colors_toggled_cb(button):
	config.set("colors", "nick_contrast_colors", str(button.get_active()))


	ncl = widgets.get_object("nickColorsList")

	if ncl:
		ncl.set_sensitive(not button.get_active())

""" advanced page signals """

def advanced_advancedSettingsClicked(button):
	d = gui.dialogs.loadDialog("advancedPreferences")
	if not d:
		logging.error("advanced settings dialog setup failed")
		return
	d.run()

""" setup/run/maintenace methods """

def setup():
	"""
	read glade stuff
	"""
	global widgets

	widgets = gui.builder.load_dialog("preferences", custom_handler = customHandler)

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
		"colors_rules_color_written": colors_rules_color_written,
		"colors_rules_autodetect_toggled": colors_rules_autodetect_toggled,
		"colors_rules_color_yesno_toggled": colors_rules_color_yesno_toggled,
	# chatting page
		"chatting_quit_message_written": chatting_quit_message_written,
		"chatting_part_message_written": chatting_part_message_written,
		"chatting_time_format_written": chatting_time_format_written,
		"chatting_log_lines_changed": chatting_log_lines_changed,
	# nick colors page
		"nick_contrast_colors_toggled_cb": nick_contrast_colors_toggled_cb,
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
	dialog = widgets.get_object("preferencesDialog")

	fillTekka()
	fillColors()
	fillChatting()
	fillNickColors()
	fillGeneralOutputFilters()

	dialog.connect("response", dialog_response_cb)
	dialog.show_all()


