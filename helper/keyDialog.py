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

class KeyDialog(gtk.Dialog):

	def __init__(self, server, channel):
		gtk.Dialog.__init__(
				self,
				title=_("Channel Key"),
				buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK,
						gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL),
				flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

		self.server = server
		self.channel = channel

		vbox = self.vbox # avoid refcount 0
		self.remove(self.vbox)

		self.hbox = gtk.HBox()

		self.image = gtk.Image()
		self.image.set_from_stock(gtk.STOCK_DIALOG_AUTHENTICATION,
				gtk.ICON_SIZE_DIALOG)

		self.hbox.add(self.image)

		self.label = gtk.Label(
				_("Enter the key for the channel %(channel)s." %\
				{ "channel": self.channel }))

		self.vbox.add(self.label)

		self.entry = gtk.Entry()
		self.entry.set_property("visibility", False)
		self.entry.connect("activate", self._entryActivated)

		self.vbox.add(self.entry)

		self.checkButton = gtk.CheckButton(_("Save key for channel"))

		self.vbox.add(self.checkButton)

		self.hbox.add(self.vbox)
		self.add(self.hbox)

		self.show_all()

	def run(self):
		key = com.sushi.server_get(self.server, self.channel, "key")
		self.entry.set_text(key)
		self.entry.set_position(len(key))

		res = gtk.Dialog.run(self)

		if res == gtk.RESPONSE_OK and self.checkButton.get_active():
			# save key for the channel
			com.sushi.server_set(self.server, self.channel,
					"key", self.entry.get_text())
		return res

	def _entryActivated(self, entry):
		self.response(gtk.RESPONSE_OK)
