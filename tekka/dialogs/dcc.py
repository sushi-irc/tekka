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
import glib
import gobject
import dbus
import logging
import pango
from gobject import TYPE_UINT64
from gettext import gettext as _
import traceback

from .. import config
from ..com import parse_from, sushi
from .. import gui
from ..helper.dcc import s_incoming

widgets = None

(COL_STATUS,
 COL_ID,
 COL_SERVER,
 COL_PARTNER,
 COL_FILE,
 COL_SIZE,
 COL_PROGRESS,
 COL_SPEED) = range(8)

# TODO: mark status for every row

class DCCWatcher(object):

	def __init__(self):
		self.timer_id = glib.timeout_add(1000, self._refresh_sends)

		self._init_cache()

	def stop(self):
		""" stop watching for dcc sends periodically """
		gobject.source_remove(self.timer_id)

	def refresh(self):
		""" manually refresh the list by calling this method """
		self._refresh_sends()

	def _init_cache(self):
		self.last_sends = []
		self.row_id_map = {}

	def _refresh_sends(self):
		sends = sushi.dcc_sends()

		if (sends == None and not sushi.connected) or len(sends) == 0:
			return

		view = widgets.get_object("transferView")
		store = view.get_model()

		# all ids
		act_sends = sends[0]

		to_remove = set(self.last_sends) - set(act_sends)
		to_update = set(act_sends) - to_remove

		for i in range(len(sends[0])):
			id, server, sender, filename, size, progress, speed, status = \
			[sends[n][i] for n in range(len(sends))]

			if id in to_update:
				if self.row_id_map.has_key(id):
					# update existing entry
					iter = self.row_id_map[id].iter

					store.set(iter,
						COL_STATUS, status,
						COL_SIZE, size,
						COL_PROGRESS, get_progress(progress, size),
						COL_SPEED, speed)
				else:
					# add new entry

					if not config.get_bool("dcc", "show_ident_in_dialog"):
						sender = parse_from(sender)[0]

					iter = store.append(row = (
						status, id, server,
						sender, filename,
						size, get_progress(progress, size),
						speed))

					self.row_id_map[id] = store[store.get_path(iter)]

		for id in to_remove:
			if self.row_id_map.has_key(id):
				store.remove(self.row_id_map[id].iter)

		self.last_sends = act_sends

		return True


def get_progress(p, s):
	return int(float(p)/s*100)

def cancel_transfer(transferID, watcher):
	sushi.dcc_send_remove(transferID)
	watcher.refresh()

def get_selected_transfer_id():
	view = widgets.get_object("transferView")
	store = view.get_model()
	cursor = view.get_cursor()

	try:
		id = dbus.UInt64(store[cursor[0]][COL_ID])
	except:
		return None
	else:
		return id

def dialog_response_cb(dialog, id, watcher):
	if id == 333: # FIXME:  replace this with a meaningful ID
				  # FIXME:: or connect to the button directly
		# remove was clicked
		def ask_are_you_sure():
			# ask if the user is sure about removing the transfer

			def dialog_reponse_cb(dialog, id, transferID):
				if id == gtk.RESPONSE_YES:
					# yes, remove it!
					cancel_transfer(transferID, watcher)
				dialog.destroy()

			transferID = get_selected_transfer_id()

			if None == transferID:
				gui.mgmt.show_error_dialog(
					title = _("No transfer selected!"),
					message = _("You must select a transfer to remove it."))

			else:
				d = gui.builder.question_dialog(
					title = _("Remove file transfer?"),
					message = _("Are you sure you want to remove the "
						"file transfer %(id)d?" % {
							"id": transferID }))
				d.connect("response", dialog_reponse_cb, transferID)
				d.show()

		ask_are_you_sure()

	else:
		global widgets

		watcher.stop()
		dialog.destroy()

		widgets = None

def run():
	dialog = widgets.get_object("DCCDialog")

	if dialog.get_property("visible"):
		return

	watcher = DCCWatcher()

	dialog.connect("response", dialog_response_cb, watcher)
	dialog.show()

def create_list_model():
	# status | id | server | sender | filename | size | progress | speed
	return gtk.ListStore(TYPE_UINT64, TYPE_UINT64, str, str, str, TYPE_UINT64, TYPE_UINT64, str)

def setup():
	global widgets

	if widgets != None:
		return

	widgets = gui.builder.load_dialog("dcc")

	transferView = widgets.get_object("transferView")
	transferView.set_model(create_list_model())

	# add direction icon column
	def type_symbol_render_cb(column, renderer, model, iter):
		status = model.get(iter, COL_STATUS)
		if status:
			if status[0] & s_incoming:
				# incoming
				renderer.set_property("stock-id", gtk.STOCK_GO_DOWN)
			else:
				# outgoing
				renderer.set_property("stock-id", gtk.STOCK_GO_UP)

	renderer = gtk.CellRendererPixbuf()
	column = gtk.TreeViewColumn("", renderer)
	column.set_cell_data_func(renderer, type_symbol_render_cb)
	transferView.append_column(column)

	c = 1
	for name in (_("ID"), _("Server"), _("Partner"), _("Filename"), _("Size")):
		column = gtk.TreeViewColumn(name, gtk.CellRendererText(), text = c)
		column.set_resizable(True)
		transferView.append_column(column)
		c += 1

	partner_col = transferView.get_column(COL_PARTNER)
	partner_col.set_expand(True)
	partner_col.get_cell_renderers()[0].set_property("ellipsize", pango.ELLIPSIZE_END)

	# progress column
	renderer = gtk.CellRendererProgress()
	column = gtk.TreeViewColumn(_("Progress"), renderer, value = c)
	column.set_resizable(True)
	transferView.append_column(column)
	c+= 1

	# speed column
	column = gtk.TreeViewColumn(_("Speed"), gtk.CellRendererText(), text = c)
	column.set_resizable(True)
	transferView.append_column(column)
