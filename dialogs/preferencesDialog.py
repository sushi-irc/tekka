# UHF = ultra high frequency :]

import config
import gtk
import gtk.glade

from __main__ import gui

from helper.expandingList import expandingList

widgets = None
nickColorsList = None

def customHandler(glade, function_name, widget_name, *x):
	if widget_name == "nickColorsList":
		global nickColorsList

		nickColorsList = expandingList(gtk.Entry)
		sw = gtk.ScrolledWindow()
		sw.add_with_viewport(nickColorsList)
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
		bval = config.getBool("tekka", name)

		child.set_active(bval)

	# set font labels
	oFont = config.get("tekka", "output_font")
	widgets.get_widget("fontSelectButton").set_font_name(oFont)

	gFont = config.get("tekka", "general_output_font")
	widgets.get_widget("fontSelectButton_generalOutput").set_font_name(gFont)

def fillColors():
	for key in ("own_nick", "own_text", "notification",
				"text_message", "text_action", "nick",
				"text_highlightmessage", "text_highlightaction"):
		val = config.get("colors", key)

		if not val:
			continue

		widgets.get_widget(key).set_text(val)

def fillChatting():
	for key in ("quit_message", "part_message"):
		val = config.get("chatting", key)
		if not val:
			continue
		widgets.get_widget(key).set_text(val)

	val = config.get("chatting", "last_log_lines", default=0)
	widgets.get_widget("last_log_lines").set_value(float(val))

def fillNickColors():
	colors = config.get("nick_colors", default={})

	if not colors:
		return

	i = 0
	for color in colors.values():
		nickColorsList.get_widget_matrix()[i][0].set_text(color)
		nickColorsList.add_row()
		i+=1
	nickColorsList.remove_row(i)

def applyNickColors():
	toClear = config.get("nick_colors", default={})
	for key in toClear:
		config.unset("nick_colors", key)

	i = 1
	for row in nickColorsList.get_widget_matrix():
		entry = row[0]

		text = entry.get_text()

		if not text:
			continue

		config.set("nick_colors", str(i), text)

		i+=1

""" tekka page signals """

def tekka_show_status_icon_toggled(button):
	config.set("tekka", "show_status_icon",
			str(button.get_active()).lower())
	gui.setStatusIcon(button.get_active())

def tekka_hide_on_close_toggled(button):
	config.set("tekka", "hide_on_close",
			str(button.get_active()).lower())

def tekka_output_font_clicked(button):
	output = gui.getWidgets().get_widget("output")

	font = button.get_font_name()

	if font:
		config.set("tekka", "output_font", font)
		gui.setFont(output, font)

def tekka_general_output_font_clicked(button):
	output = gui.getWidgets().get_widget("generalOutput")

	font = button.get_font_name()

	if font:
		config.set("tekka", "general_output_font", font)
		gui.setFont(output, font)

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

""" chatting page signals """

def chatting_quit_message_written(entry, event):
	text = entry.get_text()

	if not text:
		config.unset("chatting", "quit_message")
	else:
		config.set("chatting", "quit_message", text)

def chatting_part_message_written(entry, event):
	text = entry.get_text()

	if not text:
		config.unset("chatting", "part_message")
	else:
		config.set("chatting", "part_message", text)

def chatting_log_lines_changed(button):
	value = int(button.get_value())

	if value < 0:
		return

	config.set("chatting", "last_log_lines", str(value))

""" advanced page signals """

def advanced_advancedSettingsClicked(button):
	import dialog
	d = dialog.loadDialog("advancedPreferences")
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

	dialog.run()

	applyNickColors()

	dialog.destroy()


