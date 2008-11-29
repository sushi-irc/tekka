# UHF = ultra high frequency :]

import config
import gtk
import gtk.glade

widgets = None

def fillChild(category, table, child):
	name = child.get_property("name")

	if type(child) == gtk.CheckButton:
		value = config.getBool(category, name, "")

		child.set_active(value)
		
	elif type(child) == gtk.Label:
		oldText = child.get_text()
		value = config.get(category, name[:-len("_label")], "")

		if value:
			child.set_text(value)
		else:
			child.set_text(oldText)

	elif type(child) == gtk.Entry:
		value = config.get(category, name, "")
		child.set_text(value)

	elif type(child) == gtk.SpinButton:
		value = int (config.get(category, name, ""))
		child.set_value(value)

def fillValues(categories):
	
	for category in categories:

		table = widgets.get_widget("%sTable" % category)

		if not table:
			print "table '%sTable' not found." % category

		for child in table.get_children():

			# This i more like a hack for subcontainer (*Box)
			# to handle their childs, too
			if type(child) == gtk.HBox or type(child) == gtk.VBox:
				for subchild in child.get_children():
					fillChild(category, child, subchild)
			
			fillChild(category, table, child)

def applyChild(category, table, child):
	name = child.get_property("name")

	if type(child) == gtk.CheckButton:
		value = str(child.get_active()).lower()
		config.set(category, name, value)
		
	elif type(child) == gtk.Entry:
		value = child.get_text()
		config.set(category, name, value)

	elif type(child) == gtk.SpinButton:
		value = str(int(child.get_value()))
		config.set(category, name, value)

def applyValues(categories):
	
	for category in categories:

		table = widgets.get_widget("%sTable" % category)

		if not table:
			print "table '%sTable' not found." % category

		for child in table.get_children():

			# This i more like a hack for subcontainer (*Box)
			# to handle their childs, too
			if type(child) == gtk.HBox or type(child) == gtk.VBox:
				for subchild in child.get_children():
					applyChild(category, child, subchild)
			
			applyChild(category, table, child)

def tekka_output_font_fontSelectionButton_clicked_cb(button):
	pass

def tekka_general_output_font_fontSelectionButton_clicked_cb(button):
	pass

def setup():
	"""
	read glade stuff
	"""
	global widgets

	path = config.get("gladefiles","dialogs") + "preferences.glade"
	widgets = gtk.glade.XML(path)

	sigdic = {
		"tekka_output_font_fontSelectionButton_clicked_cb" :
			tekka_output_font_fontSelectionButton_clicked_cb,
		"tekka_general_output_font_fontSelectionButton_clicked_cb" :
			tekka_general_output_font_fontSelectionButton_clicked_cb,
	}

	widgets.signal_autoconnect(sigdic)

def run():
	categories = ("tekka","colors","chatting")
	dialog = widgets.get_widget("preferencesDialog")
	
	fillValues(categories)

	if dialog.run() == gtk.RESPONSE_OK:
		applyValues(categories)
		# TODO: restart everything

	dialog.destroy()


