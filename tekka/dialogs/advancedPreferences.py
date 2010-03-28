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

import gtk
import gobject
import pango

from .. import gui
from .. import config

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
	configView = widgets.get_object("configView")
	configStore = widgets.get_object("pref_store")

	for category in ("tekka","colors","chatting","dcc","colors"):
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

def configValueEdited(renderer, path, newText):
	model = widgets.get_object("configView").get_model()
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

	widgets = gui.builder.load_dialog("advancedPreferences")

	configView = widgets.get_object("configView")

	widgets.get_object("value_renderer").connect("edited",
			configValueEdited)
	widgets.get_object("value_column").set_cell_data_func(
			widgets.get_object("value_renderer"),
			renderValue)
	widgets.get_object("option_column").set_cell_data_func(
			widgets.get_object("option_renderer"),
			renderOption)


def run():
	dialog = widgets.get_object("advancedPreferences")

	fillConfigView()

	dialog.run()
	dialog.destroy()
