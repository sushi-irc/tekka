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

def fillValues():
	
	for category in ("tekka","colors","chatting"):

		table = widgets.get_widget("%sTable" % category)

		if not table:
			print "table '%sTable' not found." % category

		for child in table.get_children():
			if type(child) == gtk.HBox or type(child) == gtk.VBox:
				for subchild in child.get_children():
					fillChild(category, child, subchild)
			fillChild(category, table, child)


def setup(dialogInterface):
	"""
	read glade stuff
	"""
	global widgets

	widgets = gtk.glade.XML(config.get("gladefiles","dialogs"), "preferencesDialog")

def run():
	dialog = widgets.get_widget("preferencesDialog")
	
	fillValues()

	dialog.run()

	dialog.destroy()


