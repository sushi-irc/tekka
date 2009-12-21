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

""" dcc inline dialog.
	displayed on incoming dcc call
"""

import gtk
from gettext import gettext as _

import tekka.signals as signals
from tekka.com import sushi
from .inline_dialog import InlineDialog

class DCCDialog(InlineDialog):

	def __init__(self, id, nick, filename, size, resumable):
		InlineDialog.__init__(self,
			buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK,
						gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
						gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE),
			icon = gtk.STOCK_DIALOG_INFO)

		self.table = gtk.Table(rows = 3, columns = 2)

		self.transfer_id = id
		self.transfer_info = {
			"id": id,
			"nick": nick,
			"filename": filename,
			"size": size,
			"resumable": resumable,
			"original_directory": sushi.dcc_send_get(id, "directory")}

		self.label = gtk.Label(None)
		self._update_label()

		self.table.attach(self.label, 0, 2, 0, 2, xoptions = gtk.FILL)

		# Setup the destination chooser button
		self.destination_dialog = None
		self.destination_button = gtk.Button(_("Select destination"))
		self.destination_button.connect("clicked", self._destination_button_clicked_cb)
		self.table.attach(self.destination_button, 0, 1, 2, 3, xoptions = gtk.FILL)
		self.destination_button.set_property("border-width", 6)

		self.vbox.add(self.table)

	def _destination_button_clicked_cb(self, dialog):
		def create_file_dialog():
			def _file_dialog_response_cb(dialog, id):
				if id == gtk.RESPONSE_OK:
					# apply directory
					sushi.dcc_send_set(self.transfer_id, "directory", dialog.get_current_folder())
					self._update_label()

				self.destination_dialog = None
				dialog.destroy()

			d = gtk.FileChooserDialog(
				title = _("Select a destination to save the file"),
				action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
				buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))

			d.connect("response", _file_dialog_response_cb)
			self.destination_dialog = d

			return d

		if not self.destination_dialog:
			d = create_file_dialog()
			d.show_all()

	def _update_label(self):
		def resumable_str():
			if (self.transfer_info["resumable"]
			and sushi.dcc_send_get(self.transfer_id, "directory") \
			== self.transfer_info["original_directory"]):
				return _("\n<b>Info:</b> If you don't choose another "
						"destination, this file will be resumed.")
			else:
				return ""

		self.label.set_markup(
			"<b>"+_("Incoming file transfer")+"\n</b>"+
			_(	"Sender: ”%(nick)s”\n"
	  			"Filename: “%(filename)s“\n"
  				"File size: %(bytes)d bytes\n"
				"Destination: %(destination)s"
				"%(resumable)s" % \
			{
				"nick": self.transfer_info["nick"],
				"filename": self.transfer_info["filename"],
				"bytes": self.transfer_info["size"],
				"destination": sushi.dcc_send_get(self.transfer_id, "directory"),
				"resumable": resumable_str()
			}))

	def show(self):
		if sushi.remote:
			self.destination_button.set_sensitive(False)
		InlineDialog.show(self)

	def response(self, id):
		InlineDialog.response(self, id)
