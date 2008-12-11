# INSERT LICENSE HEADER HERE

import gtk
import gtk.glade
import config
import gobject

widgets = None

def addCategory(store, category):
	""" add parent item to store and return the treeiter """
	iter = store.append(None, (category,"",""))

	return iter

def fillConfigView():
	configView = widgets.get_widget("configView")
	configStore = configView.get_model()

	for category in ("tekka","colors","chatting"):
		cDict = config.get(category, default=None)

		if not cDict:
			continue

		iter = addCategory(configStore, category)

		if not iter:
			continue

		for (key, value) in cDict.items():
			default = str(config.getDefault(category, key))
			configStore.append(iter, row=(key, value, default))

def renderOption(column, cell, model, iter):
	pass

def renderValue(column, cell, model, iter):
	pass

def renderDefaultValue(column, cell, model, iter):
	pass

def setup():
	""" called initially """
	global widgets
	gladePath = config.get("gladefiles", "dialogs") + "advancedPreferences.glade"
	widgets = gtk.glade.XML(gladePath)

	configView = widgets.get_widget("configView")

	c = 0
	for name in ("Option", "Value", "Default Value"):
		renderer = gtk.CellRendererText()

		column = gtk.TreeViewColumn(name, renderer, text=c)

		# set custom rendering function (render<key>)
		column.set_cell_data_func(renderer,
				eval("render%s" % name.replace(" ","")))

		configView.append_column(column)
		c+=1

	store = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
			gobject.TYPE_STRING)

	configView.set_model(store)

def run():
	dialog = widgets.get_widget("advancedPreferences")

	fillConfigView()

	dialog.run()
	dialog.destroy()
