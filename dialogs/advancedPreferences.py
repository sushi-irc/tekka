# INSERT LICENSE HEADER HERE

import gtk
import gtk.glade
import config
import gobject
import pango

widgets = None

def addCategory(store, category):
	""" add parent item to store and return the treeiter """
	iter = store.append(None, (category,"",""))

	return iter

def fillConfigView():
	"""
	fill config treeview with categories,
	options/values and defaults
	"""
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
			default = str(config.get_default(category, key))
			configStore.append(iter, row=(key, value, default))

def renderOption(column, renderer, model, iter):
	if not model.iter_parent(iter):
		# category row, markup bold
		renderer.set_property("weight", pango.WEIGHT_BOLD)
	else:
		renderer.set_property("weight", pango.WEIGHT_NORMAL)

def renderValue(column, renderer, model, iter):
	if not model.iter_parent(iter):
		renderer.set_property("editable", False)
	else:
		renderer.set_property("editable", True)

def renderDefaultValue(column, renderer, model, iter):
	pass

def configValueEdited(renderer, path, newText):
	model = widgets.get_widget("configView").get_model()
	treeIter = model.get_iter(path)

	catIter = model.iter_parent(treeIter)

	if not catIter:
		return

	model.set(treeIter, 1, newText)

	category = model.get(catIter, 0)[0]
	option = model[path][0]
	value = model[path][1]

	config.set(category, option, value)

def setup():
	""" called initially """
	global widgets
	gladePath = config.get("gladefiles", "dialogs") + "advancedPreferences.glade"
	widgets = gtk.glade.XML(gladePath)

	configView = widgets.get_widget("configView")

	c = 0
	for name in ("Option", "Value", "Default Value"):
		renderer = gtk.CellRendererText()

		if name == "Value":
			# value column is editable
			renderer.set_property("editable", True)
			renderer.connect("edited", configValueEdited)

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
