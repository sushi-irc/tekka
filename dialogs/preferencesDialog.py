# UHF = ultra high frequency :]

import config
import gtk
import gtk.glade
from gobject import idle_add

import gui_control as gui
import dialog_control

from helper.expandingList import expandingList

widgets = None
nickColorsList = None

def generalOutputFilterList_instanced_widget_cb(elist, row, column, obj):
	if column == 0:
		obj.set_property("label", "Negate")

def customHandler(glade, function_name, widget_name, *x):
	if widget_name == "nickColorsList":
		global nickColorsList

		nickColorsList = expandingList(gtk.Entry)
		sw = gtk.ScrolledWindow()
		sw.add_with_viewport(nickColorsList)
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
	oFont = config.get("tekka", "output_font")
	widgets.get_widget("fontSelectButton").set_font_name(oFont)

	gFont = config.get("tekka", "general_output_font")
	widgets.get_widget("fontSelectButton_generalOutput").set_font_name(gFont)

	iFont = config.get("tekka", "input_font")
	widgets.get_widget("fontSelectButton_inputBar").set_font_name(iFont)

	if config.get_bool("tekka", "input_font_is_output_font"):
		widgets.get_widget("fontSelectButton_inputBar").set_sensitive(False)

def fillColors():
	for key in ("own_nick", "own_text", "notification",
				"text_message", "text_action", "nick",
				"text_highlightmessage", "text_highlightaction",
				"last_log"):
		val = config.get("colors", key)

		if not val:
			continue

		widgets.get_widget(key).set_text(val)

def fillChatting():
	for key in ("quit_message", "part_message"):
		val = config.get("chatting", key)
		widgets.get_widget(key).set_text(val)

	val = config.get("chatting", "last_log_lines", default=0)
	widgets.get_widget("last_log_lines").set_value(float(val))

def fillNickColors():
	colors = config.get_list("colors", "nick_colors")

	if not colors:
		return

	i = 0
	for color in colors:
		nickColorsList.get_widget_matrix()[i][0].set_text(color)
		nickColorsList.add_row()
		i+=1
	nickColorsList.remove_row(i)

def fillGeneralOutputFilters():
	filter = config.get_list("general_output", "filter")

	if not filter:
		return

	i=0
	for filter_rule in filter:

		if not filter_rule:
			continue
			
		pairs = filter_rule.split(" and ")

		for pair in pairs:
			def set_negated(i):
					generalOutputFilterList.get_widget_matrix()[i][0].set_active(True)

			if not pair:
				continue

			key, value = pair.split(" == ")

			if key.startswith("not ("):
				key = key[len("not ("):]
				set_negated(i)

			if value[-1] == ")":
				value = value[:-1]
				set_negated(i)

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
	config.set_list("colors","nick_colors", [n[0].get_text() for n in nickColorsList.get_widget_matrix() if n and len(n) >= 1 and n[0].get_text()])

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
			str(button.get_active()).lower())
	gui.setStatusIcon(button.get_active())

def tekka_hide_on_close_toggled(button):
	config.set("tekka", "hide_on_close",
			str(button.get_active()).lower())

def tekka_output_font_clicked(button):
	output = gui.widgets.get_widget("output")

	font = button.get_font_name()

	if font:
		config.set("tekka", "output_font", font)
		gui.setFont(output, font)

		if config.get_bool("tekka","input_font_is_output_font"):
			gui.setFont(gui.widgets.get_widget("inputBar"), font)

def tekka_general_output_font_clicked(button):
	output = gui.widgets.get_widget("generalOutput")

	font = button.get_font_name()

	if font:
		config.set("tekka", "general_output_font", font)
		gui.setFont(output, font)

def tekka_input_bar_font_clicked(button):
	font = button.get_font_name()
	widget = gui.widgets.get_widget("inputBar")

	if font:
		config.set("tekka","input_font",font)
		gui.setFont(widget, font)

def tekka_input_font_is_output_font_toggled(button):
	config.set("tekka", "input_font_is_output_font",
			str(button.get_active()).lower())
	widget = gui.widgets.get_widget("inputBar")

	if button.get_active():
		# apply the new font and save the old
		gui.setFont(widget, config.get("tekka","output_font"))
		widgets.get_widget("fontSelectButton_inputBar").set_sensitive(False)

	else:
		# reset to the old font
		gui.setFont(widget, config.get("tekka","input_font"))
		widgets.get_widget("fontSelectButton_inputBar").set_sensitive(True)

def tekka_auto_expand_toggled(button):
	config.set("tekka", "auto_expand",
			str(button.get_active()).lower())

def tekka_rgba_toggled(button):
	config.set("tekka", "rgba",
			str(button.get_active()).lower())

def tekka_close_maki_on_close_toggled(button):
	config.set("tekka", "close_maki_on_close",
			str(button.get_active()).lower())

""" colors page signals """

def colors_set_color_from_entry(entry, key):
	text = entry.get_text()

	if not text:
		config.unset("colors", key)
	else:
		config.set("colors", key, text)

def colors_own_text_written(entry, event):
	colors_set_color_from_entry(entry, "own_text")

def colors_own_nick_written(entry, event):
	colors_set_color_from_entry(entry, "own_nick")

def colors_notification_written(entry, event):
	colors_set_color_from_entry(entry, "notification")

def colors_messages_written(entry, event):
	colors_set_color_from_entry(entry, "text_message")

def colors_actions_written(entry, event):
	colors_set_color_from_entry(entry, "text_action")

def colors_highlighted_messages_written(entry, event):
	colors_set_color_from_entry(entry, "text_highlightmessage")

def colors_highlighted_actions_written(entry, event):
	colors_set_color_from_entry(entry, "text_highlightaction")

def colors_default_nick_written(entry, event):
	colors_set_color_from_entry(entry, "nick")

def colors_last_log_written(entry, event):
	colors_set_color_from_entry(entry, "last_log")

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
		"tekka_output_font_clicked": tekka_output_font_clicked,
		"tekka_general_output_font_clicked": tekka_general_output_font_clicked,
		"tekka_input_bar_font_clicked": tekka_input_bar_font_clicked,
		"tekka_input_font_is_output_font_toggled": tekka_input_font_is_output_font_toggled,
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

def run():
	dialog = widgets.get_widget("preferencesDialog")

	fillTekka()
	fillColors()
	fillChatting()
	fillNickColors()
	fillGeneralOutputFilters()

	dialog.run()

	applyNickColors()
	applyGeneralOutputFilter()

	dialog.destroy()


