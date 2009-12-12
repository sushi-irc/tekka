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
import dbus
import logging
from gobject import TYPE_UINT64
from threading import Thread
from time import sleep
from gettext import gettext as _
import traceback

import config
from com import sushi
from lib import dialog_control
from helper.dcc import s_incoming

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

# TODO: accept/deny for incomings

class PollThread(Thread):

	def __init__(self):
		Thread.__init__(self)

		self._stop = True

		self.row_id_map = {}
		self.last_sends = []

	def run(self):
		Thread.run(self)

		while not self._stop:

			gtk.gdk.threads_enter()
			try:
				self.apply_dbus_sends()
			except BaseException as e:
				logging.error("Error in PollThread: %s\n%s" % (e, traceback.format_exc()))
			gtk.gdk.threads_leave()

			sleep(1)

	def start(self):
		self._stop = False
		Thread.start(self)

	def stop(self):
		self._stop = True

	def get_progress(self, p, s):
		return int(float(p)/s*100)

	def apply_dbus_sends(self):
		# FIXME: main gui freeze if main window is killed and dialog is still running

		sends = sushi.dcc_sends()

		if len(sends) == 0:
			return

		view = widgets.get_widget("transferView")
		store = view.get_model()

		act_sends = [n for n in sends[0]]

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
						COL_PROGRESS, self.get_progress(progress, size),
						COL_SPEED, speed)
				else:
					# add new entry
					iter = store.append(row = (
						status, id, server,
						sender, filename,
						size, self.get_progress(progress, size),
						speed))
					self.row_id_map[id] = store[store.get_path(iter)]

		for id in to_remove:
			if self.row_id_map.has_key(id):
				store.remove(self.row_id_map[id].iter)

		self.last_sends = act_sends

def cancel_focused_transfer(poll_thread):
	view = widgets.get_widget("transferView")
	store = view.get_model()

	cursor = view.get_cursor()

	if None == cursor:
		pass
	else:
		sushi.dcc_send_remove(dbus.UInt64(store[cursor[0]][COL_ID]))
		poll_thread.apply_dbus_sends()

def dialog_response_cb(dialog, id, poll_thread):
	if id == 333:
		# remove was clicked
		cancel_focused_transfer(poll_thread)

	else:
		poll_thread.stop()
		dialog.destroy()

def run():
	dialog = widgets.get_widget("DCCDialog")

	poll_thread = PollThread()
	poll_thread.start()

	dialog.connect("response", dialog_response_cb, poll_thread)
	dialog.show_all()

def create_list_model():
	# status | id | server | sender | filename | size | progress | speed
	return gtk.ListStore(TYPE_UINT64, TYPE_UINT64, str, str, str, TYPE_UINT64, TYPE_UINT64, str)

def setup():
	global widgets

	widgets = dialog_control.build_dialog("dcc")

	transferView = widgets.get_widget("transferView")
	transferView.set_model(create_list_model())

	# add direction icon column
	def type_symbol_render_cb(column, renderer, model, iter):
		status = model.get(iter, COL_STATUS)
		if status:
			if status[0] & s_incoming:
				# incoming
				image = gtk.Image()
				image.set_from_stock(gtk.STOCK_GO_DOWN, gtk.ICON_SIZE_BUTTON)
				renderer.set_property("pixbuf", image.get_property("pixbuf"))
			else:
				# outgoing
				image = gtk.Image()
				image.set_from_stock(gtk.STOCK_GO_UP, gtk.ICON_SIZE_BUTTON)
				renderer.set_property("pixbuf", image.get_property("pixbuf"))

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
