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
import os
import logging

from gettext import gettext as _

from ..gui import builder
from ..gui import mgmt
from .. import plugins as pinterface
from .. import config
from ..lib import plugin_config_dialog

widgets = None

(COL_LOADED,
 COL_AUTOLOAD,
 COL_NAME,
 COL_PATH,
 COL_VERSION,
 COL_DESC,
 COL_AUTHOR) = range(7)


def run():
	""" show the dialog """

	def dialog_response_cb(dialog, response_id):
		if response_id != 0:
			dialog.destroy()

	dialog = widgets.get_object("plugins")

	main_window = mgmt.widgets.get_object("main_window")
	dialog.set_transient_for(main_window)

	dialog.connect("response", dialog_response_cb)
	dialog.show_all()


def update_button_sensitivity(loaded):
	widgets.get_object("unloadButton").set_sensitive(loaded)
	widgets.get_object("loadButton").set_sensitive(not loaded)


def loadPlugin_clicked_cb(button):
	""" load active plugin.

		on success:
		- set loaded flag in treeview
		- update button states
	"""

	view = widgets.get_object("pluginView")
	store = view.get_model()

	path = view.get_cursor()[0]
	if not path:
		d = builder.information_dialog(
								_("No plugin selected."),
								_("You must select a plugin to load it."))
		d.connect("response", lambda w,i: w.destroy())
		d.show_all()
		return

	logging.info("loading plugin '%s'..." % (store[path][COL_NAME]))

	if pinterface.load(store[path][COL_NAME]):
		store.set(store.get_iter(path), COL_LOADED, True)
		update_button_sensitivity(loaded=True)


def unloadPlugin_clicked_cb(button):
	""" unload active plugin.

		on success:
		- set COL_LOADED in treeview False
		- update button states
	"""

	view = widgets.get_object("pluginView")
	store = view.get_model()

	path = view.get_cursor()[0]

	if not path:
		d = builder.information_dialog(
								_("No plugin selected."),
								_("You must select a plugin to unload it."))
		d.connect("response", lambda w,i: w.destroy())
		d.show_all()
		return

	logging.info("unloading plugin '%s'..." % (store[path][COL_NAME]))

	if pinterface.unload(store[path][COL_NAME]):
		store.set(store.get_iter(path), COL_LOADED, False)
		update_button_sensitivity(loaded=False)


def configureButton_clicked_cb(button):
	""" build and show configuration dialog for the currently
		selected plugin
	"""

	def dialog_response_cb(dialog, rID):
		""" apply the values and close the configuration dialog """

		dialog.save()
		dialog.destroy()

	pluginView = widgets.get_object("pluginView")
	path = pluginView.get_cursor()[0]

	plugin_name = pluginView.get_model()[path][COL_NAME]

	dialog = plugin_config_dialog.PluginConfigDialog(plugin_name)
	dialog.connect("response", dialog_response_cb)

	dialog.show_all()


def autoloadRenderer_toggled_cb(renderer, path):
	store = widgets.get_object("pluginStore")

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

		loaded = pluginView.get_model()[path][COL_LOADED]

		update_button_sensitivity(loaded)

		options,err = pinterface.get_options(pluginName)

		if err != None:
			logging.error(err)
			mgmt.show_inline_message(
				"Error in %s" % (pluginName),
				"The config of plugin %s is faulty: %s." % (
					pluginName, err),
				dtype="error")

		logging.debug(options)

		if options:
			widgets.get_object("configureButton").set_sensitive(True)
		else:
			widgets.get_object("configureButton").set_sensitive(False)


def loadPluginList():
	view = widgets.get_object("pluginView")

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
					list.index(item)
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

	widgets = builder.load_dialog("plugins")

	sigdic = {
		"loadButton_clicked_cb":
			loadPlugin_clicked_cb,
		"unloadButton_clicked_cb":
			unloadPlugin_clicked_cb,
		"configureButton_clicked_cb":
			configureButton_clicked_cb,
		"pluginView_button_press_event_cb":
			pluginView_button_press_event_cb,
		"autoloadRenderer_toggled_cb":
			autoloadRenderer_toggled_cb,
	}

	widgets.connect_signals(sigdic)

	loadPluginList()
