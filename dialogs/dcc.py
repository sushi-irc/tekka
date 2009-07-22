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
from gobject import TYPE_UINT64
from threading import Thread
from time import sleep
from gettext import gettext as _

import config
from com import sushi

widgets = None

# TODO: mark status for every row

# TODO: accept/deny for incomings

class PollThread(Thread):

	def __init__(self):
		Thread.__init__(self)

		self._stop = True

	def run(self):
		Thread.run(self)

		while not self._stop:

			gtk.gdk.threads_enter()
			print "refreshing!"
			try:
				apply_dbus_sends()
			except BaseException,e:
				print "-"*34, e, "-"*34
			gtk.gdk.threads_leave()

			sleep(1)

	def start(self):
		self._stop = False
		Thread.start(self)

	def stop(self):
		self._stop = True

def get_progress(p, s):
	return int(float(p)/s*100)

def apply_dbus_sends():
	# TODO: detection of removed entries
	# FIXME: main gui freeze if gui is killed and dialog is running
	sends = sushi.dcc_sends()
	view = widgets.get_widget("transferView")
	store = view.get_model()
	lost = []

	for i in range(len(sends[0])):
		# id, server, sender, filename, size, progress, speed, status
		id, server, sender, filename, size, progress, speed, status = \
			[sends[n][i] for n in range(len(sends))]
		found = False

		for row in store:
			if row[0] == id:
				# update values
				found = True

				store.set(row.iter,
					4, size,
					5, get_progress(progress, size),
					6, speed)
		if not found:
			# apply transfer
			store.append(row = (
					id, server,
					sender, filename,
					size, get_progress(progress, size),
					speed))

def cancel_focused_transfer():
	view = widgets.get_widget("transferView")
	store = view.get_model()

	cursor = view.get_cursor()

	if None == cursor:
		pass
	else:
		sushi.dcc_send_remove(dbus.UInt64(store[cursor[0]][0]))

def dialog_response_cb(dialog, id, poll_thread):
	if id == 333:
		# remove was clicked
		cancel_focused_transfer()

	else:
		poll_thread.stop()
		dialog.destroy()

def run():
	dialog = widgets.get_widget("DCCDialog")

	poll_thread = PollThread()
	poll_thread.start()

	dialog.connect("response", dialog_response_cb, poll_thread)
	dialog.show_all()

def setup():
	global widgets

	path = config.get("gladefiles","dialogs") + "dcc.glade"
	widgets = gtk.glade.XML(path)

	transferView = widgets.get_widget("transferView")
	model = gtk.ListStore(TYPE_UINT64, str, str, str, TYPE_UINT64, TYPE_UINT64, str)
		# id | server | sender | filename | size | progress | speed
	transferView.set_model(model)

	c = 0
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
