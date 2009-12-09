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
from gettext import gettext as _

import signals
import helper.dcc
from com import sushi
from lib.inline_dialog import InlineDialog

class DCCDialog(InlineDialog):

	"""
	[ICON] Incoming file transfer from %s: %s. [Accept]
	                                           [Deny]
	       [ Dest. Dir]                        [Cancel]
	"""

	def __init__(self, id, nick, filename, size, resumable):
		InlineDialog.__init__(self,
			buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK,
						gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
						gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE),
			icon = gtk.STOCK_DIALOG_INFO)

		self.transfer_id = id
		self.table = gtk.Table(rows = 3, columns = 1)

		self.label = gtk.Label(None)
		self.label.set_property("xalign", 0.0)
		self.label.set_markup(
				"<b>"+_("Incoming file transfer")+"\n</b>"+
				_("Sender: ”%(nick)s”\n"
				  "Filename: “%(filename)s“\n"
				  "File size: %(bytes)d bytes"
				  "%(resumable)s" % \
				{ "nick": nick,
				  "filename": filename,
				  "bytes": size,
				  "resumable": (resumable and
				  		_("\nIf you don't choose another destination, "
						  "this file will be resumed.") or "")
				}))
		self.table.attach(self.label, 0, 1, 0, 2)

		self.dest_checkbox = gtk.CheckButton()
		self.dest_checkbox.set_label(_("Save to the default directory"))
		self.dest_checkbox.set_active(True)
		self.table.attach(self.dest_checkbox, 0, 1, 2, 3)

		self.vbox.add(self.table)

		signals.connect_signal("dcc_send", self.dcc_send_cb)

	def dcc_send_cb(self, time, id, server, sender, filename, size,
	progress, speed, status):
		def file_dialog_response_cb(dialog, id, dcc_id):
			sushi.dcc_send_set(dcc_id, "directory",
				dialog.get_current_folder())
			dialog.destroy()

		def ask_for_directory():
			file_dialog = gtk.FileChooserDialog(
				title="Select a directory to save in...",
				buttons=(gtk.STOCK_CANCEL,1,gtk.STOCK_OK,2))

			file_dialog.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
			file_dialog.set_current_folder(
				sushi.dcc_send_get(id, "directory"))

			file_dialog.connect("response", file_dialog_response_cb, id)
			file_dialog.show_all()

		if (not self.dest_checkbox.get_active()
		and id == self.transfer_id
		and status & helper.dcc.s_running):
			ask_for_directory()

	def show(self):
		if sushi.remote:
			self.dest_checkbox.set_sensitive(False)
		InlineDialog.show(self)

	def response(self, id):
		InlineDialog.response(self, id)
