# coding: UTF-8
"""
Copyright (c) 2008 Marian Tietz
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

import gtk
import gtk.glade
import os
import gobject
from gobject import TYPE_BOOLEAN
import logging

from gettext import gettext as _

from lib import plugin_control as pinterface
import config

import sushi as psushi

widgets = None

(COL_LOADED,
 COL_AUTOLOAD,
 COL_NAME,
 COL_PATH,
 COL_VERSION,
 COL_DESC,
 COL_AUTHOR) = range(7)

def dialog_response_cb(dialog, response_id):
	if response_id != 0:
		dialog.destroy()

def run():
	dialog = widgets.get_widget("plugins")

	dialog.connect("response", dialog_response_cb)
	dialog.show_all()

def loadPlugin_clicked_cb(button):
	view = widgets.get_widget("pluginView")
	store = view.get_model()

	path = view.get_cursor()[0]
	if not path:
		# TODO: what about informing the user that there is no row active
		return

	logging.info("loading plugin '%s'..." % (store[path][COL_NAME]))

	if pinterface.load(store[path][COL_NAME]):
		store.set(store.get_iter(path), COL_LOADED, True)

def unloadPlugin_clicked_cb(button):
	view = widgets.get_widget("pluginView")
	store = view.get_model()

	path = view.get_cursor()[0]
	if not path:
		# TODO: see todo in loadPlugin_clicked_cb
		return

	logging.info("unloading plugin '%s'..." % (store[path][COL_NAME]))

	if pinterface.unload(store[path][COL_NAME]):
		store.set(store.get_iter(path), COL_LOADED, False)

def configureButton_clicked_cb(button):
	""" build and show configuration dialog for the currently
		selected plugin
	"""

	def dialog_response_cb(dialog, rID):
		""" apply the values and close the configuration dialog """
		cSection = pinterface.get_plugin_config_section(plugin_name)
		config.create_section(cSection)

		for (key, value) in dialog.map.items():
			logging.debug("DRCB: Result: %s -> %s" % (key, str(value)))
			config.set(cSection, key, str(value))

		dialog.destroy()

	pluginView = widgets.get_widget("pluginView")
	path = pluginView.get_cursor()[0]

	try:
		options = pinterface.get_options(
			pluginView.get_model()[path][COL_NAME])
	except IndexError:
		return

	plugin_name = pluginView.get_model()[path][COL_NAME]
	cSection = pinterface.get_plugin_config_section(plugin_name)

	dialog = gtk.Dialog(
		title = _("Configure %(name)s" % {"name": plugin_name}),
		buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
	dialog.connect("response", dialog_response_cb)

	table = gtk.Table(rows = len(options), columns = 2)
	table.set_property("column-spacing", 12)

	dataMap = {} # config_key : value
	rowCount = 0

	for (opt, label, type, value) in options:

		wLabel = gtk.Label(label+": ")
		wLabel.set_property("xalign", 0)

		widget = None

		cValue = config.get(cSection, opt) or value
		dataMap[opt] = cValue or value

		if type == psushi.TYPE_STRING:
			# Simple text entry
			widget = gtk.Entry()
			widget.set_text(cValue)

			widget.connect("changed",
				lambda w,f,o: f(o,w.get_text()),
				dataMap.__setitem__, opt)

		elif type == psushi.TYPE_PASSWORD:
			# Hidden char. entry
			widget = gtk.Entry()
			widget.set_text(cValue)
			widget.set_property("visibility", False)

			widget.connect("changed",
				lambda w,f,o: f(o, w.get_text()),
				dataMap.__setitem__, opt)

		elif type == psushi.TYPE_NUMBER:
			# Number entry field
			widget = gtk.SpinButton()
			widget.set_range(-99999,99999)
			widget.set_increments(1, 5)
			widget.set_value(int(cValue))

			widget.connect("value-changed",
				lambda w,f,o: f(o, w.get_value()),
				dataMap.__setitem__, opt)

		elif type == psushi.TYPE_BOOL:
			# Check button for boolean values
			widget = gtk.CheckButton()
			if type(value) == bool:
				widget.set_active(cValue)
			else:
				widgets.set_active(cValue.lower() != "false")

			widget.connect("toggle",
				lambda w,f,o: f(o, w.get_active()),
				dataMap.__setitem__, opt)

		elif type == psushi.TYPE_CHOICE:
			# Multiple values. Stored as [0] = key and [1] = value
			wModel = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
			widget = gtk.ComboBox(wModel)

			widget.connect("changed",
				lambda w,f,o: f(o, w.get_active() >= 0 \
				and w.get_model()[w.get_active()][1] or ""),
				dataMap.__setitem__, opt)

			wRenderer = gtk.CellRendererText()
			widget.pack_start(wRenderer, True)
			widget.add_attribute(wRenderer, "text", 0)

			for (key, val) in value:
				wModel.append(row = (key, val))

			# this is tricky, if there's a saved value,
			# find the matching value (second field!)
			# and set the index to that position.
			if cValue and cValue != value:
				i = 0
				for row in wModel:
					if row[1] == cValue:
						break
					i+=1
				widget.set_active(i)
			else:
				widget.set_active(0)

		else:
			raise TypeError, "Wrong type given: %d" % (type)


		table.attach(wLabel, 0, 1, rowCount, rowCount+1)
		table.attach(widget, 1, 2, rowCount, rowCount+1)

		rowCount += 1

	dialog.plugin_name = plugin_name
	dialog.map = dataMap

	# put another vbox arround it because
	# d.vbox.set_property("border-width",..) does not work...
	vbox = gtk.VBox()
	vbox.set_property("border-width", 12)
	vbox.pack_start(table)
	dialog.vbox.pack_start(vbox)

	dialog.show_all()

def cellRendererToggle_toggled_cb(renderer, path, pluginView):
	store = pluginView.get_model()

	iter = store.get_iter(path)
	value = not store.get_value(iter, COL_AUTOLOAD)
	store.set(iter, COL_AUTOLOAD, value)

	list = config.get("autoload_plugins").items()
	name = store[path][COL_NAME]

	if not value:
		i = [i for (i,v) in list if v == name]
		if i:
			i = i[0]
		else:
			return
		config.unset("autoload_plugins", str(i))
	else:
		# activated
		config.set("autoload_plugins", str(len(list)+1), name)

def pluginView_button_press_event_cb(pluginView, event):
	""" activate the configure button if the selected plugin
		supports configuration
	"""

	if event.button == 1:
		# left click

		try:
			path = pluginView.get_path_at_pos(int(event.x),int(event.y))[0]
			pluginName = pluginView.get_model()[path][COL_NAME]

		except IndexError:
			return # no plugin selected
		except TypeError:
			return # s.a.a.

		options = pinterface.get_options(pluginName)

		if options:
			widgets.get_widget("configureButton").set_sensitive(True)
		else:
			widgets.get_widget("configureButton").set_sensitive(False)

def loadPluginList():
	view = widgets.get_widget("pluginView")

	view.get_model().clear()

	paths = config.get_list("tekka", "plugin_dirs", [])

	if not paths:
		logging.error("loadPluginList: no plugin paths!")
		return False

	list = config.get("autoload_plugins", default={}).values()

	for path in paths:
		try:
			for item in os.listdir(path):

				if item[-3:] != ".py":
					continue

				# we got a module here

				loaded = pinterface.is_loaded(item)

				try:
					i = list.index(item)
				except ValueError:
					autoload = False
				else:
					autoload = True

				info = pinterface.get_info(item)

				if not info:
					logging.debug(
						"loadPluginList: no info for plugin '%s'" % (info))
					version = "N/A"
					desc = "N/A"
					author = "N/A"
				else:
					desc, version, author = info

				view.get_model().append(
					(loaded,
					autoload,
					item,
					os.path.join(path,item),
					version,
					desc,
					author))
		except OSError:
			continue

	return True

def setup():
	global widgets

	path = config.get("gladefiles","dialogs") + "plugins.glade"
	widgets = gtk.glade.XML(path)

	sigdic = {
		"loadButton_clicked_cb" : loadPlugin_clicked_cb,
		"unloadButton_clicked_cb" : unloadPlugin_clicked_cb,
		"configureButton_clicked_cb": configureButton_clicked_cb,
		"pluginView_button_press_event_cb": pluginView_button_press_event_cb
	}

	widgets.signal_autoconnect(sigdic)

	pluginView = widgets.get_widget("pluginView")
	model = gtk.ListStore(
		TYPE_BOOLEAN, # chkbutton
		TYPE_BOOLEAN, # chkbutton
		str, # name
		str, # path
		str, # version
		str, # description
		str) # author
	pluginView.set_model(model)

	# isLoaded column
	renderer = gtk.CellRendererToggle()
	renderer.set_data("column", 0)
	column = gtk.TreeViewColumn("Loaded", renderer, active=0)
	column.set_resizable(True)
	pluginView.append_column(column)

	c = 1
	for name in ("Autoload","Name","Path","Version","Description", "Author"):
		if c == 1:
			renderer = gtk.CellRendererToggle()
			renderer.set_data("column", c)
			renderer.connect("toggled", cellRendererToggle_toggled_cb, pluginView)
			column = gtk.TreeViewColumn(name, renderer, active=c)
		else:
			renderer = gtk.CellRendererText()
			column = gtk.TreeViewColumn(name, renderer, text=c)
		column.set_resizable(True)
		column.set_fixed_width(80)
		pluginView.append_column(column)
		c+=1

	loadPluginList()
