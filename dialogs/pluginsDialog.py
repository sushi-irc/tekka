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
import tekka as plugins
import os
import config
from gobject import TYPE_BOOLEAN

widgets = None

(COL_LOADED,
COL_AUTOLOAD,
COL_NAME,
COL_PATH,
COL_VERSION,
COL_DESC) = range(6)

def run():
	dialog = widgets.get_widget("plugins")

	while True:
		result = dialog.run()
		if result in (gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT):
			dialog.destroy()
			break

def loadPlugin_clicked_cb(button):
	view = widgets.get_widget("pluginView")
	store = view.get_model()

	path = view.get_cursor()[0]
	if not path:
		print "No row activated!"
		return

	print "loading plugin '%s'..." % (store[path][COL_NAME])

	if plugins.loadPlugin(store[path][COL_NAME]):
		store.set(store.get_iter(path), COL_LOADED, True)
	else:
		# TODO: print error in msgbox
		pass

def unloadPlugin_clicked_cb(button):
	view = widgets.get_widget("pluginView")
	store = view.get_model()

	path = view.get_cursor()[0]
	if not path:
		print "No row activated!"
		return

	print "unloading plugin '%s'..." % (store[path][COL_NAME])
	if plugins.unloadPlugin(store[path][COL_NAME]):
		store.set(store.get_iter(path), COL_LOADED, False)

def cellRendererToggle_toggled_cb(renderer, path, pluginView):
	store = pluginView.get_model()

	iter = store.get_iter(path)
	value = not store.get_value(iter, COL_AUTOLOAD)
	store.set(iter, COL_AUTOLOAD, value)

	list = config.get("autoload_plugins").items()
	name = store[path][COL_NAME]

	if not value:
		i = [i for (i,v) in list if v == name]
		if i: i = i[0]
		else: return
		config.unset("autoload_plugins", str(i))
	else:
		# activated
		config.set("autoload_plugins", str(len(list)+1), name)

def loadPluginList():
	view = widgets.get_widget("pluginView")

	view.get_model().clear()

	# TODO:  replace this with "plugin_path",
	# TODO:: a string seperated by ':'.
	path = config.get("tekka", "plugin_dir")

	if not path:
		print "no plugin path!"
		return False

	list = config.get("autoload_plugins", default={}).values()

	try:
		for item in os.listdir(path):
			if item[-3:] == ".py":
				name = item[:-3]

				loaded = plugins.isLoaded(name)

				try:
					i = list.index(name)
				except ValueError:
					autoload = False
				else:
					autoload = True

				info = plugins.getInfo(name)
				if not info:
					print "no info for plugin '%s'" % name
					version = "N/A"
					desc = "N/A"
				else:
					desc,version = info

				view.get_model().append((loaded, autoload, name, path+"/"+item, version, desc))
	except OSError:
		return False

	return True

def setup():
	global widgets

	path = config.get("gladefiles","dialogs") + "plugins.glade"
	widgets = gtk.glade.XML(path)

	sigdic = {
		"loadButton_clicked_cb" : loadPlugin_clicked_cb,
		"unloadButton_clicked_cb" : unloadPlugin_clicked_cb
	}

	widgets.signal_autoconnect(sigdic)

	pluginView = widgets.get_widget("pluginView")
	model = gtk.ListStore(TYPE_BOOLEAN, TYPE_BOOLEAN, str, str, str, str)
		# chkbutton | chkbutton | channel | user | topic
	pluginView.set_model(model)

	# isLoaded column
	renderer = gtk.CellRendererToggle()
	renderer.set_data("column", 0)
	column = gtk.TreeViewColumn("Loaded", renderer, active=0)
	column.set_resizable(True)
	pluginView.append_column(column)

	c = 1
	for name in ("Autoload","Name","Path","Version","Description"):
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
