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
import com
from gettext import gettext as _
from lib.inline_dialog import InlineDialog

class KeyDialog(InlineDialog):

	def __init__(self, server, channel):
		InlineDialog.__init__(
				self, icon = gtk.STOCK_DIALOG_AUTHENTICATION,
				buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
					gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))

		self.server = server
		self.channel = channel

		self.sub_hbox = gtk.HBox()
		self.sub_vbox = gtk.VBox()

		self.label = gtk.Label(
				_("Enter the key for the channel %(channel)s." %\
				{ "channel": self.channel }))

		self.sub_vbox.add(self.label)

		self.entry = gtk.Entry()
		self.entry.set_property("visibility", False)
		self.entry.connect("activate", self._entryActivated)

		self.sub_vbox.add(self.entry)

		self.checkButton = gtk.CheckButton(_("Save key for channel"))

		self.sub_vbox.add(self.checkButton)

		self.sub_hbox.add(self.sub_vbox)
		self.vbox.add(self.sub_hbox)

		key = com.sushi.server_get(self.server, self.channel, "key")
		self.entry.set_text(key)
		self.entry.set_position(len(key))

	def response(self, id):
		if id == gtk.RESPONSE_OK and self.checkButton.get_active():
			# save key for the channel
			com.sushi.server_set(self.server, self.channel,
					"key", self.entry.get_text())

		InlineDialog.response(self, id)

	def _entryActivated(self, entry):
		self.response(gtk.RESPONSE_OK)
